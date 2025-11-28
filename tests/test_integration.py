"""Integration tests with realistic SAS scripts."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, "src")

from sasparser import parse, extract_tables, extract_fields, extract_dependencies, extract_all


# Sample ETL script for integration testing
SAMPLE_ETL_SCRIPT = """
/*******************************************************************************
* Sample ETL Pipeline - Sales Data Processing
*******************************************************************************/

/* Define library references */
LIBNAME raw '/data/raw';
LIBNAME staging '/data/staging';
LIBNAME mart '/data/mart';

/* Set macro variables */
%LET report_date = 2024-01-15;
%LET min_order_value = 100;

/* Step 1: Load and clean customer data */
DATA staging.customers_clean;
    SET raw.customers;
    first_name = PROPCASE(first_name);
    last_name = PROPCASE(last_name);
    full_name = CATX(' ', first_name, last_name);
    email = LOWCASE(STRIP(email));
    tenure_days = INTCK('day', signup_date, TODAY());
    IF lifetime_value > 10000 THEN premium_flag = 1;
    ELSE premium_flag = 0;
    WHERE status = 'ACTIVE';
    KEEP customer_id first_name last_name full_name email
         signup_date tenure_days lifetime_value premium_flag segment region;
RUN;

/* Step 2: Process order transactions */
DATA staging.orders_processed;
    SET raw.orders;
    order_total = quantity * unit_price;
    discount_amount = order_total * (discount_pct / 100);
    net_amount = order_total - discount_amount;
    order_year = YEAR(order_date);
    order_month = MONTH(order_date);
    IF WEEKDAY(order_date) IN (1, 7) THEN weekend_order = 1;
    ELSE weekend_order = 0;
    DROP discount_pct;
RUN;

/* Step 3: Sort and merge */
PROC SORT DATA=staging.orders_processed OUT=staging.orders_sorted;
    BY customer_id;
RUN;

PROC SORT DATA=staging.customers_clean OUT=staging.customers_sorted;
    BY customer_id;
RUN;

DATA staging.orders_enriched;
    MERGE staging.orders_sorted (IN=a)
          staging.customers_sorted (IN=b);
    BY customer_id;
    IF a AND b;
RUN;

/* Step 4: Aggregate metrics */
PROC MEANS DATA=staging.orders_enriched NOPRINT;
    CLASS customer_id;
    VAR net_amount quantity;
    OUTPUT OUT=staging.customer_agg
        SUM(net_amount)=total_revenue
        MEAN(net_amount)=avg_order_value;
RUN;

/* Step 5: Create final summary */
DATA mart.customer_summary;
    MERGE staging.customers_clean
          staging.customer_agg;
    BY customer_id;
    IF total_revenue > 5000 THEN customer_tier = 'Gold';
    ELSE IF total_revenue > 1000 THEN customer_tier = 'Silver';
    ELSE customer_tier = 'Bronze';
RUN;

/* Step 6: Print report */
PROC PRINT DATA=mart.customer_summary (OBS=100);
    VAR customer_id full_name total_revenue customer_tier;
