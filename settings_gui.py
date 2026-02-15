"""GUI settings window for Voice Typer (tkinter, no extra dependencies)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from voice_typer import AppConfig, load_config, save_config, normalize_hotkey, DEFAULT_CONFIG_PATH


ENGINES = ("whisper", "assemblyai", "google", "gemini")
WHISPER_MODELS = ("tiny", "base", "small", "medium", "large-v3")
WHISPER_DEVICES = ("auto", "cpu", "cuda")
WHISPER_COMPUTE_TYPES = ("int8", "float16", "float32")
LANGUAGES = ("nl", "en", "de", "fr", "es", "nl-NL", "en-US", "de-DE", "fr-FR", "es-ES")


class SettingsWindow:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.config = load_config(config_path)
        self.result: AppConfig | None = None

        self.root = tk.Tk()
        self.root.title("Voice Typer — Instellingen")
        self.root.resizable(False, False)

        self._build_ui()
        self._populate_from_config()
        self._on_engine_changed()
        self._center_window()

    # ── layout ──────────────────────────────────────────────

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=16)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Title
        ttk.Label(main, text="Voice Typer Instellingen", font=("", 16, "bold")).grid(
            row=0, column=0, pady=(0, 10), sticky="w"
        )

        # Notebook (tabs)
        notebook = ttk.Notebook(main)
        notebook.grid(row=1, column=0, sticky="nsew", pady=(0, 14))
        main.rowconfigure(1, weight=1)
        main.columnconfigure(0, weight=1)

        general_tab = ttk.Frame(notebook, padding=12)
        notebook.add(general_tab, text="  Algemeen  ")
        self._build_general_tab(general_tab)

        engine_tab = ttk.Frame(notebook, padding=12)
        notebook.add(engine_tab, text="  Engine Instellingen  ")
        self._build_engine_tab(engine_tab)

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=2, column=0, sticky="e")
        ttk.Button(btn_frame, text="Annuleren", command=self._on_cancel).grid(
            row=0, column=0, padx=(0, 8)
        )
        save_btn = ttk.Button(btn_frame, text="Opslaan", command=self._on_save)
        save_btn.grid(row=0, column=1)

    def _build_general_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        row = 0

        # Engine
        ttk.Label(parent, text="Engine:").grid(row=row, column=0, sticky="w", pady=5)
        self.engine_var = tk.StringVar()
        engine_cb = ttk.Combobox(
            parent, textvariable=self.engine_var, values=ENGINES, state="readonly", width=22
        )
        engine_cb.grid(row=row, column=1, sticky="w", pady=5)
        engine_cb.bind("<<ComboboxSelected>>", lambda _: self._on_engine_changed())
        row += 1

        # Hotkey
        ttk.Label(parent, text="Hotkey:").grid(row=row, column=0, sticky="w", pady=5)
        self.hotkey_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.hotkey_var, width=25).grid(
            row=row, column=1, sticky="w", pady=5
        )
        row += 1

        # Language
        ttk.Label(parent, text="Taal:").grid(row=row, column=0, sticky="w", pady=5)
        self.language_var = tk.StringVar()
        ttk.Combobox(parent, textvariable=self.language_var, values=LANGUAGES, width=22).grid(
            row=row, column=1, sticky="w", pady=5
        )
        row += 1

        # Sample rate
        ttk.Label(parent, text="Sample rate:").grid(row=row, column=0, sticky="w", pady=5)
        self.sample_rate_var = tk.IntVar()
        ttk.Spinbox(
            parent, textvariable=self.sample_rate_var, from_=8000, to=48000, increment=8000, width=10
        ).grid(row=row, column=1, sticky="w", pady=5)
        row += 1

        # Append space
        self.append_space_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Spatie toevoegen na transcriptie", variable=self.append_space_var).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=5
        )

    def _build_engine_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)

        # ── Whisper ──
        self.whisper_frame = ttk.LabelFrame(parent, text="Whisper", padding=10)
        self.whisper_frame.columnconfigure(1, weight=1)

        ttk.Label(self.whisper_frame, text="Model:").grid(row=0, column=0, sticky="w", pady=4)
        self.whisper_model_var = tk.StringVar()
        ttk.Combobox(
            self.whisper_frame, textvariable=self.whisper_model_var,
            values=WHISPER_MODELS, state="readonly", width=18
        ).grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(self.whisper_frame, text="Device:").grid(row=1, column=0, sticky="w", pady=4)
        self.whisper_device_var = tk.StringVar()
        ttk.Combobox(
            self.whisper_frame, textvariable=self.whisper_device_var,
            values=WHISPER_DEVICES, state="readonly", width=18
        ).grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(self.whisper_frame, text="Compute type:").grid(row=2, column=0, sticky="w", pady=4)
        self.whisper_compute_var = tk.StringVar()
        ttk.Combobox(
            self.whisper_frame, textvariable=self.whisper_compute_var,
            values=WHISPER_COMPUTE_TYPES, state="readonly", width=18
        ).grid(row=2, column=1, sticky="w", pady=4)

        # ── AssemblyAI ──
        self.assemblyai_frame = ttk.LabelFrame(parent, text="AssemblyAI", padding=10)
        self.assemblyai_frame.columnconfigure(1, weight=1)

        ttk.Label(self.assemblyai_frame, text="API Key:").grid(row=0, column=0, sticky="w", pady=4)
        self.assemblyai_key_var = tk.StringVar()
        self._assemblyai_entry = ttk.Entry(
            self.assemblyai_frame, textvariable=self.assemblyai_key_var, width=34, show="*"
        )
        self._assemblyai_entry.grid(row=0, column=1, sticky="w", pady=4)
        self._assemblyai_show_btn = ttk.Button(
            self.assemblyai_frame, text="Toon", width=7,
            command=lambda: self._toggle_show(self._assemblyai_entry, self._assemblyai_show_btn)
        )
        self._assemblyai_show_btn.grid(row=0, column=2, padx=(6, 0), pady=4)

        # ── Google ──
        self.google_frame = ttk.LabelFrame(parent, text="Google Speech-to-Text", padding=10)
        self.google_frame.columnconfigure(1, weight=1)

        ttk.Label(self.google_frame, text="Credentials:").grid(row=0, column=0, sticky="w", pady=4)
        self.google_creds_var = tk.StringVar()
        ttk.Entry(self.google_frame, textvariable=self.google_creds_var, width=30).grid(
            row=0, column=1, sticky="w", pady=4
        )
        ttk.Button(self.google_frame, text="Browse...", command=self._browse_google_creds).grid(
            row=0, column=2, padx=(6, 0), pady=4
        )

        # ── Gemini ──
        self.gemini_frame = ttk.LabelFrame(parent, text="Gemini", padding=10)
        self.gemini_frame.columnconfigure(1, weight=1)

        ttk.Label(self.gemini_frame, text="API Key:").grid(row=0, column=0, sticky="w", pady=4)
        self.gemini_key_var = tk.StringVar()
        self._gemini_entry = ttk.Entry(
            self.gemini_frame, textvariable=self.gemini_key_var, width=34, show="*"
        )
        self._gemini_entry.grid(row=0, column=1, sticky="w", pady=4)
        self._gemini_show_btn = ttk.Button(
            self.gemini_frame, text="Toon", width=7,
            command=lambda: self._toggle_show(self._gemini_entry, self._gemini_show_btn)
        )
        self._gemini_show_btn.grid(row=0, column=2, padx=(6, 0), pady=4)

    # ── dynamic engine panel ────────────────────────────────

    def _on_engine_changed(self) -> None:
        engine = self.engine_var.get()
        for frame in (self.whisper_frame, self.assemblyai_frame, self.google_frame, self.gemini_frame):
            frame.grid_remove()

        mapping = {
            "whisper": self.whisper_frame,
            "assemblyai": self.assemblyai_frame,
            "google": self.google_frame,
            "gemini": self.gemini_frame,
        }
        target = mapping.get(engine)
        if target is not None:
            target.grid(row=0, column=0, sticky="ew", pady=6)

    # ── populate / save ─────────────────────────────────────

    def _populate_from_config(self) -> None:
        c = self.config
        self.engine_var.set(c.engine)
        self.hotkey_var.set(c.hotkey)
        self.language_var.set(c.language)
        self.sample_rate_var.set(c.sample_rate)
        self.append_space_var.set(c.append_space)
        self.whisper_model_var.set(c.whisper_model)
        self.whisper_device_var.set(c.whisper_device)
        self.whisper_compute_var.set(c.whisper_compute_type)
        self.assemblyai_key_var.set(c.assemblyai_api_key)
        self.google_creds_var.set(c.google_credentials_path)
        self.gemini_key_var.set(c.gemini_api_key)

    def _on_save(self) -> None:
        hotkey_raw = self.hotkey_var.get().strip()
        if not hotkey_raw:
            messagebox.showerror("Fout", "Hotkey mag niet leeg zijn.")
            return
        try:
            normalized = normalize_hotkey(hotkey_raw)
        except ValueError as exc:
            messagebox.showerror("Fout", str(exc))
            return

        new_config = AppConfig(
            engine=self.engine_var.get(),
            hotkey=normalized,
            language=self.language_var.get().strip() or "nl",
            sample_rate=self.sample_rate_var.get(),
            append_space=self.append_space_var.get(),
            whisper_model=self.whisper_model_var.get(),
            whisper_device=self.whisper_device_var.get(),
            whisper_compute_type=self.whisper_compute_var.get(),
            assemblyai_api_key=self.assemblyai_key_var.get().strip(),
            google_credentials_path=self.google_creds_var.get().strip(),
            gemini_api_key=self.gemini_key_var.get().strip(),
        )
        save_config(new_config, self.config_path)
        self.result = new_config
        messagebox.showinfo("Opgeslagen", f"Configuratie opgeslagen naar\n{self.config_path}")
        self.root.destroy()

    def _on_cancel(self) -> None:
        self.root.destroy()

    # ── helpers ──────────────────────────────────────────────

    def _browse_google_creds(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecteer Google credentials JSON",
            filetypes=[("JSON bestanden", "*.json"), ("Alle bestanden", "*.*")],
        )
        if path:
            self.google_creds_var.set(path)

    @staticmethod
    def _toggle_show(entry: ttk.Entry, btn: ttk.Button) -> None:
        if entry.cget("show") == "*":
            entry.configure(show="")
            btn.configure(text="Verberg")
        else:
            entry.configure(show="*")
            btn.configure(text="Toon")

    def _center_window(self) -> None:
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"+{x}+{y}")

    # ── run ──────────────────────────────────────────────────

    def run(self) -> AppConfig | None:
        self.root.mainloop()
        return self.result


def open_settings_window(config_path: Path | None = None) -> AppConfig | None:
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    window = SettingsWindow(config_path)
    return window.run()


if __name__ == "__main__":
    open_settings_window()
