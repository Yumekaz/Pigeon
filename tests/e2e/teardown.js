const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');

module.exports = async () => {
  const dataDirectory = process.env.PHOTO_EDITOR_E2E_DATA_DIR;
  if (!dataDirectory || !fs.existsSync(dataDirectory)) return;
  const resolved = fs.realpathSync(dataDirectory);
  const tempRoot = fs.realpathSync(os.tmpdir());
  if (!resolved.toLowerCase().startsWith(tempRoot.toLowerCase() + path.sep)
      || !path.basename(resolved).startsWith('odysseus-photo-editor-e2e-')) {
    console.warn('Retained explicitly configured test data; automatic cleanup only owns generated temporary fixtures.');
    return;
  }
  try {
    fs.rmSync(dataDirectory, { recursive: true, force: true });
  } catch (error) {
    // Playwright stops its webServer after global teardown. On Windows the
    // still-open SQLite handle can prevent deletion; retain that test fixture.
    if (process.platform === 'win32' && ['EBUSY', 'EPERM'].includes(error.code)) {
      console.warn('Retained isolated test data because the server still holds a Windows file handle.');
      return;
    }
    throw error;
  }
};
