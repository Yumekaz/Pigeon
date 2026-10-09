const { test, expect } = require('@playwright/test');
const { openBlankEditor, editorState } = require('./helpers.js');

test('anonymous toast preserves the active editor without protected log requests', async ({ page }) => {
  const logs = [];
  page.on('request', request => {
    if (request.url().includes('/api/tasks/notification-logs')) logs.push(request.method());
  });
  await openBlankEditor(page);
  const before = await editorState(page);
  await page.evaluate(async () => {
    const ui = await import('/static/js/ui.js?v=20260916largetoolscroll1');
    ui.showToast('Anonymous editor feedback');
    ui.showError('Anonymous test feedback');
  });
  await expect(page.locator('#toast')).toContainText('Anonymous test feedback');
  const after = await editorState(page);
  expect(after.layers).toEqual(before.layers);
  expect(logs).toEqual([]);
  await expect(page.locator('.ge-main-canvas')).toBeVisible();
});
