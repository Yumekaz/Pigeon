import shutil
import subprocess

import pytest


def test_skill_edit_uses_the_markdown_parent_for_nested_result_layout():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js unavailable')
    script = r'''
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('static/js/skills.js', 'utf8');
const start = source.indexOf('function _toggleSkillEdit(');
const end = source.indexOf('\nasync function _saveSkillEdit(', start);
assert(start >= 0 && end > start);
for (const [nested, hasMarkdown] of [[false, true], [true, true], [true, false]]) {
  const editor = { addEventListener() {}, focus() { this.focused = true; } };
  const button = { textContent: 'Edit' };
  const actions = {};
  const host = { children: [], insertBefore(child, anchor) {
    if (anchor && !this.children.includes(anchor)) throw Error('NotFoundError');
    const i = anchor ? this.children.indexOf(anchor) : this.children.length;
    this.children.splice(i, 0, child);
  }};
  const pre = { style: {}, textContent: 'Procedure', parentElement: host, nextSibling: actions };
  actions.parentElement = host;
  host.children = hasMarkdown ? [pre, actions] : [actions];
  const preview = nested ? { children: [host], insertBefore: host.insertBefore } : host;
  preview.querySelector = selector => selector === '.skill-md-pre' ? (hasMarkdown ? pre : null)
    : selector === '.doclib-card-expanded-actions' ? actions : null;
  preview.querySelectorAll = () => [button];
  const card = { _md: 'Procedure', querySelector: () => preview };
  const context = vm.createContext({ document: { createElement: () => editor } });
  vm.runInContext(source.slice(start, end), context);
  context._toggleSkillEdit(card, 'qa');
  assert.deepEqual(host.children, hasMarkdown ? [pre, editor, actions] : [editor, actions]);
  assert.equal(editor.value, 'Procedure');
  assert.equal(editor.focused, true);
  if (hasMarkdown) assert.equal(pre.style.display, 'none');
  assert(button.innerHTML.includes('Save'));
}
'''
    result = subprocess.run([node, '-e', script], capture_output=True, text=True,
                            encoding='utf-8', timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
