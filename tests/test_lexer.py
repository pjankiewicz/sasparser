"""Tests for the SAS lexer/tokenizer."""

import pytest
import sys
sys.path.insert(0, "src")

from sasparser.core.lexer import Lexer
from sasparser.core.tokens import TokenType


class TestLexerBasics:
    """Test basic tokenization."""

    def test_empty_input(self):
        lexer = Lexer("")
        tokens = lexer.tokenize()
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_whitespace_only(self):
        lexer = Lexer("   \n\t  ")
        tokens = lexer.tokenize()
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_identifier(self):
        lexer = Lexer("myvar")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "myvar"

    def test_identifier_with_underscore(self):
        lexer = Lexer("my_var_123")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "my_var_123"


class TestLexerKeywords:
    """Test keyword recognition."""

    def test_data_keyword(self):
        lexer = Lexer("DATA")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.DATA

    def test_case_insensitive_keywords(self):
        for kw in ["data", "DATA", "Data", "dAtA"]:
            lexer = Lexer(kw)
            tokens = lexer.tokenize()
            assert tokens[0].type == TokenType.DATA

    def test_proc_keywords(self):
        lexer = Lexer("PROC SQL")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.PROC
        assert tokens[1].type == TokenType.SQL

    def test_sql_keywords(self):
        lexer = Lexer("SELECT FROM WHERE JOIN LEFT RIGHT INNER")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]  # Exclude EOF
        assert types == [
            TokenType.SELECT, TokenType.FROM, TokenType.WHERE,
            TokenType.JOIN, TokenType.LEFT, TokenType.RIGHT, TokenType.INNER
        ]


class TestLexerLiterals:
    """Test literal tokenization."""

    def test_integer(self):
        lexer = Lexer("123")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "123"

    def test_decimal(self):
        lexer = Lexer("123.456")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "123.456"

    def test_scientific_notation(self):
        lexer = Lexer("1.5e10")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "1.5e10"

    def test_single_quoted_string(self):
        lexer = Lexer("'hello world'")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello world"

    def test_double_quoted_string(self):
        lexer = Lexer('"hello world"')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello world"

    def test_date_literal(self):
        lexer = Lexer("'01JAN2020'd")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.DATE_LITERAL


class TestLexerOperators:
    """Test operator tokenization."""

    def test_arithmetic_operators(self):
        lexer = Lexer("+ - * /")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH]

    def test_comparison_operators(self):
        lexer = Lexer("= < > <= >= <> !=")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [
            TokenType.EQUALS, TokenType.LT, TokenType.GT,
            TokenType.LE, TokenType.GE, TokenType.NE, TokenType.NE
        ]

    def test_logical_operators(self):
        lexer = Lexer("AND OR NOT")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [TokenType.AND, TokenType.OR, TokenType.NOT]


class TestLexerDelimiters:
    """Test delimiter tokenization."""

    def test_semicolon(self):
        lexer = Lexer(";")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.SEMICOLON

    def test_parentheses(self):
        lexer = Lexer("()")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.LPAREN
        assert tokens[1].type == TokenType.RPAREN

    def test_dot(self):
        lexer = Lexer(".")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.DOT


class TestLexerMacros:
    """Test macro tokenization."""

    def test_macro_variable(self):
        lexer = Lexer("&myvar")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.MACRO_VAR
        assert tokens[0].value == "&myvar"

    def test_double_ampersand(self):
        lexer = Lexer("&&myvar")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.MACRO_VAR
        assert tokens[0].value == "&&myvar"

    def test_percent_let(self):
        lexer = Lexer("%let")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.PERCENT_LET

    def test_percent_macro(self):
        lexer = Lexer("%macro")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.PERCENT_MACRO

    def test_macro_call(self):
        lexer = Lexer("%mymacro")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.MACRO_CALL
        assert tokens[0].value == "%mymacro"


class TestLexerComments:
    """Test comment handling."""

    def test_block_comment(self):
        lexer = Lexer("/* this is a comment */ DATA")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.DATA

    def test_line_comment(self):
        lexer = Lexer("* this is a comment;\nDATA")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.DATA


class TestLexerComplexStatements:
    """Test tokenization of complete statements."""

    def test_data_step(self):
        code = "DATA work.output; SET work.input; RUN;"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert TokenType.DATA in types
        assert TokenType.SET in types
        assert TokenType.RUN in types

    def test_proc_sql(self):
        code = "PROC SQL; SELECT * FROM mytable; QUIT;"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]
        assert TokenType.PROC in types
        assert TokenType.SQL in types
        assert TokenType.SELECT in types
        assert TokenType.FROM in types
        assert TokenType.QUIT in types

    def test_qualified_name(self):
        code = "work.mytable"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "work"
        assert tokens[1].type == TokenType.DOT
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "mytable"


class TestLexerLineNumbers:
    """Test line and column tracking."""

    def test_single_line(self):
        lexer = Lexer("DATA work;")
        tokens = lexer.tokenize()
        assert tokens[0].line == 1
        assert tokens[0].column == 1

    def test_multiline(self):
        code = "DATA\nwork;"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        assert tokens[0].line == 1  # DATA
        assert tokens[1].line == 2  # work
