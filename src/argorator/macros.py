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


_FOR_START_RE = re.compile(
    r"^(?P<indent>\s*)#\s*for\s+"
    r"(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s+in\s+"
    r"(?P<expr>.+?)"
    r"(?:\s*->\s*(?P<func>[A-Za-z_][A-Za-z0-9_]*))?\s*$"
)
_FOR_END_RE = re.compile(r"^\s*#\s*endfor\s*$")
_SHELL_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_BARE_FUNC_CALL_RE = re.compile(r"^(?P<indent>\s*)(?P<func>[A-Za-z_][A-Za-z0-9_]*)\s*$")
_FUNC_DEF_TEMPLATE = r"^\s*(?:function\s+)?{name}\s*\(\s*\)\s*\{"


class _ForFrame:
    def __init__(self, indent: str, var_name: str, expr: str, single_line: bool) -> None:
        self.indent = indent
        self.var_name = var_name
        self.expr = expr
        self.single_line = single_line
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

    def close_top_frame() -> None:
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

    def emit_line(line: str) -> None:
        if stack:
            stack[-1].body_lines.append(line)
        else:
            out.append(line)

    # Pre-scan helper to determine if a matching # endfor exists for a given start index
    def has_matching_endfor(start_index: int) -> bool:
        depth = 1
        for j in range(start_index + 1, len(lines)):
            if _FOR_START_RE.match(lines[j]):
                depth += 1
            elif _FOR_END_RE.match(lines[j]):
                depth -= 1
                if depth == 0:
                    return True
        return False

    def is_defined_function_anywhere(func_name: str) -> bool:
        pattern = re.compile(r"^\s*(?:function\s+)?" + re.escape(func_name) + r"\s*\(\s*\)\s*\{")
        return any(pattern.match(ln) is not None for ln in lines)

    i = 0
    while i < len(lines):
        raw_line = lines[i]
        m_start = _FOR_START_RE.match(raw_line)
        if m_start is not None:
            indent = m_start.group("indent")
            var_name = m_start.group("var")
            expr = m_start.group("expr")
            func_name = m_start.group("func")
            if func_name:
                # Expand immediately to a loop that calls the function for each item
                header = _format_for_header(indent, var_name, expr)
                call_line = f"{indent}{func_name} \"${var_name}\""
                out.append("\n".join([header, call_line, f"{indent}done"]))
                i += 1
                continue

            single_line = not has_matching_endfor(i)
            stack.append(_ForFrame(indent, var_name, expr, single_line))
            if single_line:
                # Capture the next line (if any) as the body, then auto-close
                i += 1
                if i < len(lines):
                    next_line = lines[i]
                    # If next line is a bare function name and that function is defined in the script,
                    # treat it as a call passing the loop variable as $1
                    m_call = _BARE_FUNC_CALL_RE.match(next_line)
                    if m_call is not None:
                        func_candidate = m_call.group("func")
                        indent_call = m_call.group("indent")
                        if is_defined_function_anywhere(func_candidate):
                            next_line = f"{indent_call}{func_candidate} \"${var_name}\""
                    stack[-1].body_lines.append(next_line)
                close_top_frame()
                # Do not process next_line again if we consumed it as body
                i += 1
                continue
            i += 1
            continue

        if _FOR_END_RE.match(raw_line) is not None:
            if not stack:
                emit_line(raw_line)
                i += 1
                continue
            close_top_frame()
            i += 1
            continue

        emit_line(raw_line)
        i += 1

    # If there are any unclosed frames (should not happen unless malformed), output as original comments
    while stack:
        frame = stack.pop(0)
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

