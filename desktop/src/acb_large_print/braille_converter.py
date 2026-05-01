"""Braille translation using liblouis via the ``louis`` Python bindings.

Conforms to Braille Authority of North America (BANA) standards:
  - Primary literary standard: Unified English Braille (UEB), adopted by
    BANA on January 4, 2016.  Grade 1 (uncontracted) and Grade 2
    (contracted) are both supported using the official liblouis UEB tables.
  - Legacy support: English Braille American Edition (EBAE), the pre-2016
    US standard.  Provided for interoperability with older materials and
    readers trained before the 2016 transition.
  - Technical/computer content: BANA Computer Braille Code (8-dot), using
    the ``en-us-comp8.ctb`` table.
  - BRF output uses BANA-standard line length of 40 cells per line and
    25 lines per page.

Supports:
  - English text  → Braille (UEB G1, UEB G2, EBAE G1, EBAE G2, Computer)
  - Braille (Unicode or ASCII/BRF)  → English text  (back-translation)

Output formats:
  - ``unicode``  — Unicode Braille characters (U+2800–U+28FF), suitable for
    screen display, copy-paste, and embosser-ready Unicode streams.
  - ``brf``      — ASCII Braille Ready Format (BRF), the industry-standard
    format for embossers, wrapped at the BANA-standard 40 cells per line.

Back-translation uses the same grade tables.  Results are approximate for
Grade 2 because contraction is inherently lossy (see liblouis docs §3.1
and BANA UEB Rules, §1.3 "Limitations of Back-Translation").

BANA references:
  https://www.brailleauthority.org/
  https://www.brailleauthority.org/ueb/ueb.html
  https://www.brailleauthority.org/formats/index.html

Usage::

    from acb_large_print.braille_converter import (
        braille_available,
        text_to_braille,
        braille_to_text,
        BrailleError,
        GRADES,
    )

    if braille_available():
        # Forward translation — BANA UEB Grade 2 (default)
        brl = text_to_braille("Hello, world!", grade="ueb_g2",
                               output_format="unicode")
        # Back-translation (approximate)
        back = braille_to_text(brl, grade="ueb_g2")
        # BRF output with BANA 40-cell line wrapping
        brf = text_to_braille("The cat sat.", grade="ueb_g2",
                               output_format="brf")
"""

from __future__ import annotations

__all__ = [
    "BrailleError",
    "braille_available",
    "text_to_braille",
    "braille_to_text",
    "format_brf_output",
    "GRADES",
    "OUTPUT_FORMATS",
    "BRF_LINE_LENGTH",
    "BRF_PAGE_LENGTH",
    "DEFAULT_GRADE",
]

from typing import Literal

# ---------------------------------------------------------------------------
# Optional import of louis -- graceful degradation if not installed
# ---------------------------------------------------------------------------
_louis = None
_IMPORT_ERROR: str | None = None

try:
    import louis as _louis  # type: ignore[import-untyped]
except Exception as _err:
    _IMPORT_ERROR = str(_err)


# ---------------------------------------------------------------------------
# BANA formatting constants
# ---------------------------------------------------------------------------

#: BANA-standard line length for BRF output (40 braille cells per line).
#: Source: BANA Formats Guidelines, §1.2 "Paper and Cell Dimensions".
BRF_LINE_LENGTH: int = 40

#: BANA-standard page length for formatted BRF output (25 lines per page).
#: Source: BANA Formats Guidelines, §1.2 "Paper and Cell Dimensions".
BRF_PAGE_LENGTH: int = 25

#: Maximum input characters accepted per request (prevents runaway processing).
MAX_INPUT_CHARS: int = 50_000

# ---------------------------------------------------------------------------
# Grade / table catalogue
# ---------------------------------------------------------------------------
# Each entry: (liblouis_table_file, display_name, bana_status_description)
# Tables sourced from the liblouis distribution (https://liblouis.io).
# UEB tables are maintained by the UEB Technical Committee; EBAE tables are
# the legacy en-us-g*.ctb tables.

GRADES: dict[str, tuple[str, str, str]] = {
    # ---- BANA Current Standard: Unified English Braille (UEB) ----
    "ueb_g2": (
        "en-ueb-g2.ctb",
        "UEB Grade 2 — Contracted",
        "BANA current standard (adopted 2016).  Uses contractions for common "
        "words and letter combinations.  Recommended for general literary and "
        "narrative materials.",
    ),
    "ueb_g1": (
        "en-ueb-g1.ctb",
        "UEB Grade 1 — Uncontracted",
        "BANA current standard (adopted 2016).  One braille cell per letter, "
        "no contractions.  Recommended for STEM, technical, or instructional "
        "materials where unambiguous cell-by-cell reading is required.",
    ),
    # ---- BANA-Approved Specialty Code ----
    "computer": (
        "en-us-comp8.ctb",
        "Computer Braille Code — 8-dot (CBC)",
        "BANA Computer Braille Code using 8-dot cells.  Use for source code, "
        "terminal output, file paths, and other computer-notation content.  "
        "8-dot cells provide a full ASCII mapping without ambiguity.",
    ),
    # ---- Legacy: English Braille American Edition (EBAE, pre-2016) ----
    "ebae_g2": (
        "en-us-g2.ctb",
        "EBAE Grade 2 — Contracted (Legacy)",
        "English Braille American Edition, contracted — the US standard prior "
        "to UEB adoption in 2016.  Use only for compatibility with pre-2016 "
        "documents or readers trained exclusively in EBAE.",
    ),
    "ebae_g1": (
        "en-us-g1.ctb",
        "EBAE Grade 1 — Uncontracted (Legacy)",
        "English Braille American Edition, uncontracted.  Legacy table.  "
        "Use UEB Grade 1 for new work.",
    ),
}

