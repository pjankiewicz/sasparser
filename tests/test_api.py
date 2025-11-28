"""Tests for the public API."""

import pytest
import sys
sys.path.insert(0, "src")

import sasparser
from sasparser import (
    parse, parse_file, SASParser, ParseResult,
    extract_tables, extract_fields, extract_dependencies, extract_all,
    TableInfo, FieldInfo, ExtractionResult,
    ASTVisitor, TableVisitor, FieldVisitor, DependencyVisitor,
    ASTNode, TableReference, FieldReference,
    Token, TokenType,
    ParseError, LexerError,
)


class TestPublicImports:
    """Test that all public API items are importable."""

    def test_parse_function(self):
        assert callable(parse)

    def test_sasparser_class(self):
        assert SASParser is not None
        parser = SASParser()
        assert callable(parser.parse)

    def test_result_classes(self):
        assert ParseResult is not None
        assert TableInfo is not None
        assert FieldInfo is not None
        assert ExtractionResult is not None

    def test_visitor_classes(self):
        assert ASTVisitor is not None
        assert TableVisitor is not None
        assert FieldVisitor is not None
        assert DependencyVisitor is not None

    def test_ast_classes(self):
        assert ASTNode is not None
        assert TableReference is not None
        assert FieldReference is not None

    def test_token_classes(self):
        assert Token is not None
        assert TokenType is not None

    def test_error_classes(self):
        assert ParseError is not None
        assert LexerError is not None

    def test_version(self):
        assert hasattr(sasparser, "__version__")


class TestParseFunction:
    """Test the main parse function."""

    def test_parse_returns_result(self):
        result = parse("DATA x; RUN;")
        assert isinstance(result, ParseResult)

    def test_parse_result_has_statements(self):
        result = parse("DATA x; RUN;")
        assert hasattr(result, "statements")
        assert isinstance(result.statements, list)

    def test_parse_result_has_errors(self):
        result = parse("DATA x; RUN;")
        assert hasattr(result, "errors")
        assert isinstance(result.errors, list)

    def test_parse_result_is_valid(self):
        result = parse("DATA x; RUN;")
        assert result.is_valid is True
        assert result.has_errors is False


class TestSASParserClass:
    """Test the SASParser class."""

    def test_create_parser(self):
        parser = SASParser()
        assert parser is not None

    def test_parser_parse_method(self):
        parser = SASParser()
        result = parser.parse("DATA x; RUN;")
        assert isinstance(result, ParseResult)

    def test_parser_with_error_recovery(self):
        parser = SASParser(recover_from_errors=True)
        result = parser.parse("DATA x; RUN;")
        assert result is not None


class TestExtractionFunctions:
    """Test extraction utility functions."""

    def test_extract_tables(self):
        result = parse("DATA output; SET input; RUN;")
        tables = extract_tables(result)
        assert isinstance(tables, list)
        assert len(tables) == 2

    def test_extract_fields(self):
        result = parse("DATA out; x = y + 1; RUN;")
        fields = extract_fields(result)
        assert isinstance(fields, list)

    def test_extract_dependencies(self):
        result = parse("DATA output; SET input; RUN;")
        deps = extract_dependencies(result)
        assert isinstance(deps, list)

    def test_extract_all(self):
        result = parse("DATA output; SET input; x = y; RUN;")
        extraction = extract_all(result)
        assert isinstance(extraction, ExtractionResult)
        assert hasattr(extraction, "tables")
        assert hasattr(extraction, "fields")
        assert hasattr(extraction, "dependencies")


class TestTableInfo:
    """Test TableInfo dataclass."""

    def test_table_info_qualified_name(self):
        result = parse("DATA work.output; SET mylib.input; RUN;")
        tables = extract_tables(result)
        names = [t.qualified_name for t in tables]
        assert "work.output" in names
        assert "mylib.input" in names

    def test_table_info_usage(self):
        result = parse("DATA output; SET input; RUN;")
        tables = extract_tables(result)
        # Check that usage is tracked
        for table in tables:
            assert hasattr(table, "usage")


class TestCustomVisitor:
    """Test creating custom visitors."""

    def test_custom_visitor(self):
        class CountingVisitor(ASTVisitor):
            def __init__(self):
                self.count = 0

            def visit_DataStep(self, node):
                self.count += 1
                return super().generic_visit(node)

        result = parse("DATA a; RUN; DATA b; RUN;")
        visitor = CountingVisitor()
        for stmt in result.statements:
            visitor.visit(stmt)

        assert visitor.count == 2


class TestErrorHandling:
    """Test error handling."""

    def test_empty_input(self):
        result = parse("")
        assert result.is_valid
        assert len(result.statements) == 0

    def test_whitespace_only(self):
        result = parse("   \n\t  ")
        assert result.is_valid
        assert len(result.statements) == 0
