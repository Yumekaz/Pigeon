# PIGEON redesign validation

## Executed checks

The final combined regression run passed **135 tests**. Four separate snapshot-harness checks passed (inventory coverage, script blocking, timing/font stability, and cascade sensitivity). An isolated touch-brush paint/undo check passed. The wider editor run remained incomplete; a later batch recorded 15 passes, five failures, and 71 unexecuted cases after its failure limit.

| Check | Result |
| --- | --- |
| Focused frontend regressions: startup, streaming, composer, uploads, settings, themes, window clearance | 76 passed |
| Authentication markup, CSP, launcher, setup, theme and asset checks | 21 passed |
| Publication: brand asset hashes, dependency notices, fonts, print escaping, PWA metadata and cache activation | 8 passed |
| Generated research/search presentation and OAuth/source escaping | 38 passed |
| Action contrast across brand colors and boundary cases | 8 cases passed |
| Computed styles | Earlier result withdrawn: the saved values were unstyled; see CI correction below |

JavaScript syntax was checked in 244 module/inline-script cases with zero failures.

Counts are separate suite results and overlap; they are not summed into a unique-test total. The original style baseline and unsuccessful raw attempts are retained locally. The initial baseline was invalid and has been replaced with a styled capture that verifies stylesheet loading.

## Browser evidence

The live shell, expanded sidebar and rail, Settings, Calendar, Memory, Skills, Tasks, Library, document creation, Gallery, Cookbook, Notes, email setup state, and first-run authentication screen were opened. The landing page and getting-started navigation were inspected. Existing HTML IDs were preserved: 484 in the app and 17 in authentication.

Document creation opened the editor. A complete live editing/save cycle was not established in the unconfigured-model fixture; do not treat that as a verified save flow.

## Editor release gate remains incomplete

The complete editor suite is not green. Twenty failing cases were independently reproduced against the original frontend using the same corrected locators: six adjustment/effect cases, four mobile mask/group cases, four placed-image cases, three text/shape cases, a stroke-performance case, a healing/reopen case, and the layered core-workflow case. These include missing retained-state assertions and navigation/reopen races. No editor rendering or persistence algorithm was rewritten for the redesign.

Selected core interaction cases passed, and the gallery layout regression introduced by changed header spacing was corrected and verified. Stale shared-toolbar locators were redirected to the visible layer controls. Windows fixture cleanup now retains locked data and only removes owned generated temporary directories.

## Limits

Live model responses, provider switching against real services, agent execution, research generation, vector retrieval, email delivery, CalDAV synchronization, GPU serving, and credential-dependent integrations remain unverified. The preview has no configured model/email accounts or ChromaDB. Installed PWA appearance on physical devices and Firefox/WebKit were not tested. Chromium and the desktop browser supplied the rendered evidence.

Required attribution and notices were checked against the original files. Ten staged vendored artifacts retain their recorded hashes. Publication excludes runtime data, dependency environments, raw captures, and internal planning records. Initial source import preserves inherited whitespace; the new design files are checked separately.

## CI correction

Remote CI on `bec3feb` exposed 20 failed tests across four shards. A branding replacement had changed the internal `X-Odysseus-Run-Id` header; it is restored for streaming identity, Stop, and resume. Login asset paths now remain relative under reverse-proxy mounts. The app entry, every app stylesheet, and their service-worker entries share `pigeon2`; the service-worker cache is `pigeon-v3`.

The earlier computed-style baseline had unstyled browser defaults, so its reported design coverage is withdrawn. The harness now supplies frozen stylesheet sources on every capture and rejects any unloaded stylesheet. The replacement raw capture is retained locally; Linux CI also retains raw computed values to diagnose platform differences.

Public-document inventory checks now cover the published guides, rather than requiring internal migration/audit notes. Product-label assertions and the issue checker match PIGEON, while the checker still accepts the historical revision heading. The generated configuration reference and README authentication guidance are synchronized.

This private repository cannot use GitHub CodeQL without the required entitlement. At the owner's request, CodeQL is replaced by Semgrep Community Edition for first-party Python/JavaScript; the existing actionlint/zizmor workflow continues auditing Actions. Semgrep runs with metrics disabled and fails on ERROR-level findings or configuration/scanner errors. Findings remain downloadable in Actions artifacts. This is different analysis coverage, not a claim of CodeQL equivalence.

The corrected combined affected suite passed 119 tests locally. A separate cache/editor integration group passed 29 tests, and the missing-stylesheet rejection test passed. The first corrected Linux CI run passed the full computed-style comparison and streaming regressions; five remaining failures were cache-entry identity assertions, the cache namespace assertion, and an unpublished Outlook guide link. Those contracts and the public guide are now synchronized. Workflow output values pass through environment variables so strict Semgrep parsing can audit their shell scripts.
