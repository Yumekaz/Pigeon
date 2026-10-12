# PIGEON: teammate Windows setup and verification

This guide reproduces the CPU-compatible supporting setup used on Mihir's laptop. It uses the original checkpoint, not the experimental `pigeon_phase` repository. Application source stays unchanged. Installation requires internet; cloud models and public web search also require internet.

These commands were assembled from the working installation. The complete fresh-machine procedure below has **not yet been executed on a teammate's laptop**. Package consistency and local readiness are different from functional feature verification.

## 1. Prerequisites and clean checkout

Install Git, Python **3.12**, and Node.js **22**. Use a normal PowerShell terminal. Prefer a short folder outside OneDrive. Allow several GB of disk space for environments, browser binaries and models. Do not copy Mihir's data, API keys, `.env`, or virtual environments.

```powershell
git clone https://github.com/Yumekaz/Pigeon.git
cd Pigeon
git checkout --detach 8390cc0e32f457b4309d5aa0d65ae5cc16df7989
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install "chromadb-client==1.5.9" "fastembed==0.9.0" "faster-whisper==1.2.1" "rapidocr==3.9.2" "onnxruntime==1.31.0" "PyMuPDF==1.28.2" "markitdown[docx,pptx,xlsx,xls]==0.1.6" "ddgs==9.16.0" "psd-tools==1.24.0" "soundfile==0.14.0" "yt-dlp==2026.8.19"
.\.venv\Scripts\python.exe -m pip check
```

Stop and resolve dependency errors before continuing. The feature packages above match the working laptop; `requirements.txt` itself contains unpinned core dependencies, so this is not a complete frozen dependency lock. Save the actual installation record:

```powershell
.\.venv\Scripts\python.exe -m pip freeze > installed-app-versions.txt
```

Do **not** install all of `requirements-optional.txt` indiscriminately: it includes Kokoro/Torch. They are outside this CPU setup.

## 2. Install ChromaDB separately

ChromaDB is the background vector database. Its lightweight client belongs in the app environment; the full server belongs in a separate environment.

```powershell
py -3.12 -m venv .chroma-venv
.\.chroma-venv\Scripts\python.exe -m pip install --upgrade pip
.\.chroma-venv\Scripts\python.exe -m pip install "chromadb==1.5.9"
.\.chroma-venv\Scripts\python.exe -m pip check
.\.chroma-venv\Scripts\python.exe -m pip freeze > installed-chroma-versions.txt
```

## 3. FFmpeg and speech weights

Download a Windows essentials build from [Gyan's FFmpeg builds](https://www.gyan.dev/ffmpeg/builds/), verify its published checksum, and extract it. The working laptop used FFmpeg/FFprobe **9.0.2 essentials**. Add its `bin` folder to the application terminal's PATH, replacing the example path with the actual extracted location:

```powershell
$env:PATH = 'C:\Tools\ffmpeg\bin;' + $env:PATH
ffmpeg -version
ffprobe -version
```

Download and load only the small Whisper `base` speech model, on CPU:

```powershell
.\.venv\Scripts\python.exe -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8'); print('Whisper base ready')"
```

This proves model loading, not microphone/transcription accuracy. FastEmbed downloads its MiniLM embedding model on first initialization. Leave internet available for initial setup; do not enable offline flags before model downloads finish. OCR may also need its model assets on first use.

## 4. Start the two services

Keep **two terminals** open, both in the cloned Pigeon directory. These environment variables apply only to their respective terminals and avoid overwriting a `.env` file.

**Terminal A — ChromaDB:**

```powershell
$env:ANONYMIZED_TELEMETRY = 'false'
.\.chroma-venv\Scripts\chroma.exe run --host 127.0.0.1 --port 8100 --path .\data\chroma
```

**Terminal B — PIGEON:** set the FFmpeg PATH here as described above, then:

```powershell
$env:AUTH_ENABLED = 'true'
$env:LOCALHOST_BYPASS = 'false'
$env:CHROMADB_HOST = '127.0.0.1'
$env:CHROMADB_PORT = '8100'
$env:FASTEMBED_CACHE_PATH = Join-Path (Get-Location).Path 'data\fastembed_cache'
$env:FASTEMBED_THREADS = '2'
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 7000
```

Open **http://127.0.0.1:7000/**. Create your own account through first-time setup. Add your provider and API key in Settings, or connect your separately installed local-model server. Do not send keys in chat or commit them.

Choose **DuckDuckGo** as the search provider. For local speech recognition, enable speech-to-text, choose provider **local** and model **base**. Keep local Kokoro disabled until its CUDA requirements are separately checked.

The ordinary `launch-windows.ps1` does not start ChromaDB. Mihir's `START_LOCAL_PIGEON.ps1` is an ignored machine-local helper and will **not** appear in this clone. Use the two-terminal procedure above.

Stop each owned service with **Ctrl+C in its terminal**. On subsequent days, repeat section 4; do not reinstall packages each time. Keep `data` and downloaded model caches to retain settings/history and avoid redownloads.

## 5. Acceptance checklist — record real results

- [ ] Both environments report no broken requirements.
- [ ] `Invoke-RestMethod http://127.0.0.1:8100/api/v2/heartbeat` returns a heartbeat.
- [ ] PIGEON opens, account creation/login works, and history survives restart.
- [ ] App startup logs show FastEmbed loaded and memory vector initialization without connection errors.
- [ ] Save a synthetic name in Memory; in a **new chat**, ask for it. Check the correct reply and recalled-memory badge. Repeat after restarting both services.
- [ ] Upload a synthetic text/PDF/Office document, ask a question, and check against its actual contents.
- [ ] Create, edit, save and reopen a simple document.
- [ ] Search the web and check that cited pages support the answer.
- [ ] Record a short microphone sentence and check the transcription; confirm local STT is selected.
- [ ] Test OCR with a synthetic image whose text is known.
- [ ] Test the notes, calendar, tasks, skills and other features intended for the demonstration.
- [ ] For local chat: record model/server/version, actual RTX VRAM, response quality, latency and tool-call behavior. Successful plain chat does not prove agent/tool compatibility.
- [ ] Record failures and logs; do not mark features passed merely because their libraries import.

On Mihir's machine, package checks, Chroma heartbeat, semantic retrieval, CPU Whisper loading, synthetic OCR and FFmpeg version checks passed. Mihir also demonstrated a real chat recalling his saved name. This is **not** a full application acceptance claim or a result for your laptop.

## 6. Troubleshooting and scope

- **Memory appears enabled but recalls nothing:** check Chroma heartbeat and embedding startup logs first. Enabled is a feature preference, not a service-health indicator. The checkpoint's keyword fallback can miss questions such as “who am I?”.
- **Port occupied:** stop your own earlier service or investigate the owner. Do not terminate unknown processes.
- **Model download fails:** preserve the error and check connectivity/certificate configuration. Do not disable TLS validation.
- **FFmpeg missing:** set PATH in Terminal B and verify both binary commands there.
- **Fresh account unexpectedly appears after prior use:** check that you launched from the same clone/data location. Do not reset or overwrite existing data.

Local Kokoro, local chat serving, image generation, real email/CalDAV/CardDAV synchronization and other external integrations require separate setup. An RTX 3050 does not automatically make every local model fit. The checkpoint's restricted browser-action boundary remains unchanged; installing dependencies does not enable general browser/desktop/mobile control.

Keep API keys, data, models, environments and generated version records local. Preserve PIGEON's AGPL licence and upstream notices; FFmpeg and optional packages have their own licence obligations. This guide is a documentation handoff, not integration of the archived expansion.
