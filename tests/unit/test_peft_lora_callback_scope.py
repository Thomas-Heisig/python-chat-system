import ast
from pathlib import Path


def test_cancellation_callback_owns_event_instead_of_using_missing_closure() -> None:
    source = Path("app/training/trainers/peft_lora.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    callback = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "CancellationCallback"
    )
    step_end = next(
        node for node in callback.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "on_step_end"
    )
    names = {node.id for node in ast.walk(step_end) if isinstance(node, ast.Name)}
    attributes = {
        (node.value.attr, node.attr)
        for node in ast.walk(step_end)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute)
        and isinstance(node.value.value, ast.Name) and node.value.value.id == "self"
    }

    assert "cancelled" not in names
    assert ("cancellation_event", "is_set") in attributes


def test_elapsed_time_is_returned_by_run_attempt_without_missing_outer_start_time() -> None:
    source = Path("app/training/trainers/peft_lora.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    train = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "train"
    )
    invalid_reassignments = [
        node for node in train.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "elapsed" for target in node.targets)
        and any(isinstance(item, ast.Name) and item.id == "start_time" for item in ast.walk(node.value))
    ]
    assert invalid_reassignments == []
