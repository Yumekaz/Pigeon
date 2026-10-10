import shutil
import subprocess

import pytest


def test_completed_tab_contains_successful_outputs_only():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js unavailable')
    script = r'''
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('static/js/tasks.js', 'utf8');
const start = source.indexOf('function _isChatResultRun(');
const end = source.indexOf('\nasync function _renderCompletedView(', start);
assert(start >= 0 && end > start);
const context = vm.createContext({});
vm.runInContext(source.slice(start, end), context);
for (const status of ['aborted', 'failed', 'error', 'running', 'queued', 'skipped', '']) {
  assert.equal(context._isChatResultRun({status, kind:'llm', result:'Queued — waiting for PIGEON to be idle…'}), false);
}
for (const status of ['success', 'completed']) {
  assert.equal(context._isChatResultRun({status, kind:'llm', result:'Task demo works.'}), true);
  assert.equal(context._isChatResultRun({status, kind:'research', result:'Report.'}), true);
  assert.equal(context._isChatResultRun({status, kind:'llm', result:' '}), false);
}
'''
    subprocess.run([node, '-e', script], check=True, capture_output=True, text=True)
