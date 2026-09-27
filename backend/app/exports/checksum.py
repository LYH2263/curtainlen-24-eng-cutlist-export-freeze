"""裁幅清单内容的稳定哈希。

只依赖标准库，保证核对命令在任何环境都能重算出同一摘要。
"""
import hashlib
import json


def canonical_json(obj) -> str:
    """确定性序列化：键排序、紧凑分隔符、UTF-8 中文不转义。"""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_checksum(line_items, totals) -> str:
    """对行项目与合计计算稳定哈希（sha256）。"""
    blob = canonical_json({"line_items": line_items, "totals": totals})
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()