#: Default grade key — UEB Grade 2, the BANA literary standard.
DEFAULT_GRADE: str = "ueb_g2"

OUTPUT_FORMATS: dict[str, str] = {
    "unicode": "Unicode Braille (⠓⠑⠇⠇⠕)",
    "brf": "BRF — ASCII Braille Ready Format (.brf, 40 cells/line)",
}

# Display table that maps braille cells to printable ASCII (BRF convention).
# en-us-brf.dis is the standard BANA/North-American BRF mapping.
_BRF_DIS: str = "en-us-brf.dis"

# Unicode display table — maps braille cells to U+2800 Unicode Braille.
_UNICODE_DIS: str = "unicode.dis"


# ---------------------------------------------------------------------------
# Public exceptions
# ---------------------------------------------------------------------------


class BrailleError(Exception):
    """Raised when a braille translation or back-translation fails."""


# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------


def braille_available() -> bool:
    """Return True if the ``louis`` library is installed and functional."""
    return _louis is not None


def get_unavailability_reason() -> str:
    """Return a human-readable explanation of why braille is unavailable."""
    if _louis is not None:
        return ""
    if _IMPORT_ERROR:
        return (
            "The liblouis Python bindings (``louis``) are not installed. "
            f"Install with: pip install louis   (error: {_IMPORT_ERROR})"
        )
    return "liblouis Python bindings are not available on this system."


# ---------------------------------------------------------------------------
# BRF formatting helpers (BANA-compliant)
# ---------------------------------------------------------------------------


def format_brf_output(
    text: str,
    line_length: int = BRF_LINE_LENGTH,
    page_length: int = BRF_PAGE_LENGTH,
    paginate: bool = False,
) -> str:
    """Wrap BRF text at the BANA-standard line length (40 cells per line).

    BANA Formats Guidelines §1.2 specifies:
    - Line length: 40 cells
    - Page length: 25 lines

    Word-wrap is applied at word boundaries where possible.  Hard wraps are
    used only when a single token exceeds the line length.

    Args:
        text: Raw BRF text from liblouis (ASCII braille characters).
        line_length: Cells per line.  Defaults to ``BRF_LINE_LENGTH`` (40).
        page_length: Lines per page.  Defaults to ``BRF_PAGE_LENGTH`` (25).
        paginate: If True, insert a form-feed character (\\x0c) after each
            page of ``page_length`` lines.  Disabled by default for plain
            file output; enable for embosser-ready streams.

    Returns:
        BRF text with BANA-compliant line wrapping (and optional pagination).
    """
    raw_lines = text.splitlines()
    wrapped: list[str] = []

    for raw_line in raw_lines:
        if not raw_line.strip():
            wrapped.append("")
            continue
        # Word-wrap within each source line at line_length cells.
        remaining = raw_line
        while len(remaining) > line_length:
            # Prefer breaking at the last space at or before the limit.
            break_pos = remaining.rfind(" ", 0, line_length + 1)
            if break_pos <= 0:
                # No space -- hard wrap at the cell limit.
                break_pos = line_length
            wrapped.append(remaining[:break_pos].rstrip())
            remaining = remaining[break_pos:].lstrip()
        if remaining:
            wrapped.append(remaining)

    if not paginate:
        return "\n".join(wrapped)

    # Insert form-feed (ASCII 0x0C) between pages.
    pages: list[str] = []
    for i in range(0, len(wrapped), page_length):
        page_lines = wrapped[i : i + page_length]
        pages.append("\n".join(page_lines))
    return "\x0c".join(pages)


# ---------------------------------------------------------------------------
# Forward translation: text → braille
# ---------------------------------------------------------------------------


