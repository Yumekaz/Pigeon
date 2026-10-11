# PIGEON hackathon readiness

Verification period: 9–11 October 2026. This report consolidates actual browser
walkthroughs, subsequent repairs, and automated regressions. It supersedes the
older reports' pending-issue status where a successful repair retest is listed.
It does not turn an inspected menu, a mocked test, or an upstream capability into
proof of a working external integration.

## Verdict

The core cloud-workspace demonstration has successful browser evidence: chat,
document creation and reading, simple workspace coding, indexed retrieval,
manual task execution, calendar editing, skills, web fetching and short research.
Haiku weather lookup and the final section-linked research retest also passed.

There is no evidence for the claim that every feature works on every machine.
Mail/synchronization services, local GPU serving, image/audio providers, some
specialist tools, and physical-device installation remain separate gates.
No heavyweight local LLM was downloaded for this verification.

## Feature catalogue and coverage

“Browser verified” means the particular described flow was actually exercised.
It does not cover all permutations of the feature family.

| Feature family | What PIGEON provides | Demonstrated behavior | Remaining scope |
| --- | --- | --- | --- |
| Chat | Cloud/local endpoints, streaming, Agent/Chat modes, stop, message actions, Markdown/code, context controls and model picker | Real Luna and Haiku replies; stop/cancellation in the earlier walkthrough; explicit model selection | All provider/model combinations, queue/retry permutations and every rich renderer |
| Conversations | History, session library, search, sorting/filtering, folders, archive/restore and bulk actions | Library filtering, archive/restore; repaired global search returns matching titles/messages and correct local times | Every bulk/folder/export branch |
| Nobody mode | Temporary conversations with memory/skill injection and saved history disabled | Real short reply without a matching saved library session | No forensic deletion or privacy guarantee inferred from this UI test |
| Prompts/personas/groups | Prompt injection, editable personas, sequential group replies and other interaction modes | Two sequential persona participants using Luna; prompt/persona controls inspected | All modes, persona expansion and unrestricted multi-model/teacher calls |
| Coding agent | Workspace selection; file read/write/edit/patch/search; shell/Python; plans and background work | Real standalone HTML written and read back on Luna and Haiku; completion accurately reports artifact evidence | Arbitrary projects, shell/Python execution, background jobs and patch combinations; no installations performed |
| Documents | Rich text, Markdown/code, HTML preview, AI suggestions, outline/find, versions, import/export and print | Manual edit/save/reload/preview/find, attachment import/export; agent HTML creation now preserves source/title and completes truthfully; approved saved-document list/read succeeds | Every formatting/language/export/print combination |
| Library and retrieval | Chats/documents/research/archive, uploads and indexed personal directories | Upload/attachment reading; indexed fictional reference answered correctly with a source card on Luna and Haiku; explicit personal-document toggle works | Every document type, large corpora and retrieval-quality evaluation |
| Memory | Manual memories/categories, search/edit/pin, import/export, extraction and injection | Add/search/edit/persistence and recall of a test memory | Bulk tidy, all imports/exports and automatic extraction across providers |
| Skills | Built-ins, reusable custom procedures, draft/publish, self-test, confidence/audit controls and settings | Custom draft/publish; live self-test scored 99; Edit after self-test and subsequent save work | Every skill and audit branch; Published and Verified remain distinct states |
| Deep Research | Rounds, search engines, sources, progress, categories, saved reports and follow-up chat | One-round sourced short Luna and Haiku reports; Haiku provider probe, section retrieval, persistence and Research → Chat opening | Long multi-round investigations, all search services and independent research-quality review |
| Web search/fetch | Application search service, public-page fetching and source-backed answers | Configured DuckDuckGo returns results; official Python page fetch succeeds with verified TLS | Rate limits, changing sites, blocked/logged-in pages and alternative providers requiring keys |
| Weather | Public place lookup and forecast through Open-Meteo | Haiku calls GET_WEATHER and returns Tokyo temperature, condition, observation time and source | Ambiguous place names, forecast variations and external-service availability |
| Comparison | Multiple panes, blind votes/reveal, synthesis, scores, shuffle and export | Blind comparison/vote/reveal; earlier scripted-model integration coverage | Broad live multi-provider comparison and every export/mobile configuration |
| Model Cookbook | Hardware-fit recommendations, catalogue, download/environment/serving controls and diagnostics | Catalogue and CPU-only hardware state; recommendation panels inspected | Actual download/serving/GPU/SSH operations on the friend's computer; fit estimates are not benchmarks |
| Notes | Text/checklists, tags/search, pin/archive/restore, reminders, drawing/photos/colors, goals/today | Plain/checklist create/save/reload/search, pin, completion and archive/restore | Every drawing/photo/bulk/reminder delivery branch |
| Calendar | Month/week/year/agenda, events, recurrence, classification, search and synchronization settings | Create/edit/reload; weekly series; repaired category persistence, duplicate-row display and asynchronous edit-form refresh | Actual reminder firing, CalDAV sync and email-linked event import |
| Tasks | Prompt/research/action jobs; schedules/events/webhooks; persona/model/output/chain; run/pause/history | Run Now completes a short AI task, output opens in chat; repaired Completed tab distinguishes successful output from aborted history | Future timer firing, triggers/chains/webhooks and real reminder delivery; QA timers disabled and test schedule paused |
| Email | Inbox/accounts/filter/search/tags, reader/attachments, drafts, AI replies, auto-reply and cleanup | Unconfigured setup guidance; unsent draft subject/body/Cc; earlier fixture-backed tests | Real IMAP receipt, SMTP sending, attachments and mailbox mutation; no real email sent |
| Contacts | CardDAV/import and email recipient resolution/autocomplete | Integration types inspected in email/settings | Actual import/sync/autocomplete; no separate standalone contacts page established |
| Gallery/editor | Photos/albums/projects, brush/text/shapes, selection/crop/transform, layers/masks/groups, effects/adjustments, history and export; AI editing | Browser brush, undo/redo, PNG export and draft recovery; earlier Chromium desktop/mobile editor suite: 108 passes | Every specialized action manually; hosted image generation, SAM/inpainting and other model/hardware-dependent actions |
| Settings/admin | Providers/defaults/fallbacks, search, integrations/MCP, mail/reminders, appearance, shortcuts, account/2FA and administration | Main sections inspected; retained authentication and ownership/approval regressions | Credential-dependent effects, new 2FA/setup, admin/destructive actions; protections were not weakened |
| Appearance/accessibility | PIGEON theme plus preserved themes/fonts/density, customization, keyboard controls and window docking/minimization | Light/PIGEON and density switching, narrow layout, notes docking; repaired mode-toggle accessibility state | Full assistive-technology/contrast audit, every drag/resize/snap state and real phones |
| PWA/login/public website | Manifest/icons/service-worker caching, installable browser UI, auth/setup/TOTP and public landing | Branding/static contracts and retained authenticated browser login | Fresh setup/TOTP, installed/offline/update flows on real devices and Firefox/WebKit |
| Media/specialist integrations | Voice/TTS/transcription, PDF/media/YouTube tools, APIs/webhooks, MCP, browser control, pipelines and model consultations | Catalogue inspected; some fixture/security coverage exists | Actual hardware/account/provider-dependent execution; arbitrary API or external-message actions excluded |

