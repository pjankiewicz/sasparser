"""Tests for AST visitors."""

import pytest
import sys
sys.path.insert(0, "src")

from sasparser import (
    parse, extract_tables, extract_fields, extract_dependencies,
    TableVisitor, FieldVisitor, DependencyVisitor,
)


class TestTableVisitor:
    """Test table extraction."""

    def test_data_step_input_output(self):
        result = parse("DATA output; SET input; RUN;")
        tables = extract_tables(result)
        names = [t.qualified_name for t in tables]
        assert "output" in names
        assert "input" in names

    def test_qualified_table_names(self):
        result = parse("DATA work.output; SET mylib.input; RUN;")
        tables = extract_tables(result)
        names = [t.qualified_name for t in tables]
        assert "work.output" in names
        assert "mylib.input" in names

    def test_merge_tables(self):
        result = parse("DATA out; MERGE a b c; BY id; RUN;")
        tables = extract_tables(result)
        names = [t.name for t in tables]
        assert "a" in names
        assert "b" in names
        assert "c" in names

    def test_proc_sort_tables(self):
        result = parse("PROC SORT DATA=input OUT=output; BY id; RUN;")
        tables = extract_tables(result)
        names = [t.name for t in tables]
        assert "input" in names
        assert "output" in names

    def test_input_output_classification(self):
        result = parse("DATA output; SET input; RUN;")
        visitor = TableVisitor()
        for stmt in result.statements:
            visitor.visit(stmt)

        input_names = [t.dataset for t in visitor.get_input_tables()]
        output_names = [t.dataset for t in visitor.get_output_tables()]

        assert "input" in input_names
        assert "output" in output_names


class TestFieldVisitor:
    """Test field extraction."""

    def test_assignment_fields(self):
        result = parse("DATA out; new_var = old_var + 1; RUN;")
        fields = extract_fields(result)
        names = [f.name for f in fields]
        assert "new_var" in names
        assert "old_var" in names

    def test_keep_fields(self):
        result = parse("DATA out; SET in; KEEP x y z; RUN;")
        fields = extract_fields(result)
        names = [f.name for f in fields]
        assert "x" in names
        assert "y" in names
        assert "z" in names

    def test_by_fields(self):
        result = parse("DATA out; SET in; BY region date; RUN;")
        fields = extract_fields(result)
        names = [f.name for f in fields]
        assert "region" in names
        assert "date" in names

    def test_proc_means_fields(self):
        result = parse("PROC MEANS DATA=mydata; VAR sales profit; CLASS region; RUN;")
        fields = extract_fields(result)
        names = [f.name for f in fields]
        assert "sales" in names
        assert "profit" in names
        assert "region" in names

    def test_field_read_write_tracking(self):
        result = parse("DATA out; new_var = old_var * 2; RUN;")
        visitor = FieldVisitor()
        for stmt in result.statements:
            visitor.visit(stmt)

        read_names = [f.name for f in visitor.get_read_fields()]
        write_names = [f.name for f in visitor.get_write_fields()]

        assert "old_var" in read_names
        assert "new_var" in write_names


class TestDependencyVisitor:
    """Test dependency extraction."""

    def test_simple_dependency(self):
        result = parse("DATA output; SET input; RUN;")
        deps = extract_dependencies(result)
        assert len(deps) == 1
        assert deps[0].output_table.dataset == "output"
        assert deps[0].input_tables[0].dataset == "input"

    def test_merge_dependencies(self):
        result = parse("DATA combined; MERGE left right; BY id; RUN;")
        deps = extract_dependencies(result)
        assert len(deps) == 1
        input_names = [t.dataset for t in deps[0].input_tables]
        assert "left" in input_names
        assert "right" in input_names

    def test_dependency_graph(self):
        code = """
        DATA step1; SET raw; RUN;
        DATA step2; SET step1; RUN;
        """
        result = parse(code)
        visitor = DependencyVisitor()
        for stmt in result.statements:
            visitor.visit(stmt)

        graph = visitor.get_dependency_graph()
        assert "step1" in graph
        assert "step2" in graph

    def test_proc_sort_dependency(self):
        result = parse("PROC SORT DATA=input OUT=sorted; BY id; RUN;")
        deps = extract_dependencies(result)
        assert len(deps) == 1
        assert deps[0].input_tables[0].dataset == "input"
        assert deps[0].output_table.dataset == "sorted"


class TestExtractAll:
    """Test complete extraction."""

    def test_extract_tables_from_complex_code(self):
        code = """
        DATA work.step1;
            SET raw.source;
            x = y + 1;
        RUN;

        PROC SORT DATA=work.step1 OUT=work.sorted;
            BY id;
        RUN;
        """
        result = parse(code)
        tables = extract_tables(result)
        names = [t.qualified_name for t in tables]

        assert "work.step1" in names
        assert "raw.source" in names
        assert "work.sorted" in names

    def test_extract_fields_from_complex_code(self):
        code = """
        DATA output;
            SET input;
            total = price * quantity;
            IF total > 1000 THEN flag = 1;
            KEEP id total flag;
        RUN;
        """
        result = parse(code)
        fields = extract_fields(result)
        names = [f.name for f in fields]

        assert "total" in names
        assert "price" in names
        assert "quantity" in names
        assert "flag" in names
        assert "id" in names
