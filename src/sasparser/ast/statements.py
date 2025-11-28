"""Global statement AST nodes (LIBNAME, macro, OPTIONS, etc.)."""

from __future__ import annotations
from dataclasses import dataclass, field
from .base import ASTNode


@dataclass
class Statement(ASTNode):
    """Base class for all top-level statements."""

    pass


@dataclass
class LibnameStatement(Statement):
    """LIBNAME statement."""

    name: str
    path: str
    engine: str | None = None
    options: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        parts = [f"LIBNAME {self.name}"]
        if self.engine:
            parts.append(self.engine)
        parts.append(f"'{self.path}'")
        return " ".join(parts) + ";"


@dataclass
class MacroLetStatement(Statement):
    """%LET macro variable assignment."""

    name: str
    value: str

    def __str__(self) -> str:
        return f"%LET {self.name} = {self.value};"


@dataclass
class MacroParameter(ASTNode):
    """Macro parameter definition."""

    name: str
    default_value: str | None = None


@dataclass
class MacroDefStatement(Statement):
    """%MACRO definition."""

    name: str
    parameters: list[MacroParameter] = field(default_factory=list)
    body: str = ""

    def __str__(self) -> str:
        params = ", ".join(
            p.name if p.default_value is None else f"{p.name}={p.default_value}"
            for p in self.parameters
        )
        if params:
            return f"%MACRO {self.name}({params}); ... %MEND;"
        return f"%MACRO {self.name}; ... %MEND;"


@dataclass
class MacroCallStatement(Statement):
    """Macro invocation (%macroname(...))."""

    name: str
    arguments: list[tuple[str | None, str]] = field(default_factory=list)

    def __str__(self) -> str:
        if not self.arguments:
            return f"%{self.name}"
        args = ", ".join(
            f"{k}={v}" if k else v for k, v in self.arguments
        )
        return f"%{self.name}({args})"


@dataclass
class OptionsStatement(Statement):
    """OPTIONS statement."""

    options: dict[str, str | None] = field(default_factory=dict)

    def __str__(self) -> str:
        opts = " ".join(
            f"{k}={v}" if v else k for k, v in self.options.items()
        )
        return f"OPTIONS {opts};"


@dataclass
class TitleStatement(Statement):
    """TITLE or FOOTNOTE statement."""

    text: str
    number: int | None = None
    is_footnote: bool = False

    def __str__(self) -> str:
        keyword = "FOOTNOTE" if self.is_footnote else "TITLE"
        if self.number:
            return f"{keyword}{self.number} '{self.text}';"
        return f"{keyword} '{self.text}';"


@dataclass
class CommentStatement(Statement):
    """Comment (captured for documentation purposes)."""

    text: str
    is_block: bool = False  # True for /* */, False for * ;
