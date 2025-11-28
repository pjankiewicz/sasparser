"""DATA step AST nodes."""

from __future__ import annotations
from dataclasses import dataclass, field
from .base import ASTNode, TableReference, FieldReference, DatasetOptions
from .expressions import Expression
from .statements import Statement


@dataclass
class DataStepStatement(ASTNode):
    """Base class for statements within a DATA step."""

    pass


@dataclass
class DataStep(Statement):
    """DATA step statement."""

    output_tables: list[TableReference]
    statements: list[DataStepStatement] = field(default_factory=list)
    options: DatasetOptions | None = None

    def __str__(self) -> str:
        tables = " ".join(t.qualified_name for t in self.output_tables)
        return f"DATA {tables}; ... RUN;"


@dataclass
class SetStatement(DataStepStatement):
    """SET statement - reads from datasets."""

    tables: list[TableReference]
    options: list[DatasetOptions] = field(default_factory=list)

    def __str__(self) -> str:
        tables = " ".join(t.qualified_name for t in self.tables)
        return f"SET {tables};"


@dataclass
class MergeStatement(DataStepStatement):
    """MERGE statement - combines datasets."""

    tables: list[TableReference]
    options: list[DatasetOptions] = field(default_factory=list)

    def __str__(self) -> str:
        tables = " ".join(t.qualified_name for t in self.tables)
        return f"MERGE {tables};"


@dataclass
class ByField(ASTNode):
    """Field in a BY statement with optional descending flag."""

    field: FieldReference
    descending: bool = False

    def __str__(self) -> str:
        if self.descending:
            return f"DESCENDING {self.field.name}"
        return self.field.name


@dataclass
class ByStatement(DataStepStatement):
    """BY statement - defines grouping/sorting fields."""

    fields: list[ByField]

    def __str__(self) -> str:
        fields = " ".join(str(f) for f in self.fields)
        return f"BY {fields};"


@dataclass
class WhereStatement(DataStepStatement):
    """WHERE clause - filters observations."""

    condition: Expression

    def __str__(self) -> str:
        return f"WHERE {self.condition};"


@dataclass
class IfStatement(DataStepStatement):
    """IF-THEN-ELSE statement."""

    condition: Expression
    then_statements: list[DataStepStatement]
    else_statements: list[DataStepStatement] | None = None

    def __str__(self) -> str:
        return f"IF {self.condition} THEN ...;"


@dataclass
class AssignmentStatement(DataStepStatement):
    """Variable assignment (x = expression)."""

    target: FieldReference
    expression: Expression

    def __str__(self) -> str:
        return f"{self.target.name} = {self.expression};"


@dataclass
class KeepStatement(DataStepStatement):
    """KEEP statement - variables to retain."""

    fields: list[FieldReference]

    def __str__(self) -> str:
        fields = " ".join(f.name for f in self.fields)
        return f"KEEP {fields};"


@dataclass
class DropStatement(DataStepStatement):
    """DROP statement - variables to remove."""

    fields: list[FieldReference]

    def __str__(self) -> str:
        fields = " ".join(f.name for f in self.fields)
        return f"DROP {fields};"


@dataclass
class RetainStatement(DataStepStatement):
    """RETAIN statement - variables to retain across observations."""

    variables: list[tuple[FieldReference, Expression | None]]

    def __str__(self) -> str:
        return "RETAIN ...;"


@dataclass
class LengthStatement(DataStepStatement):
    """LENGTH statement - define variable lengths."""

    definitions: list[tuple[FieldReference, int, bool]]  # (field, length, is_char)

    def __str__(self) -> str:
        return "LENGTH ...;"


@dataclass
class FormatStatement(DataStepStatement):
    """FORMAT statement - assign formats to variables."""

    formats: list[tuple[FieldReference, str]]  # (field, format)
    is_informat: bool = False

    def __str__(self) -> str:
        keyword = "INFORMAT" if self.is_informat else "FORMAT"
        return f"{keyword} ...;"


@dataclass
class ArrayStatement(DataStepStatement):
    """ARRAY statement - define array of variables."""

    name: str
    size: int | str  # Can be "*" for dynamic
    elements: list[FieldReference]
    is_char: bool = False
    char_length: int | None = None

    def __str__(self) -> str:
        return f"ARRAY {self.name}{{{self.size}}} ...;"


@dataclass
class DoStatement(DataStepStatement):
    """DO loop statement."""

    index_var: FieldReference | None = None
    start: Expression | None = None
    end: Expression | None = None
    by: Expression | None = None
    while_condition: Expression | None = None
    until_condition: Expression | None = None
    statements: list[DataStepStatement] = field(default_factory=list)

    def __str__(self) -> str:
        return "DO ...; ... END;"


@dataclass
class OutputStatement(DataStepStatement):
    """OUTPUT statement - write observation to dataset."""

    dataset: TableReference | None = None

    def __str__(self) -> str:
        if self.dataset:
            return f"OUTPUT {self.dataset.qualified_name};"
        return "OUTPUT;"


@dataclass
class InputStatement(DataStepStatement):
    """INPUT statement - read raw data."""

    specifications: list[tuple[FieldReference, str | None]]  # (field, format/informat)

    def __str__(self) -> str:
        return "INPUT ...;"


@dataclass
class PutStatement(DataStepStatement):
    """PUT statement - write to log or file."""

    items: list[Expression | str]

    def __str__(self) -> str:
        return "PUT ...;"


@dataclass
class LabelStatement(DataStepStatement):
    """LABEL statement - assign labels to variables."""

    labels: list[tuple[FieldReference, str]]

    def __str__(self) -> str:
        return "LABEL ...;"


@dataclass
class RenameStatement(DataStepStatement):
    """RENAME statement - rename variables."""

    renames: list[tuple[FieldReference, str]]  # (old_name, new_name)

    def __str__(self) -> str:
        return "RENAME ...;"
