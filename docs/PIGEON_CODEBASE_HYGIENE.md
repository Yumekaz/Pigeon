# PIGEON codebase hygiene and fresh-clone check

Checked 11 October 2026 against published main commit `3985888` on Windows,
using Python 3.12.1. This is a bounded source/startup audit, not a complete
security audit or proof of every integration on a new computer.

## Results

| Check | Observed result |
| --- | --- |
| Published source | Independently cloned Yumekaz/Pigeon main into a separate test folder; exact commit matched |
| Clone isolation | New virtual environment and new runtime data; no copied API keys, accounts, conversations or uploads |
| Python syntax | 1,803 tracked Python files parsed successfully |
| JavaScript syntax | 235 first-party application JavaScript files passed Node syntax checks |
| Runtime artifacts in source | No tracked virtual environments, node_modules, preview data, bytecode, databases, logs or actual .env files found by the targeted path check |
| Credential-pattern scan | No candidates for the checked private-key, AWS, GitHub-token and long sk-key patterns; this is not an exhaustive secret/history scan |
| Fresh Python environment | Installed requirements into a newly created venv; pip check reported no broken requirements |
| Actual startup | Existing Windows launcher created runtime directories/database/account and served the login page on an isolated custom port |
| Repeat startup | Same launcher reused the venv and started successfully again |
| Browser | New disposable account signed in; PIGEON shell loaded with no inherited model; note creation/save survived reload and reopening |
| Browser console | No error entries returned by the inspected fresh tab's error-console capture |
| Focused tests in fresh venv | 30 setup/startup/compose-contract tests passed, one deprecation warning, successful exit |
| Feature regressions in fresh venv | 190 document/evidence/calendar/task/skill/fetch/provider checks passed, seven deprecation warnings, successful exit; these are isolated tests, not new paid browser generations |
| AI/model downloads | No paid generations or heavyweight LLM downloads; embedding downloads disabled during the check |

The clone source remained unchanged. The setup-guide corrections accompany this
report; they were not needed to make the tested published app boot.

## Install conditions and failed attempts

The first install failed because this computer's HTTPS certificate chain was
not accepted by the initial pip environment. The next attempt used the previously
verified CA bundle, keeping TLS verification enabled, but encountered a malformed
compressed MCP package-index response. Both failed logs were preserved.

The successful attempt used that CA bundle and an official PyPI MCP 1.30.0 wheel
constraint with its published SHA256. That is a version allowed by `mcp<2`, not a
modified source package. Remaining dependencies resolved and installed normally
into the clean environment, using ordinary pip download/cache behavior.

These machine-specific test conditions are not presented as extra commands
every friend must use. A first install still needs internet access and a working
certificate/proxy configuration. No trusted-host/TLS bypass was used.

## Concrete findings

1. **Setup documentation drift — corrected.** The guide linked another
   repository's branch/contribution instructions, claimed automatic image
   publication even though the workflow is manually dispatched, and used the
   wrong default Docker host port. It now describes PIGEON main, its current
   source build/publishing arrangement and Docker port 7011. The Windows launcher
   remains port 7000 by default.
2. **Native companion-service requirements — clarified.** The native launcher
   does not start ChromaDB or SearXNG. The isolated app started despite the absent
   ChromaDB service and correctly logged vector retrieval/memory as degraded.
   Semantic retrieval needs ChromaDB plus embeddings; web search needs a
   configured provider. Mail/sync and model serving need their own services.
3. **Dependency reproducibility — remaining improvement.** Most Python
   requirements are unpinned. The launcher upgrades pip/checks packages on every
   run, and built-in browser MCP uses an npm `@latest` package. A future install
   can therefore differ from this one. A tested, platform-aware dependency
   constraint/release policy should be a separate cleanup milestone; blindly
   freezing optional packages from one machine is not a cross-platform lock.
4. **Large legacy modules/cascade — maintenance concern.** Agent orchestration,
   the document editor and layered CSS remain large. This is not evidence of a
   newly failing feature. Avoid wholesale splitting or cascade reordering before
   preserving explicit behavioral contracts and regression coverage.
5. **PWA offline scope — separate unresolved check.** Windows installation,
   online use and Start-menu reopening were verified by the user. The current
   worker is registered at `/static/sw.js` without an explicit root scope; its
   default scope is `/static/`, while the app starts at `/`. The inspected worker
   response has no root-scope permission header. Root-page offline control must
   be repaired/tested separately before claiming an offline shell. Installation
   success is not proof of offline behavior or offline AI.

## Simple Windows startup

Install Git and Python 3.11+ first; this check used Python 3.12. Then:

```powershell
git clone https://github.com/Yumekaz/Pigeon.git
cd Pigeon
powershell -ExecutionPolicy Bypass -File .\launch-windows.ps1
```

Choose your own admin credentials on the first interactive setup. Open
`http://127.0.0.1:7000`, then configure a provider/model server in Settings.
Do not use the old demo account or copy someone else's private data directory.

After the first install, the usual startup is one command from the Pigeon folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\launch-windows.ps1
```

Keep its terminal open. Ctrl+C stops the server. If port 7000 is occupied, add
`-Port 7001`; the launcher sets the internal port setting consistently too.
No npm frontend build, Docker or local LLM download is required to launch the
native cloud-workspace interface. Node/npm are needed for Node-based MCP tools
and browser tests. Configure optional services as described in the
[setup guide](../website/setup.md).

## Verification boundary

Fresh startup/account creation/persistence passed under the conditions above.
Cloud AI feature behavior was demonstrated in the earlier configured instance;
it was not re-billed in the empty clone. Local GPU serving, real email/CalDAV,
container builds (Docker is unavailable here), physical phones and full offline
behavior remain separate verification gates. See
[hackathon readiness](PIGEON_HACKATHON_READINESS.md) for the broader feature record.
