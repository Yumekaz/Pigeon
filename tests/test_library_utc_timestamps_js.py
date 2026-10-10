import os
import shutil
import subprocess

import pytest


def test_library_ages_interpret_naive_record_times_as_utc():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js unavailable')
    script = r'''
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { utcTimestampDate } from './static/js/utcTimestamp.js';
assert.equal(utcTimestampDate('2026-10-10T05:30:00').toISOString(), '2026-10-10T05:30:00.000Z');
assert.equal(utcTimestampDate('2026-10-10 05:30:00').toISOString(), '2026-10-10T05:30:00.000Z');
assert.equal(utcTimestampDate('2026-10-10T11:00:00+05:30').toISOString(), '2026-10-10T05:30:00.000Z');
const source = fs.readFileSync('static/js/documentLibrary.js', 'utf8');
class Clock extends Date { static now() { return Date.parse('2026-10-10T05:30:00Z'); } }
const context = vm.createContext({ Date: Clock, utcTimestampDate });
const start = source.indexOf('function libraryRelativeTime(');
const end = source.indexOf('async function libraryFetch(', start);
vm.runInContext(source.slice(start, end), context);
assert.equal(context.libraryRelativeTime('2026-10-10T05:30:00'), 'just now');
assert.equal(context.libraryRelativeTime('2026-10-10T05:28:00'), '2m ago');
assert.equal(context.libraryRelativeTime('not a timestamp'), '');
const searchSource = fs.readFileSync('static/js/search-chat.js', 'utf8');
class SearchClock extends Date {
  constructor(...args) { super(...(args.length ? args : ['2026-10-10T11:10:00Z'])); }
}
const searchContext = vm.createContext({ Date: SearchClock, utcTimestampDate });
const searchStart = searchSource.indexOf('function formatTimestamp(');
const searchEnd = searchSource.indexOf('\nfunction renderResults(', searchStart);
vm.runInContext(searchSource.slice(searchStart, searchEnd), searchContext);
const localTime = new Date('2026-10-10T11:00:00Z').toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' });
assert.equal(searchContext.formatTimestamp('2026-10-10T11:00:00'), localTime);
assert.equal(searchContext.formatTimestamp('2026-10-10T16:30:00+05:30'), localTime);
assert.equal(searchContext.formatTimestamp('not a timestamp'), '');
'''
    result = subprocess.run([node, '--input-type=module', '-e', script], capture_output=True,
        text=True, encoding='utf-8', timeout=15, env={**os.environ, 'TZ': 'Asia/Kolkata'})
    assert result.returncode == 0, result.stdout + result.stderr
