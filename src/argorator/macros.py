"""Macro expansion utilities for Argorator.

Currently supports comment-based iteration blocks that remain valid Bash in
editors, and are expanded during Argorator compilation/execution:

    # for ITEM in LIST
    echo "$ITEM"
    # endfor

Expands to:

    for ITEM in ${LIST}; do
    echo "$ITEM"
    done

Rules:
- LIST that looks like a bare shell variable name becomes ${LIST}
- Other expressions (globs like *.txt, command subs, arrays) are used verbatim
- Indentation is preserved for the opening and closing lines
- Nested loops are supported
"""
from __future__ import annotations

import re
from typing import List, Optional


_FOR_START_RE = re.compile(r"^(?P<indent>\s*)#\s*for\s+(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s+in\s+(?P<expr>.+?)\s*$")
_FOR_END_RE = re.compile(r"^\s*#\s*endfor\s*$")
_SHELL_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class _ForFrame:
    def __init__(self, indent: str, var_name: str, expr: str) -> None:
        self.indent = indent
        self.var_name = var_name
        self.expr = expr
        self.body_lines: List[str] = []


def _format_for_header(indent: str, var_name: str, expr: str) -> str:
    # If expr is a bare variable name, expand to ${VAR}; else use verbatim
    iter_expr = f"${{{expr}}}" if _SHELL_NAME_RE.match(expr) else expr
    return f"{indent}for {var_name} in {iter_expr}; do"


def expand_macros(script_text: str) -> str:
    """Expand comment-based iteration macros into pure Bash.

    If no macros are present, returns the original text unchanged.
    """
    lines = script_text.splitlines()
    out: List[str] = []
    stack: List[_ForFrame] = []

    def emit_line(line: str) -> None:
        if stack:
            stack[-1].body_lines.append(line)
        else:
            out.append(line)

    for raw_line in lines:
        m_start = _FOR_START_RE.match(raw_line)
        if m_start is not None:
            indent = m_start.group("indent")
            var_name = m_start.group("var")
            expr = m_start.group("expr")
            stack.append(_ForFrame(indent, var_name, expr))
            continue

        if _FOR_END_RE.match(raw_line) is not None:
            if not stack:
                # Unmatched end; pass through
                emit_line(raw_line)
                continue
            frame = stack.pop()
            expanded_block = []
            expanded_block.append(_format_for_header(frame.indent, frame.var_name, frame.expr))
            expanded_block.extend(frame.body_lines)
            expanded_block.append(f"{frame.indent}done")
            block_text = "\n".join(expanded_block)
            if stack:
                stack[-1].body_lines.append(block_text)
            else:
                out.append(block_text)
            continue

        emit_line(raw_line)

    # If there are any unclosed frames, fall back to original comment blocks
    while stack:
        frame = stack.pop(0)  # preserve original order for reconstruction
        out.append(f"{frame.indent}# for {frame.var_name} in {frame.expr}")
        out.extend(frame.body_lines)
        out.append(f"{frame.indent}# endfor")

    # Preserve trailing newline if present in original text
    result = "\n".join(out)
    if script_text.endswith("\n"):
        result += "\n"
    return result


def parse_for_loop_variables(script_text: str) -> List[str]:
    """Detect loop variables introduced by standard Bash for-loops.

    Matches: for VAR in ...; do
    Returns a list of variable names.
    """
    pattern = re.compile(r"^\s*for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\b", re.MULTILINE)
    return pattern.findall(script_text)

