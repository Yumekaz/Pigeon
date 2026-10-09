# Browser End-to-End Tests

The photo editor release gate launches an isolated, authentication-disabled
PIGEON server on port `7013` with a temporary SQLite database.

```bash
npm install
npm run test:photo-editor:install
npm run test:photo-editor
```

Set `PHOTO_EDITOR_E2E_PORT` to use another port. Failure screenshots and traces
are written to `test-results/photo-editor/`. The server uses the repository
`.venv` automatically; set `ODYSSEUS_TEST_PYTHON` to another Python executable
when using a different environment layout.

The harness reads the gallery/editor import versions from the shipped app and
panel registry. It must use those singleton modules, rather than importing a
second unversioned editor or adding retry query strings.

Stroke responsiveness measures 240 samples through the production browser
mouse-event handlers, with the five-second processing limit unchanged. It
records the measured processing time as an attachment and checks painting,
thumbnail updates, undo and redo. This separates processing from automation
round-trip overhead; ordinary interaction cases still use native browser input.