RUN;
"""


class TestETLScriptParsing:
    """Test parsing of a complete ETL script."""

    def test_parse_complete_script(self):
        """Test that the complete script parses without errors."""
        result = parse(SAMPLE_ETL_SCRIPT)
        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.statements) > 0

    def test_statement_count(self):
        """Test that expected number of statements are parsed."""
        result = parse(SAMPLE_ETL_SCRIPT)
        # Should have: LIBNAME x3, %LET x2, DATA x5, PROC SORT x2, PROC MEANS x1, PROC PRINT x1
        assert len(result.statements) >= 10


class TestETLTableExtraction:
    """Test table extraction from ETL script."""

    def test_extract_all_tables(self):
        """Test that all tables are extracted."""
        result = parse(SAMPLE_ETL_SCRIPT)
        tables = extract_tables(result)

        # Get all table names
        table_names = [t.qualified_name for t in tables]

        # Check for expected tables
        assert "raw.customers" in table_names
        assert "raw.orders" in table_names
        assert "staging.customers_clean" in table_names
        assert "staging.orders_processed" in table_names
        assert "staging.orders_enriched" in table_names
        assert "mart.customer_summary" in table_names

    def test_input_tables(self):
        """Test that input tables are correctly identified."""
        result = parse(SAMPLE_ETL_SCRIPT)
        extraction = extract_all(result)

        input_names = [t.qualified_name for t in extraction.input_tables]

        # Raw tables should be inputs
        assert "raw.customers" in input_names
        assert "raw.orders" in input_names

    def test_output_tables(self):
        """Test that output tables are correctly identified."""
        result = parse(SAMPLE_ETL_SCRIPT)
        extraction = extract_all(result)

        output_names = [t.qualified_name for t in extraction.output_tables]

        # Staging tables should be outputs
        assert "staging.customers_clean" in output_names
        assert "staging.orders_processed" in output_names


class TestETLFieldExtraction:
    """Test field extraction from ETL script."""

    def test_extract_fields(self):
        """Test that fields are extracted."""
        result = parse(SAMPLE_ETL_SCRIPT)
        fields = extract_fields(result)

        field_names = [f.name for f in fields]

        # Check for expected fields
        assert "customer_id" in field_names
        assert "first_name" in field_names
        assert "last_name" in field_names
        assert "email" in field_names
        assert "order_total" in field_names
        assert "net_amount" in field_names

    def test_created_fields(self):
        """Test that created/calculated fields are identified."""
        result = parse(SAMPLE_ETL_SCRIPT)
        fields = extract_fields(result)

        # Fields that are created (written)
        write_fields = [f.name for f in fields if f.usage == "write"]

        # These are calculated fields
        assert "order_total" in write_fields
        assert "net_amount" in write_fields
        assert "discount_amount" in write_fields

    def test_kept_fields(self):
        """Test that KEEP statement fields are tracked."""
        result = parse(SAMPLE_ETL_SCRIPT)
        fields = extract_fields(result)

        kept_fields = [f.name for f in fields if f.usage == "kept"]

        assert "customer_id" in kept_fields
        assert "email" in kept_fields


class TestETLDependencies:
    """Test dependency extraction from ETL script."""

    def test_extract_dependencies(self):
        """Test that dependencies are extracted."""
        result = parse(SAMPLE_ETL_SCRIPT)
        deps = extract_dependencies(result)

        assert len(deps) > 0

    def test_data_lineage(self):
        """Test that data lineage is correct."""
        result = parse(SAMPLE_ETL_SCRIPT)
        deps = extract_dependencies(result)

        # Build a simple dependency map
        dep_map = {}
        for dep in deps:
            out = dep.output_table.qualified_name
            inputs = [t.qualified_name for t in dep.input_tables]
            dep_map[out] = inputs

        # staging.customers_clean comes from raw.customers
        if "staging.customers_clean" in dep_map:
            assert "raw.customers" in dep_map["staging.customers_clean"]

        # staging.orders_processed comes from raw.orders
        if "staging.orders_processed" in dep_map:
            assert "raw.orders" in dep_map["staging.orders_processed"]


class TestComplexScenarios:
    """Test complex SAS scenarios."""

    def test_merge_with_multiple_inputs(self):
        """Test MERGE statement with multiple input tables."""
        code = """
        DATA output;
            MERGE table1 table2 table3;
            BY id;
        RUN;
        """
        result = parse(code)
        deps = extract_dependencies(result)

        assert len(deps) == 1
        input_names = [t.dataset for t in deps[0].input_tables]
        assert "table1" in input_names
        assert "table2" in input_names
        assert "table3" in input_names

    def test_proc_sort_chain(self):
        """Test PROC SORT with DATA= and OUT=."""
        code = """
        PROC SORT DATA=input OUT=sorted;
            BY key;
        RUN;

        DATA final;
            SET sorted;
        RUN;
        """
        result = parse(code)
        tables = extract_tables(result)

        names = [t.name for t in tables]
        assert "input" in names
        assert "sorted" in names
        assert "final" in names

    def test_multiple_data_steps_pipeline(self):
        """Test a multi-step data pipeline."""
        code = """
        DATA step1;
            SET raw;
            x = y + 1;
        RUN;

        DATA step2;
            SET step1;
            z = x * 2;
        RUN;

        DATA step3;
            SET step2;
            final = z + 100;
        RUN;
        """
        result = parse(code)
        deps = extract_dependencies(result)

        # Should have 3 dependencies
        assert len(deps) == 3

        # Check lineage
        dep_map = {d.output_table.dataset: [t.dataset for t in d.input_tables] for d in deps}

        assert "raw" in dep_map.get("step1", [])
        assert "step1" in dep_map.get("step2", [])
        assert "step2" in dep_map.get("step3", [])

    def test_script_with_macros(self):
        """Test script with macro variables."""
        code = """
        %LET lib = work;
        %LET table = mydata;

        DATA &lib..output;
            SET &lib..&table;
        RUN;
        """
        result = parse(code)
        assert result.is_valid
        assert len(result.statements) >= 1
