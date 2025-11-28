# SASParser

A Python library for parsing SAS code into Abstract Syntax Trees (AST). Extract tables, fields, and dependencies from SAS programs.

## Features

- **Zero dependencies** - Uses only Python 3.10+ standard library
- **Full AST** - Complete abstract syntax tree representation
- **Table extraction** - Identify all input/output tables
- **Field extraction** - Track field usage (read, write, keep, drop)
- **Dependency analysis** - Build data lineage graphs
- **Extensible** - Custom visitors for specialized analysis

## Supported SAS Constructs

- DATA steps (SET, MERGE, BY, WHERE, IF/THEN/ELSE, KEEP, DROP, OUTPUT)
- PROC SQL (SELECT, JOIN, CREATE TABLE, INSERT, UPDATE, DELETE)
- PROC SORT, PROC MEANS/SUMMARY, PROC FREQ, PROC PRINT
- LIBNAME statements
- Macro definitions and calls (%LET, %MACRO, %MEND)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd sasparser

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install with dev dependencies (for testing)
pip install -e ".[dev]"
```

## Quick Start

```python
from sasparser import parse, extract_tables, extract_fields

# Parse SAS code
sas_code = """
DATA work.sales_summary;
    SET raw.daily_sales;
    total = quantity * price;
    IF total > 1000 THEN flag = 1;
    KEEP customer_id date total flag;
RUN;

PROC SORT DATA=work.sales_summary;
    BY customer_id date;
RUN;
"""

result = parse(sas_code)

# Extract tables
tables = extract_tables(result)
for t in tables:
    print(f"Table: {t.qualified_name} ({t.usage})")

# Extract fields
fields = extract_fields(result)
for f in fields:
    print(f"Field: {f.name}")
```

Output:
```
Table: work.sales_summary (output)
Table: raw.daily_sales (input)
Field: total
Field: quantity
Field: price
Field: flag
Field: customer_id
Field: date
```

## Usage Examples

### Parse and Inspect AST

```python
from sasparser import parse

result = parse("DATA out; SET in; x = y + 1; RUN;")

# Check for errors
if result.has_errors:
    for error in result.errors:
        print(f"Error: {error}")
else:
    # Iterate over statements
    for stmt in result.statements:
        print(f"Statement type: {type(stmt).__name__}")
```

### Extract Table Dependencies

```python
from sasparser import parse, extract_dependencies

code = """
DATA step1; SET raw_data; RUN;
DATA step2; SET step1; RUN;
DATA final; MERGE step1 step2; BY id; RUN;
"""

result = parse(code)
deps = extract_dependencies(result)

for dep in deps:
    inputs = ", ".join(t.dataset for t in dep.input_tables)
    print(f"{dep.output_table.dataset} <- {inputs}")
```

Output:
```
step1 <- raw_data
step2 <- step1
final <- step1, step2
```

### Custom Visitor

```python
from sasparser import parse, ASTVisitor

class TableCounter(ASTVisitor):
    def __init__(self):
        self.count = 0

    def visit_TableReference(self, node):
        self.count += 1
        return super().generic_visit(node)

result = parse("DATA a; SET b c d; RUN;")
visitor = TableCounter()
for stmt in result.statements:
    visitor.visit(stmt)

print(f"Total table references: {visitor.count}")
```

### Full Extraction

```python
from sasparser import parse, extract_all

result = parse(sas_code)
extraction = extract_all(result)

print("Input tables:", [t.qualified_name for t in extraction.input_tables])
print("Output tables:", [t.qualified_name for t in extraction.output_tables])
print("All fields:", [f.name for f in extraction.fields])
```

## Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_lexer.py

# Run with coverage
pytest --cov=sasparser
```

## Project Structure

```
sasparser/
├── pyproject.toml          # Project configuration
├── README.md               # This file
├── .gitignore
├── src/
│   └── sasparser/
│       ├── __init__.py     # Public API
│       ├── parser.py       # Main parser
│       ├── models.py       # Extraction utilities
│       ├── core/
│       │   ├── tokens.py   # Token types
│       │   ├── lexer.py    # Tokenizer
│       │   └── errors.py   # Error classes
│       ├── ast/
│       │   ├── base.py     # Base AST nodes
│       │   ├── expressions.py
│       │   ├── statements.py
│       │   ├── data_step.py
│       │   ├── proc_sql.py
│       │   └── proc_other.py
│       ├── handlers/
│       │   ├── base.py     # Handler base class
│       │   ├── data_step.py
│       │   ├── proc_sql.py
│       │   ├── proc_sort.py
│       │   ├── proc_means.py
│       │   ├── proc_freq.py
│       │   ├── proc_print.py
│       │   ├── macro.py
│       │   └── libname.py
│       └── visitors/
│           ├── base.py     # Visitor base class
│           ├── table_visitor.py
│           ├── field_visitor.py
│           └── dependency_visitor.py
├── tests/
│   ├── test_lexer.py
│   ├── test_data_step.py
│   ├── test_procs.py
│   ├── test_visitors.py
│   └── test_api.py
└── examples/
    └── analyze_script.py   # Example usage script
```

## API Reference

### Main Functions

- `parse(source: str) -> ParseResult` - Parse SAS code
- `parse_file(filepath: str) -> ParseResult` - Parse SAS file
- `extract_tables(result: ParseResult) -> list[TableInfo]` - Extract tables
- `extract_fields(result: ParseResult) -> list[FieldInfo]` - Extract fields
- `extract_dependencies(result: ParseResult) -> list[TableDependency]` - Extract dependencies
- `extract_all(result: ParseResult) -> ExtractionResult` - Extract everything

### Classes

- `SASParser` - Main parser class
- `ParseResult` - Parsing result with statements and errors
- `TableInfo` - Table information (name, library, usage)
- `FieldInfo` - Field information (name, table, usage)
- `ASTVisitor` - Base class for custom visitors

## License

MIT License
