# Voice Typer (macOS + Windows)

Dicteer-app met globale hotkey:
- Druk hotkey 1x: opname start
- Druk dezelfde hotkey opnieuw: opname stopt
- Transcriptie wordt direct getypt op de plek waar je cursor staat (ook in terminal)

Ondersteunde engines:
- `whisper` (lokaal, via `faster-whisper`)
- `assemblyai` (cloud API)
- `google` (Google Speech-to-Text)

## Snelle start met dubbelklik

### macOS
- Dubbelklik `install_mac.command` (eenmalig)
- Dubbelklik daarna `start_mac.command`

### Windows
- Dubbelklik `install_windows.bat` (eenmalig)
- Dubbelklik daarna `start_windows.bat`

## Handmatige installatie (fallback)

```bash
cd /Users/jamese/voicetyping
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2) Configuratie maken

```bash
python voice_typer.py setup
```

Dit maakt standaard `~/.voice-typer.toml`.

Voorbeelden:
- Hotkey: `ctrl+alt+d`
- macOS hotkey met command: `cmd+shift+d`
- Taal: `nl` (Whisper/AssemblyAI) of `nl-NL` (Google)

## 2b) GUI Instellingen (optioneel)

```bash
python voice_typer.py settings
```

Dit opent een grafisch instellingenvenster waar je alle opties kunt aanpassen.

## 3) Starten

```bash
python voice_typer.py run
```

Met overrides:

```bash
python voice_typer.py run --engine whisper --hotkey ctrl+alt+space --language nl
```

## Engine-specifiek

### Whisper (aanrader voor privacy/offline)
- Geen API key nodig.
- Kies model in setup (`tiny`, `base`, `small`, `medium`, `large-v3`).

### AssemblyAI
- Zet `assemblyai_api_key` in `~/.voice-typer.toml` of env var `ASSEMBLYAI_API_KEY`.

### Google Speech-to-Text
- Zet `google_credentials_path` in `~/.voice-typer.toml` of env var `GOOGLE_APPLICATION_CREDENTIALS`.

## macOS permissies (belangrijk)

Geef je terminal/python-app toegang via:
- `System Settings -> Privacy & Security -> Accessibility`
- `System Settings -> Privacy & Security -> Input Monitoring`
- `System Settings -> Privacy & Security -> Microphone`

Als je `.command` niet direct start:
- Run eenmalig in terminal:

```bash
cd /Users/jamese/voicetyping
chmod +x install_mac.command start_mac.command
```

## Windows permissies

- Zet microfoon-toegang aan in privacy settings.
- Als typen in sommige apps geblokkeerd is: start terminal als Administrator.

## Tip voor stabiel gebruik

Run de app in een apart terminalvenster en focus daarna op het venster waar je wilt typen.
