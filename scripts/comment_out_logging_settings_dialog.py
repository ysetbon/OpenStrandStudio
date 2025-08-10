import io
import os
import re
import sys


def comment_out_logging_and_fix_blocks(file_path: str) -> None:
    with io.open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 1) Comment out import logging
    text = re.sub(r"(?m)^(\s*)import\s+logging\s*$", r"\1# import logging", text)

    # 2) Comment out all occurrences of logging. calls (works for inline too)
    text = re.sub(r"logging\.", r"# logging.", text)

    # Write intermediate state
    with io.open(file_path, 'w', encoding='utf-8', newline='') as f:
        f.write(text)

    # 3) Iteratively compile and insert 'pass' where an indented block is now empty
    # We handle both SyntaxError and IndentationError reporting expected blocks
    max_iterations = 200
    for _ in range(max_iterations):
        try:
            compile(open(file_path, 'r', encoding='utf-8').read(), file_path, 'exec')
            break
        except (SyntaxError, IndentationError) as e:
            msg = getattr(e, 'msg', str(e))
            lineno = getattr(e, 'lineno', None)
            if lineno is None:
                raise

            if 'expected an indented block' not in msg and 'expected an indented block' not in str(e):
                # Not the empty-block case; re-raise
                raise

            # Insert a 'pass' line right after the reported line with proper indentation
            with io.open(file_path, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()

            idx = lineno - 1
            if idx < 0 or idx >= len(lines):
                raise

            line = lines[idx]
            # Determine base indent of the block header
            leading_ws = re.match(r"^([ \t]*)", line).group(1)

            # Compute child indent: prefer 4 spaces beyond current indent
            # If original file uses tabs, follow with a tab
            if '\t' in leading_ws and leading_ws.strip(' \t') == '':
                child_indent = leading_ws + '\t'
            else:
                child_indent = leading_ws + '    '

            # Insert a 'pass' below if not already present immediately
            insert_at = idx + 1
            lines.insert(insert_at, f"{child_indent}pass")

            with io.open(file_path, 'w', encoding='utf-8', newline='') as f:
                f.write("\n".join(lines) + ("\n" if text.endswith("\n") else ""))
    else:
        raise RuntimeError('Reached maximum iterations while fixing empty blocks')


if __name__ == '__main__':
    # Default relative path
    target = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'settings_dialog.py')
    if len(sys.argv) > 1:
        target = sys.argv[1]
    comment_out_logging_and_fix_blocks(target)
    print('Commented out logging and fixed empty blocks in', target)


