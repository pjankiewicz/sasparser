"""Base visitor class for AST traversal."""

from __future__ import annotations
from abc import ABC
from typing import Any
from ..ast.base import ASTNode, TableReference, FieldReference
from ..ast.expressions import (
    Expression,
    Literal,
    FieldExpression,
    BinaryExpression,
    UnaryExpression,
    FunctionCall,
    CaseExpression,
    InExpression,
    BetweenExpression,
    IsNullExpression,
)
from ..ast.statements import (
    Statement,
    LibnameStatement,
    MacroLetStatement,
    MacroDefStatement,
    MacroCallStatement,
    OptionsStatement,
    TitleStatement,
)
from ..ast.data_step import (
    DataStep,
    SetStatement,
    MergeStatement,
    ByStatement,
    WhereStatement,
    IfStatement,
    AssignmentStatement,
    KeepStatement,
    DropStatement,
    OutputStatement,
)
from ..ast.proc_sql import (
    ProcSQL,
    SelectStatement,
    FromClause,
    FromItem,
    JoinClause,
    SelectColumn,
    OrderByItem,
    CreateTableStatement,
    InsertStatement,
    UpdateStatement,
    DeleteStatement,
)
from ..ast.proc_other import (
    ProcSort,
    ProcMeans,
    ProcFreq,
    ProcPrint,
)


