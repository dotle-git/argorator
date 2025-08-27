from argorator.contexts import AnalysisContext
from argorator.analyzers import detect_shell_interpreter


def analyze(script_text: str):
    ctx = AnalysisContext(script_text=script_text)
    detect_shell_interpreter(ctx)
    return ctx.shell_cmd


def test_bash_direct():
    script = """#!/bin/bash\necho ok\n"""
    assert analyze(script) == ["/bin/bash"]


def test_bash_env():
    script = """#!/usr/bin/env bash\necho ok\n"""
    assert analyze(script) == ["/bin/bash"]


def test_sh_direct():
    script = """#!/bin/sh\necho ok\n"""
    assert analyze(script) == ["/bin/sh"]


def test_dash_direct():
    script = """#!/bin/dash\necho ok\n"""
    assert analyze(script) == ["/bin/sh"]


def test_sh_env():
    script = """#!/usr/bin/env sh\necho ok\n"""
    assert analyze(script) == ["/bin/sh"]


def test_dash_env():
    script = """#!/usr/bin/env dash\necho ok\n"""
    assert analyze(script) == ["/bin/sh"]


def test_zsh_not_misclassified_as_sh():
    script = """#!/bin/zsh\necho ok\n"""
    assert analyze(script) == ["/bin/zsh"]

