"""PROC SQL handler."""

from __future__ import annotations
from . import register
from .base import BaseHandler, ParseContext
from ..core.tokens import Token, TokenType
from ..ast.base import TableReference, FieldReference
from ..ast.proc_sql import (
    ProcSQL, SelectStatement, SelectColumn, FromClause, FromItem,
    JoinClause, JoinType, OrderByItem, CreateTableStatement,
    InsertStatement, UpdateStatement, DeleteStatement, SQLStatement,
)
from ..ast.expressions import Expression, FieldExpression, Literal


@register
class ProcSQLHandler(BaseHandler):
    """Handler for PROC SQL parsing."""

    @staticmethod
    def trigger_tokens() -> set[TokenType]:
        return {TokenType.PROC}

    @staticmethod
    def can_handle(tokens: list[Token], pos: int) -> bool:
        return (
            pos + 1 < len(tokens)
            and tokens[pos].type == TokenType.PROC
            and tokens[pos + 1].type == TokenType.SQL
        )

    def parse(self, ctx: ParseContext) -> tuple[ProcSQL, int]:
        """Parse PROC SQL block."""
        pos = ctx.pos + 2  # Skip PROC SQL

        # Parse options until semicolon
        options: dict[str, str] = {}
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
            if ctx.tokens[pos].type == TokenType.IDENTIFIER:
                opt_name = ctx.tokens[pos].value
                pos += 1
                if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.EQUALS:
                    pos += 1
                    if pos < len(ctx.tokens):
                        options[opt_name] = ctx.tokens[pos].value
                        pos += 1
            else:
                pos += 1

        if pos < len(ctx.tokens):
            pos += 1  # Skip semicolon

        # Parse SQL statements until QUIT
        statements: list[SQLStatement] = []
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.QUIT:
            new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
            stmt, pos = self._parse_sql_statement(new_ctx)
            if stmt:
                statements.append(stmt)

        # Skip QUIT;
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.QUIT:
            pos += 1
            if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.SEMICOLON:
                pos += 1

        return ProcSQL(statements=statements, options=options), pos

    def _parse_sql_statement(
        self, ctx: ParseContext
    ) -> tuple[SQLStatement | None, int]:
        """Parse a single SQL statement."""
        token = ctx.tokens[ctx.pos]

        if token.type == TokenType.SELECT:
            return self._parse_select(ctx)
        elif token.type == TokenType.CREATE:
            return self._parse_create(ctx)
        elif token.type == TokenType.INSERT:
            return self._parse_insert(ctx)
        elif token.type == TokenType.UPDATE:
            return self._parse_update(ctx)
        elif token.type == TokenType.DELETE:
            return self._parse_delete(ctx)
        else:
            # Skip to semicolon
            pos = ctx.pos
            while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
                pos += 1
            if pos < len(ctx.tokens):
                pos += 1
            return None, pos

    def _parse_select(self, ctx: ParseContext) -> tuple[SelectStatement, int]:
        """Parse SELECT statement."""
        pos = ctx.pos + 1  # Skip SELECT

        # Check for DISTINCT
        distinct = False
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.DISTINCT:
            distinct = True
            pos += 1

        # Parse select list
        columns: list[SelectColumn] = []
        select_all = False
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.STAR:
            select_all = True
            pos += 1
        else:
            columns, pos = self._parse_select_list(ctx.tokens, pos)

        # Parse FROM clause
        from_clause: FromClause | None = None
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.FROM:
            pos += 1
            from_clause, pos = self._parse_from_clause(ctx, pos)

        # Parse JOINs
        joins: list[JoinClause] = []
        while pos < len(ctx.tokens) and ctx.tokens[pos].type in {
            TokenType.JOIN, TokenType.LEFT, TokenType.RIGHT,
            TokenType.INNER, TokenType.FULL, TokenType.CROSS
        }:
            join, pos = self._parse_join(ctx, pos)
            joins.append(join)

        # Parse WHERE, GROUP BY, HAVING, ORDER BY
        where: Expression | None = None
        group_by: list[FieldReference] = []
        having: Expression | None = None
        order_by: list[OrderByItem] = []

        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
            tok = ctx.tokens[pos]
            if tok.type == TokenType.WHERE:
                pos += 1
                where, pos = self._parse_expression_until(
                    ctx.tokens, pos,
                    {TokenType.SEMICOLON, TokenType.GROUP, TokenType.HAVING,
                     TokenType.ORDER, TokenType.QUIT}
                )
            elif tok.type == TokenType.GROUP:
                pos += 1  # Skip GROUP
                if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.BY:
                    pos += 1  # Skip BY
                group_by, pos = self._parse_group_by(ctx.tokens, pos)
            elif tok.type == TokenType.HAVING:
                pos += 1
                having, pos = self._parse_expression_until(
                    ctx.tokens, pos,
                    {TokenType.SEMICOLON, TokenType.ORDER, TokenType.QUIT}
                )
            elif tok.type == TokenType.ORDER:
                pos += 1  # Skip ORDER
                if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.BY:
                    pos += 1  # Skip BY
                order_by, pos = self._parse_order_by(ctx.tokens, pos)
            else:
                pos += 1

        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.SEMICOLON:
            pos += 1

        return SelectStatement(
            columns=columns,
            from_clause=from_clause,
            joins=joins,
            where=where,
            group_by=group_by,
            having=having,
            order_by=order_by,
            distinct=distinct,
            select_all=select_all,
        ), pos

    def _parse_select_list(
        self, tokens: list[Token], pos: int
    ) -> tuple[list[SelectColumn], int]:
        """Parse SELECT column list."""
        columns: list[SelectColumn] = []

        while pos < len(tokens):
            tok = tokens[pos]
            if tok.type in {TokenType.FROM, TokenType.SEMICOLON}:
                break

            if tok.type == TokenType.COMMA:
                pos += 1
                continue

            # Parse expression (simplified: just field or literal)
            expr, pos = self._parse_simple_expression(tokens, pos)

            # Check for alias
            alias: str | None = None
            if pos < len(tokens) and tokens[pos].type == TokenType.AS:
                pos += 1
                if pos < len(tokens) and tokens[pos].type == TokenType.IDENTIFIER:
                    alias = tokens[pos].value
                    pos += 1

            columns.append(SelectColumn(expression=expr, alias=alias))

        return columns, pos

    def _parse_from_clause(
        self, ctx: ParseContext, pos: int
    ) -> tuple[FromClause, int]:
        """Parse FROM clause."""
        items: list[FromItem] = []

        while pos < len(ctx.tokens):
            tok = ctx.tokens[pos]
            if tok.type in {
                TokenType.WHERE, TokenType.GROUP, TokenType.HAVING,
                TokenType.ORDER, TokenType.SEMICOLON, TokenType.QUIT,
                TokenType.JOIN, TokenType.LEFT, TokenType.RIGHT,
                TokenType.INNER, TokenType.FULL, TokenType.CROSS
            }:
                break

            if tok.type == TokenType.COMMA:
                pos += 1
                continue

            if tok.type == TokenType.IDENTIFIER:
                new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
                table, pos = self._parse_table_ref(new_ctx)
                alias: str | None = None

                # Check for alias
                if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.AS:
                    pos += 1
                if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.IDENTIFIER:
                    # Check if it's actually a keyword
                    if ctx.tokens[pos].value.lower() not in {
                        "where", "group", "having", "order", "left", "right",
                        "inner", "full", "cross", "join", "on"
                    }:
                        alias = ctx.tokens[pos].value
                        pos += 1

                items.append(FromItem(source=table, alias=alias))
            elif tok.type == TokenType.LPAREN:
                # Subquery
                pos += 1
                if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.SELECT:
                    new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
                    subquery, pos = self._parse_select(new_ctx)
                    if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.RPAREN:
                        pos += 1
                    alias = None
                    if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.AS:
                        pos += 1
                    if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.IDENTIFIER:
                        alias = ctx.tokens[pos].value
                        pos += 1
                    items.append(FromItem(source=subquery, alias=alias))
            else:
                pos += 1

        return FromClause(items=items), pos

    def _parse_join(
        self, ctx: ParseContext, pos: int
    ) -> tuple[JoinClause, int]:
        """Parse JOIN clause."""
        join_type = JoinType.INNER

        # Parse join type
        if ctx.tokens[pos].type == TokenType.LEFT:
            join_type = JoinType.LEFT
            pos += 1
            if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.OUTER:
                pos += 1
        elif ctx.tokens[pos].type == TokenType.RIGHT:
            join_type = JoinType.RIGHT
            pos += 1
            if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.OUTER:
                pos += 1
        elif ctx.tokens[pos].type == TokenType.FULL:
            join_type = JoinType.FULL
            pos += 1
            if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.OUTER:
                pos += 1
        elif ctx.tokens[pos].type == TokenType.CROSS:
            join_type = JoinType.CROSS
            pos += 1
        elif ctx.tokens[pos].type == TokenType.INNER:
            pos += 1

        # Skip JOIN keyword
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.JOIN:
            pos += 1

        # Parse table
        table: FromItem | None = None
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.IDENTIFIER:
            new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
            table_ref, pos = self._parse_table_ref(new_ctx)
            alias = None
            if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.AS:
                pos += 1
            if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.IDENTIFIER:
                if ctx.tokens[pos].value.lower() != "on":
                    alias = ctx.tokens[pos].value
                    pos += 1
            table = FromItem(source=table_ref, alias=alias)

        # Parse ON condition
        condition: Expression | None = None
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.ON:
            pos += 1
            condition, pos = self._parse_expression_until(
                ctx.tokens, pos,
                {TokenType.WHERE, TokenType.GROUP, TokenType.HAVING,
                 TokenType.ORDER, TokenType.SEMICOLON, TokenType.QUIT,
                 TokenType.JOIN, TokenType.LEFT, TokenType.RIGHT,
                 TokenType.INNER, TokenType.FULL, TokenType.CROSS}
            )

        return JoinClause(
            join_type=join_type,
            table=table or FromItem(source=TableReference(dataset="unknown")),
            condition=condition
        ), pos

    def _parse_group_by(
        self, tokens: list[Token], pos: int
    ) -> tuple[list[FieldReference], int]:
        """Parse GROUP BY fields."""
        fields: list[FieldReference] = []
        while pos < len(tokens):
            tok = tokens[pos]
            if tok.type in {TokenType.HAVING, TokenType.ORDER, TokenType.SEMICOLON}:
                break
            if tok.type == TokenType.COMMA:
                pos += 1
                continue
            if tok.type == TokenType.IDENTIFIER:
                fields.append(FieldReference(name=tok.value))
                pos += 1
            else:
                pos += 1
        return fields, pos

    def _parse_order_by(
        self, tokens: list[Token], pos: int
    ) -> tuple[list[OrderByItem], int]:
        """Parse ORDER BY items."""
        items: list[OrderByItem] = []
        while pos < len(tokens):
            tok = tokens[pos]
            if tok.type == TokenType.SEMICOLON:
                break
            if tok.type == TokenType.COMMA:
                pos += 1
                continue
            if tok.type == TokenType.IDENTIFIER:
                field = FieldReference(name=tok.value)
                pos += 1
                desc = False
                if pos < len(tokens) and tokens[pos].type == TokenType.DESC:
                    desc = True
                    pos += 1
                elif pos < len(tokens) and tokens[pos].type == TokenType.ASC:
                    pos += 1
                items.append(OrderByItem(field=field, descending=desc))
            else:
                pos += 1
        return items, pos

    def _parse_create(self, ctx: ParseContext) -> tuple[CreateTableStatement, int]:
        """Parse CREATE TABLE/VIEW statement."""
        pos = ctx.pos + 1  # Skip CREATE
        is_view = False

        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.VIEW:
            is_view = True
            pos += 1
        elif pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.TABLE:
            pos += 1

        # Parse target table
        new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
        target, pos = self._parse_table_ref(new_ctx)

        # Skip AS
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.AS:
            pos += 1

        # Parse SELECT
        new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
        select, pos = self._parse_select(new_ctx)

        return CreateTableStatement(target=target, select=select, is_view=is_view), pos

    def _parse_insert(self, ctx: ParseContext) -> tuple[InsertStatement, int]:
        """Parse INSERT statement (simplified)."""
        pos = ctx.pos + 1  # Skip INSERT
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.INTO:
            pos += 1

        new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
        target, pos = self._parse_table_ref(new_ctx)

        # Skip to semicolon (simplified)
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
            pos += 1
        if pos < len(ctx.tokens):
            pos += 1

        return InsertStatement(target=target), pos

    def _parse_update(self, ctx: ParseContext) -> tuple[UpdateStatement, int]:
        """Parse UPDATE statement (simplified)."""
        pos = ctx.pos + 1  # Skip UPDATE

        new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
        target, pos = self._parse_table_ref(new_ctx)

        # Skip to semicolon (simplified)
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
            pos += 1
        if pos < len(ctx.tokens):
            pos += 1

        return UpdateStatement(target=target), pos

    def _parse_delete(self, ctx: ParseContext) -> tuple[DeleteStatement, int]:
        """Parse DELETE statement."""
        pos = ctx.pos + 1  # Skip DELETE
        if pos < len(ctx.tokens) and ctx.tokens[pos].type == TokenType.FROM:
            pos += 1

        new_ctx = ParseContext(ctx.tokens, pos, ctx.macro_vars, ctx.libraries)
        target, pos = self._parse_table_ref(new_ctx)

        # Skip to semicolon
        while pos < len(ctx.tokens) and ctx.tokens[pos].type != TokenType.SEMICOLON:
            pos += 1
        if pos < len(ctx.tokens):
            pos += 1

        return DeleteStatement(target=target), pos

    def _parse_simple_expression(
        self, tokens: list[Token], pos: int
    ) -> tuple[Expression, int]:
        """Parse simple expression (field, literal, or function)."""
        if pos >= len(tokens):
            return Literal(value=""), pos

        tok = tokens[pos]

        if tok.type == TokenType.IDENTIFIER:
            name = tok.value
            pos += 1
            # Check for table.field
            if pos < len(tokens) and tokens[pos].type == TokenType.DOT:
                pos += 1
                if pos < len(tokens) and tokens[pos].type == TokenType.IDENTIFIER:
                    field_name = tokens[pos].value
                    pos += 1
                    return FieldExpression(
                        field=FieldReference(name=field_name, table_alias=name)
                    ), pos
            # Check for function call
            if pos < len(tokens) and tokens[pos].type == TokenType.LPAREN:
                # Skip function arguments
                depth = 1
                pos += 1
                while pos < len(tokens) and depth > 0:
                    if tokens[pos].type == TokenType.LPAREN:
                        depth += 1
                    elif tokens[pos].type == TokenType.RPAREN:
                        depth -= 1
                    pos += 1
            return FieldExpression(field=FieldReference(name=name)), pos

        if tok.type == TokenType.NUMBER:
            pos += 1
            return Literal(value=tok.value, literal_type="number"), pos

        if tok.type == TokenType.STRING:
            pos += 1
            return Literal(value=tok.value, literal_type="string"), pos

        if tok.type == TokenType.STAR:
            pos += 1
            return Literal(value="*", literal_type="string"), pos

        pos += 1
        return Literal(value=tok.value), pos

    def _parse_expression_until(
        self, tokens: list[Token], pos: int, stop: set[TokenType]
    ) -> tuple[Expression, int]:
        """Parse expression until stop token (simplified)."""
        fields: list[FieldReference] = []
        start_pos = pos

        while pos < len(tokens) and tokens[pos].type not in stop:
            if tokens[pos].type == TokenType.IDENTIFIER:
                name = tokens[pos].value
                pos += 1
                table_alias = None
                if pos < len(tokens) and tokens[pos].type == TokenType.DOT:
                    pos += 1
                    if pos < len(tokens) and tokens[pos].type == TokenType.IDENTIFIER:
                        table_alias = name
                        name = tokens[pos].value
                        pos += 1
                fields.append(FieldReference(name=name, table_alias=table_alias))
            else:
                pos += 1

        if not fields:
            return Literal(value="<expression>"), pos

        if len(fields) == 1:
            return FieldExpression(field=fields[0]), pos

        # Return first field for now
        return FieldExpression(field=fields[0]), pos
