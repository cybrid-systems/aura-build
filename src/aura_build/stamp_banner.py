"""Banner comment vs stamp-info hash literal agreement.

true agrees only with #t. false agrees only with #f. A missing banner or
literal is disagreement. This module does not set incr_proven or fiber_live.
"""

from __future__ import annotations

import re


def stamp_banner_agrees(text: str) -> bool:
    """True only when incr_proven and fiber_live banners match their #t/#f literals."""
    incr = _pair(text, "incr_proven")
    fiber = _pair(text, "fiber_live")
    if incr is None or fiber is None:
        return False
    return incr and fiber


def _pair(text: str, name: str) -> bool | None:
    banner = re.search(rf"(?m)^;\s*{name}=(true|false)\s*$", text)
    literal = re.search(rf'"{name}"\s+#([tf])\b', text)
    if banner is None or literal is None:
        return None
    want = "t" if banner.group(1) == "true" else "f"
    return want == literal.group(1)
