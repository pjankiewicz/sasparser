"""PROC SQL AST nodes."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from .base import ASTNode, TableReference, FieldReference
from .expressions import Expression
from .statements import Statement


class JoinType(Enum):
    """SQL JOIN types."""

    INNER = "INNER"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    FULL = "FULL"
    CROSS = "CROSS"


@dataclass
class SQLStatement(ASTNode):
    """Base class for SQL statements within PROC SQL."""

    pass


@dataclass
class ProcSQL(Statement):
    """PROC SQL block."""

    statements: list[SQLStatement] = field(default_factory=list)
    options: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        return "PROC SQL; ... QUIT;"


@dataclass
class SelectColumn(ASTNode):
    """Column in SELECT list."""

    expression: Expression
    alias: str | None = None

    def __str__(self) -> str:
        if self.alias:
            return f"{self.expression} AS {self.alias}"
        return str(self.expression)


@dataclass
class FromItem(ASTNode):
    """Item in FROM clause (table or subquery)."""

    source: TableReference | SelectStatement
    alias: str | None = None

    @property
    def is_subquery(self) -> bool:
        return isinstance(self.source, SelectStatement)

    def __str__(self) -> str:
        if self.alias:
            return f"{self.source} AS {self.alias}"
        return str(self.source)


@dataclass
class FromClause(ASTNode):
    """FROM clause with table sources."""

    items: list[FromItem]

    def __str__(self) -> str:
        return "FROM " + ", ".join(str(i) for i in self.items)


@dataclass
class JoinClause(ASTNode):
    """JOIN clause."""

    join_type: JoinType
    table: FromItem
    condition: Expression | None = None

    def __str__(self) -> str:
        parts = [self.join_type.value, "JOIN", str(self.table)]
        if self.condition:
            parts.extend(["ON", str(self.condition)])
        return " ".join(parts)


@dataclass
class OrderByItem(ASTNode):
    """ORDER BY item."""

    field: FieldReference | Expression
    descending: bool = False

    def __str__(self) -> str:
        suffix = " DESC" if self.descending else ""
        return str(self.field) + suffix


@dataclass
class SelectStatement(SQLStatement):
    """SELECT query."""

    columns: list[SelectColumn]
    from_clause: FromClause | None = None
    joins: list[JoinClause] = field(default_factory=list)
    where: Expression | None = None
    group_by: list[FieldReference | Expression] = field(default_factory=list)
    having: Expression | None = None
    order_by: list[OrderByItem] = field(default_factory=list)
    distinct: bool = False
    select_all: bool = False  # SELECT *

    def __str__(self) -> str:
        parts = ["SELECT"]
        if self.distinct:
            parts.append("DISTINCT")
        if self.select_all:
            parts.append("*")
        else:
            parts.append(", ".join(str(c) for c in self.columns))
        if self.from_clause:
            parts.append(str(self.from_clause))
        return " ".join(parts)


@dataclass
class CreateTableStatement(SQLStatement):
    """CREATE TABLE AS SELECT."""

    target: TableReference
    select: SelectStatement
    is_view: bool = False

    def __str__(self) -> str:
        keyword = "VIEW" if self.is_view else "TABLE"
        return f"CREATE {keyword} {self.target.qualified_name} AS ..."


@dataclass
class InsertStatement(SQLStatement):
    """INSERT INTO statement."""

    target: TableReference
    columns: list[FieldReference] = field(default_factory=list)
    values: list[list[Expression]] = field(default_factory=list)
    select: SelectStatement | None = None

    def __str__(self) -> str:
        return f"INSERT INTO {self.target.qualified_name} ..."


@dataclass
class UpdateStatement(SQLStatement):
    """UPDATE statement."""

    target: TableReference
    assignments: list[tuple[FieldReference, Expression]] = field(default_factory=list)
    where: Expression | None = None

    def __str__(self) -> str:
        return f"UPDATE {self.target.qualified_name} SET ..."


@dataclass
class DeleteStatement(SQLStatement):
    """DELETE FROM statement."""

    target: TableReference
    where: Expression | None = None

    def __str__(self) -> str:
        return f"DELETE FROM {self.target.qualified_name} ..."


@dataclass
class DropStatement(SQLStatement):
    """DROP TABLE/VIEW statement."""

    target: TableReference
    is_view: bool = False

    def __str__(self) -> str:
        keyword = "VIEW" if self.is_view else "TABLE"
        return f"DROP {keyword} {self.target.qualified_name}"


@dataclass
class AlterTableStatement(SQLStatement):
    """ALTER TABLE statement."""

    target: TableReference
    action: str  # ADD, DROP, MODIFY
    column: FieldReference | None = None
    definition: str | None = None

    def __str__(self) -> str:
        return f"ALTER TABLE {self.target.qualified_name} {self.action} ..."
