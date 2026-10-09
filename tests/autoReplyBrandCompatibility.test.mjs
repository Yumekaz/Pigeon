import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const source = readFileSync(new URL('../static/js/emailLibrary/settingsPage.js', import.meta.url), 'utf8').replace(/\r\n/g, '\n');
const start = source.indexOf('async function _findAutoReplyCalendarEventUids(');
const end = source.indexOf('async function _syncAutoReplyCalendarEventNow(', start);
assert.ok(start >= 0 && end > start, 'Production discovery function is present');
const discover = new Function('fetch', 'API_BASE', '_autoReplyDateValue', '_todayDateInputValue',
  source.slice(start, end) + ';return _findAutoReplyCalendarEventUids;');

test('auto-reply discovery reuses historical and PIGEON calendar entries for the account', async () => {
  const events = [
    { uid: 'legacy', description: 'Odysseus email auto reply - account:one' },
    { uid: 'current', description: 'PIGEON email auto reply - account:one' },
    { uid: 'other', description: 'PIGEON email auto reply - account:two' },
    { uid: 'manual', description: 'Away from work' },
  ];
  const fn = discover(async () => ({ ok: true, json: async () => ({ events }) }), '',
    value => value || '', () => '2026-10-09');
  assert.deepEqual(await fn({ start: '2026-10-09' }, 'one'), ['legacy', 'current']);
});
