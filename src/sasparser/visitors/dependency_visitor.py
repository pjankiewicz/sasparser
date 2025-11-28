"""Visitor for extracting table dependencies from AST."""

from __future__ import annotations
from dataclasses import dataclass, field
from .base import ASTVisitor
from ..ast.base import ASTNode, TableReference


@dataclass
class TableDependency:
    """Represents a dependency where output_table depends on input_tables."""

    output_table: TableReference
    input_tables: list[TableReference]
    statement_type: str  # 'data_step', 'proc_sql', etc.


class DependencyVisitor(ASTVisitor):
    """Visitor that extracts table dependency relationships.

    Tracks which tables are created from which source tables,
    enabling data lineage and dependency analysis.
    """

    def __init__(self) -> None:
        self.dependencies: list[TableDependency] = []
        self._current_inputs: list[TableReference] = []
        self._current_outputs: list[TableReference] = []
        self._current_type: str = ""

    def get_dependencies(self) -> list[TableDependency]:
        """Get all table dependencies."""
        return self.dependencies

    def get_dependency_graph(self) -> dict[str, list[str]]:
        """Get dependency graph as adjacency list.

        Returns dict mapping output table -> list of input tables.
        """
        graph: dict[str, list[str]] = {}
        for dep in self.dependencies:
            out_name = dep.output_table.qualified_name
            inputs = [t.qualified_name for t in dep.input_tables]
            if out_name not in graph:
                graph[out_name] = []
            graph[out_name].extend(inputs)
        return graph

    def get_reverse_dependencies(self) -> dict[str, list[str]]:
        """Get reverse dependency graph.

        Returns dict mapping input table -> list of output tables that use it.
        """
        graph: dict[str, list[str]] = {}
        for dep in self.dependencies:
            out_name = dep.output_table.qualified_name
            for inp in dep.input_tables:
                inp_name = inp.qualified_name
                if inp_name not in graph:
                    graph[inp_name] = []
                graph[inp_name].append(out_name)
        return graph

    def _flush_dependency(self) -> None:
        """Create dependency record from current state."""
        if self._current_outputs and self._current_inputs:
            for out_table in self._current_outputs:
                self.dependencies.append(
                    TableDependency(
                        output_table=out_table,
                        input_tables=list(self._current_inputs),
                        statement_type=self._current_type,
                    )
                )
        self._current_inputs = []
        self._current_outputs = []

    # DATA step
    def visit_DataStep(self, node: ASTNode) -> None:
        from ..ast.data_step import DataStep

        assert isinstance(node, DataStep)
        self._current_type = "data_step"
        self._current_inputs = []
        self._current_outputs = list(node.output_tables)
        for stmt in node.statements:
            self.visit(stmt)
        self._flush_dependency()

    def visit_SetStatement(self, node: ASTNode) -> None:
        from ..ast.data_step import SetStatement

        assert isinstance(node, SetStatement)
        self._current_inputs.extend(node.tables)

    def visit_MergeStatement(self, node: ASTNode) -> None:
        from ..ast.data_step import MergeStatement

        assert isinstance(node, MergeStatement)
        self._current_inputs.extend(node.tables)

    # PROC SQL
    def visit_ProcSQL(self, node: ASTNode) -> None:
        from ..ast.proc_sql import ProcSQL

        assert isinstance(node, ProcSQL)
        for stmt in node.statements:
            self._current_type = "proc_sql"
            self._current_inputs = []
            self._current_outputs = []
            self.visit(stmt)
            self._flush_dependency()

    def visit_CreateTableStatement(self, node: ASTNode) -> None:
        from ..ast.proc_sql import CreateTableStatement

        assert isinstance(node, CreateTableStatement)
        if node.target:
            self._current_outputs.append(node.target)
        if node.select:
            self.visit(node.select)

    def visit_SelectStatement(self, node: ASTNode) -> None:
        from ..ast.proc_sql import SelectStatement
        from ..ast.base import TableReference

        assert isinstance(node, SelectStatement)
        if node.from_clause:
            for item in node.from_clause.items:
                if isinstance(item.source, TableReference):
                    self._current_inputs.append(item.source)
                else:
                    # Subquery - visit it
                    self.visit(item.source)
        for join in node.joins:
            if join.table:
                if isinstance(join.table.source, TableReference):
                    self._current_inputs.append(join.table.source)
                else:
                    self.visit(join.table.source)

    def visit_InsertStatement(self, node: ASTNode) -> None:
        from ..ast.proc_sql import InsertStatement

        assert isinstance(node, InsertStatement)
        if node.target:
            self._current_outputs.append(node.target)
        if node.select:
            self.visit(node.select)

    # Other PROCs
    def visit_ProcSort(self, node: ASTNode) -> None:
        from ..ast.proc_other import ProcSort

        assert isinstance(node, ProcSort)
        self._current_type = "proc_sort"
        self._current_inputs = []
        self._current_outputs = []
        if node.input_table:
            self._current_inputs.append(node.input_table)
        if node.output_table:
            self._current_outputs.append(node.output_table)
        elif node.input_table:
            # In-place sort, output same as input
            self._current_outputs.append(node.input_table)
        self._flush_dependency()

    def visit_ProcMeans(self, node: ASTNode) -> None:
        from ..ast.proc_other import ProcMeans

        assert isinstance(node, ProcMeans)
        self._current_type = "proc_means"
        self._current_inputs = []
        self._current_outputs = []
        if node.input_table:
            self._current_inputs.append(node.input_table)
        if node.output_table:
            self._current_outputs.append(node.output_table)
        self._flush_dependency()

    def visit_ProcFreq(self, node: ASTNode) -> None:
        from ..ast.proc_other import ProcFreq

        assert isinstance(node, ProcFreq)
        self._current_type = "proc_freq"
        self._current_inputs = []
        self._current_outputs = []
        if node.input_table:
            self._current_inputs.append(node.input_table)
        if node.output_table:
            self._current_outputs.append(node.output_table)
        self._flush_dependency()