class ASTVisitor(ABC):
    """Base visitor for traversing AST nodes.

    Implements the visitor pattern. Override specific visit_* methods
    to handle different node types. The default implementations traverse
    children recursively.
    """

    def visit(self, node: ASTNode | None) -> Any:
        """Visit a node by dispatching to the appropriate visit_* method."""
        if node is None:
            return None

        method_name = f"visit_{node.__class__.__name__}"
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def generic_visit(self, node: ASTNode) -> Any:
        """Default visitor that traverses all child nodes."""
        # Get all fields that might contain child nodes
        if hasattr(node, "__dataclass_fields__"):
            for field_name in node.__dataclass_fields__:
                value = getattr(node, field_name)
                self._visit_value(value)
        return None

    def _visit_value(self, value: Any) -> None:
        """Visit a value that might be a node, list, or dict."""
        if isinstance(value, ASTNode):
            self.visit(value)
        elif isinstance(value, list):
            for item in value:
                self._visit_value(item)
        elif isinstance(value, dict):
            for v in value.values():
                self._visit_value(v)

    # Table and field references
    def visit_TableReference(self, node: TableReference) -> Any:
        return self.generic_visit(node)

    def visit_FieldReference(self, node: FieldReference) -> Any:
        return self.generic_visit(node)

    # Expressions
    def visit_Literal(self, node: Literal) -> Any:
        return self.generic_visit(node)

    def visit_FieldExpression(self, node: FieldExpression) -> Any:
        return self.generic_visit(node)

    def visit_BinaryExpression(self, node: BinaryExpression) -> Any:
        self.visit(node.left)
        self.visit(node.right)
        return None

    def visit_UnaryExpression(self, node: UnaryExpression) -> Any:
        self.visit(node.operand)
        return None

    def visit_FunctionCall(self, node: FunctionCall) -> Any:
        for arg in node.arguments:
            self.visit(arg)
        return None

    def visit_CaseExpression(self, node: CaseExpression) -> Any:
        for cond, result in node.cases:
            self.visit(cond)
            self.visit(result)
        self.visit(node.else_result)
        return None

    def visit_InExpression(self, node: InExpression) -> Any:
        self.visit(node.left)
        for val in node.values:
            self.visit(val)
        return None

    def visit_BetweenExpression(self, node: BetweenExpression) -> Any:
        self.visit(node.value)
        self.visit(node.low)
        self.visit(node.high)
        return None

    def visit_IsNullExpression(self, node: IsNullExpression) -> Any:
        self.visit(node.operand)
        return None

    # Statements
    def visit_LibnameStatement(self, node: LibnameStatement) -> Any:
        return self.generic_visit(node)

    def visit_MacroLetStatement(self, node: MacroLetStatement) -> Any:
        return self.generic_visit(node)

    def visit_MacroDefStatement(self, node: MacroDefStatement) -> Any:
        return self.generic_visit(node)

    def visit_MacroCallStatement(self, node: MacroCallStatement) -> Any:
        return self.generic_visit(node)

    def visit_OptionsStatement(self, node: OptionsStatement) -> Any:
        return self.generic_visit(node)

    def visit_TitleStatement(self, node: TitleStatement) -> Any:
        return self.generic_visit(node)

    # DATA step
    def visit_DataStep(self, node: DataStep) -> Any:
        for table in node.output_tables:
            self.visit(table)
        for stmt in node.statements:
            self.visit(stmt)
        return None

    def visit_SetStatement(self, node: SetStatement) -> Any:
        for table in node.tables:
            self.visit(table)
        return None

    def visit_MergeStatement(self, node: MergeStatement) -> Any:
        for table in node.tables:
            self.visit(table)
        return None

    def visit_ByStatement(self, node: ByStatement) -> Any:
        for by_field in node.fields:
            self.visit(by_field.field)
        return None

    def visit_WhereStatement(self, node: WhereStatement) -> Any:
        self.visit(node.condition)
        return None

    def visit_IfStatement(self, node: IfStatement) -> Any:
        self.visit(node.condition)
        for stmt in node.then_statements:
            self.visit(stmt)
        if node.else_statements:
            for stmt in node.else_statements:
                self.visit(stmt)
        return None

    def visit_AssignmentStatement(self, node: AssignmentStatement) -> Any:
        self.visit(node.target)
        self.visit(node.expression)
        return None

    def visit_KeepStatement(self, node: KeepStatement) -> Any:
        for field in node.fields:
            self.visit(field)
        return None

    def visit_DropStatement(self, node: DropStatement) -> Any:
        for field in node.fields:
            self.visit(field)
        return None

    def visit_OutputStatement(self, node: OutputStatement) -> Any:
        self.visit(node.dataset)
        return None

    # PROC SQL
    def visit_ProcSQL(self, node: ProcSQL) -> Any:
        for stmt in node.statements:
            self.visit(stmt)
        return None

    def visit_SelectStatement(self, node: SelectStatement) -> Any:
        for col in node.columns:
            self.visit(col)
        self.visit(node.from_clause)
        for join in node.joins:
            self.visit(join)
        self.visit(node.where)
        for item in node.group_by:
            self.visit(item)
        self.visit(node.having)
        for item in node.order_by:
            self.visit(item)
        return None

    def visit_SelectColumn(self, node: SelectColumn) -> Any:
        self.visit(node.expression)
        return None

    def visit_FromClause(self, node: FromClause) -> Any:
        for item in node.items:
            self.visit(item)
        return None

    def visit_FromItem(self, node: FromItem) -> Any:
        if isinstance(node.source, TableReference):
            self.visit(node.source)
        else:
            self.visit(node.source)  # Subquery SelectStatement
        return None

    def visit_JoinClause(self, node: JoinClause) -> Any:
        self.visit(node.table)
        self.visit(node.condition)
        return None

    def visit_OrderByItem(self, node: OrderByItem) -> Any:
        self.visit(node.field)
        return None

    def visit_CreateTableStatement(self, node: CreateTableStatement) -> Any:
        self.visit(node.target)
        self.visit(node.select)
        return None

    def visit_InsertStatement(self, node: InsertStatement) -> Any:
        self.visit(node.target)
        for col in node.columns:
            self.visit(col)
        for row in node.values:
            for val in row:
                self.visit(val)
        if node.select:
            self.visit(node.select)
        return None

    def visit_UpdateStatement(self, node: UpdateStatement) -> Any:
        self.visit(node.target)
        for col, val in node.assignments:
            self.visit(col)
            self.visit(val)
        self.visit(node.where)
        return None

    def visit_DeleteStatement(self, node: DeleteStatement) -> Any:
        self.visit(node.target)
        self.visit(node.where)
        return None

    # Other PROCs
    def visit_ProcSort(self, node: ProcSort) -> Any:
        self.visit(node.input_table)
        self.visit(node.output_table)
        for by_field in node.by_fields:
            self.visit(by_field.field)
        return None

    def visit_ProcMeans(self, node: ProcMeans) -> Any:
        self.visit(node.input_table)
        self.visit(node.output_table)
        for field in node.var_fields:
            self.visit(field)
        for field in node.class_fields:
            self.visit(field)
        for by_field in node.by_fields:
            self.visit(by_field.field)
        return None

    def visit_ProcFreq(self, node: ProcFreq) -> Any:
        self.visit(node.input_table)
        self.visit(node.output_table)
        for table_spec in node.tables:
            for field in table_spec.fields:
                self.visit(field)
        for by_field in node.by_fields:
            self.visit(by_field.field)
        return None

    def visit_ProcPrint(self, node: ProcPrint) -> Any:
        self.visit(node.input_table)
        for field in node.var_fields:
            self.visit(field)
        for by_field in node.by_fields:
            self.visit(by_field.field)
        return None
