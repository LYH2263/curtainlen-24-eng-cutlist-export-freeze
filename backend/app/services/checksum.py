"""Stable content checksum for frozen cut-sheet exports.

The checksum covers exactly the line items and the totals — nothing else —
so a frozen file can be re-verified without touching the database.
"""
import hashlib
import json


def canonical_json(payload) -> str:
    """Deterministic serialization: sorted keys, tight separators, UTF-8."""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_checksum(lines, totals) -> str:
    """Stable hash over the export's line items and totals."""
    payload = {"lines": lines, "totals": totals}
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
