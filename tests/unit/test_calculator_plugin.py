from __future__ import annotations

import asyncio

import pytest

from app.tools.executor import PluginExecutor


def test_calculator_does_not_break_function_names_with_constants() -> None:
    executor = PluginExecutor()

    result = asyncio.run(executor.execute("calculator", {"expression": "ceil(2.2) + e"}))

    assert "error" not in result
    assert pytest.approx(result["result"], rel=1e-8) == 5.71828183


def test_calculator_supports_degree_mode_from_settings() -> None:
    executor = PluginExecutor()

    result = asyncio.run(
        executor.execute(
            "calculator",
            {"expression": "sin(30)"},
            {"angle_mode": "deg", "precision": 6},
        )
    )

    assert "error" not in result
    assert pytest.approx(result["result"], rel=1e-6) == 0.5


def test_calculator_supports_preset_actions_without_expression() -> None:
    executor = PluginExecutor()

    result = asyncio.run(executor.execute("calculator", {"action": "preset_percentage"}))

    assert "error" not in result
    assert pytest.approx(result["result"], rel=1e-8) == 211.65


def test_calculator_rejects_keyword_arguments() -> None:
    executor = PluginExecutor()

    result = asyncio.run(executor.execute("calculator", {"expression": "round(1.234, ndigits=1)"}))

    assert result.get("error") == "Ungültige oder unsichere Zeichen im Ausdruck"


def test_calculator_rejects_boolean_constants() -> None:
    executor = PluginExecutor()

    result = asyncio.run(executor.execute("calculator", {"expression": "True + 1"}))

    assert result.get("error") == "Ungültige oder unsichere Zeichen im Ausdruck"


def test_calculator_supports_min_max_functions() -> None:
    executor = PluginExecutor()

    result = asyncio.run(executor.execute("calculator", {"expression": "max(2, min(10, 4))"}))

    assert "error" not in result
    assert result["result"] == 4


def test_calculator_supports_hyperbolic_functions() -> None:
    executor = PluginExecutor()

    result = asyncio.run(executor.execute("calculator", {"expression": "sinh(0) + cosh(0) + tanh(0)"}))

    assert "error" not in result
    assert pytest.approx(result["result"], rel=1e-8) == 1.0


def test_calculator_supports_inverse_trig_in_radians() -> None:
    executor = PluginExecutor()

    result = asyncio.run(executor.execute("calculator", {"expression": "asin(0.5) + acos(0.5) + atan(1)"}))

    assert "error" not in result
    assert pytest.approx(result["result"], rel=1e-8) == 2.35619449


def test_calculator_supports_inverse_trig_degree_mode() -> None:
    executor = PluginExecutor()

    result = asyncio.run(
        executor.execute(
            "calculator",
            {"expression": "asin(0.5) + acos(0.5) + atan(1)"},
            {"angle_mode": "deg", "precision": 6},
        )
    )

    assert "error" not in result
    assert pytest.approx(result["result"], rel=1e-6) == 135.0
