#!/usr/bin/env python3
"""Global dictation app that types transcribed speech at the current cursor."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import threading
import time
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib

try:
    import rumps

    _HAS_RUMPS = True
except ImportError:
    _HAS_RUMPS = False


DEFAULT_CONFIG_PATH = Path.home() / ".voice-typer.toml"


@dataclass
class AppConfig:
    engine: str = "whisper"
    hotkey: str = "<ctrl>+<alt>+d"
    language: str = "nl"
    sample_rate: int = 16000
    append_space: bool = True
    whisper_model: str = "small"
    whisper_device: str = "auto"
    whisper_compute_type: str = "int8"
    assemblyai_api_key: str = ""
    google_credentials_path: str = ""
    gemini_api_key: str = ""


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return default


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_str(value: Any, default: str) -> str:
    if value is None:
        return default
    return str(value)


def normalize_hotkey(hotkey: str) -> str:
    token_map = {
        "ctrl": "<ctrl>",
        "control": "<ctrl>",
        "alt": "<alt>",
        "option": "<alt>",
        "shift": "<shift>",
        "cmd": "<cmd>",
        "command": "<cmd>",
        "win": "<cmd>",
        "windows": "<cmd>",
    }
    parts = [part.strip() for part in hotkey.split("+") if part.strip()]
    if not parts:
        raise ValueError("Hotkey is leeg.")

    normalized: list[str] = []
    for part in parts:
        raw = part.lower()
        if raw.startswith("<") and raw.endswith(">"):
            normalized.append(raw)
            continue
        normalized.append(token_map.get(raw, raw))
    return "+".join(normalized)


def normalize_google_language(language: str) -> str:
    if "-" in language:
        return language
    defaults = {
        "nl": "nl-NL",
        "en": "en-US",
        "de": "de-DE",
        "fr": "fr-FR",
        "es": "es-ES",
    }
    return defaults.get(language.lower(), language)


def normalize_assemblyai_language(language: str) -> str:
    if "-" in language:
        return language.split("-", maxsplit=1)[0]
    return language


def load_config(config_path: Path) -> AppConfig:
    config = AppConfig()
    if not config_path.exists():
        return config

    with config_path.open("rb") as handle:
        data = tomllib.load(handle)

    return AppConfig(
        engine=_as_str(data.get("engine"), config.engine).lower(),
        hotkey=_as_str(data.get("hotkey"), config.hotkey),
        language=_as_str(data.get("language"), config.language),
        sample_rate=_as_int(data.get("sample_rate"), config.sample_rate),
        append_space=_as_bool(data.get("append_space"), config.append_space),
        whisper_model=_as_str(data.get("whisper_model"), config.whisper_model),
        whisper_device=_as_str(data.get("whisper_device"), config.whisper_device),
        whisper_compute_type=_as_str(
            data.get("whisper_compute_type"), config.whisper_compute_type
        ),
        assemblyai_api_key=_as_str(data.get("assemblyai_api_key"), ""),
        google_credentials_path=_as_str(data.get("google_credentials_path"), ""),
        gemini_api_key=_as_str(data.get("gemini_api_key"), ""),
    )


def save_config(config: AppConfig, config_path: Path) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)

    def quote(value: str) -> str:
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    lines = [
        f"engine = {quote(config.engine)}",
        f"hotkey = {quote(config.hotkey)}",
        f"language = {quote(config.language)}",
        f"sample_rate = {config.sample_rate}",
        f"append_space = {'true' if config.append_space else 'false'}",
        f"whisper_model = {quote(config.whisper_model)}",
        f"whisper_device = {quote(config.whisper_device)}",
        f"whisper_compute_type = {quote(config.whisper_compute_type)}",
        f"assemblyai_api_key = {quote(config.assemblyai_api_key)}",
        f"google_credentials_path = {quote(config.google_credentials_path)}",
        f"gemini_api_key = {quote(config.gemini_api_key)}",
        "",
    ]
    config_path.write_text("\n".join(lines), encoding="utf-8")


def _recording_to_wav(audio_f32: Any, sample_rate: int, np_module: Any) -> Path:
    clipped = np_module.clip(audio_f32, -1.0, 1.0)
    int_audio = (clipped * 32767).astype(np_module.int16)

    file_descriptor, wav_path = tempfile.mkstemp(prefix="voice_typer_", suffix=".wav")
    os.close(file_descriptor)
    with wave.open(wav_path, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes(int_audio.tobytes())
    return Path(wav_path)


class AudioRecorder:
    def __init__(self, sample_rate: int) -> None:
        self.sample_rate = sample_rate
        self._frames: list[Any] = []
        self._stream: Any | None = None
        self._lock = threading.Lock()
        try:
            import numpy as np
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError(
                "Audio dependencies ontbreken. Installeer met: pip install -r requirements.txt"
            ) from exc
        self._np = np
        self._sd = sd

    def _callback(self, indata: Any, _frames: int, _time: Any, status: Any) -> None:
        if status:
            print(f"[audio] waarschuwing: {status}", file=sys.stderr)
        self._frames.append(indata.copy())

    def start(self) -> None:
        with self._lock:
            if self._stream is not None:
                raise RuntimeError("Opname is al gestart.")
            self._frames.clear()
            device = self._sd.default.device[0]
            self._stream = self._sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                device=device,
                callback=self._callback,
            )
            self._stream.start()

    def stop(self) -> Path:
        with self._lock:
            if self._stream is None:
                raise RuntimeError("Opname is niet actief.")
            self._stream.stop()
            self._stream.close()
            self._stream = None
            if not self._frames:
                raise RuntimeError("Geen audio ontvangen. Controleer microfooninstellingen.")
            audio_data = self._np.concatenate(self._frames, axis=0).flatten()
        return _recording_to_wav(audio_data, self.sample_rate, self._np)


class TextTyper:
    def __init__(self) -> None:
        try:
            from pynput.keyboard import Controller
        except ImportError as exc:
            raise RuntimeError(
                "Keyboard dependency ontbreekt. Installeer met: pip install -r requirements.txt"
            ) from exc
        self._controller = Controller()

    def type_text(self, text: str) -> None:
        # Kleine delay zodat de hotkey-combinatie volledig is losgelaten.
        time.sleep(0.08)
        self._controller.type(text)


class WhisperTranscriber:
    def __init__(self, config: AppConfig) -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper ontbreekt. Installeer met: pip install -r requirements.txt"
            ) from exc
        self._model = WhisperModel(
            config.whisper_model,
            device=config.whisper_device,
            compute_type=config.whisper_compute_type,
        )
        self._language = config.language or None

    def transcribe(self, audio_path: Path) -> str:
        segments, _info = self._model.transcribe(
            str(audio_path),
            language=self._language,
            vad_filter=True,
            beam_size=5,
        )
        parts = [segment.text.strip() for segment in segments if segment.text.strip()]
        return " ".join(parts).strip()


class AssemblyAITranscriber:
    def __init__(self, config: AppConfig) -> None:
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError(
                "requests ontbreekt. Installeer met: pip install -r requirements.txt"
            ) from exc
        self._requests = requests
        self._api_key = config.assemblyai_api_key or os.getenv("ASSEMBLYAI_API_KEY", "")
        if not self._api_key:
            raise RuntimeError(
                "AssemblyAI key ontbreekt. Zet assemblyai_api_key in config of ASSEMBLYAI_API_KEY."
            )
        self._language = normalize_assemblyai_language(config.language or "nl")
        self._headers = {"authorization": self._api_key}
        self._base_url = "https://api.assemblyai.com/v2"

    def _upload(self, audio_path: Path) -> str:
        with audio_path.open("rb") as handle:
            response = self._requests.post(
                f"{self._base_url}/upload",
                headers=self._headers,
                data=handle,
                timeout=120,
            )
        response.raise_for_status()
        payload = response.json()
        return payload["upload_url"]

    def transcribe(self, audio_path: Path) -> str:
        upload_url = self._upload(audio_path)
        create_response = self._requests.post(
            f"{self._base_url}/transcript",
            headers={**self._headers, "content-type": "application/json"},
            json={
                "audio_url": upload_url,
                "language_code": self._language,
                "punctuate": True,
                "format_text": True,
            },
            timeout=60,
        )
        create_response.raise_for_status()
        transcript_id = create_response.json()["id"]

        deadline = time.time() + 300
        while time.time() < deadline:
            status_response = self._requests.get(
                f"{self._base_url}/transcript/{transcript_id}",
                headers=self._headers,
                timeout=30,
            )
            status_response.raise_for_status()
            payload = status_response.json()
            status = payload.get("status")
            if status == "completed":
                return payload.get("text", "").strip()
            if status == "error":
                raise RuntimeError(payload.get("error", "AssemblyAI transcriptie mislukt."))
            time.sleep(1.2)
        raise TimeoutError("AssemblyAI transcriptie timeout na 5 minuten.")


class GoogleTranscriber:
    def __init__(self, config: AppConfig) -> None:
        if config.google_credentials_path:
            os.environ.setdefault(
                "GOOGLE_APPLICATION_CREDENTIALS", config.google_credentials_path
            )
        try:
            from google.cloud import speech
        except ImportError as exc:
            raise RuntimeError(
                "google-cloud-speech ontbreekt. Installeer met: pip install -r requirements.txt"
            ) from exc
        self._speech = speech
        self._client = speech.SpeechClient()
        self._sample_rate = config.sample_rate
        self._language = normalize_google_language(config.language or "nl-NL")

    def transcribe(self, audio_path: Path) -> str:
        with audio_path.open("rb") as handle:
            audio_bytes = handle.read()
        audio = self._speech.RecognitionAudio(content=audio_bytes)
        config = self._speech.RecognitionConfig(
            encoding=self._speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self._sample_rate,
            language_code=self._language,
            enable_automatic_punctuation=True,
            model="latest_long",
        )
        response = self._client.recognize(config=config, audio=audio)
        results = []
        for result in response.results:
            if result.alternatives:
                results.append(result.alternatives[0].transcript.strip())
        return " ".join(part for part in results if part).strip()


class GeminiTranscriber:
    def __init__(self, config: AppConfig) -> None:
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise RuntimeError(
                "google-generativeai ontbreekt. Installeer met: pip install google-generativeai"
            ) from exc
        self._genai = genai
        api_key = config.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "Gemini key ontbreekt. Zet gemini_api_key in config of GEMINI_API_KEY."
            )
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel("gemini-2.0-flash")
        self._language = config.language or "nl"

    def transcribe(self, audio_path: Path) -> str:
        with audio_path.open("rb") as handle:
            audio_bytes = handle.read()
        audio_file = {"mime_type": "audio/wav", "data": audio_bytes}
        response = self._model.generate_content(
            [
                f"Transcribeer de volgende audio nauwkeurig in het {self._language}. "
                "Geef alleen de letterlijke transcriptie terug, geen uitleg.",
                audio_file,
            ]
        )
        return response.text.strip()


def create_transcriber(config: AppConfig) -> Any:
    if config.engine == "whisper":
        return WhisperTranscriber(config)
    if config.engine == "assemblyai":
        return AssemblyAITranscriber(config)
    if config.engine == "google":
        return GoogleTranscriber(config)
    if config.engine == "gemini":
        return GeminiTranscriber(config)
    raise ValueError("Ongeldige engine. Kies whisper, assemblyai, google of gemini.")


class VoiceTyperApp:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.recorder = AudioRecorder(config.sample_rate)
        self.typer = TextTyper()
        self.transcriber = create_transcriber(config)
        self._lock = threading.Lock()
        self._is_recording = False
        self._is_busy = False

    def toggle_recording(self) -> None:
        with self._lock:
            if self._is_busy:
                print("Nog bezig met de vorige transcriptie.")
                return
            if not self._is_recording:
                try:
                    self.recorder.start()
                except Exception as exc:  # noqa: BLE001
                    print(f"Kon opname niet starten: {exc}", file=sys.stderr)
                    return
                self._is_recording = True
                print("Opname gestart...")
                return

            try:
                audio_path = self.recorder.stop()
            except Exception as exc:  # noqa: BLE001
                self._is_recording = False
                print(f"Kon opname niet stoppen: {exc}", file=sys.stderr)
                return
            self._is_recording = False
            self._is_busy = True
            print("Transcriberen...")

        threading.Thread(
            target=self._transcribe_and_type, args=(audio_path,), daemon=True
        ).start()

    def _transcribe_and_type(self, audio_path: Path) -> None:
        try:
            text = self.transcriber.transcribe(audio_path).strip()
            if not text:
                print("Geen tekst herkend.")
                return
            if self.config.append_space:
                text_to_type = f"{text} "
            else:
                text_to_type = text
            self.typer.type_text(text_to_type)
            print(f"Getypt: {text}")
        except Exception as exc:  # noqa: BLE001
            print(f"Transcriptie mislukt: {exc}", file=sys.stderr)
        finally:
            audio_path.unlink(missing_ok=True)
            with self._lock:
                self._is_busy = False

    def _start_hotkey_listener(self, normalized_hotkey: str) -> None:
        from pynput.keyboard import GlobalHotKeys

        with GlobalHotKeys({normalized_hotkey: self.toggle_recording}) as listener:
            listener.join()

    def run(self) -> None:
        try:
            from pynput.keyboard import GlobalHotKeys  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "pynput ontbreekt. Installeer met: pip install -r requirements.txt"
            ) from exc

        normalized_hotkey = normalize_hotkey(self.config.hotkey)
        print("Voice Typer actief.")
        print(f"Engine: {self.config.engine}")
        print(f"Hotkey: {normalized_hotkey}")
        print("Druk dezelfde hotkey om opname te starten/stoppen. Stop met Ctrl+C.")

        if not _HAS_RUMPS:
            self._start_hotkey_listener(normalized_hotkey)
            return

        # Start pynput hotkey listener in background thread
        hotkey_thread = threading.Thread(
            target=self._start_hotkey_listener,
            args=(normalized_hotkey,),
            daemon=True,
        )
        hotkey_thread.start()

        # Build rumps menubar app on main thread
        menubar = rumps.App("VT", quit_button=None)
        status_item = rumps.MenuItem("Status: klaar", callback=None)
        stop_item = rumps.MenuItem("Stop", callback=lambda _: rumps.quit_application())
        menubar.menu = [status_item, None, stop_item]

        @rumps.timer(0.5)
        def update_status(_):
            with self._lock:
                recording = self._is_recording
                busy = self._is_busy
            if recording:
                menubar.title = "\U0001F534 VT"
                status_item.title = "Status: opname..."
            elif busy:
                menubar.title = "\u23F3 VT"
                status_item.title = "Status: transcriberen..."
            else:
                menubar.title = "VT"
                status_item.title = "Status: klaar"

        menubar.run()


def prompt(question: str, default: str) -> str:
    value = input(f"{question} [{default}]: ").strip()
    return value or default


def run_setup(config_path: Path) -> None:
    existing = load_config(config_path) if config_path.exists() else AppConfig()
    print(f"Configuratiebestand: {config_path}")

    engine = prompt("Engine (whisper / assemblyai / google / gemini)", existing.engine).lower()
    while engine not in {"whisper", "assemblyai", "google", "gemini"}:
        print("Kies whisper, assemblyai, google of gemini.")
        engine = prompt("Engine (whisper / assemblyai / google / gemini)", existing.engine).lower()

    hotkey = prompt("Hotkey (bijv. ctrl+alt+d)", existing.hotkey)
    language = prompt("Taalcode (bijv. nl of nl-NL)", existing.language)
    sample_rate = _as_int(prompt("Sample rate", str(existing.sample_rate)), 16000)
    append_space_raw = prompt(
        "Spatie toevoegen na elke transcriptie? (y/n)",
        "y" if existing.append_space else "n",
    ).lower()
    append_space = append_space_raw.startswith("y")

    whisper_model = existing.whisper_model
    whisper_device = existing.whisper_device
    whisper_compute_type = existing.whisper_compute_type
    assemblyai_api_key = existing.assemblyai_api_key
    google_credentials_path = existing.google_credentials_path
    gemini_api_key = existing.gemini_api_key

    if engine == "whisper":
        whisper_model = prompt("Whisper model (tiny/base/small/medium/large-v3)", whisper_model)
        whisper_device = prompt("Whisper device (auto/cpu/cuda)", whisper_device)
        whisper_compute_type = prompt("Whisper compute_type (int8/float16/float32)", whisper_compute_type)
    if engine == "assemblyai":
        assemblyai_api_key = prompt("AssemblyAI API key", assemblyai_api_key or "plak-hier-je-key")
    if engine == "google":
        google_credentials_path = prompt(
            "Pad naar Google credentials JSON", google_credentials_path or "C:/pad/naar/key.json"
        )
    if engine == "gemini":
        gemini_api_key = prompt("Gemini API key", gemini_api_key or "plak-hier-je-key")

    config = AppConfig(
        engine=engine,
        hotkey=hotkey,
        language=language,
        sample_rate=sample_rate,
        append_space=append_space,
        whisper_model=whisper_model,
        whisper_device=whisper_device,
        whisper_compute_type=whisper_compute_type,
        assemblyai_api_key=assemblyai_api_key,
        google_credentials_path=google_credentials_path,
        gemini_api_key=gemini_api_key,
    )
    save_config(config, config_path)
    print("Configuratie opgeslagen.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Global dictation app: spreek en laat tekst typen op de huidige cursor."
    )
    subcommands = parser.add_subparsers(dest="command")

    run_parser = subcommands.add_parser("run", help="Start de dicteer-app")
    run_parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    run_parser.add_argument("--engine", choices=["whisper", "assemblyai", "google", "gemini"])
    run_parser.add_argument("--hotkey")
    run_parser.add_argument("--language")
    run_parser.add_argument("--no-space", action="store_true")

    setup_parser = subcommands.add_parser("setup", help="Maak of wijzig je config")
    setup_parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))

    settings_parser = subcommands.add_parser("settings", help="Open GUI instellingen")
    settings_parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))

    return parser


def apply_runtime_overrides(config: AppConfig, args: argparse.Namespace) -> AppConfig:
    if getattr(args, "engine", None):
        config.engine = args.engine
    if getattr(args, "hotkey", None):
        config.hotkey = args.hotkey
    if getattr(args, "language", None):
        config.language = args.language
    if getattr(args, "no_space", False):
        config.append_space = False
    return config


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        argv = ["run"]

    args = parser.parse_args(argv)
    command = args.command or "run"

    if command == "setup":
        run_setup(Path(args.config).expanduser())
        return 0

    if command == "settings":
        from settings_gui import open_settings_window
        open_settings_window(Path(args.config).expanduser())
        return 0

    config_path = Path(args.config).expanduser()
    config = load_config(config_path)
    config = apply_runtime_overrides(config, args)

    try:
        app = VoiceTyperApp(config)
        app.run()
    except KeyboardInterrupt:
        print("\nAfgesloten.")
    except Exception as exc:  # noqa: BLE001
        print(f"Fout: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
