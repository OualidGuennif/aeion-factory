// The application has no filesystem or PID access to this verifier container.
// Emit counts and source locations, never response bodies, test names or raw output.
import { run } from 'node:test';

const result = { tests: 0, passed: 0, failed: 0, skipped: 0, cancelled: 0, todo: 0,
  assertions: 0, test_errors: 0, errors: [] };
let summarySuccess = false;
const stream = run({ files: ['/opt/aeion-checker/acceptance.mjs'], isolation: 'process',
  concurrency: 1, timeout: 90000, execArgv: [],
  env: { PATH: '/usr/local/bin:/usr/bin:/bin', HOME: '/tmp',
    BASE_URL: 'http://127.0.0.1:8080', PLAYWRIGHT_BROWSERS_PATH: '/ms-playwright' } });
for await (const event of stream) {
  if (event.type === 'test:fail') {
    const error = event.data.details?.error;
    if (error?.failureType === 'subtestsFailed' || error?.failureType === 'cancelledByParent') continue;
    const isAssertion = error?.cause?.code === 'ERR_ASSERTION' || error?.code === 'ERR_ASSERTION';
    const rawName = String(error?.cause?.name || error?.name || '');
    const errorType = /^[A-Za-z][A-Za-z0-9_]{0,31}$/.test(rawName)
      ? rawName : (isAssertion ? 'AssertionError' : 'Error');
    if (isAssertion) result.assertions++;
    else result.test_errors++;
    if (result.errors.length < 20) result.errors.push({
      line: Number.isSafeInteger(event.data.line) ? event.data.line : 0,
      code: isAssertion ? 'assertion_failed' : 'test_error',
      error_type: errorType });
  }
  if (event.type === 'test:summary' && !event.data.file) {
    summarySuccess = event.data.success === true;
    const counts = event.data.counts;
    for (const key of ['tests', 'passed', 'failed', 'skipped', 'cancelled', 'todo']) {
      result[key] = Number.isSafeInteger(counts?.[key]) ? counts[key] : -1;
    }
  }
}
const passed = summarySuccess && result.tests > 0 && result.passed === result.tests
  && result.failed === 0 && result.skipped === 0 && result.cancelled === 0 && result.todo === 0
  && result.assertions === 0 && result.test_errors === 0;
process.stdout.write(JSON.stringify({ ...result, passed }) + '\n');
process.exitCode = passed ? 0 : 1;
