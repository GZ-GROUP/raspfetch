"""Minimal i18n for RASPFETCH.

Messages live in locales/<language>.lang as ``key=text`` lines. The Bash scripts
read the same files (see common.sh), so every user-facing string of a language
is in a single place. Use %s for arguments and %% for a literal percent sign.
"""
from __future__ import annotations

import os
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parent / "locales"
DEFAULT_LANGUAGE = "en"


def available_languages() -> list[str]:
    """Language codes that have a catalog in locales/."""
    return sorted(path.stem for path in LOCALES_DIR.glob("*.lang"))


def load_catalog(language: str) -> dict[str, str]:
    """Reads a key=text catalog, skipping blank lines and # comments."""
    catalog: dict[str, str] = {}
    path = LOCALES_DIR / f"{language}.lang"
    if not path.is_file():
        return catalog
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, text = line.split("=", 1)
        catalog[key] = text
    return catalog


class Translator:
    def __init__(self, language: str = DEFAULT_LANGUAGE) -> None:
        self.set_language(language)

    def set_language(self, language: str) -> None:
        if language not in available_languages():
            language = DEFAULT_LANGUAGE
        self.language = language
        # English is loaded first so a missing translation falls back to it.
        self.messages = load_catalog(DEFAULT_LANGUAGE) | load_catalog(language)

    def next_language(self) -> None:
        """Switches to the next available language (wraps around)."""
        languages = available_languages()
        index = languages.index(self.language) if self.language in languages else -1
        self.set_language(languages[(index + 1) % len(languages)])

    def t(self, key: str, *args: object) -> str:
        """Returns the translated message for key, formatted with args."""
        text = self.messages.get(key, key)
        try:
            return text % args
        except (TypeError, ValueError):
            return text


translator = Translator(os.environ.get("RASPFETCH_LANG", DEFAULT_LANGUAGE))
t = translator.t
