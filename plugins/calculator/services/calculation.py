from __future__ import annotations

import ast
import math
import operator
from typing import Callable

from plugins.calculator.constants import MATH_CONSTANTS, MATH_FUNCTIONS

BINARY_OPERATORS: dict[type[ast.AST], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
UNARY_OPERATORS: dict[type[ast.AST], Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class ExpressionValidationError(ValueError):
    """Raised when an expression is syntactically valid but violates safety rules."""


class CalculatorEvaluator:
    def is_safe_expression(self, node: ast.AST) -> bool:
        allowed_nodes: tuple[type[ast.AST], ...] = (
            ast.Expression,
            ast.Constant,
            ast.BinOp,
            ast.UnaryOp,
            ast.Name,
            ast.Call,
            ast.Load,
            ast.Mod,
            ast.Pow,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.USub,
            ast.UAdd,
        )
        for child in ast.walk(node):
            if not any(isinstance(child, t) for t in allowed_nodes):
                return False
            if isinstance(child, ast.Constant):
                if isinstance(child.value, bool):
                    return False
                if not isinstance(child.value, (int, float)):
                    return False
            if isinstance(child, ast.Name) and child.id not in MATH_FUNCTIONS and child.id not in MATH_CONSTANTS:
                return False
            if isinstance(child, ast.Call):
                if not isinstance(child.func, ast.Name):
                    return False
                if child.func.id not in MATH_FUNCTIONS:
                    return False
                if child.keywords:
                    return False
                for arg in child.args:
                    if not self.is_safe_expression(arg):
                        return False
        return True

    def evaluate(self, node: ast.AST, *, angle_mode: str) -> float:
        if isinstance(node, ast.Expression):
            return self.evaluate(node.body, angle_mode=angle_mode)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                raise ExpressionValidationError("Boolesche Werte sind nicht erlaubt")
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ExpressionValidationError("Nur numerische Konstanten sind erlaubt")

        if isinstance(node, ast.Name) and node.id in MATH_CONSTANTS:
            return float(MATH_CONSTANTS[node.id])

        if isinstance(node, ast.BinOp) and type(node.op) in BINARY_OPERATORS:
            left = self.evaluate(node.left, angle_mode=angle_mode)
            right = self.evaluate(node.right, angle_mode=angle_mode)
            try:
                result = BINARY_OPERATORS[type(node.op)](left, right)
                return float(result)
            except ZeroDivisionError:
                raise ZeroDivisionError()
            except Exception:
                raise ValueError("Ungültige Operation")

        if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPERATORS:
            operand = self.evaluate(node.operand, angle_mode=angle_mode)
            return float(UNARY_OPERATORS[type(node.op)](operand))

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            function_name = node.func.id
            if function_name in MATH_FUNCTIONS:
                if node.keywords:
                    raise ExpressionValidationError("Keyword-Argumente sind nicht erlaubt")
                args = [self.evaluate(arg, angle_mode=angle_mode) for arg in node.args]
                try:
                    result = self._call_function(function_name, args, angle_mode=angle_mode)
                    return float(result)
                except Exception as exc:
                    raise ValueError(f"Fehler in Funktion '{function_name}': {str(exc)}")
            raise ValueError(f"Unbekannte Funktion: {function_name}")

        raise ValueError("Ungültiger Ausdruck")

    def _call_function(self, function_name: str, args: list[float], *, angle_mode: str) -> float:
        if function_name in {"sin", "cos", "tan"} and args:
            angle = args[0]
            if angle_mode == "deg":
                angle = math.radians(angle)
            return float(MATH_FUNCTIONS[function_name](angle))

        if function_name in {"asin", "acos", "atan"} and args:
            if len(args) != 1:
                raise ValueError(f"{function_name} erwartet genau 1 Argument")
            result = float(MATH_FUNCTIONS[function_name](args[0]))
            if angle_mode == "deg":
                return float(math.degrees(result))
            return result

        if function_name == "factorial":
            if len(args) != 1:
                raise ValueError("factorial erwartet genau 1 Argument")
            value = args[0]
            if not float(value).is_integer() or value < 0:
                raise ValueError("factorial erwartet eine nichtnegative Ganzzahl")
            return float(math.factorial(int(value)))

        if function_name == "round":
            if len(args) == 1:
                return float(round(args[0]))
            if len(args) == 2:
                return float(round(args[0], int(args[1])))
            raise ValueError("round erwartet 1 oder 2 Argumente")

        return float(MATH_FUNCTIONS[function_name](*args))
