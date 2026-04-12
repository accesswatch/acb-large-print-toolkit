"""Convert documents to ACB-compliant HTML using Pandoc.

Wraps the Pandoc CLI to convert text-oriented document formats into
standalone, accessible HTML with embedded ACB Large Print CSS.
Supported input: .md, .rst, .odt, .rtf, .docx, .epub.

Pandoc is an external dependency -- not a Python package.  The module
falls back gracefully when it is not installed.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

log = logging.getLogger("acb_large_print")

# Input formats Pandoc handles well for ACB HTML output.
# Deliberately scoped to document types relevant to accessibility conversion
# (not the full 40+ formats Pandoc supports).
PANDOC_INPUT_EXTENSIONS: set[str] = {
    ".md",      # Markdown (GFM)
    ".rst",     # reStructuredText
    ".odt",     # OpenDocument Text
    ".rtf",     # Rich Text Format
    ".docx",    # Word (Pandoc's own reader)
    ".epub",    # ePub e-books
}

# Pandoc input format flag for each extension
_INPUT_FORMAT: dict[str, str] = {
    ".md": "gfm",
    ".rst": "rst",
    ".odt": "odt",
    ".rtf": "rtf",
    ".docx": "docx",
    ".epub": "epub",
}

# ---------------------------------------------------------------------------
# Minimal ACB CSS for embedding in Pandoc output
# (mirrors styles/acb-large-print.css -- keep in sync)
# ---------------------------------------------------------------------------
_ACB_CSS = """\
html { font-size: 100%; }
body {
  font-family: Arial, sans-serif;
  font-size: 1.5rem;
  font-weight: 400;
  color: #1a1a1a;
  background-color: #ffffff;
  text-align: left;
  line-height: 1.5;
  letter-spacing: 0.12em;
  word-spacing: 0.16em;
  margin: 0 auto;
  padding: 1rem 1rem;
  max-width: 70ch;
  hyphens: none;
  -webkit-hyphens: none;
  columns: 1;
}
h1, h2 {
  font-family: Arial, sans-serif;
  font-size: 1.833rem;
  font-weight: 700;
  line-height: 1.5;
  text-align: left;
  text-transform: none;
  margin-top: 1.5em;
  margin-bottom: 1em;
}
h3, h4, h5, h6 {
  font-family: Arial, sans-serif;
  font-size: 1.667rem;
  font-weight: 700;
  line-height: 1.5;
  text-align: left;
  text-transform: none;
  margin-top: 1.5em;
  margin-bottom: 1em;
}
p {
  margin-top: 0;
  margin-bottom: 2em;
}
em, .acb-emphasis {
  font-style: normal;
  text-decoration: underline;
  text-decoration-thickness: 2px;
  text-underline-offset: 3px;
}
u {
  text-decoration: underline;
  text-decoration-thickness: 2px;
  text-underline-offset: 3px;
}
a {
  color: #0055cc;
  text-decoration: underline;
  text-decoration-thickness: 1px;
}
a:hover, a:focus {
  text-decoration-thickness: 2px;
  outline: 2px solid currentColor;
  outline-offset: 2px;
}
ul { list-style-type: disc; padding-left: 1.5em; margin-top: 0; margin-bottom: 2em; }
ul li { margin-bottom: 0; padding-left: 0.5em; }
ul li::marker { color: #1a1a1a; font-size: 1.2em; }
ol { list-style-type: decimal; padding-left: 1.5em; margin-top: 0; margin-bottom: 2em; }
ol li { margin-bottom: 0; padding-left: 0.5em; }
table { border-collapse: collapse; width: 100%; font-size: inherit; }
th, td { text-align: left; padding: 0.5em 0.75em; border: 1px solid #666; }
th { font-weight: 700; }
caption { font-size: 1.5rem; font-weight: 700; text-align: left; margin-bottom: 0.5em; }
figure { margin: 1.5em 0; }
figcaption { font-size: 1.5rem; margin-top: 0.5em; }
img { max-width: 100%; height: auto; }
@media print {
  body { line-height: 1.15; color: #000; background-color: #faf8f0; max-width: none; padding: 0; }
  @page { margin: 1in; }
  @page :left { margin-left: 1.5in; }
  a { color: #000; text-decoration: underline; }
}
"""


def pandoc_available() -> bool:
    """Return True if the Pandoc CLI is installed and reachable."""
    return shutil.which("pandoc") is not None


def pandoc_version() -> str | None:
    """Return the Pandoc version string, or None if not installed."""
    exe = shutil.which("pandoc")
    if not exe:
        return None
    try:
        result = subprocess.run(
            [exe, "--version"],
            capture_output=True, text=True, timeout=10,
        )
        first_line = result.stdout.strip().splitlines()[0]
        return first_line  # e.g. "pandoc 3.1.13"
    except (subprocess.SubprocessError, IndexError):
        return None


def convert_to_html(
    src_path: Path,
    output_path: Path | None = None,
    *,
    title: str | None = None,
    css_path: Path | None = None,
    lang: str = "en",
) -> tuple[Path, str]:
    """Convert a document to ACB-compliant standalone HTML via Pandoc.

    Args:
        src_path: Path to input file (.md, .rst, .odt, .rtf, .docx).
        output_path: Optional path for the .html file.  Defaults to same
            directory / stem as *src_path* with ``.html`` extension.
        title: Document title for the HTML ``<title>`` element.
            Defaults to the input filename stem.
        css_path: Optional path to an external CSS file.  If provided,
            its contents are embedded in the HTML ``<head>``.  If omitted,
            the built-in ACB Large Print CSS is used.
        lang: BCP-47 language tag for the ``<html lang>`` attribute.

    Returns:
        (output_path, html_text)

    Raises:
        FileNotFoundError: If *src_path* does not exist.
        ValueError: If the extension is not in PANDOC_INPUT_EXTENSIONS.
        RuntimeError: If Pandoc is not installed or conversion fails.
    """
    src_path = Path(src_path)
    if not src_path.exists():
        raise FileNotFoundError(f"File not found: {src_path}")

    ext = src_path.suffix.lower()
    if ext not in PANDOC_INPUT_EXTENSIONS:
        raise ValueError(
            f"Cannot convert '{ext}' files to HTML. "
            f"Supported: {', '.join(sorted(PANDOC_INPUT_EXTENSIONS))}"
        )

    exe = shutil.which("pandoc")
    if not exe:
        raise RuntimeError(
            "Pandoc is not installed. "
            "Install it from https://pandoc.org/installing.html"
        )

    if output_path is None:
        output_path = src_path.with_suffix(".html")
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if title is None:
        title = src_path.stem.replace("-", " ").replace("_", " ")

    # Resolve CSS: use provided file or the built-in ACB CSS
    if css_path and css_path.exists():
        css_text = css_path.read_text(encoding="utf-8")
    else:
        css_text = _ACB_CSS

    # Write a temporary header-include file with the CSS
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        header_file = tmp_dir / "acb-header.html"
        header_file.write_text(
            f"<style>\n{css_text}\n</style>\n",
            encoding="utf-8",
        )

        input_fmt = _INPUT_FORMAT.get(ext, "markdown")

        cmd = [
            exe,
            "--standalone",
            "--from", input_fmt,
            "--to", "html5",
            "--include-in-header", str(header_file),
            "--metadata", f"title={title}",
            "--metadata", f"lang={lang}",
            "--output", str(output_path),
            str(src_path),
        ]

        log.info("Running: %s", " ".join(cmd))
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            stderr = result.stderr.strip()
            raise RuntimeError(
                f"Pandoc conversion failed (exit code {result.returncode}): "
                f"{stderr}"
            )

        html_text = output_path.read_text(encoding="utf-8")
        log.info(
            "Pandoc conversion complete: %s -> %s (%d characters)",
            src_path.name, output_path.name, len(html_text),
        )
        return output_path, html_text

    finally:
        # Clean up temp header file
        shutil.rmtree(tmp_dir, ignore_errors=True)
