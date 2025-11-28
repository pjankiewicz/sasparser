#!/usr/bin/env python3
"""
Example: Analyze a SAS script to extract tables and fields.

This script demonstrates how to use sasparser to:
1. Parse a SAS script
2. Extract all tables used (input and output)
3. Extract all fields referenced
4. Show data dependencies (lineage)

Usage:
    python examples/analyze_script.py
    python examples/analyze_script.py path/to/script.sas
"""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sasparser import (
    parse,
    parse_file,
    extract_tables,
    extract_fields,
    extract_dependencies,
    extract_all,
)


def print_separator(title: str = "") -> None:
    """Print a section separator."""
    print("\n" + "=" * 70)
    if title:
        print(f" {title}")
        print("=" * 70)


def analyze_sas_code(source: str, source_name: str = "SAS Code") -> None:
    """Analyze SAS code and print extracted information."""

    print_separator(f"Analyzing: {source_name}")

    # Parse the code
    result = parse(source)

    # Check for errors
    if result.has_errors:
        print("\nParsing Errors:")
        for error in result.errors:
            print(f"  - {error}")
        print()

    print(f"\nParsed {len(result.statements)} statements")

    # Extract everything
    extraction = extract_all(result)

    # --- Tables ---
    print_separator("TABLES")

    if extraction.input_tables:
        print("\nInput Tables (data sources):")
        for t in extraction.input_tables:
            print(f"  - {t.qualified_name}")

    if extraction.output_tables:
        print("\nOutput Tables (created/modified):")
        for t in extraction.output_tables:
            print(f"  - {t.qualified_name}")

    # --- Fields ---
    print_separator("FIELDS")

    if extraction.fields:
        # Group by usage type
        read_fields = [f for f in extraction.fields if f.usage == "read"]
        write_fields = [f for f in extraction.fields if f.usage == "write"]
        kept_fields = [f for f in extraction.fields if f.usage == "kept"]
        dropped_fields = [f for f in extraction.fields if f.usage == "dropped"]

        def format_field(f):
            """Format a field with its source tables."""
            if f.source_tables:
                tables = ", ".join(f.source_tables)
                return f"{f.name} (from: {tables})"
            return f.name

        if read_fields:
            print(f"\nFields Read ({len(read_fields)}):")
            # Sort by name but show with source tables
            for f in sorted(read_fields, key=lambda x: x.name.lower()):
                print(f"  - {format_field(f)}")

        if write_fields:
            print(f"\nFields Written/Created ({len(write_fields)}):")
            for f in sorted(write_fields, key=lambda x: x.name.lower()):
                print(f"  - {format_field(f)}")

        if kept_fields:
            print(f"\nFields in KEEP statements ({len(kept_fields)}):")
            for f in sorted(kept_fields, key=lambda x: x.name.lower()):
                print(f"  - {format_field(f)}")

        if dropped_fields:
            print(f"\nFields in DROP statements ({len(dropped_fields)}):")
            for f in sorted(dropped_fields, key=lambda x: x.name.lower()):
                print(f"  - {format_field(f)}")

    # --- Dependencies ---
    print_separator("DATA LINEAGE")

    if extraction.dependencies:
        print("\nData flow (output <- inputs):")
        for dep in extraction.dependencies:
            inputs = ", ".join(t.qualified_name for t in dep.input_tables)
            output = dep.output_table.qualified_name
            print(f"  {output}")
            print(f"    <- {inputs}")
            print(f"    ({dep.statement_type})")
    else:
        print("\nNo dependencies found.")

    print_separator()


def main():
    """Main entry point."""

    # Check if a file path was provided
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        if not Path(filepath).exists():
            print(f"Error: File not found: {filepath}")
            sys.exit(1)

        with open(filepath) as f:
            source = f.read()
        analyze_sas_code(source, filepath)
    else:
        # Use the sample ETL script
        sample_path = Path(__file__).parent / "sample_etl.sas"
        if sample_path.exists():
            with open(sample_path) as f:
                source = f.read()
            analyze_sas_code(source, "sample_etl.sas")
        else:
            # Use inline example
            example_code = """
/* Example SAS ETL Script */
LIBNAME mylib '/data';

DATA work.cleaned_sales;
    SET mylib.raw_sales;
    total = quantity * price;
    profit = total - cost;
    IF profit > 0 THEN profitable = 1;
    ELSE profitable = 0;
    KEEP order_id customer_id product_id total profit profitable order_date;
RUN;

PROC SORT DATA=work.cleaned_sales OUT=work.sorted_sales;
    BY customer_id order_date;
RUN;

DATA work.customer_orders;
    SET work.sorted_sales;
    BY customer_id;
    RETAIN running_total 0;
    running_total = running_total + total;
    IF LAST.customer_id THEN OUTPUT;
RUN;

PROC MEANS DATA=work.customer_orders;
    CLASS customer_id;
    VAR total profit;
RUN;
"""
            analyze_sas_code(example_code, "Inline Example")


if __name__ == "__main__":
    main()