## Confirmed repairs and their evidence

Private browser evidence retains failed attempts alongside successful reruns.
The case numbers identify evidence checkpoints, not independent test totals.

| Problem | Repair outcome | Successful browser checkpoint |
| --- | --- | --- |
| HTML document source contained metadata and lost title tags; completion incorrectly said no artifact | Envelope-aware parsing and committed-document receipts preserve source and truthful completion | 02 |
| Editor list/read misrouted, stopped at listing, or failed after approval | Correct document read contract and discovery chain; approval continuation no longer rebinds identity before validating it | 33, Haiku |
| Simple coding produced a file but reported incomplete | Context trimming and evidence inference repaired; model version “5.5” is not treated as another output file | 25 Luna; 35 Haiku |
| Indexed recall was not demonstrated through the UI | Explicit retrieval controls and appropriate source context; generated reference is answered with a source card | 14 Luna; 36 Haiku |
| Manual tasks aborted during unrelated foreground activity | Passive notification requests do not interrupt manual work; completed results and output-session recovery corrected | 10–11, 22 |
| Calendar category disappeared; refresh closed edits and duplicated recurrence rows | Persist category, preserve active edits and deduplicate recurrence master display | 17–18 |
| Skills Edit threw a DOM error after self-test | Edit placement handles nested self-test controls; publication/verification labels separated | 05–08 |
| Search displayed UTC timestamps as local wall times | Shared UTC parser for database timestamps, excluding calendar wall times | 24 |
| Official-page fetch stalled on one resolved address | Fall back among validated public addresses while retaining TLS hostname, redirect validation and limits | 21 |
| Short research was forced into a long report and truncated | Explicit upper word bound suppresses long-template expansion | 27 |
| Haiku research/probes failed on a deprecated temperature field | Retry once without the field only after a specific provider rejection; retries remain accounted for | 38 confirms probe recovery |
| Mode switching left stale web accessibility state | aria-pressed now tracks the actual mode-restored checkbox state | 37 confirms enabled weather path |
| A section URL yielded top-of-page index text rather than its definition | Prioritize the observed semantic fragment section before bounded full-page excerpts; unknown anchors retain ordinary extraction | 39, Haiku |

