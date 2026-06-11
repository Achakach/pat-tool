"""Tests for column copier."""
import pytest
from openpyxl import Workbook
from src.columns import (
    col_letter_to_index, build_pw_column, build_ip_column,
    copy_column, clean_sheet_name, find_matching_sheet
)


class TestColLetter:
    @pytest.mark.parametrize("letter,expected", [("A", 1), ("Z", 26), ("AA", 27)])
    def test_conversion(self, letter, expected):
        assert col_letter_to_index(letter) == expected


class TestPwColumn:
    def test_fills_column(self):
        wb = Workbook()
        ws = wb.active
        ws["A1"] = "header"
        ws["A2"] = "data"
        ws["A3"] = "data2"
        build_pw_column(ws, "xxxck01", "B", 2)
        assert ws["B2"].value == "xxxck01"
        assert ws["B3"].value == "xxxck01"
        wb.close()


class TestIpColumn:
    def test_lookup(self):
        wb = Workbook()
        ws = wb.active
        ws["D1"] = "header"
        ws["D2"] = "CR10SDA"
        ws["D3"] = "CR11SDA"
        # Create log sheet
        log = wb.create_sheet("Get Log")
        log["A1"] = "CR10SDA_10.10.10.10"
        log["B1"] = "CR11SDA_10.10.11.11"
        build_ip_column(ws, "D", log, "E", 2)
        assert ws["E2"].value == "10.10.10.10"
        assert ws["E3"].value == "10.10.11.11"
        wb.close()


class TestCopyColumn:
    def test_copy(self):
        wb = Workbook()
        ws = wb.active
        ws["A2"] = "val1"
        ws["A3"] = "val2"
        copy_column(ws, "A", "B", 2)
        assert ws["B2"].value == "val1"
        assert ws["B3"].value == "val2"
        wb.close()


class TestSheetMatching:
    def test_clean(self):
        assert clean_sheet_name("2.3. IP & Port Assignment(P.4)") == "ip & port assignment"
        assert clean_sheet_name("IP & Port Assignment") == "ip & port assignment"

    def test_find(self):
        wb = Workbook()
        wb.active.title = "2.3. IP & Port Assignment(P.4)"
        assert find_matching_sheet(wb, "IP & Port Assignment") == "2.3. IP & Port Assignment(P.4)"
        wb.close()
