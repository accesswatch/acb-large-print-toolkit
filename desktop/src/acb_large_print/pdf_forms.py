"""PDF form inspection for round-trip eligibility and field extraction."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import fitz  # PyMuPDF

    HAS_PYMUPDF = True
except ImportError:  # pragma: no cover - exercised by unit tests via monkeypatch
    HAS_PYMUPDF = False

_NOISE_TOKENS = {"fld", "field", "txt", "cb", "rb", "grp", "opt", "val"}


def inspect_pdf_form(file_path: str | Path) -> dict[str, Any]:
    """Inspect a PDF and return v1 slice-1 form classification and extraction."""
    src = Path(file_path)
    result: dict[str, Any] = {
        "file_path": str(src),
        "classification": {
            "class": "unsupported",
            "round_trip_support": "no",
            "supported": False,
            "reason": "",
        },
        "warnings": [],
        "fields": [],
        "summary": {
            "total_fields": 0,
            "field_type_counts": {},
            "low_confidence_fields": 0,
        },
    }

    if not HAS_PYMUPDF:
        result["classification"]["reason"] = (
            "PyMuPDF is not installed; PDF form inspection requires it "
            "(pip install pymupdf)."
        )
        result["warnings"].append("pymupdf_unavailable")
        return result

    doc = fitz.open(str(src))
    try:
        if _has_xfa(doc):
            result["classification"] = {
                "class": "xfa_unsupported",
                "round_trip_support": "no",
                "supported": False,
                "reason": (
                    "This PDF appears to use XFA forms, which are not supported "
                    "for v1 round-trip write-back."
                ),
            }
            result["warnings"].append("xfa_form_not_supported")
            return result

        extracted_fields = _extract_fields(doc)
        result["fields"] = extracted_fields
        result["summary"] = _build_summary(extracted_fields)

        if not extracted_fields:
            result["classification"] = {
                "class": "static_or_flattened",
                "round_trip_support": "no",
                "supported": False,
                "reason": (
                    "No interactive AcroForm fields were detected. "
                    "Use assisted template or surrogate mode."
                ),
            }
            result["warnings"].append("no_interactive_fields")
            return result

        if any(f["field_type"] == "signature" for f in extracted_fields):
            result["classification"] = {
                "class": "signed_or_signature_fields",
                "round_trip_support": "limited",
                "supported": False,
                "reason": (
                    "Signature fields were detected. Write-back may invalidate "
                    "signatures and is blocked by default."
                ),
            }
            result["warnings"].append("signature_present")
            return result

        weak_ratio = _weak_metadata_ratio(extracted_fields)
        if weak_ratio >= 0.40:
            result["classification"] = {
                "class": "acroform_weak_metadata",
                "round_trip_support": "limited",
                "supported": True,
                "reason": (
                    "AcroForm fields were found, but metadata quality is weak. "
                    "Helper review is recommended before fill and write-back."
                ),
            }
            result["warnings"].append("weak_field_metadata")
        else:
            result["classification"] = {
                "class": "acroform_supported",
                "round_trip_support": "yes",
                "supported": True,
                "reason": (
                    "AcroForm fields were detected and are eligible for v1 "
                    "round-trip flow."
                ),
            }

        return result
    finally:
        doc.close()


def _has_xfa(doc: Any) -> bool:
    """Return True when catalog indicates XFA."""
    try:
        is_form_pdf = int(getattr(doc, "is_form_pdf", 0) or 0)
        if is_form_pdf == 2:
            return True
    except Exception:
        pass

    try:
        catalog = doc.pdf_catalog()
        if not catalog:
            return False
        xfa = doc.xref_get_key(catalog, "XFA")
        return bool(xfa and xfa[0] != "null")
    except Exception:
        return False


def _extract_fields(doc: Any) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    seen_names: dict[str, int] = {}

    for page_index in range(getattr(doc, "page_count", 0)):
        page = doc[page_index]
        widgets = list(page.widgets() or [])
        for widget_index, widget in enumerate(widgets, start=1):
            raw_name = str(getattr(widget, "field_name", "") or "").strip()
            inferred = _infer_label(widget, raw_name)
            field_type = _map_field_type(getattr(widget, "field_type", None))

            option_values = _normalize_options(getattr(widget, "choice_values", None))
            warnings: list[str] = []
            if inferred["confidence"] < 0.6:
                warnings.append("low_label_confidence")
            if not raw_name:
                warnings.append("missing_field_name")

            key = raw_name or f"__unnamed_{page_index + 1}_{widget_index}"
            seen_names[key] = seen_names.get(key, 0) + 1

            fields.append(
                {
                    "raw_field_name": raw_name,
                    "widget_id": str(getattr(widget, "xref", "") or f"p{page_index + 1}-w{widget_index}"),
                    "page_number": page_index + 1,
                    "field_type": field_type,
                    "current_value": _normalize_value(getattr(widget, "field_value", "")),
                    "option_values": option_values,
                    "inferred_label": {
                        "value": inferred["label"],
                        "confidence": inferred["confidence"],
                        "evidence_sources": inferred["evidence_sources"],
                        "human_confirmed": False,
                    },
                    "warnings": warnings,
                }
            )

    for field in fields:
        name = field["raw_field_name"] or ""
        key = name or f"__unnamed_{field['page_number']}_{field['widget_id']}"
        if seen_names.get(key, 0) > 1:
            field["warnings"].append("duplicate_field_name")

    return fields


def _map_field_type(field_type: Any) -> str:
    mapping = {
        getattr(fitz, "PDF_WIDGET_TYPE_TEXT", -1): "text",
        getattr(fitz, "PDF_WIDGET_TYPE_CHECKBOX", -1): "checkbox",
        getattr(fitz, "PDF_WIDGET_TYPE_RADIOBUTTON", -1): "radio",
        getattr(fitz, "PDF_WIDGET_TYPE_LISTBOX", -1): "listbox",
        getattr(fitz, "PDF_WIDGET_TYPE_COMBOBOX", -1): "combobox",
        getattr(fitz, "PDF_WIDGET_TYPE_SIGNATURE", -1): "signature",
        getattr(fitz, "PDF_WIDGET_TYPE_BUTTON", -1): "button",
    }
    if field_type in mapping:
        return mapping[field_type]
    return "unknown"


def _normalize_options(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    return [text] if text else []


def _normalize_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _infer_label(widget: Any, raw_name: str) -> dict[str, Any]:
    explicit = str(getattr(widget, "field_label", "") or "").strip()
    if explicit:
        return {
            "label": explicit,
            "confidence": 0.96,
            "evidence_sources": ["explicit_field_label"],
        }

    tooltip = str(getattr(widget, "field_name_alt", "") or "").strip()
    if tooltip:
        return {
            "label": tooltip,
            "confidence": 0.9,
            "evidence_sources": ["alternate_field_name"],
        }

    parsed = _parse_field_name(raw_name)
    if parsed:
        confidence = 0.78 if raw_name else 0.45
        source = "parsed_field_name" if raw_name else "fallback_unknown_name"
        return {
            "label": parsed,
            "confidence": confidence,
            "evidence_sources": [source],
        }

    return {
        "label": "Unlabeled field",
        "confidence": 0.35,
        "evidence_sources": ["fallback_default_label"],
    }


def _parse_field_name(raw_name: str) -> str:
    if not raw_name:
        return ""

    text = raw_name
    text = text.replace(".", " ")
    text = text.replace("_", " ")
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    text = re.sub(r"[^A-Za-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""

    tokens = []
    for token in text.split(" "):
        low = token.lower()
        if low in _NOISE_TOKENS:
            continue
        if low == "dob":
            tokens.append("Date of Birth")
            continue
        if low == "zip":
            tokens.append("ZIP")
            continue
        tokens.append(token.title())

    return " ".join(t for t in tokens if t).strip()


def _weak_metadata_ratio(fields: list[dict[str, Any]]) -> float:
    if not fields:
        return 1.0
    weak = 0
    for field in fields:
        conf = float(field.get("inferred_label", {}).get("confidence", 0.0))
        raw_name = str(field.get("raw_field_name", "") or "").strip()
        if conf < 0.6 or not raw_name:
            weak += 1
    return weak / len(fields)


def _build_summary(fields: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    low_conf = 0
    for field in fields:
        t = str(field.get("field_type", "unknown"))
        counts[t] = counts.get(t, 0) + 1
        conf = float(field.get("inferred_label", {}).get("confidence", 0.0))
        if conf < 0.6:
            low_conf += 1
    return {
        "total_fields": len(fields),
        "field_type_counts": counts,
        "low_confidence_fields": low_conf,
    }

