"""AST nodes for other PROC statements (SORT, MEANS, FREQ, PRINT, etc.)."""

from __future__ import annotations
from dataclasses import dataclass, field
from .base import ASTNode, TableReference, FieldReference
from .statements import Statement
from .data_step import ByField


@dataclass
class ProcStatement(Statement):
    """Base class for PROC statements."""

    input_table: TableReference | None = None


@dataclass
class ProcSort(ProcStatement):
    """PROC SORT statement."""

    output_table: TableReference | None = None
    by_fields: list[ByField] = field(default_factory=list)
    nodupkey: bool = False
    noduprec: bool = False
    options: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        parts = ["PROC SORT"]
        if self.input_table:
            parts.append(f"DATA={self.input_table.qualified_name}")
        if self.output_table:
            parts.append(f"OUT={self.output_table.qualified_name}")
        return " ".join(parts) + "; ... RUN;"


@dataclass
class ProcMeans(ProcStatement):
    """PROC MEANS/SUMMARY statement."""

    output_table: TableReference | None = None
    var_fields: list[FieldReference] = field(default_factory=list)
    class_fields: list[FieldReference] = field(default_factory=list)
    by_fields: list[ByField] = field(default_factory=list)
    statistics: list[str] = field(default_factory=list)  # N, MEAN, STD, etc.
    options: dict[str, str] = field(default_factory=dict)
    is_summary: bool = False  # True for PROC SUMMARY

    def __str__(self) -> str:
        keyword = "SUMMARY" if self.is_summary else "MEANS"
        parts = [f"PROC {keyword}"]
        if self.input_table:
            parts.append(f"DATA={self.input_table.qualified_name}")
        return " ".join(parts) + "; ... RUN;"


@dataclass
class TableSpec(ASTNode):
    """Table specification for PROC FREQ (field*field)."""

    fields: list[FieldReference] = field(default_factory=list)

    def __str__(self) -> str:
        return "*".join(f.name for f in self.fields)


@dataclass
class ProcFreq(ProcStatement):
    """PROC FREQ statement."""

    tables: list[TableSpec] = field(default_factory=list)
    by_fields: list[ByField] = field(default_factory=list)
    output_table: TableReference | None = None
    options: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        parts = ["PROC FREQ"]
        if self.input_table:
            parts.append(f"DATA={self.input_table.qualified_name}")
        return " ".join(parts) + "; ... RUN;"


@dataclass
class ProcPrint(ProcStatement):
    """PROC PRINT statement."""

    var_fields: list[FieldReference] = field(default_factory=list)
    by_fields: list[ByField] = field(default_factory=list)
    obs: int | None = None
    options: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        parts = ["PROC PRINT"]
        if self.input_table:
            parts.append(f"DATA={self.input_table.qualified_name}")
        return " ".join(parts) + "; ... RUN;"


@dataclass
class ProcContents(ProcStatement):
    """PROC CONTENTS statement."""

    output_table: TableReference | None = None
    options: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        parts = ["PROC CONTENTS"]
        if self.input_table:
            parts.append(f"DATA={self.input_table.qualified_name}")
        return " ".join(parts) + "; RUN;"


@dataclass
class ProcTranspose(ProcStatement):
    """PROC TRANSPOSE statement."""

    output_table: TableReference | None = None
    var_fields: list[FieldReference] = field(default_factory=list)
    id_field: FieldReference | None = None
    by_fields: list[ByField] = field(default_factory=list)
    options: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        parts = ["PROC TRANSPOSE"]
        if self.input_table:
            parts.append(f"DATA={self.input_table.qualified_name}")
        return " ".join(parts) + "; ... RUN;"


@dataclass
class ProcGeneric(ProcStatement):
    """Generic/unknown PROC statement."""

    proc_name: str = ""
    output_table: TableReference | None = None
    body: str = ""
    options: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        parts = [f"PROC {self.proc_name}"]
        if self.input_table:
            parts.append(f"DATA={self.input_table.qualified_name}")
        return " ".join(parts) + "; ... RUN;"
