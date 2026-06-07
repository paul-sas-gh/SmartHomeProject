"""
text_loader.py — Citire, curățare și împărțire în propoziții a fișierelor text.

Utilizare:
    from app.parsers.text_loader import load_text, load_sentences

"""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


def _clean(text: str) -> str:
    """
    Normalizează textul:
    - elimină caractere de control (cu excepția newline)
    - normalizează spațiile multiple la un singur spațiu per linie
    - elimină liniile goale redundante (mai mult de una consecutivă)
    - trim whitespace la capetele textului
    """
    # Elimină caractere de control (tab-uri devin spații)
    text = text.replace("\t", " ")
    # Elimină caractere non-printabile (cu excepția \n)
    text = re.sub(r"[^\S\n]+", " ", text)
    # Trim spații la capătul fiecărei linii
    lines = [line.strip() for line in text.splitlines()]
    # Elimină linii goale consecutive (păstrează cel mult una)
    cleaned_lines: list[str] = []
    prev_empty = False
    for line in lines:
        if line == "":
            if not prev_empty:
                cleaned_lines.append(line)
            prev_empty = True
        else:
            cleaned_lines.append(line)
            prev_empty = False
    return "\n".join(cleaned_lines).strip()


def load_text_from_string(text: str) -> str:
    """
    Primește un string direct și returnează textul curat (fără citire din fișier).

    Args:
        text: Text brut în limbaj natural.

    Returns:
        Textul normalizat.
    """
    cleaned = _clean(text)
    if not cleaned:
        raise ValueError("Textul este gol sau conține doar whitespace.")
    logger.info("Text inline normalizat: %d caractere.", len(cleaned))
    return cleaned


def load_text(path: str) -> str:
    """
    Citește un fișier .txt și returnează textul curat ca string.

    Args:
        path: Calea relativă sau absolută a fișierului.

    Returns:
        Textul curat (string).

    Raises:
        FileNotFoundError: Dacă fișierul nu există.
        ValueError: Dacă fișierul este gol după curățare.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Fișierul nu există: {file_path.resolve()}")

    raw = file_path.read_text(encoding="utf-8")
    cleaned = _clean(raw)

    if not cleaned:
        raise ValueError(f"Fișierul este gol sau conține doar whitespace: {path}")

    logger.info("Fișier încărcat: %s (%d caractere)", path, len(cleaned))
    return cleaned


def load_sentences(path: str) -> list[str]:
    """
    Citește un fișier .txt și returnează lista de propoziții non-goale.

    Împărțirea în propoziții se face prin regex pe semne de punctuație terminale
    (., !, ?) urmate de spații/newline, fără a depinde de spaCy în această fază.

    Args:
        path: Calea fișierului text.

    Returns:
        Listă de propoziții curate.
    """
    text = load_text(path)

    # Împarte pe '. ', '! ', '? ', '.\n', '!\n', '?\n'
    raw_sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in raw_sentences if s.strip()]

    logger.info("Propoziții detectate: %d", len(sentences))
    for i, sent in enumerate(sentences, start=1):
        logger.debug("  [%d] %s", i, sent)

    return sentences
