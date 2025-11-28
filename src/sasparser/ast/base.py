"""Base AST node classes and common node types."""

from __future__ import annotations
from abc import ABC
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..visitors.base import ASTVisitor


@dataclass
class SourceLocation:
    """Source code location for error reporting."""

    line: int
    column: int
    end_line: int | None = None
    end_column: int | None = None

    def __str__(self) -> str:
        if self.end_line and self.end_line != self.line:
            return f"{self.line}:{self.column}-{self.end_line}:{self.end_column}"
        return f"{self.line}:{self.column}"


@dataclass
class ASTNode(ABC):
    """Base class for all AST nodes."""

    location: SourceLocation | None = field(
        default=None, repr=False, compare=False, kw_only=True
    )

    def accept(self, visitor: ASTVisitor):
        """Accept a visitor (double dispatch pattern)."""
        method_name = f"visit_{self.__class__.__name__}"
        method = getattr(visitor, method_name, visitor.generic_visit)
        return method(self)


@dataclass
class TableReference(ASTNode):
    """Reference to a SAS table/dataset."""

    dataset: str
    library: str | None = None

    @property
    def qualified_name(self) -> str:
        """Return fully qualified name (library.dataset or just dataset)."""
        if self.library:
            return f"{self.library}.{self.dataset}"
        return self.dataset

    def __str__(self) -> str:
        return self.qualified_name

    def __hash__(self) -> int:
        return hash((self.library, self.dataset))


@dataclass
class FieldReference(ASTNode):
    """Reference to a field/column."""

    name: str
    table_alias: str | None = None

    @property
    def qualified_name(self) -> str:
        """Return qualified name if table alias is present."""
        if self.table_alias:
            return f"{self.table_alias}.{self.name}"
        return self.name

    def __str__(self) -> str:
        return self.qualified_name

    def __hash__(self) -> int:
        return hash((self.table_alias, self.name))


@dataclass
class MacroVariable(ASTNode):
    """Macro variable reference (&var)."""

    name: str
    resolved_value: str | None = None

    def __str__(self) -> str:
        return f"&{self.name}"

    def __hash__(self) -> int:
        return hash(self.name)


@dataclass
class DatasetOptions(ASTNode):
    """Dataset options like (keep=x drop=y where=(condition))."""

    options: dict[str, str] = field(default_factory=dict)
    in_var: str | None = None  # IN= variable for merge

    def __bool__(self) -> bool:
        return bool(self.options) or self.in_var is not None
