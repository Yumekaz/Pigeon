# PIGEON feature validation

Historical report from October 9. See [hackathon readiness](PIGEON_HACKATHON_READINESS.md)
for the October 10–11 browser repair results, current usage snapshot and remaining gates.

Validated on October 9, 2026. The configured application paths below work in the tested environment. This report does not claim that unconfigured external integrations have been tested live.

## Results

| Area | Evidence | Result |
| --- | --- | --- |
| Chat, history and streaming | Real gpt-6-luna responses through the application and browser; authenticated local-provider integration | Pass |
| Agent document reads | Real gpt-6-luna native calls through the signed-in ownership gate; exact document content returned | Pass |
| Document writing assistance | Real Concise-menu prompt, exact-action approval/resume, two saved inline suggestions, unchanged source and successful completion | Pass |
| Documents and library | Create/edit/save/read/delete integration; repeated uploads remain listed and indexed | Pass |
| Retrieval | Real local ChromaDB and FastEmbed indexing; no paid embedding provider | Pass in isolated configured instance |
| Comparison | Blind comparison, separate responses, voting and reveal with local scripted models | Pass; live multi-provider comparison not tested |
| Notes, calendar and scheduled-task records | Authenticated create/read/update/delete and persistence checks | Pass; external synchronization and real scheduled model execution not tested |
| Memory | Add/list/search/delete with local vector service | Pass |
| Email and contacts interface | Fixture-backed email integration and frontend stream, stale-response, escaping and error tests | Pass; real IMAP/SMTP delivery not tested |
| Skills, settings and administration | Ownership, update, approval, settings-shell and interface regressions | Pass within tested coverage |
| Cookbook | Catalog/hardware-fit/state checks; a machine without NVIDIA tools reports its CPU-only state correctly | Pass; model download/serving not tested live |
| Gallery and image editor | Complete desktop/mobile Chromium suite: painting, masks, layers, groups, transforms, adjustments, clipboard, undo/redo, project recovery and exports | **108 passed** |
| Theme, density and responsive styles | Full styled snapshot matches digest `57a46fa4e0697cda`; contrast and frontend control tests | Pass |
| Local cost block | Real application Chat and Agent flows against an empty-budget fixture; no OpenAI request, retry or provider-outage mislabeling | Pass |

## Executed checks

- Complete editor suite: **108 passed**. The final mobile popover correction also passed **28 repeated selection/toolbar cases**.
- Authenticated integration suite: **19 passed**, including real persistence, a local scripted provider, document-tool approval/resume and no duplicate provider request after approved suggestions.
- Broad feature regression batch: **307 passed, 5 skipped**. Windows text encoding and file-URL harness defects were corrected; unavailable symlink privileges are explicitly skipped.
- Direct JavaScript feature suite: **209 passed, 1 skipped**.
- Durable Windows journal suite: **21 passed, 2 skipped**; includes independent threads/processes and restart recovery. The skipped directory-fsync checks require POSIX facilities.
- Windows file producers now preserve exact requested UTF-8/newline bytes, enabling content-hash readback verification across platforms: **143 passed, 1 skipped** across file effects, non-destructive-write and argument tests. Windows cannot create the quoted filename used by the skipped case.
- Final focused authorization, approval, transport, streaming, journal and cost checks: **212 passed, 2 skipped**. The final budget/PWA group passed **20 tests**. Counts overlap and must not be added into a unique-test total.
- Full computed-style capture matched the committed styled baseline. Original failed attempts and raw captures remain preserved locally and are excluded from publication.

## Repairs made during validation

Anonymous notification logging previously called protected routes and could trigger a page reload during editing. It now respects authenticated state without relaxing endpoint security. Editor fixes retain committed adjustment values, locked-layer move behavior, pixel-aligned marquee geometry, usable narrow-screen menus and accessible long draft lists. Completed brush strokes and imported projects schedule autosave, preventing recovery of earlier pixels or transforms.

The native-tool transport recognizes GPT-6 and uses Luna's supported reasoning/output-token settings. Writing-menu formatting instructions no longer masquerade as a new code artifact. Bound editor source reaches the actual provider request as untrusted data, not system authority. Approved saved suggestions finish with an accurate confirmation instead of provoking duplicate generations.

The action journal now uses binary descriptors on Windows so newline conversion cannot corrupt byte offsets. Windows byte-range locks serialize independent writers. Existing POSIX locking and its durability guarantees remain intact. Repeated personal-library uploads refresh the file inventory without duplicating owner-stamped vector indexing.

## Budget reconciliation and guard

The approved additional allowance remains **$0.05 total**. There is no fixed request-count limit and no reset endpoint. All live generations used **gpt-6-luna**.

The supplied usage export accounted for all 14 successful historical requests, including background calls. At the published Standard rates, those requests calculate to $0.00096109. The ledger conservatively holds $0.001057199 for the entire exported day, including the earlier separately authorized test and a possible 10% regional premium.

The guard obtains a model-specific input count for the immutable Responses payload, reserves the maximum input/cache-write and capped output cost atomically, and only then permits generation. Standard service tier is forced; hosted tools, image/audio input and other models are blocked. Streamed and buffered usage is captured. Retries and background generations are independent reservations. Missing usage, cancellation and ambiguous failures retain their maximum reservation. Unexpected usage above a reservation freezes the guard. Historical evidence is retained, and a missing/corrupt ledger fails closed.

At the end of live generation testing, the conservative amount accounted for or held was **$0.0166206865**, leaving **$0.0333793135** from the original $0.05. This includes retries, background generations and retained uncertainty holds; no allowance was reset or added.

The guard is a validation utility in `scripts/luna_cost_guard.py`, rather than a general billing system. Its ledger and the original export are private runtime artifacts. Rates must be reviewed before future use. The account's invoice remains authoritative; conservative ledger holds are not an assertion of exact billed spending. Pricing was checked against [official gpt-6-luna documentation](https://developers.openai.com/api/docs/models/gpt-6-luna).

## Remaining verification limits

Real IMAP/SMTP accounts, CalDAV synchronization, GPU model serving, hosted image generation/editing, voice hardware and credential-dependent MCP integrations were not supplied. Live web-search/deep-research completion was not established. Their local interface, ownership and error-handling coverage is reported separately from live service coverage.

The anonymous preview cannot perform operations that require an owned authenticated agent context. Those paths were verified in the separate signed-in instance; ownership checks were preserved.

A broader native-resource security batch originally recorded **128 passes, 55 failures and 2 skips** on Windows. Its raw failed attempt is preserved. The concrete filesystem newline/readback failures were subsequently corrected and verified separately. Trusted native-browser producer tests assume a Linux producer/Unix permissions and remain unsupported on this Windows host; that batch is not declared green. The standalone native browser broker fails closed on unsupported platforms; the app's built-in MCP browser is a separate path. Native-browser platform parity still requires separate compatibility work before that capability can be claimed fully verified.

Physical-device PWA installation, Firefox/WebKit and live service interoperability remain unverified. The public website, manifest and service-worker contracts retain their branding; the cache namespace is `pigeon-v5`. No GitHub checks were inspected or awaited for this publication, as requested.

Required licensing, acknowledgments and provenance remain preserved. API keys, account identifiers, databases, model downloads, raw traces and machine-specific runtime records are not published.
