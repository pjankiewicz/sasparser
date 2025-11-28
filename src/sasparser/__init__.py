"""
SASParser - A Python library for parsing SAS code into Abstract Syntax Trees.

This library provides comprehensive SAS code parsing capabilities including:
- Full AST representation of SAS programs
- Support for DATA steps, PROC SQL, and common SAS procedures
- Macro and LIBNAME statement handling
- Visitor pattern for custom AST analysis
- Extraction utilities for tables, fields, and dependencies

Usage:
    from sasparser import parse, SASParser

    # Quick parsing
    result = parse(sas_code)
    for stmt in result.statements:
        print(stmt)

    # Extract tables and fields
    from sasparser import extract_tables, extract_fields
    tables = extract_tables(result)
    fields = extract_fields(result)

    # Get dependency graph
    from sasparser import extract_dependencies
    deps = extract_dependencies(result)
"""

from .parser import SASParser, ParseResult, parse, parse_file
from .models import (
    TableInfo,
    FieldInfo,
    ExtractionResult,
    extract_tables,
    extract_fields,
    extract_dependencies,
    extract_all,
)
from .visitors import (
    ASTVisitor,
    TableVisitor,
    FieldVisitor,
    DependencyVisitor,
)

# Core types for advanced usage
from .ast.base import ASTNode, TableReference, FieldReference
from .core.tokens import Token, TokenType
from .core.errors import ParseError, LexerError

__version__ = "0.1.0"

__all__ = [
    # Main parser
    "SASParser",
    "ParseResult",
    "parse",
    "parse_file",
    # Extraction
    "TableInfo",
    "FieldInfo",
    "ExtractionResult",
    "extract_tables",
    "extract_fields",
    "extract_dependencies",
    "extract_all",
    # Visitors
    "ASTVisitor",
    "TableVisitor",
    "FieldVisitor",
    "DependencyVisitor",
    # Core types
    "ASTNode",
    "TableReference",
    "FieldReference",
    "Token",
    "TokenType",
    "ParseError",
    "LexerError",
]
