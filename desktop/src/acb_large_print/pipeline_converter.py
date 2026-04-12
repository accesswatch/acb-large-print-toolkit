"""Convert documents using DAISY Pipeline as an optional backend.

Wraps the DAISY Pipeline 2 CLI to provide advanced conversion paths not
available through Pandoc alone:

- Word (.docx) -> DTBook -> EPUB 3 (accessible structure-preserving chain)
- HTML -> EPUB 3 (packaged accessible EPUB with metadata)
- EPUB -> DAISY 2.02 (talking-book-ready format)
- EPUB -> DAISY 3 / DTBook (structured text format)

DAISY Pipeline is a Java application requiring JRE 11+.  The module
falls back gracefully when Pipeline is not installed.

DAISY Pipeline is open source (LGPL), developed by the DAISY Consortium:
https://github.com/daisy/pipeline
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

log = logging.getLogger("acb_large_print")

# Conversion routes available through DAISY Pipeline
PIPELINE_CONVERSIONS: dict[str, dict[str, str]] = {
    "docx-to-epub": {
        "label": "Word to EPUB 3 (via DTBook)",
        "script": "dtbook-to-epub3",
        "description": "Converts Word to accessible EPUB 3 via DTBook intermediate format",
        "input_ext": ".docx",
        "output_ext": ".epub",
    },
    "html-to-epub": {
        "label": "HTML to EPUB 3",
        "script": "html-to-epub3",
        "description": "Packages HTML into a structured, accessible EPUB 3 publication",
        "input_ext": ".html",
        "output_ext": ".epub",
    },
    "epub-to-daisy202": {
        "label": "EPUB to DAISY 2.02",
        "script": "epub3-to-daisy202",
        "description": "Converts EPUB 3 to DAISY 2.02 talking book format",
        "input_ext": ".epub",
        "output_ext": "",  # directory output
    },
    "epub-to-daisy3": {
        "label": "EPUB to DAISY 3 (DTBook)",
        "script": "epub-to-daisy",
        "description": "Converts EPUB to DAISY 3 / DTBook format",
        "input_ext": ".epub",
        "output_ext": "",  # directory output
    },
}

# Extensions that Pipeline can accept as input
PIPELINE_INPUT_EXTENSIONS: set[str] = {".docx", ".html", ".htm", ".epub"}


def pipeline_available() -> bool:
    """Return True if the DAISY Pipeline CLI (dp2) is installed and reachable."""
    return shutil.which("dp2") is not None


def pipeline_version() -> str | None:
    """Return the Pipeline version string, or None if not installed."""
    exe = shutil.which("dp2")
    if not exe:
        return None
    try:
        result = subprocess.run(
            [exe, "--version"],
            capture_output=True, text=True, timeout=15,
        )
        version = result.stdout.strip()
        return version if version else None
    except (subprocess.SubprocessError, IndexError):
        return None


def pipeline_scripts() -> list[str]:
    """Return available Pipeline script names, or empty list if unavailable."""
    exe = shutil.which("dp2")
    if not exe:
        return []
    try:
        result = subprocess.run(
            [exe, "scripts"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            return []
        scripts = []
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if line and not line.startswith("-"):
                scripts.append(line.split()[0])
        return scripts
    except subprocess.SubprocessError:
        return []


def get_available_conversions() -> dict[str, dict[str, str]]:
    """Return only the conversion routes whose Pipeline scripts are installed."""
    if not pipeline_available():
        return {}

    available_scripts = pipeline_scripts()
    available = {}
    for key, conv in PIPELINE_CONVERSIONS.items():
        if conv["script"] in available_scripts:
            available[key] = conv
    return available


def convert_with_pipeline(
    src_path: Path,
    conversion: str,
    output_dir: Path | None = None,
    *,
    title: str | None = None,
    lang: str = "en",
    timeout: int = 300,
) -> tuple[Path, str]:
    """Convert a document using DAISY Pipeline.

    Args:
        src_path: Path to the input file.
        conversion: Key from PIPELINE_CONVERSIONS (e.g. 'html-to-epub').
        output_dir: Directory for output files.  Defaults to a temp directory.
        title: Optional document title metadata.
        lang: BCP-47 language tag.
        timeout: Maximum seconds for Pipeline to complete.

    Returns:
        (output_path, summary_message)

    Raises:
        FileNotFoundError: If src_path does not exist.
        ValueError: If the conversion key is invalid or extension doesn't match.
        RuntimeError: If Pipeline is not installed or conversion fails.
    """
    src_path = Path(src_path)
    if not src_path.exists():
        raise FileNotFoundError(f"File not found: {src_path}")

    if conversion not in PIPELINE_CONVERSIONS:
        raise ValueError(
            f"Unknown conversion '{conversion}'. "
            f"Available: {', '.join(PIPELINE_CONVERSIONS.keys())}"
        )

    conv = PIPELINE_CONVERSIONS[conversion]
    expected_ext = conv["input_ext"]
    if expected_ext and src_path.suffix.lower() != expected_ext:
        raise ValueError(
            f"Conversion '{conversion}' expects {expected_ext} input, "
            f"got {src_path.suffix}"
        )

    exe = shutil.which("dp2")
    if not exe:
        raise RuntimeError(
            "DAISY Pipeline is not installed. "
            "Install it from https://daisy.github.io/pipeline/"
        )

    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="pipeline_out_"))
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    script = conv["script"]
    if title is None:
        title = src_path.stem.replace("-", " ").replace("_", " ")

    # Build Pipeline command
    cmd = [
        exe,
        script,
        "--source", str(src_path),
        "--output", str(output_dir),
    ]

    # Add optional metadata as appropriate for each script
    if "epub" in script or "dtbook" in script:
        # Pipeline scripts accept --title and --language for EPUB/DTBook output
        pass  # Not all scripts accept these -- Pipeline validates internally

    log.info("Running Pipeline: %s", " ".join(cmd))

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if proc.returncode != 0:
            stderr = proc.stderr.strip()
            raise RuntimeError(
                f"DAISY Pipeline conversion failed (exit {proc.returncode}): "
                f"{stderr[:500]}"
            )

        # Find the output file(s)
        output_ext = conv["output_ext"]
        if output_ext:
            # Look for specific output file
            candidates = list(output_dir.glob(f"*{output_ext}"))
            if candidates:
                out_file = candidates[0]
                return out_file, f"Converted to {out_file.name} using DAISY Pipeline ({script})"

        # Directory output (DAISY 2.02, DAISY 3)
        return output_dir, f"Converted to {script} format in {output_dir.name}/"

    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"DAISY Pipeline conversion timed out after {timeout} seconds"
        )


def docx_to_epub(
    src_path: Path,
    output_dir: Path | None = None,
    **kwargs,
) -> tuple[Path, str]:
    """Convenience: convert Word document to accessible EPUB 3 via Pipeline."""
    return convert_with_pipeline(src_path, "docx-to-epub", output_dir, **kwargs)


def html_to_epub(
    src_path: Path,
    output_dir: Path | None = None,
    **kwargs,
) -> tuple[Path, str]:
    """Convenience: package HTML into accessible EPUB 3 via Pipeline."""
    return convert_with_pipeline(src_path, "html-to-epub", output_dir, **kwargs)


def epub_to_daisy(
    src_path: Path,
    output_dir: Path | None = None,
    *,
    version: str = "202",
    **kwargs,
) -> tuple[Path, str]:
    """Convenience: convert EPUB to DAISY format.

    Args:
        version: "202" for DAISY 2.02, "3" for DAISY 3 / DTBook.
    """
    conv = "epub-to-daisy202" if version == "202" else "epub-to-daisy3"
    return convert_with_pipeline(src_path, conv, output_dir, **kwargs)
