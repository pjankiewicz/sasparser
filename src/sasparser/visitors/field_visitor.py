"""Visitor for extracting field references from AST."""

from __future__ import annotations
from dataclasses import dataclass
from .base import ASTVisitor
from ..ast.base import ASTNode, FieldReference


@dataclass
class FieldUsage:
    """Information about how a field is used."""

    field: FieldReference
    usage_type: str  # 'read', 'write', 'both', 'kept', 'dropped'
    context: str  # e.g., 'data_step', 'proc_sql.select', 'proc_sql.where'
    table_context: str | None = None  # The table this field belongs to


class FieldVisitor(ASTVisitor):
    """Visitor that extracts all field references from an AST.

    Tracks field usage patterns including reads, writes, and transformations.
    """

    def __init__(self) -> None:
        self.read_fields: list[FieldReference] = []
        self.write_fields: list[FieldReference] = []
        self.kept_fields: list[FieldReference] = []
        self.dropped_fields: list[FieldReference] = []
        self.all_usages: list[FieldUsage] = []
        self._current_context: str = ""
        self._current_table: str | None = None

    def get_all_fields(self) -> list[FieldReference]:
        """Get all unique fields referenced."""
        seen: set[str] = set()
        result: list[FieldReference] = []
        all_fields = (
            self.read_fields + self.write_fields + self.kept_fields + self.dropped_fields
        )
        for field in all_fields:
            key = field.name.lower()
            if field.table_alias:
                key = f"{field.table_alias.lower()}.{key}"
            if key not in seen:
                seen.add(key)
                result.append(field)
        return result

    def get_read_fields(self) -> list[FieldReference]:
        """Get unique fields that are read."""
        seen: set[str] = set()
        result: list[FieldReference] = []
        for field in self.read_fields:
            key = field.name.lower()
            if key not in seen:
                seen.add(key)
                result.append(field)
        return result

    def get_write_fields(self) -> list[FieldReference]:
        """Get unique fields that are written (assigned)."""
        seen: set[str] = set()
        result: list[FieldReference] = []
        for field in self.write_fields:
            key = field.name.lower()
            if key not in seen:
                seen.add(key)
                result.append(field)
        return result

    def _add_read(self, field: FieldReference | None) -> None:
        if field:
            self.read_fields.append(field)
            self.all_usages.append(
                FieldUsage(
                    field=field,
                    usage_type="read",
                    context=self._current_context,
                    table_context=self._current_table,
                )
            )

    def _add_write(self, field: FieldReference | None) -> None:
        if field:
            self.write_fields.append(field)
            self.all_usages.append(
                FieldUsage(
                    field=field,
                    usage_type="write",
                    context=self._current_context,
                    table_context=self._current_table,
                )
            )

    # Field references
    def visit_FieldReference(self, node: FieldReference) -> None:
        self._add_read(node)

    def visit_FieldExpression(self, node: ASTNode) -> None:
        from ..ast.expressions import FieldExpression

        assert isinstance(node, FieldExpression)
        self._add_read(node.field)

    # DATA step
    def visit_DataStep(self, node: ASTNode) -> None:
        from ..ast.data_step import DataStep

        assert isinstance(node, DataStep)
        self._current_context = "data_step"
        for stmt in node.statements:
            self.visit(stmt)

    def visit_AssignmentStatement(self, node: ASTNode) -> None:
        from ..ast.data_step import AssignmentStatement

        assert isinstance(node, AssignmentStatement)
        # Target is written
        self._add_write(node.target)
        # Value expression is read
        old_context = self._current_context
        self._current_context = "data_step.assignment"
        self.visit(node.expression)
        self._current_context = old_context

    def visit_KeepStatement(self, node: ASTNode) -> None:
        from ..ast.data_step import KeepStatement

        assert isinstance(node, KeepStatement)
        for field in node.fields:
            self.kept_fields.append(field)
            self.all_usages.append(
                FieldUsage(
                    field=field,
                    usage_type="kept",
                    context="data_step.keep",
                    table_context=self._current_table,
                )
            )

    def visit_DropStatement(self, node: ASTNode) -> None:
        from ..ast.data_step import DropStatement

        assert isinstance(node, DropStatement)
        for field in node.fields:
            self.dropped_fields.append(field)
            self.all_usages.append(
                FieldUsage(
                    field=field,
                    usage_type="dropped",
                    context="data_step.drop",
                    table_context=self._current_table,
                )
            )

    def visit_ByStatement(self, node: ASTNode) -> None:
        from ..ast.data_step import ByStatement

        assert isinstance(node, ByStatement)
        old_context = self._current_context
        self._current_context = f"{self._current_context}.by"
        for by_field in node.fields:
            self._add_read(by_field.field)
        self._current_context = old_context

    def visit_WhereStatement(self, node: ASTNode) -> None:
        from ..ast.data_step import WhereStatement

        assert isinstance(node, WhereStatement)
        old_context = self._current_context
        self._current_context = f"{self._current_context}.where"
        self.visit(node.condition)
        self._current_context = old_context

    def visit_IfStatement(self, node: ASTNode) -> None:
        from ..ast.data_step import IfStatement

        assert isinstance(node, IfStatement)
        old_context = self._current_context
        self._current_context = f"{self._current_context}.if"
        self.visit(node.condition)
        self._current_context = old_context
        for stmt in node.then_statements:
            self.visit(stmt)
        if node.else_statements:
            for stmt in node.else_statements:
                self.visit(stmt)

    # PROC SQL
    def visit_ProcSQL(self, node: ASTNode) -> None:
        from ..ast.proc_sql import ProcSQL

        assert isinstance(node, ProcSQL)
        self._current_context = "proc_sql"
        for stmt in node.statements:
            self.visit(stmt)

    def visit_SelectStatement(self, node: ASTNode) -> None:
        from ..ast.proc_sql import SelectStatement

        assert isinstance(node, SelectStatement)
        old_context = self._current_context
        self._current_context = "proc_sql.select"
        for col in node.columns:
            self.visit(col)
        self._current_context = "proc_sql.from"
        self.visit(node.from_clause)
        for join in node.joins:
            self._current_context = "proc_sql.join"
            self.visit(join)
        if node.where:
            self._current_context = "proc_sql.where"
            self.visit(node.where)
        if node.group_by:
            self._current_context = "proc_sql.group_by"
            for item in node.group_by:
                self.visit(item)
        if node.having:
            self._current_context = "proc_sql.having"
            self.visit(node.having)
        if node.order_by:
            self._current_context = "proc_sql.order_by"
            for item in node.order_by:
                self.visit(item)
        self._current_context = old_context

    def visit_OrderByItem(self, node: ASTNode) -> None:
        from ..ast.proc_sql import OrderByItem
        from ..ast.base import FieldReference

        assert isinstance(node, OrderByItem)
        if isinstance(node.field, FieldReference):
            self._add_read(node.field)
        else:
            self.visit(node.field)

    # Other PROCs
    def visit_ProcSort(self, node: ASTNode) -> None:
        from ..ast.proc_other import ProcSort

        assert isinstance(node, ProcSort)
        self._current_context = "proc_sort.by"
        for by_field in node.by_fields:
            self._add_read(by_field.field)

    def visit_ProcMeans(self, node: ASTNode) -> None:
        from ..ast.proc_other import ProcMeans

        assert isinstance(node, ProcMeans)
        self._current_context = "proc_means.var"
        for field in node.var_fields:
            self._add_read(field)
        self._current_context = "proc_means.class"
        for field in node.class_fields:
            self._add_read(field)
        self._current_context = "proc_means.by"
        for by_field in node.by_fields:
            self._add_read(by_field.field)

    def visit_ProcFreq(self, node: ASTNode) -> None:
        from ..ast.proc_other import ProcFreq

        assert isinstance(node, ProcFreq)
        self._current_context = "proc_freq.tables"
        for table_spec in node.tables:
            for field in table_spec.fields:
                self._add_read(field)
        self._current_context = "proc_freq.by"
        for by_field in node.by_fields:
            self._add_read(by_field.field)

    def visit_ProcPrint(self, node: ASTNode) -> None:
        from ..ast.proc_other import ProcPrint

        assert isinstance(node, ProcPrint)
        self._current_context = "proc_print.var"
        for field in node.var_fields:
            self._add_read(field)
        self._current_context = "proc_print.by"
        for by_field in node.by_fields:
            self._add_read(by_field.field)
