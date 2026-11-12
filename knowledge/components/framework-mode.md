---
type: Component
title: "Framework mode and the owner's settings"
description: "The owner's per-clone settings (the doc gate, the aeion-framework address): one reader, one owner-only switch, guarded from agents; framework mode is on only while an address is set."
status: draft
generated:
  by: aeion-template/4.0
  at: 2026-11-12
sources:
  - id: reader
    resource: ../../.claude/hooks/aeion_settings.py
    title: "The single settings reader"
  - id: switch
    resource: ../../tools/aeion-settings
    title: "The owner's switch"
  - id: tests
    resource: ../../tools/framework/tests/test_settings.py
    title: "The settings regressions"
---

# Framework mode and the owner's settings

## Intent

Let a project use aeion-framework's AxiomSpec without making it anyone else's burden. Framework mode
is off by default; the owner turns it on by giving the API address of the service that holds the
project's spec. The same per-clone settings carry the doc gate's mode. Agents read the settings and
never change them.

## Data sources

| Source | What is read | Owner | Freshness |
| --- | --- | --- | --- |
| `.aeion/settings.json` (ignored local state, with or without git) | `doc_gate`, `framework` | the owner, through `tools/aeion-settings` | each read |
| `AEION_FRAMEWORK_URL` | an address overriding the file for one process tree (CI, a container, a sandbox) | whoever starts the process | each read |
| `AEION_FRAMEWORK_TOKEN` | a gateway token, sent as `Authorization: Bearer`; never stored, never printed | the owner's environment | each request |
| `{address}/health/ready` | `version` of the running aeion-framework service | the service | at connect; at session start, cached ten minutes in `.aeion/framework-health.json` |
| committed code | `@req ID` annotations, the framework's convention | the project | each session start |

## Inputs

- `tools/aeion-settings` with no argument shows the settings and where each comes from.
- `tools/aeion-settings doc-gate enforce|warn|off`.
- `tools/aeion-settings framework [URL]`: without a URL it asks on a terminal, and refuses (exit 2)
  without one. An address is an `http://` or `https://` URL with a host, no credentials, no query or
  fragment, at most 2,048 characters.
- `tools/aeion-settings framework off`.

## Outputs

- `doc_gate()` answers `enforce`, `warn` or `off`; `enforce` when absent.
- `framework()` answers the address and its source, or none: no address means framework mode is off.
- Connect saves the address only after `/health/ready` answers 200 with a `version` from 1.1 up to,
  not including, 2.0 (tested 1.1.9), then prints the Claude Code MCP command for `{address}/mcp/`
  without running it. Refusals, exit 1, nothing saved: an invalid address, an unreachable service, a
  non-200 answer, an unsupported or missing version.
- Session start prints one line: `doc gate: <mode>; framework: off | on → <address> (aeion-framework
  <version>, ready) | on → <address>, but <why>`, and when the code carries `@req` IDs but no address
  is set, the hint to connect.
- The guards refuse an agent's write of `.aeion/settings.json` (Edit, Write, a redirection, a copy, an
  interpreter) and an agent's `tools/aeion-settings doc-gate|framework`; reading and showing stay open.

## Invariants

1. A settings file that cannot be read, or holds an unknown gate, fails closed: the gate enforces,
   framework mode is off, and session start names the problem.
2. An address is saved only from a ready service in the supported range; unknown is never ready.
3. The token never reaches a file or the output.
4. Only the owner changes a setting; the agent's guards refuse every write path they recognize.
5. CI never depends on framework mode.

| Invariant | Test |
| --- | --- |
| 1 | `tools/framework/tests/test_settings.py` (`test_an_unreadable_file_fails_closed`, `test_the_gate_takes_only_its_three_modes`); session-start cases in `.claude/hooks/test_hooks.py` |
| 2 | `test_settings.py` (`test_connect_refuses_and_saves_nothing`, `test_a_service_that_is_not_ready_or_too_old_or_absent`) against a local stand-in for `/health/ready` |
| 3 | `test_settings.py` (`test_the_token_travels_only_in_the_header`) |
| 4 | `.claude/hooks/test_hooks.py` (`bash deny settings write`, `path deny: … on .aeion/settings.json`) |
| 5 | the stand-in service is local; no test reaches the network |

## Determinism

Deterministic: the settings, the address check and the version range are plain functions of their
inputs. The readiness probe depends on the network and is bounded by a three-second timeout.

## Acceptance checks

- `tools/aeion-settings` prints `doc gate: enforce` and `framework: off` on a fresh clone.
- In an agent session, `tools/aeion-settings doc-gate off` and an Edit of `.aeion/settings.json` are refused.
- `tools/aeion-settings framework http://127.0.0.1:1` is refused as unreachable, and nothing is saved.

## Out of scope

- Storing the address in a committed file: committed `@req` annotations are the team's signal.
- Running or installing the aeion-framework service.
- Authentication: the service has none; a gateway in front of it owns that.
