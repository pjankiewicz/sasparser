"""High-level models and extraction utilities."""

from __future__ import annotations
from dataclasses import dataclass, field
from .ast.base import TableReference, FieldReference
from .visitors.table_visitor import TableVisitor, TableUsage
from .visitors.field_visitor import FieldVisitor, FieldUsage
from .visitors.dependency_visitor import DependencyVisitor, TableDependency
from .parser import ParseResult


@dataclass
class TableInfo:
    """Extracted table information."""

    name: str
    library: str | None = None
    usage: str = ""  # 'input', 'output', 'both'
    contexts: list[str] = field(default_factory=list)

    @property
    def qualified_name(self) -> str:
        if self.library:
            return f"{self.library}.{self.name}"
        return self.name


@dataclass
class FieldInfo:
    """Extracted field information."""

    name: str
    table: str | None = None
    usage: str = ""  # 'read', 'write', 'kept', 'dropped'
    contexts: list[str] = field(default_factory=list)


@dataclass
class ExtractionResult:
    """Result of extracting tables and fields from parsed SAS code."""

    tables: list[TableInfo] = field(default_factory=list)
    fields: list[FieldInfo] = field(default_factory=list)
    dependencies: list[TableDependency] = field(default_factory=list)
    input_tables: list[TableInfo] = field(default_factory=list)
    output_tables: list[TableInfo] = field(default_factory=list)


def extract_tables(result: ParseResult) -> list[TableInfo]:
    """Extract all table references from a parse result.

    Args:
        result: ParseResult from parsing SAS code.

    Returns:
        List of TableInfo with usage information.
    """
    visitor = TableVisitor()
    for stmt in result.statements:
        visitor.visit(stmt)

    # Build table info list
    tables_dict: dict[str, TableInfo] = {}
    for usage in visitor.all_usages:
        key = usage.table.qualified_name
        if key not in tables_dict:
            tables_dict[key] = TableInfo(
                name=usage.table.dataset,
                library=usage.table.library,
                usage=usage.usage_type,
                contexts=[usage.context],
            )
        else:
            info = tables_dict[key]
            if info.usage != usage.usage_type:
                info.usage = "both"
            if usage.context not in info.contexts:
                info.contexts.append(usage.context)

    return list(tables_dict.values())


def extract_fields(result: ParseResult) -> list[FieldInfo]:
    """Extract all field references from a parse result.

    Args:
        result: ParseResult from parsing SAS code.

    Returns:
        List of FieldInfo with usage information.
    """
    visitor = FieldVisitor()
    for stmt in result.statements:
        visitor.visit(stmt)

    # Build field info list
    fields_dict: dict[str, FieldInfo] = {}
    for usage in visitor.all_usages:
        key = usage.field.name.lower()
        if usage.field.table_alias:
            key = f"{usage.field.table_alias.lower()}.{key}"

        if key not in fields_dict:
            fields_dict[key] = FieldInfo(
                name=usage.field.name,
                table=usage.field.table_alias,
                usage=usage.usage_type,
                contexts=[usage.context],
            )
        else:
            info = fields_dict[key]
            if info.usage != usage.usage_type and usage.usage_type != "read":
                info.usage = usage.usage_type
            if usage.context not in info.contexts:
                info.contexts.append(usage.context)

    return list(fields_dict.values())


def extract_dependencies(result: ParseResult) -> list[TableDependency]:
    """Extract table dependencies from a parse result.

    Args:
        result: ParseResult from parsing SAS code.

    Returns:
        List of TableDependency showing data lineage.
    """
    visitor = DependencyVisitor()
    for stmt in result.statements:
        visitor.visit(stmt)
    return visitor.get_dependencies()


def extract_all(result: ParseResult) -> ExtractionResult:
    """Extract all tables, fields, and dependencies from a parse result.

    Args:
        result: ParseResult from parsing SAS code.

    Returns:
        ExtractionResult with complete information.
    """
    table_visitor = TableVisitor()
    field_visitor = FieldVisitor()
    dep_visitor = DependencyVisitor()

    for stmt in result.statements:
        table_visitor.visit(stmt)
        field_visitor.visit(stmt)
        dep_visitor.visit(stmt)

    tables = extract_tables(result)
    fields = extract_fields(result)
    dependencies = dep_visitor.get_dependencies()

    input_tables = [t for t in tables if t.usage in ("input", "both")]
    output_tables = [t for t in tables if t.usage in ("output", "both")]

    return ExtractionResult(
        tables=tables,
        fields=fields,
        dependencies=dependencies,
        input_tables=input_tables,
        output_tables=output_tables,
    )
