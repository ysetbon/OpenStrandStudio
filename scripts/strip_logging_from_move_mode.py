import ast
import io
import os
import sys


TARGET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "move_mode.py")


def read_file(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()


def write_file(path: str, lines: list) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def root_name_of_attr(func: ast.AST):
    node = func
    while isinstance(node, ast.Attribute):
        node = node.value
    if isinstance(node, ast.Name):
        return node.id
    return None


def is_logging_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    return root_name_of_attr(node.func) == "logging"


def is_logging_import(node: ast.AST) -> bool:
    if isinstance(node, ast.ImportFrom):
        return node.module == "logging"
    if isinstance(node, ast.Import):
        for alias in node.names:
            if alias.name == "logging" or alias.name.startswith("logging."):
                return True
    return False


def is_logging_related_stmt(node: ast.stmt) -> bool:
    # Direct logging calls like logging.info(...)
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and is_logging_call(node.value):
        return True

    # import logging / from logging import ...
    if is_logging_import(node):
        return True

    # logger = logging.getLogger(...), or any assignment where RHS is a logging.* call
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        value = node.value if isinstance(node, ast.Assign) else node.value
        if isinstance(value, ast.Call) and is_logging_call(value):
            return True

    # simple statements within PerformanceLogger that touch logging might be covered above
    return False


def gather_line_span(node: ast.AST) -> tuple:
    start = getattr(node, "lineno", None)
    end = getattr(node, "end_lineno", start)
    return start, end


def mark_delete_span(spans: list, node: ast.AST):
    start, end = gather_line_span(node)
    if start is None:
        return
    spans.append((start, end if end is not None else start))


def compute_indent(line: str) -> str:
    return line[: len(line) - len(line.lstrip(" \t"))]


def main():
    src_lines = read_file(TARGET_PATH)
    source = "".join(src_lines)

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"SyntaxError parsing {TARGET_PATH}: {e}")
        sys.exit(1)

    deletions: list[tuple[int, int]] = []
    pass_insertions: dict[int, str] = {}

    # First pass: mark logging-related statements for deletion
    for node in ast.walk(tree):
        if isinstance(node, ast.stmt) and is_logging_related_stmt(node):
            mark_delete_span(deletions, node)

    # Second pass: find empty blocks that would become empty after deleting logging-only statements
    def maybe_insert_pass_for_block(body_nodes: list[ast.stmt]):
        if not body_nodes:
            return
        # If ALL nodes in body are logging-related, we'll replace first line with a 'pass'
        if all(is_logging_related_stmt(n) for n in body_nodes):
            first = body_nodes[0]
            start_line = getattr(first, "lineno", None)
            if start_line is None:
                return
            line_text = src_lines[start_line - 1]
            indent = compute_indent(line_text)
            # record insertion: insert at the first body line
            pass_insertions[start_line] = f"{indent}pass\n"

    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            maybe_insert_pass_for_block(getattr(node, "body", []))
            # For If/While/For/Try, also handle orelse/finally/except bodies
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With)):
                maybe_insert_pass_for_block(getattr(node, "orelse", []))
            if isinstance(node, ast.Try):
                maybe_insert_pass_for_block(getattr(node, "finalbody", []))
                maybe_insert_pass_for_block(getattr(node, "orelse", []))
                for handler in getattr(node, "handlers", []):
                    maybe_insert_pass_for_block(getattr(handler, "body", []))

    # Build a fast lookup for deletions
    to_delete_lines: set[int] = set()
    for start, end in deletions:
        for i in range(start, end + 1):
            to_delete_lines.add(i)

    # Additionally handle single-line 'import logging, X' by textual surgery if needed
    # We'll transform those lines before deletion logic runs
    # If a line starts with 'import ' and contains 'logging', try to drop only the logging token
    for idx, line in enumerate(src_lines, start=1):
        stripped = line.strip()
        if stripped.startswith("import ") and "logging" in stripped and idx not in to_delete_lines:
            # Replace 'logging as name' or 'logging' with nothing, handling commas
            # This is a conservative textual approach
            # Patterns to remove: 'logging as alias', 'logging'
            import_part = stripped[len("import ") :]
            parts = [p.strip() for p in import_part.split(",")]
            new_parts = []
            for p in parts:
                if p.startswith("logging ") or p == "logging" or p.startswith("logging."):
                    continue
                new_parts.append(p)
            if len(new_parts) != len(parts):
                if new_parts:
                    new_line = f"import {', '.join(new_parts)}\n"
                else:
                    new_line = "\n"  # effectively delete the line
                # Preserve original indentation
                indent = line[: len(line) - len(line.lstrip())]
                src_lines[idx - 1] = indent + new_line

    # Reconstruct file with deletions and pass insertions
    new_lines: list[str] = []
    for idx, line in enumerate(src_lines, start=1):
        # Insert 'pass' if requested at this position
        if idx in pass_insertions:
            new_lines.append(pass_insertions[idx])
        # Skip lines marked for deletion
        if idx in to_delete_lines:
            continue
        new_lines.append(line)

    write_file(TARGET_PATH, new_lines)
    print(f"Stripped logging from: {TARGET_PATH}")


if __name__ == "__main__":
    main()


