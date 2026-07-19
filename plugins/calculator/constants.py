from __future__ import annotations

import math
import re
from typing import Any, Callable

INTENT_PATTERN = r"\b(rechnen|plus|minus|mal|geteilt|[\d\+\-\*/\(\)]|sqrt|sin|cos|tan|asin|acos|atan|sinh|cosh|tanh|log|ln|exp|abs|π|pi|e)\b"

ACTION_PRESETS: dict[str, str] = {
    "preset_percentage": "249 * 0.85",
    "preset_circle_area": "pi * 12**2",
    "preset_trig": "sin(30) + cos(60)",
    "preset_log_mix": "log(1000) + ln(e**2)",
}

MATH_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "log": math.log10,
    "ln": math.log,
    "exp": math.exp,
    "abs": abs,
    "floor": math.floor,
    "ceil": math.ceil,
    "round": round,
    "factorial": math.factorial,
    "min": min,
    "max": max,
}

MATH_CONSTANTS: dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}

UNICODE_PI_PATTERN = re.compile(r"π")
