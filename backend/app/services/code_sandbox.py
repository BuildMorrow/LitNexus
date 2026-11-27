"""Isolated Python Code Sandbox Service for Exploratory Data Analysis (EDA).

Features:
- AST security filtering blocking OS/network/file-IO modules, unsafe builtins, and dunder escapes
- Auto-repair for markdown-fenced or mis-indented Python snippets
- Auto-injects uploaded CSV into `df` (pandas DataFrame), plus `np`, `stats`, and `plt`
- Captures Matplotlib figures as Base64 PNG strings and enforces execution timeout
"""

import ast
import asyncio
import base64
import contextlib
import io
import re
import textwrap
import time
from typing import Any

from pydantic import BaseModel, Field

DISALLOWED_MODULES = {
    "os",
    "subprocess",
    "sys",
    "shutil",
    "socket",
    "http",
    "urllib",
    "requests",
    "httpx",
    "ftplib",
    "telnetlib",
    "smtplib",
    "pty",
    "ctypes",
    "importlib",
    "builtins",
    "posix",
    "nt",
    "_thread",
    "threading",
    "multiprocessing",
    "asyncio",
    "signal",
    "tempfile",
    "webbrowser",
    "pathlib",
    "pickle",
}

DISALLOWED_CALLS = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "open",
    "input",
    "exit",
    "quit",
    "globals",
    "locals",
    "vars",
    "getattr",
    "setattr",
    "delattr",
}

DISALLOWED_DUNDER_ATTRS = {
    "__subclasses__",
    "__globals__",
    "__builtins__",
    "__class__",
    "__mro__",
    "__bases__",
    "__code__",
}


class CodeExecutionRequest(BaseModel):
    code: str = Field(min_length=1, max_length=20000)
    timeout_seconds: float = Field(default=10.0, ge=0.5, le=30.0)


class CodeExecutionResponse(BaseModel):
    success: bool
    error: str | None = None
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: int = 0
    figures: list[str] = Field(default_factory=list)


class SecurityCheckVisitor(ast.NodeVisitor):
    """AST visitor rejecting forbidden imports, unsafe builtins, and dunder escapes."""

    def __init__(self) -> None:
        self.errors: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            mod_root = alias.name.split(".")[0]
            if mod_root in DISALLOWED_MODULES:
                self.errors.append(
                    f"Importing module '{alias.name}' is prohibited in sandbox for security reasons."
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            mod_root = node.module.split(".")[0]
            if mod_root in DISALLOWED_MODULES:
                self.errors.append(
                    f"Importing from '{node.module}' is prohibited in sandbox for security reasons."
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in DISALLOWED_CALLS:
            self.errors.append(
                f"Direct invocation of '{node.func.id}()' is prohibited in sandbox."
            )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in DISALLOWED_DUNDER_ATTRS:
            self.errors.append(
                f"Access to restricted attribute '{node.attr}' is prohibited in sandbox."
            )
        self.generic_visit(node)


def smart_repair_python_code(code: str) -> str:
    """Clean markdown code fences and normalize whitespace/indentation."""
    if not code:
        return ""
    cleaned = code.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:python|py)?\s*\n", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\n```$", "", cleaned)
    cleaned = cleaned.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n").replace("\t", "    ")
    return textwrap.dedent(cleaned).strip()


def validate_python_code(code: str) -> str | None:
    """Parse code AST and enforce sandbox security rules."""
    repaired = smart_repair_python_code(code)
    if not repaired:
        return "Code snippet is empty."
    try:
        tree = ast.parse(repaired)
    except SyntaxError as exc:
        return f"Syntax Error at line {exc.lineno}: {exc.msg}"

    visitor = SecurityCheckVisitor()
    visitor.visit(tree)
    if visitor.errors:
        return " | ".join(visitor.errors)
    return None


class CodeSandboxService:
    """Isolated Python execution engine with timeout enforcement and Matplotlib capture."""

    def _execute_sync(self, code: str, csv_text: str) -> CodeExecutionResponse:
        start_time = time.perf_counter()
        repaired = smart_repair_python_code(code)
        security_err = validate_python_code(repaired)
        if security_err:
            return CodeExecutionResponse(
                success=False,
                error=security_err,
                execution_time_ms=int((time.perf_counter() - start_time) * 1000),
            )

        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        from scipy import stats

        plt.close("all")

        def safe_import(name: str, *args: Any, **kwargs: Any) -> Any:
            root = name.split(".")[0]
            if root in DISALLOWED_MODULES:
                raise ImportError(f"Importing module '{name}' is prohibited in sandbox.")
            return __import__(name, *args, **kwargs)

        df = pd.read_csv(io.StringIO(csv_text)) if csv_text and csv_text.strip() else pd.DataFrame()

        sandbox_globals: dict[str, Any] = {
            "__builtins__": {
                "__import__": safe_import,
                "abs": abs,
                "all": all,
                "any": any,
                "bool": bool,
                "dict": dict,
                "enumerate": enumerate,
                "filter": filter,
                "float": float,
                "format": format,
                "int": int,
                "isinstance": isinstance,
                "len": len,
                "list": list,
                "map": map,
                "max": max,
                "min": min,
                "pow": pow,
                "print": print,
                "range": range,
                "repr": repr,
                "round": round,
                "set": set,
                "sorted": sorted,
                "str": str,
                "sum": sum,
                "tuple": tuple,
                "type": type,
                "zip": zip,
                "Exception": Exception,
                "ValueError": ValueError,
                "TypeError": TypeError,
                "KeyError": KeyError,
            },
            "df": df,
            "pd": pd,
            "pandas": pd,
            "np": np,
            "numpy": np,
            "stats": stats,
            "plt": plt,
        }

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        figures: list[str] = []

        try:
            with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
                exec(compile(repaired, "<litnexus-sandbox>", "exec"), sandbox_globals, sandbox_globals)

            for fig_num in plt.get_fignums():
                fig = plt.figure(fig_num)
                img_buf = io.BytesIO()
                fig.savefig(img_buf, format="png", dpi=140, bbox_inches="tight")
                figures.append(base64.b64encode(img_buf.getvalue()).decode("ascii"))
            plt.close("all")

            return CodeExecutionResponse(
                success=True,
                stdout=stdout_buf.getvalue().strip(),
                stderr=stderr_buf.getvalue().strip(),
                execution_time_ms=int((time.perf_counter() - start_time) * 1000),
                figures=figures,
            )
        except Exception as exc:
            plt.close("all")
            return CodeExecutionResponse(
                success=False,
                error=f"{type(exc).__name__}: {exc}",
                stdout=stdout_buf.getvalue().strip(),
                stderr=stderr_buf.getvalue().strip(),
                execution_time_ms=int((time.perf_counter() - start_time) * 1000),
                figures=figures,
            )

    async def execute_code_async(
        self,
        code: str,
        csv_text: str = "",
        timeout_seconds: float = 10.0,
    ) -> CodeExecutionResponse:
        loop = asyncio.get_running_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, self._execute_sync, code, csv_text),
                timeout=timeout_seconds,
            )
        except TimeoutError:
            return CodeExecutionResponse(
                success=False,
                error=f"Execution timed out after {timeout_seconds:.1f}s limit.",
                execution_time_ms=int(timeout_seconds * 1000),
            )


code_sandbox = CodeSandboxService()
