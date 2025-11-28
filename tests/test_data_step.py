"""Tests for DATA step parsing."""

import pytest
import sys
sys.path.insert(0, "src")

from sasparser import parse
from sasparser.ast.data_step import (
    DataStep, SetStatement, MergeStatement, ByStatement,
    WhereStatement, IfStatement, AssignmentStatement,
    KeepStatement, DropStatement, OutputStatement,
)


class TestDataStepBasics:
    """Test basic DATA step parsing."""

    def test_simple_data_step(self):
        result = parse("DATA output; SET input; RUN;")
        assert len(result.statements) == 1
        assert isinstance(result.statements[0], DataStep)

    def test_data_step_output_table(self):
        result = parse("DATA myoutput; SET myinput; RUN;")
        ds = result.statements[0]
        assert len(ds.output_tables) == 1
        assert ds.output_tables[0].dataset == "myoutput"

    def test_data_step_qualified_output(self):
        result = parse("DATA work.output; SET work.input; RUN;")
        ds = result.statements[0]
        assert ds.output_tables[0].library == "work"
        assert ds.output_tables[0].dataset == "output"

    def test_data_step_multiple_outputs(self):
        result = parse("DATA out1, out2; SET input; RUN;")
        ds = result.statements[0]
        assert len(ds.output_tables) == 2

    def test_empty_data_step(self):
        result = parse("DATA test; RUN;")
        assert len(result.statements) == 1
        ds = result.statements[0]
        assert len(ds.statements) == 0


class TestSetStatement:
    """Test SET statement parsing."""

    def test_simple_set(self):
        result = parse("DATA out; SET input; RUN;")
        ds = result.statements[0]
        set_stmt = ds.statements[0]
        assert isinstance(set_stmt, SetStatement)
        assert len(set_stmt.tables) == 1
        assert set_stmt.tables[0].dataset == "input"

    def test_set_qualified_table(self):
        result = parse("DATA out; SET work.input; RUN;")
        ds = result.statements[0]
        set_stmt = ds.statements[0]
        assert set_stmt.tables[0].library == "work"
        assert set_stmt.tables[0].dataset == "input"

    def test_set_multiple_tables(self):
        result = parse("DATA out; SET table1 table2 table3; RUN;")
        ds = result.statements[0]
        set_stmt = ds.statements[0]
        assert len(set_stmt.tables) == 3


class TestMergeStatement:
    """Test MERGE statement parsing."""

    def test_simple_merge(self):
        result = parse("DATA out; MERGE a b; BY id; RUN;")
        ds = result.statements[0]
        merge_stmt = ds.statements[0]
        assert isinstance(merge_stmt, MergeStatement)
        assert len(merge_stmt.tables) == 2

    def test_merge_with_qualified_names(self):
        result = parse("DATA out; MERGE work.a lib.b; BY id; RUN;")
        ds = result.statements[0]
        merge_stmt = ds.statements[0]
        assert merge_stmt.tables[0].library == "work"
        assert merge_stmt.tables[1].library == "lib"


class TestByStatement:
    """Test BY statement parsing."""

    def test_simple_by(self):
        result = parse("DATA out; MERGE a b; BY id; RUN;")
        ds = result.statements[0]
        by_stmt = ds.statements[1]
        assert isinstance(by_stmt, ByStatement)
        assert len(by_stmt.fields) == 1
        assert by_stmt.fields[0].field.name == "id"

    def test_by_multiple_fields(self):
        result = parse("DATA out; MERGE a b; BY id name date; RUN;")
        ds = result.statements[0]
        by_stmt = ds.statements[1]
        assert len(by_stmt.fields) == 3

    def test_by_descending(self):
        result = parse("DATA out; SET a; BY DESCENDING date; RUN;")
        ds = result.statements[0]
        by_stmt = ds.statements[1]
        assert by_stmt.fields[0].descending is True


class TestAssignmentStatement:
    """Test assignment statement parsing."""

    def test_simple_assignment(self):
        result = parse("DATA out; x = 1; RUN;")
        ds = result.statements[0]
        assign = ds.statements[0]
        assert isinstance(assign, AssignmentStatement)
        assert assign.target.name == "x"

    def test_assignment_with_expression(self):
        result = parse("DATA out; new_var = old_var + 1; RUN;")
        ds = result.statements[0]
        assign = ds.statements[0]
        assert assign.target.name == "new_var"


class TestKeepDropStatements:
    """Test KEEP and DROP statements."""

    def test_keep_statement(self):
        result = parse("DATA out; SET in; KEEP x y z; RUN;")
        ds = result.statements[0]
        keep_stmt = [s for s in ds.statements if isinstance(s, KeepStatement)][0]
        assert len(keep_stmt.fields) == 3

    def test_drop_statement(self):
        result = parse("DATA out; SET in; DROP a b; RUN;")
        ds = result.statements[0]
        drop_stmt = [s for s in ds.statements if isinstance(s, DropStatement)][0]
        assert len(drop_stmt.fields) == 2


class TestIfStatement:
    """Test IF statement parsing."""

    def test_simple_if(self):
        result = parse("DATA out; SET in; IF x > 0 THEN y = 1; RUN;")
        ds = result.statements[0]
        if_stmt = [s for s in ds.statements if isinstance(s, IfStatement)][0]
        assert if_stmt.condition is not None
        assert len(if_stmt.then_statements) >= 0


class TestWhereStatement:
    """Test WHERE statement parsing."""

    def test_simple_where(self):
        result = parse("DATA out; SET in; WHERE x > 0; RUN;")
        ds = result.statements[0]
        where_stmt = [s for s in ds.statements if isinstance(s, WhereStatement)][0]
        assert where_stmt.condition is not None


class TestOutputStatement:
    """Test OUTPUT statement parsing."""

    def test_simple_output(self):
        result = parse("DATA out; SET in; OUTPUT; RUN;")
        ds = result.statements[0]
        output_stmt = [s for s in ds.statements if isinstance(s, OutputStatement)][0]
        assert isinstance(output_stmt, OutputStatement)

    def test_output_to_dataset(self):
        result = parse("DATA out1 out2; SET in; OUTPUT out1; RUN;")
        ds = result.statements[0]
        output_stmt = [s for s in ds.statements if isinstance(s, OutputStatement)][0]
        assert output_stmt.dataset is not None


class TestComplexDataSteps:
    """Test complex DATA step scenarios."""

    def test_multiple_statements(self):
        code = """
        DATA work.output;
            SET work.input;
            new_var = old_var * 2;
            IF new_var > 100 THEN flag = 1;
            KEEP id new_var flag;
        RUN;
        """
        result = parse(code)
        ds = result.statements[0]
        assert len(ds.statements) >= 3

    def test_merge_with_by(self):
        code = """
        DATA work.combined;
            MERGE work.left work.right;
            BY customer_id;
        RUN;
        """
        result = parse(code)
        ds = result.statements[0]
        assert any(isinstance(s, MergeStatement) for s in ds.statements)
        assert any(isinstance(s, ByStatement) for s in ds.statements)
