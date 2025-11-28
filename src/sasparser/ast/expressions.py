"""Expression AST nodes."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .base import ASTNode, FieldReference, MacroVariable


@dataclass
class Expression(ASTNode):
    """Base class for all expressions."""

    def get_field_refs(self) -> list[FieldReference]:
        """Extract all field references from this expression."""
        return []

    def get_macro_vars(self) -> list[MacroVariable]:
        """Extract all macro variables from this expression."""
        return []


@dataclass
class Literal(Expression):
    """Literal value (string, number, date)."""

    value: Any
    literal_type: str = "string"  # "string", "number", "date", "time", "datetime"

    def __str__(self) -> str:
        if self.literal_type == "string":
            return f"'{self.value}'"
        return str(self.value)


@dataclass
class FieldExpression(Expression):
    """Expression that is a field reference."""

    field: FieldReference

    def get_field_refs(self) -> list[FieldReference]:
        return [self.field]

    def __str__(self) -> str:
        return str(self.field)


@dataclass
class MacroVarExpression(Expression):
    """Expression that is a macro variable reference."""

    macro_var: MacroVariable

    def get_macro_vars(self) -> list[MacroVariable]:
        return [self.macro_var]

    def __str__(self) -> str:
        return str(self.macro_var)


@dataclass
class BinaryExpression(Expression):
    """Binary operation (a + b, a AND b, etc.)."""

    left: Expression
    operator: str
    right: Expression

    def get_field_refs(self) -> list[FieldReference]:
        return self.left.get_field_refs() + self.right.get_field_refs()

    def get_macro_vars(self) -> list[MacroVariable]:
        return self.left.get_macro_vars() + self.right.get_macro_vars()

    def __str__(self) -> str:
        return f"({self.left} {self.operator} {self.right})"


@dataclass
class UnaryExpression(Expression):
    """Unary operation (NOT x, -x, etc.)."""

    operator: str
    operand: Expression

    def get_field_refs(self) -> list[FieldReference]:
        return self.operand.get_field_refs()

    def get_macro_vars(self) -> list[MacroVariable]:
        return self.operand.get_macro_vars()

    def __str__(self) -> str:
        return f"({self.operator} {self.operand})"


@dataclass
class FunctionCall(Expression):
    """Function call expression."""

    name: str
    arguments: list[Expression] = field(default_factory=list)

    def get_field_refs(self) -> list[FieldReference]:
        refs = []
        for arg in self.arguments:
            refs.extend(arg.get_field_refs())
        return refs

    def get_macro_vars(self) -> list[MacroVariable]:
        vars = []
        for arg in self.arguments:
            vars.extend(arg.get_macro_vars())
        return vars

    def __str__(self) -> str:
        args = ", ".join(str(a) for a in self.arguments)
        return f"{self.name}({args})"


@dataclass
class CaseExpression(Expression):
    """CASE WHEN ... THEN ... ELSE ... END expression."""

    cases: list[tuple[Expression, Expression]]  # (condition, result) pairs
    else_result: Expression | None = None

    def get_field_refs(self) -> list[FieldReference]:
        refs = []
        for cond, result in self.cases:
            refs.extend(cond.get_field_refs())
            refs.extend(result.get_field_refs())
        if self.else_result:
            refs.extend(self.else_result.get_field_refs())
        return refs

    def get_macro_vars(self) -> list[MacroVariable]:
        vars = []
        for cond, result in self.cases:
            vars.extend(cond.get_macro_vars())
            vars.extend(result.get_macro_vars())
        if self.else_result:
            vars.extend(self.else_result.get_macro_vars())
        return vars


@dataclass
class InExpression(Expression):
    """IN expression (x IN (1, 2, 3))."""

    left: Expression
    values: list[Expression]
    negated: bool = False

    def get_field_refs(self) -> list[FieldReference]:
        refs = self.left.get_field_refs()
        for v in self.values:
            refs.extend(v.get_field_refs())
        return refs

    def get_macro_vars(self) -> list[MacroVariable]:
        vars = self.left.get_macro_vars()
        for v in self.values:
            vars.extend(v.get_macro_vars())
        return vars


@dataclass
class BetweenExpression(Expression):
    """BETWEEN expression (x BETWEEN a AND b)."""

    value: Expression
    low: Expression
    high: Expression
    negated: bool = False

    def get_field_refs(self) -> list[FieldReference]:
        return (
            self.value.get_field_refs()
            + self.low.get_field_refs()
            + self.high.get_field_refs()
        )

    def get_macro_vars(self) -> list[MacroVariable]:
        return (
            self.value.get_macro_vars()
            + self.low.get_macro_vars()
            + self.high.get_macro_vars()
        )


@dataclass
class IsNullExpression(Expression):
    """IS NULL / IS NOT NULL expression."""

    operand: Expression
    negated: bool = False

    def get_field_refs(self) -> list[FieldReference]:
        return self.operand.get_field_refs()

    def get_macro_vars(self) -> list[MacroVariable]:
        return self.operand.get_macro_vars()

    def __str__(self) -> str:
        if self.negated:
            return f"({self.operand} IS NOT NULL)"
        return f"({self.operand} IS NULL)"


@dataclass
class SubqueryExpression(Expression):
    """Subquery as expression."""

    subquery: "SelectStatement"  # Forward reference

    def get_field_refs(self) -> list[FieldReference]:
        # Subquery fields are in their own scope
        return []
