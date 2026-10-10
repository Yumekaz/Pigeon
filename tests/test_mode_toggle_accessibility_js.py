import shutil
import subprocess

import pytest


def test_mode_restore_keeps_accessible_web_state_equal_to_request_permission():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js unavailable')
    script = r'''
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('static/app.js', 'utf8');
const start = source.indexOf('function applyModeToToggles(');
const end = source.indexOf('(function initModeToggle()', start);
assert(start >= 0 && end > start);
const button = { style:{}, attrs:{'aria-pressed':'true'},
  classList:{toggle(name,value){button.active=value;}},
  setAttribute(name,value){this.attrs[name]=value;} };
const checkbox = {checked:true};
const context = vm.createContext({
  MODE_TOOLS:[{btnId:'web',checkboxId:'permission',stateKey:'web'}],
  el:id=>id==='web'?button:checkbox,
  loadToolPref:(_,mode)=>mode==='chat',
});
vm.runInContext(source.slice(start,end),context);
for (const mode of ['agent','chat']) {
  context.applyModeToToggles(mode);
  assert.equal(button.attrs['aria-pressed'],String(checkbox.checked));
  assert.equal(button.active,checkbox.checked);
}
'''
    subprocess.run([node, '-e', script], check=True, capture_output=True, text=True)
