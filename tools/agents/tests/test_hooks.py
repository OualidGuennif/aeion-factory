#!/usr/bin/env python3
"""Exercise native adapter payloads against real guards and Git state, without model calls."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
loader = importlib.machinery.SourceFileLoader('factory_agent_hook', str(ROOT / 'tools/agents/hook.py'))
spec = importlib.util.spec_from_loader('factory_agent_hook', loader)
hook = importlib.util.module_from_spec(spec)
loader.exec_module(hook)


class HookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        shutil.copytree(ROOT / '.claude/hooks', self.root / '.claude/hooks')
        shutil.copytree(ROOT / 'tools/knowledge', self.root / 'tools/knowledge')
        shutil.copytree(ROOT / 'tools/repo-health', self.root / 'tools/repo-health')
        (self.root / 'knowledge/components').mkdir(parents=True)
        (self.root / 'work').mkdir()
        (self.root / 'work/current.md').write_text('# Current work\n')
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        self.git('config','user.name','Test')
        self.git('config','user.email','test@example.invalid')
        self.git('add','.')
        self.git('commit','-qm','initial')
        self.event = {'session_id':'native-fixture', 'hook_event_name':'PreToolUse',
                      'tool_name':'Bash','tool_input':{'command':'git status --short'}}

    def git(self,*args):
        return subprocess.run(['git',*args],cwd=self.root,capture_output=True,text=True,check=True).stdout.strip()

    def call(self,provider='codex',**changes):
        return hook.handle(self.root,provider,{**self.event,**changes})

    def test_secret_bash_is_denied_by_real_guard(self):
        for provider in ('codex','opencode'):
            with self.assertRaises(ValueError):
                self.call(provider,tool_input={'command':'cat .env'})
        self.assertEqual(self.call(),{})

    def test_native_patch_paths_include_deletions_and_renames(self):
        patch_text='*** Begin Patch\n*** Update File: safe.py\n*** Move to: .env\n@@\n-a\n+b\n*** End Patch\n'
        with self.assertRaises(ValueError):
            self.call(tool_name='apply_patch',tool_input={'command':patch_text})
        self.assertEqual(hook.edit_paths({'tool_name':'apply_patch','tool_input':{'patchText':'*** Delete File: old.py'}}),['old.py'])

    def test_opencode_camelcase_read_path_is_guarded(self):
        with self.assertRaises(ValueError):
            self.call('opencode',tool_name='Read',tool_input={'filePath':str(self.root/'.env')})
        self.assertEqual(self.call('opencode',tool_name='Read',tool_input={'filePath':'README.md'}),{})

    def test_crlf_patch_secret_paths_are_normalized_before_guarding(self):
        for kind in ('Add File', 'Update File', 'Delete File', 'Move to'):
            patch_text=f'*** Begin Patch\r\n*** {kind}: .env\r\n*** End Patch\r\n'
            with self.assertRaises(ValueError):
                self.call(tool_name='apply_patch',tool_input={'command':patch_text})

    def test_before_compaction_refuses_missing_and_changed_checkpoint(self):
        for provider in ('codex','opencode'):
            result=self.call(provider,hook_event_name='PreCompact')
            self.assertFalse(result['continue'])
            key=hook.key(provider,self.event)
            state_file=self.root/'.factory/context'/f'{key}.json'
            state=json.loads(state_file.read_text())
            handover=hook.budget.handover_path(self.root,key)
            state['checkpoint']={'tree':hook.budget.fingerprint(self.root),'handover':hook.budget.hashlib.sha256(handover.read_bytes()).hexdigest()}
            hook.budget.atomic(state_file,json.dumps(state))
            self.assertNotIn('continue',self.call(provider,hook_event_name='PreCompact'))
            (self.root/'changed.py').write_text('changed\n')
            self.assertFalse(self.call(provider,hook_event_name='PreCompact')['continue'])
            (self.root/'changed.py').unlink()

    def test_compaction_resets_receipt_but_keeps_recovery_pointer(self):
        self.call()
        key=hook.key('codex',self.event)
        state_file=self.root/'.factory/context'/f'{key}.json'
        state=json.loads(state_file.read_text());state['checkpoint']={'tree':'old'};state_file.write_text(json.dumps(state))
        result=self.call(hook_event_name='SessionStart',source='compact')
        self.assertIn(key,result['hookSpecificOutput']['additionalContext'])
        self.assertNotIn('checkpoint',json.loads(state_file.read_text()))

    def test_provider_and_native_sessions_are_isolated(self):
        self.assertNotEqual(hook.key('codex',self.event),hook.key('opencode',self.event))
        self.assertNotEqual(hook.key('codex',self.event),hook.key('codex',{'session_id':'other'}))

    def test_malformed_adapter_input_has_processable_denial(self):
        result=subprocess.run(['python3',str(ROOT/'tools/agents/hook.py'),'codex'],input='[]',capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertIn('refused',result.stderr)

    def test_oversized_pretool_payload_is_a_native_blocking_exit(self):
        event={**self.event,'tool_name':'apply_patch','tool_input':{'command':'*** Add File: .env\n'+'x'*(2*1024*1024)}}
        result=subprocess.run(['python3',str(ROOT/'tools/agents/hook.py'),'codex'],input=json.dumps(event),capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertNotIn('*** Add File',result.stderr)

    def test_missing_native_command_or_file_path_is_not_an_implicit_allow(self):
        for tool in ('Bash', 'Read', 'Edit', 'Write'):
            with self.assertRaises(ValueError):
                self.call(tool_name=tool,tool_input={})

    def test_native_range_fields_survive_shared_intake_guards(self):
        path=self.root/'many.log';path.write_text('line\n'*401)
        with self.assertRaises(ValueError):
            self.call(tool_name='Read',tool_input={'filePath':str(path)})
        self.assertEqual(self.call('opencode',tool_name='Read',tool_input={'path':str(path),'offset':350,'limit':20}),{})
        self.assertEqual(self.call(tool_name='Grep',tool_input={'path':str(path),'pattern':'line','head_limit':20}),{})

    def test_large_native_edits_are_not_treated_as_full_reads(self):
        path=self.root/'large.txt';path.write_text('x'*65537)
        for name,data in [('Edit',{'file_path':str(path)}),('Write',{'path':str(path)}),
                          ('apply_patch',{'command':f'*** Update File: {path}\n@@\n-a\n+b'})]:
            self.assertEqual(self.call(tool_name=name,tool_input=data),{})

    def test_managed_launch_aligns_pwd_with_the_actual_project_root(self):
        launcher=self.root/'tools/agents/run';launcher.parent.mkdir(parents=True)
        shutil.copy2(ROOT/'tools/agents/run',launcher)
        gate=self.root/'tools/architecture/refresh';gate.parent.mkdir(parents=True)
        gate.write_text('#!/bin/sh\nexit 0\n');gate.chmod(0o755)
        native=self.root/'bin/opencode';native.parent.mkdir()
        native.write_text(f'#!{hook.sys.executable}\nimport json,os,sys\nprint("2.1.4" if "--version" in sys.argv else json.dumps({{"cwd":os.getcwd(),"pwd":os.getenv("PWD")}}))\n')
        native.chmod(0o755)
        caller=self.root/'caller';caller.mkdir()
        result=subprocess.run([hook.sys.executable,str(launcher),'opencode'],cwd=caller,
                              env={'PATH':str(native.parent)+os.pathsep+os.defpath,'PWD':str(caller)},capture_output=True,text=True,check=True)
        self.assertEqual(json.loads(result.stdout),{'cwd':str(self.root),'pwd':str(self.root)})

    def test_read_only_loop_denies_writers_and_shell_composition(self):
        for command in ('tools/efficiency/bundle','tools/architecture/setup','git diff --output=x',
                        'gh issue list; touch unexpected'):
            with patch.dict(hook.subprocess.os.environ,{'FACTORY_LOOP_READ_ONLY':'1'}):
                with self.assertRaises(ValueError):
                    self.call(tool_input={'command':command})


if __name__=='__main__':unittest.main()
