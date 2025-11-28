"""Visitor for extracting table references from AST."""

from __future__ import annotations
from dataclasses import dataclass, field
from .base import ASTVisitor
from ..ast.base import ASTNode, TableReference


@dataclass
class TableUsage:
    """Information about how a table is used."""

    table: TableReference
    usage_type: str  # 'input', 'output', 'both'
    context: str  # e.g., 'data_step', 'proc_sql', 'proc_sort'


class TableVisitor(ASTVisitor):
    """Visitor that extracts all table references from an AST.

    Tracks both input (read) and output (written) tables, and the
    context in which they appear.
    """

    def __init__(self) -> None:
        self.input_tables: list[TableReference] = []
        self.output_tables: list[TableReference] = []
        self.all_usages: list[TableUsage] = []
        self._current_context: str = ""

    def get_all_tables(self) -> list[TableReference]:
        """Get all unique tables referenced."""
        seen: set[str] = set()
        result: list[TableReference] = []
        for table in self.input_tables + self.output_tables:
            key = table.qualified_name
            if key not in seen:
                seen.add(key)
                result.append(table)
        return result

    def get_input_tables(self) -> list[TableReference]:
        """Get unique input (read) tables."""
        seen: set[str] = set()
        result: list[TableReference] = []
        for table in self.input_tables:
            key = table.qualified_name
            if key not in seen:
                seen.add(key)
                result.append(table)
        return result

    def get_output_tables(self) -> list[TableReference]:
        """Get unique output (written) tables."""
        seen: set[str] = set()
        result: list[TableReference] = []
        for table in self.output_tables:
            key = table.qualified_name
            if key not in seen:
                seen.add(key)
                result.append(table)
        return result

    def _add_input(self, table: TableReference | None) -> None:
        if table:
            self.input_tables.append(table)
            self.all_usages.append(
                TableUsage(table=table, usage_type="input", context=self._current_context)
            )

    def _add_output(self, table: TableReference | None) -> None:
        if table:
            self.output_tables.append(table)
            self.all_usages.append(
                TableUsage(table=table, usage_type="output", context=self._current_context)
            )

    # DATA step
    def visit_DataStep(self, node: ASTNode) -> None:
        from ..ast.data_step import DataStep

        assert isinstance(node, DataStep)
        self._current_context = "data_step"
        for table in node.output_tables:
            self._add_output(table)
        for stmt in node.statements:
            self.visit(stmt)

    def visit_SetStatement(self, node: ASTNode) -> None:
        from ..ast.data_step import SetStatement

        assert isinstance(node, SetStatement)
        for table in node.tables:
            self._add_input(table)

    def visit_MergeStatement(self, node: ASTNode) -> None:
        from ..ast.data_step import MergeStatement

        assert isinstance(node, MergeStatement)
        for table in node.tables:
            self._add_input(table)

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
        self.visit(node.from_clause)
        for join in node.joins:
            self.visit(join)

    def visit_FromClause(self, node: ASTNode) -> None:
        from ..ast.proc_sql import FromClause

        assert isinstance(node, FromClause)
        for item in node.items:
            self.visit(item)

    def visit_FromItem(self, node: ASTNode) -> None:
        from ..ast.proc_sql import FromItem
        from ..ast.base import TableReference

        assert isinstance(node, FromItem)
        if isinstance(node.source, TableReference):
            self._add_input(node.source)
        else:
            # Subquery
            self.visit(node.source)

    def visit_JoinClause(self, node: ASTNode) -> None:
        from ..ast.proc_sql import JoinClause

        assert isinstance(node, JoinClause)
        self.visit(node.table)

    def visit_CreateTableStatement(self, node: ASTNode) -> None:
        from ..ast.proc_sql import CreateTableStatement

        assert isinstance(node, CreateTableStatement)
        self._add_output(node.target)
        if node.select:
            self.visit(node.select)

    def visit_InsertStatement(self, node: ASTNode) -> None:
        from ..ast.proc_sql import InsertStatement

        assert isinstance(node, InsertStatement)
        self._add_output(node.target)
        if node.select:
            self.visit(node.select)

    def visit_UpdateStatement(self, node: ASTNode) -> None:
        from ..ast.proc_sql import UpdateStatement

        assert isinstance(node, UpdateStatement)
        # Update both reads and writes
        self._add_input(node.target)
        self._add_output(node.target)

    def visit_DeleteStatement(self, node: ASTNode) -> None:
        from ..ast.proc_sql import DeleteStatement

        assert isinstance(node, DeleteStatement)
        self._add_output(node.target)

    # Other PROCs
    def visit_ProcSort(self, node: ASTNode) -> None:
        from ..ast.proc_other import ProcSort

        assert isinstance(node, ProcSort)
        self._current_context = "proc_sort"
        self._add_input(node.input_table)
        # Output defaults to input if not specified
        if node.output_table:
            self._add_output(node.output_table)
        else:
            self._add_output(node.input_table)

    def visit_ProcMeans(self, node: ASTNode) -> None:
        from ..ast.proc_other import ProcMeans

        assert isinstance(node, ProcMeans)
        self._current_context = "proc_means"
        self._add_input(node.input_table)
        self._add_output(node.output_table)

    def visit_ProcFreq(self, node: ASTNode) -> None:
        from ..ast.proc_other import ProcFreq

        assert isinstance(node, ProcFreq)
        self._current_context = "proc_freq"
        self._add_input(node.input_table)
        self._add_output(node.output_table)

    def visit_ProcPrint(self, node: ASTNode) -> None:
        from ..ast.proc_other import ProcPrint

        assert isinstance(node, ProcPrint)
        self._current_context = "proc_print"
        self._add_input(node.input_table)
