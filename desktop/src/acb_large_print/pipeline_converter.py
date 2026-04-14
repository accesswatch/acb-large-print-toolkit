"""Convert documents using DAISY Pipeline 2 as a REST service.

Connects to a DAISY Pipeline 2 web service (typically running as a Docker
sidecar) to provide advanced conversion paths not available through Pandoc
alone:

- Word (.docx) -> DTBook -> EPUB 3 (accessible structure-preserving chain)
- HTML -> EPUB 3 (packaged accessible EPUB with metadata)
- EPUB -> DAISY 2.02 (talking-book-ready format)
- EPUB -> DAISY 3 / DTBook (structured text format)

The Pipeline service must run in local-filesystem mode with authentication
disabled (the default Docker configuration).  Communication uses the Pipeline
REST API documented at https://daisy.github.io/pipeline/WebServiceAPI.

DAISY Pipeline is open source (LGPL), developed by the DAISY Consortium:
https://github.com/daisy/pipeline
"""

from __future__ import annotations

import io
import logging
import os
import time
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import requests

log = logging.getLogger("acb_large_print")

# Where the Pipeline web service lives -- override with PIPELINE_URL env var.
PIPELINE_BASE_URL = os.environ.get("PIPELINE_URL", "http://pipeline:8181/ws")

# Namespace used in Pipeline XML responses
_NS = "http://www.daisy.org/ns/pipeline/data"

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

# ---------------------------------------------------------------------------
# Pipeline availability helpers
# ---------------------------------------------------------------------------


def pipeline_available() -> bool:
    """Return True if the Pipeline web service is reachable."""
    try:
        resp = requests.get(f"{PIPELINE_BASE_URL}/alive", timeout=5)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def pipeline_version() -> str | None:
    """Return the Pipeline version string, or None if not reachable."""
    try:
        resp = requests.get(f"{PIPELINE_BASE_URL}/alive", timeout=5)
        if resp.status_code != 200:
            return None
        root = ET.fromstring(resp.content)
        # <alive> element has @version attribute
        return root.get("version")
    except (requests.RequestException, ET.ParseError):
        return None


def pipeline_scripts() -> list[str]:
    """Return available Pipeline script names, or empty list if unavailable."""
    try:
        resp = requests.get(f"{PIPELINE_BASE_URL}/scripts", timeout=10)
        if resp.status_code != 200:
            return []
        root = ET.fromstring(resp.content)
        scripts = []
        for script_el in root.iter(f"{{{_NS}}}script"):
            script_id = script_el.get("id")
            if script_id:
                scripts.append(script_id)
        return scripts
    except (requests.RequestException, ET.ParseError):
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


# ---------------------------------------------------------------------------
# Job submission and result retrieval
# ---------------------------------------------------------------------------


def _wait_for_job(job_id: str, timeout: int = 300, poll: float = 2.0) -> ET.Element:
    """Poll a Pipeline job until it completes or times out.

    Returns the final job XML element.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        resp = requests.get(f"{PIPELINE_BASE_URL}/jobs/{job_id}", timeout=10)
        resp.raise_for_status()
        job_el = ET.fromstring(resp.content)
        status = job_el.get("status", "")
        if status in ("SUCCESS", "FAIL", "ERROR"):
            return job_el
        time.sleep(poll)
    raise RuntimeError(f"Pipeline job {job_id} timed out after {timeout}s")


def _download_result(job_id: str) -> bytes:
    """Download the zipped result of a completed Pipeline job."""
    resp = requests.get(f"{PIPELINE_BASE_URL}/jobs/{job_id}/result", timeout=60)
    resp.raise_for_status()
    return resp.content


def _delete_job(job_id: str) -> None:
    """Clean up a Pipeline job."""
    try:
        requests.delete(f"{PIPELINE_BASE_URL}/jobs/{job_id}", timeout=5)
    except requests.RequestException:
        pass  # best-effort cleanup


def convert_with_pipeline(
    src_path: Path,
    conversion: str,
    output_dir: Path | None = None,
    *,
    title: str | None = None,
    lang: str = "en",
    timeout: int = 300,
) -> tuple[Path, str]:
    """Convert a document using DAISY Pipeline REST API.

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
        RuntimeError: If Pipeline is not reachable or conversion fails.
    """
    import tempfile

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

    if not pipeline_available():
        raise RuntimeError(
            "DAISY Pipeline service is not reachable at "
            f"{PIPELINE_BASE_URL}. Is the pipeline container running?"
        )

    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="pipeline_out_"))
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    script = conv["script"]
    if title is None:
        title = src_path.stem.replace("-", " ").replace("_", " ")

    # Build the jobRequest XML and zip the source file for multipart upload
    job_request_xml = (
        f'<jobRequest xmlns="http://www.daisy.org/ns/pipeline/data">'
        f'<script href="{PIPELINE_BASE_URL}/scripts/{script}"/>'
        f'<input name="source"><item value="./{src_path.name}"/></input>'
        f"</jobRequest>"
    )

    # Create a zip containing the source file
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(src_path, src_path.name)
    zip_buf.seek(0)

    # Submit the job via multipart POST
    log.info("Submitting Pipeline job: script=%s, source=%s", script, src_path.name)
    resp = requests.post(
        f"{PIPELINE_BASE_URL}/jobs",
        files={
            "job-request": ("job-request.xml", job_request_xml, "application/xml"),
            "job-data": ("job-data.zip", zip_buf, "application/zip"),
        },
        timeout=30,
    )
    if resp.status_code != 201:
        raise RuntimeError(
            f"Pipeline rejected the job (HTTP {resp.status_code}): "
            f"{resp.text[:500]}"
        )

    job_el = ET.fromstring(resp.content)
    job_id = job_el.get("id")
    if not job_id:
        raise RuntimeError("Pipeline returned a job with no ID")

    log.info("Pipeline job created: %s", job_id)

    try:
        # Wait for completion
        final = _wait_for_job(job_id, timeout=timeout)
        status = final.get("status", "")
        if status != "SUCCESS":
            raise RuntimeError(f"Pipeline job {job_id} ended with status: {status}")

        # Download the result zip
        result_bytes = _download_result(job_id)

        # Extract results to output_dir
        with zipfile.ZipFile(io.BytesIO(result_bytes)) as zf:
            zf.extractall(output_dir)

        # Find the output file
        output_ext = conv["output_ext"]
        if output_ext:
            candidates = list(output_dir.rglob(f"*{output_ext}"))
            if candidates:
                out_file = candidates[0]
                return (
                    out_file,
                    f"Converted to {out_file.name} using DAISY Pipeline ({script})",
                )

        # Directory output (DAISY 2.02, DAISY 3)
        return output_dir, f"Converted to {script} format in {output_dir.name}/"

    finally:
        _delete_job(job_id)


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
