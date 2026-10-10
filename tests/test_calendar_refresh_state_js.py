import shutil
import subprocess

import pytest


def test_refresh_waits_for_network_preserves_forms_and_hides_recurrence_master():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js unavailable')
    script = r'''
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('static/js/calendar.js', 'utf8');
const start = source.indexOf('function _filterPool(');
const end = source.indexOf('// Prefetch surrounding', start);
assert(start >= 0 && end > start);
(async () => {
  for (const editing of [false, true]) {
    let resolveFetch, renders = 0;
    const context = vm.createContext({
      fetch: () => new Promise(resolve => { resolveFetch = resolve; }),
      document: { querySelector: () => editing ? {} : null },
      console, API_BASE: '', _localDateOf: s => String(s).slice(0, 10),
      _saveCache() {}, _render() { renders++; },
    });
    vm.runInContext(`let _allEvents = {cached: {uid:'cached', dtstart:'2026-10-11',dtend:'2026-10-11'}};
      let _events = [], _fetchedRanges = [], _open = true;
      function _rangeIsCached() { return false; }
      ` + source.slice(start, end), context);
    let complete = false;
    const pending = context._fetchEvents('2026-10-11', '2026-10-12', true).then(() => { complete = true; });
    await Promise.resolve();
    assert.equal(complete, false, 'forced refresh returned before its response');
    resolveFetch({ok: true, json: async () => ({events: [
      {uid:'series',rrule:'FREQ=WEEKLY',dtstart:'2026-10-11',dtend:'2026-10-11'},
      {uid:'series::2026-10-11',is_recurrence:true,dtstart:'2026-10-11',dtend:'2026-10-11'},
      {uid:'independent',dtstart:'2026-10-11',dtend:'2026-10-11'},
    ]})});
    await pending;
    assert.equal(complete, true);
    assert.equal(renders, editing ? 0 : 1, 'refresh replaced an active edit form');
    const ids = vm.runInContext('_events.map(e => e.uid).sort().join(",")', context);
    assert.equal(ids, 'independent,series::2026-10-11');
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
'''
    result = subprocess.run([node, '-e', script], capture_output=True, text=True,
                            encoding='utf-8', timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