Ownership, approval, public-address validation and output limits remain enforced.
Local budget errors are labeled as PIGEON guard blocks rather than provider
outages. Rejected or ambiguous provider calls retain conservative usage holds.

## Automated evidence

- Main repair regression batch: **1,645 passed**, four deprecation warnings,
  successful process exit. This predates the two subsequent provider/model
  compatibility commits and the latest section-extraction change.
- Latest provider compatibility, session model recovery, mode accessibility and
  minimized-document contracts: **18 passed**, four deprecation warnings,
  successful process exit.
- Section extraction, content parity, URL guards, byte caps, plaintext and
  validated-address fallback: **63 passed**, one deprecation warning,
  successful process exit.
- Earlier image-editor Chromium suite: **108 passed**. This is prior automated
  evidence, not a new exhaustive manual editor walkthrough.

These batches overlap. Do not add them into a purported unique test count.
Two sandboxed focused-test attempts stalled creating Windows asyncio's local
socket pair; their logs were preserved. The reviewed unrestricted mocked rerun
passed. No paid provider requests are used by these focused test suites.
Earlier native-browser security/platform tests were not all green on Windows;
native producer parity remains unverified. No GitHub checks were inspected or
awaited during this work.

## Usage controls

The OpenAI ledger retains its original history and one explicitly authorized
$0.05 extension: total ceiling **$0.10**, conservative used/held
**$0.0643092615**, remaining **$0.0356907385**. Its gateway remains stopped and
no OpenAI generation was sent in this final pass.

New live tests use only the configured Haiku 5.5 route. A separate durable
500,000-token QA allocation conservatively reserves input and output before
each request, counts retries/background calls, retains unknown-usage holds and
fails closed. It does not reset the OpenAI ledger. Exact coupon expiry and the
provider invoice are not verified; local holds are not an invoice claim.
Latest Haiku snapshot: **166,109 settled tokens**, **229,044 conservatively held
for unknown-usage requests**, **104,847 remaining** within the QA allocation;
the guard is not frozen. Rejected temperature attempts are included in the
unknown-usage holds, not assumed to be free or silently discarded.

## Suggested demonstration

1. Select the explicitly configured cloud model; start a short chat.
2. Select a disposable workspace and ask for a small standalone HTML file.
   Show the saved file and readback result; do not claim it was executed unless
   you actually open/run it.
3. Ask the agent to create an HTML editor document; approve the named action,
   then show its immediate preview and a saved-document read.
4. Enable Personal documents and ask a fact from the generated indexed sample;
   show its source card.
5. Show Notes, a recurring Calendar event with a saved category, a custom Skill
   and its self-test, and a short task using Run Now.
6. Enable web access after switching modes, then demonstrate a public weather
   lookup or one-round sourced research.
7. Show the editor's basic brush/export/recovery and the comparison controls.

Describe local GPU serving, real mail/sync, image generation and voice as
available integration capabilities awaiting your group's configured test,
rather than claiming they were demonstrated on this computer.

## Final browser research retest

Later device checkpoint: the user installed PIGEON through Chrome on Windows,
provided an installed-window screenshot with a working Haiku reply, and confirmed
Start-menu reopening and retained chat history. Windows online installation and
reopening are therefore user-verified. Phone installation and offline behavior
remain unverified; see the [hygiene report](PIGEON_CODEBASE_HYGIENE.md) for the
service-worker scope finding.

The identical one-round, 80-word fact-check query was repeated on Haiku.
The actual fetched content now begins with the requested function signature
and definition rather than the index. Its saved report gives a TRUE verdict,
quotes the newline default, cites the official page and opens through Research
→ Chat. The earlier unverified report remains as failed-attempt evidence.

The caveat says the newline default appears in the signature rather than the
prose. This is slightly imprecise: the prose also explains that output is
followed by `end`, while the explicit newline value is in the signature.
This is a model-analysis limitation, not a reason to claim perfect research
quality. The PASS covers section retrieval, the grounded core verdict and the
saved-report flow.
