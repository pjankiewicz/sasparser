"""Tests for PROC statement parsing."""

import pytest
import sys
sys.path.insert(0, "src")

from sasparser import parse
from sasparser.ast.proc_other import ProcSort, ProcMeans, ProcFreq, ProcPrint


class TestProcSort:
    """Test PROC SORT parsing."""

    def test_simple_proc_sort(self):
        result = parse("PROC SORT DATA=mydata; BY id; RUN;")
        assert len(result.statements) == 1
        assert isinstance(result.statements[0], ProcSort)

    def test_proc_sort_with_out(self):
        result = parse("PROC SORT DATA=input OUT=output; BY id; RUN;")
        ps = result.statements[0]
        assert ps.input_table is not None
        assert ps.output_table is not None

    def test_proc_sort_nodupkey(self):
        result = parse("PROC SORT DATA=mydata NODUPKEY; BY id; RUN;")
        ps = result.statements[0]
        assert ps.nodupkey is True

    def test_proc_sort_multiple_by_fields(self):
        result = parse("PROC SORT DATA=mydata; BY region date; RUN;")
        ps = result.statements[0]
        assert len(ps.by_fields) == 2

    def test_proc_sort_descending(self):
        result = parse("PROC SORT DATA=mydata; BY DESCENDING date; RUN;")
        ps = result.statements[0]
        assert ps.by_fields[0].descending is True


class TestProcMeans:
    """Test PROC MEANS/SUMMARY parsing."""

    def test_simple_proc_means(self):
        result = parse("PROC MEANS DATA=mydata; VAR x y; RUN;")
        assert len(result.statements) == 1
        assert isinstance(result.statements[0], ProcMeans)

    def test_proc_means_var_statement(self):
        result = parse("PROC MEANS DATA=mydata; VAR sales profit; RUN;")
        pm = result.statements[0]
        assert len(pm.var_fields) == 2

    def test_proc_means_class_statement(self):
        result = parse("PROC MEANS DATA=mydata; CLASS region; VAR sales; RUN;")
        pm = result.statements[0]
        assert len(pm.class_fields) == 1

    def test_proc_summary(self):
        result = parse("PROC SUMMARY DATA=mydata; VAR x; RUN;")
        pm = result.statements[0]
        assert pm.is_summary is True


class TestProcFreq:
    """Test PROC FREQ parsing."""

    def test_simple_proc_freq(self):
        result = parse("PROC FREQ DATA=mydata; TABLES gender; RUN;")
        assert len(result.statements) == 1
        assert isinstance(result.statements[0], ProcFreq)

    def test_proc_freq_tables(self):
        result = parse("PROC FREQ DATA=mydata; TABLES gender*region; RUN;")
        pf = result.statements[0]
        assert len(pf.tables) == 1


class TestProcPrint:
    """Test PROC PRINT parsing."""

    def test_simple_proc_print(self):
        result = parse("PROC PRINT DATA=mydata; RUN;")
        assert len(result.statements) == 1
        assert isinstance(result.statements[0], ProcPrint)

    def test_proc_print_with_var(self):
        result = parse("PROC PRINT DATA=mydata; VAR id name; RUN;")
        pp = result.statements[0]
        assert len(pp.var_fields) == 2

    def test_proc_print_with_obs(self):
        result = parse("PROC PRINT DATA=mydata (OBS=10); RUN;")
        pp = result.statements[0]
        assert pp.obs == 10


class TestProcWithQualifiedNames:
    """Test PROCs with qualified table names."""

    def test_proc_sort_qualified(self):
        result = parse("PROC SORT DATA=work.input OUT=work.output; BY id; RUN;")
        ps = result.statements[0]
        assert ps.input_table.library == "work"
        assert ps.input_table.dataset == "input"
        assert ps.output_table.library == "work"
        assert ps.output_table.dataset == "output"

    def test_proc_means_qualified(self):
        result = parse("PROC MEANS DATA=mylib.sales; VAR amount; RUN;")
        pm = result.statements[0]
        assert pm.input_table.library == "mylib"
        assert pm.input_table.dataset == "sales"
