<p align="center"><img src="assets/branding/pigeon-bird.png" alt="PIGEON" width="160"></p>
<h1 align="center">PIGEON</h1>
<p align="center">A quiet space for ambitious work.</p>
<p align="center">A self-hosted AI workspace for chat, agents, research, documents, and your daily tools.</p>
<p align="center"><a href="#getting-started">Getting started</a> · <a href="website/setup.md">Setup guide</a> · <a href="LICENSE">License</a></p>

![PIGEON workspace](assets/branding/pigeon-workspace.png)

## Your workspace, under your control

Bring local models and cloud providers into one place. Work across conversations, research, writing, and personal tools without handing over your workspace.

| Workspace | Capabilities |
| --- | --- |
| Chat and agents | Streaming conversations, model selection, tool approvals, MCP, skills, memory, voice, and uploads |
| Research and writing | Deep research, sources, document editing, version history, personal retrieval, and exports |
| Models | Side-by-side comparison, blind voting, hardware-aware recommendations, downloads, and serving |
| Daily tools | Email and contacts, notes, tasks, reminders, calendar, and gallery |
| Creative tools | Image editing with layers, masks, selections, adjustments, history, and exports |
| Personalization | PIGEON Midnight, additional themes, custom colors, font choices, density, and keyboard shortcuts |

## Getting started

```sh
git clone https://github.com/Yumekaz/Pigeon.git
cd Pigeon
```

On Windows, use the native launcher:

```powershell
powershell -ExecutionPolicy Bypass -File .\launch-windows.ps1
```

The launcher prepares dependencies and starts the application on the local address it prints. Follow the first-run account setup. Provider credentials, email accounts, and optional services are configured separately.

For other platforms and deployment options, see the [setup guide](website/setup.md). Container configurations retain compatible internal identifiers; release images are published separately from source changes.

## Development

The frontend uses HTML, CSS, and native JavaScript modules, served by FastAPI. The ordered legacy stylesheets are followed by `static/css/pigeon.css`; themes map shared presentation tokens onto existing preferences.

```sh
python -m pip install -r requirements-dev.txt
npm ci
npx playwright install chromium
python -m pytest
npm run test:photo-editor
```

Use an isolated data directory for tests. Windows runs should use UTF-8. See [test guidance](tests/README.md) for fixtures, focused runs, and external-service prerequisites.

## Security

Keep authentication enabled for deployed instances. Bind locally unless you deliberately configure network access. Keep credentials, databases, uploads, and runtime artifacts out of version control. See [SECURITY.md](SECURITY.md).

## License and acknowledgments

PIGEON is distributed under **AGPL-3.0-or-later**. Required source provenance, upstream acknowledgments, and third-party notices are preserved in [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md), [LICENSE](LICENSE), and [licenses/](licenses/).