def text_to_braille(
    text: str,
    *,
    grade: str = DEFAULT_GRADE,
    output_format: Literal["unicode", "brf"] = "unicode",
) -> str:
    """Translate plain English text to braille per BANA standards.

    Args:
        text: Input text.  Must be non-empty, max ``MAX_INPUT_CHARS`` chars.
        grade: One of the keys in ``GRADES`` (default ``"ueb_g2"`` — BANA
            current literary standard).
        output_format: ``"unicode"`` for Unicode Braille (U+2800–U+28FF);
            ``"brf"`` for ASCII BRF wrapped at the BANA 40-cell line limit.

    Returns:
        Translated braille string in the requested format.

    Raises:
        BrailleError: On any translation failure or missing library.
    """
    if not braille_available():
        raise BrailleError(get_unavailability_reason())

    if not text or not text.strip():
        raise BrailleError("Input text is empty.")

    if len(text) > MAX_INPUT_CHARS:
        raise BrailleError(
            f"Input too long ({len(text):,} chars). "
            f"Maximum is {MAX_INPUT_CHARS:,} characters per request."
        )

    if grade not in GRADES:
        raise BrailleError(
            f"Unknown grade '{grade}'. Valid choices: {', '.join(GRADES)}."
        )
    if output_format not in OUTPUT_FORMATS:
        raise BrailleError(
            f"Unknown output format '{output_format}'. "
            f"Valid choices: {', '.join(OUTPUT_FORMATS)}."
        )

    table_file, _display_name, _desc = GRADES[grade]

    try:
        if output_format == "brf":
            # BRF: prepend the BANA/North-American BRF display table so
            # liblouis maps braille cells to printable ASCII characters.
            result: str = _louis.translateString(  # type: ignore[union-attr]
                [_BRF_DIS, table_file], text
            )
            # Apply BANA 40-cell line wrapping.
            result = format_brf_output(result)
        else:
            # Unicode Braille: use the unicode.dis display table so output
            # characters are in the standard U+2800–U+28FF range.
            result = _louis.translateString(  # type: ignore[union-attr]
                [_UNICODE_DIS, table_file], text
            )
    except Exception as exc:
        raise BrailleError(f"Translation failed: {exc}") from exc

    return result


# ---------------------------------------------------------------------------
# Back-translation: braille → text
# ---------------------------------------------------------------------------


def braille_to_text(
    braille_text: str,
    *,
    grade: str = DEFAULT_GRADE,
) -> str:
    """Back-translate braille (Unicode or BRF ASCII) to plain English text.

    Both Unicode Braille (U+2800–U+28FF) and ASCII BRF representations are
    accepted.  BRF input is normalised to Unicode Braille before translation.

    Note: Back-translation accuracy is inherently limited for Grade 2/EBAE
    contracted braille because contraction is a lossy operation (multiple
    print forms may map to the same braille cells).  BANA UEB Rules §1.3
    documents these limitations.  Grade 1 and Computer Braille back-
    translation are lossless for the ASCII range.

    Args:
        braille_text: Input braille string (Unicode or BRF ASCII).
        grade: The ``GRADES`` key matching the grade the input was encoded in.

    Returns:
        Back-translated plain-text string.

    Raises:
        BrailleError: On any back-translation failure or missing library.
    """
    if not braille_available():
        raise BrailleError(get_unavailability_reason())

    if not braille_text or not braille_text.strip():
        raise BrailleError("Input braille text is empty.")

    if len(braille_text) > MAX_INPUT_CHARS:
        raise BrailleError(
            f"Input too long ({len(braille_text):,} chars). "
            f"Maximum is {MAX_INPUT_CHARS:,} characters per request."
        )

    if grade not in GRADES:
        raise BrailleError(
            f"Unknown grade '{grade}'. Valid choices: {', '.join(GRADES)}."
        )

    table_file, _display_name, _desc = GRADES[grade]

    # Normalise BRF ASCII → Unicode Braille if needed before back-translation.
    normalized = _normalize_brf_if_needed(braille_text)

    try:
        result: str = _louis.backTranslateString(  # type: ignore[union-attr]
            [table_file], normalized
        )
    except Exception as exc:
        raise BrailleError(f"Back-translation failed: {exc}") from exc

    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _normalize_brf_if_needed(text: str) -> str:
    """Convert BRF ASCII braille to Unicode Braille when the input is BRF.

    BRF uses characters in the range 0x20–0x5F (space through underscore).
    The mapping is: braille_unicode = chr(0x2800 + (ord(brf_char) - 0x20)).
    Unicode Braille is detected by the presence of any character in U+2800–
    U+28FF; if found the string is returned unchanged.
    """
    if any("\u2800" <= ch <= "\u28ff" for ch in text):
        return text  # Already Unicode Braille.

    converted: list[str] = []
    for ch in text:
        code = ord(ch)
        if 0x20 <= code <= 0x5F:
            converted.append(chr(0x2800 + (code - 0x20)))
        else:
            # Pass through non-BRF characters (newlines, carriage returns, etc.)
            converted.append(ch)
    return "".join(converted)


def louis_version() -> str:
    """Return the liblouis version string, or 'unavailable'."""
    if _louis is None:
        return "unavailable"
    try:
        return _louis.version()  # type: ignore[union-attr]
    except Exception:
        return "unknown"
