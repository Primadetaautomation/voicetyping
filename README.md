# Voice Typer (macOS + Windows)

Dicteer-app met globale hotkey:
- Druk hotkey 1x: opname start
- Druk dezelfde hotkey opnieuw: opname stopt
- Transcriptie wordt direct getypt op de plek waar je cursor staat

Ondersteunde engines:
- `whisper` (lokaal, offline, geen API key nodig)
- `gemini` (Google Gemini, snel en nauwkeurig)
- `assemblyai` (cloud API)
- `google` (Google Speech-to-Text)

## Installatie op een nieuwe PC

### Stap 1: Download het project

```bash
git clone https://github.com/Primadetaautomation/voicetyping.git
cd voicetyping
```

Of download als ZIP: klik "Code" > "Download ZIP" op GitHub.

### Stap 2: Installeer (dubbelklik)

**macOS:**
- Dubbelklik `install_mac.command`
- Het script checkt Python, installeert dependencies, en opent het settings venster

**Windows:**
- Dubbelklik `install_windows.bat`
- Het script checkt Python, installeert dependencies, en opent het settings venster

> Vereist: Python 3.10+ ([download hier](https://www.python.org/downloads/))
> Windows: vink "Add Python to PATH" aan tijdens installatie!

### Stap 3: Start

**macOS:** Dubbelklik `start_mac.command`
**Windows:** Dubbelklik `start_windows.bat`

Dat is het! Druk je hotkey (standaard Ctrl+Alt+D) om te dicteren.

## Configuratie

### GUI Settings (aanbevolen)

```bash
python voice_typer.py settings
```

Opent een grafisch venster waar je alles kunt instellen: engine, hotkey, taal, API keys.

### CLI Setup (alternatief)

```bash
python voice_typer.py setup
```

Interactieve wizard in de terminal.

### Handmatig starten

```bash
python voice_typer.py run
```

Met overrides:

```bash
python voice_typer.py run --engine whisper --hotkey ctrl+alt+space --language nl
```

## Engines

| Engine | Type | API Key | Snelheid |
|--------|------|---------|----------|
| Whisper | Lokaal/offline | Niet nodig | Medium |
| Gemini | Cloud (Google) | Ja ([krijg hier](https://aistudio.google.com/apikey)) | Snel |
| AssemblyAI | Cloud | Ja | Snel |
| Google STT | Cloud | Credentials JSON | Snel |

## macOS permissies (belangrijk!)

Geef je terminal app toegang via Systeeminstellingen > Privacy en beveiliging:

1. **Microfoon** - voor audio opname
2. **Toegankelijkheid** - voor tekst typen
3. **Invoerbewaking** - voor globale hotkey

Als `.command` bestanden niet starten, run eenmalig:

```bash
chmod +x install_mac.command start_mac.command
```

## Windows permissies

- Zet microfoon-toegang aan in privacy settings
- Als typen niet werkt in sommige apps: start terminal als Administrator

## Tips

- Run de app in een apart terminalvenster en focus daarna op het venster waar je wilt typen
- macOS hotkey: Ctrl+Option+D (Option = Alt)
- Config bestand: `~/.voice-typer.toml`
