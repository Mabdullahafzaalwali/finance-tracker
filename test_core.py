"""Automated tests for the Personal Finance Tracker core (core.py).

Uses unittest and imports only core.py, so every test runs without a screen.
Each Must requirement has at least one normal, one boundary and one invalid test
(test plan T1-T27 in the FRD). File tests use a temporary file, never the real
transactions.csv.

Run with:  python -m unittest -v
"""

import os
import tempfile
import time
import unittest
from datetime import date, timedelta

import core

# A date that is safely in the past for any run after late November 2026, used
# for "normal" cases. Boundary cases compute today / tomorrow from date.today().
PAST_DATE = "2026-11-20"
TODAY = date.today().strftime(core.DATE_FORMAT)
TOMORROW = (date.today() + timedelta(days=1)).strftime(core.DATE_FORMAT)


class TestAdd(unittest.TestCase):
    """FR1 - add a transaction with validation."""

    def test_T01_add_normal(self):
        """T1 (normal): a valid entry is stored with id 1 and count 1."""
        tracker = core.FinanceTracker()
        tx = tracker.add(PAST_DATE, "expense", "Food", "12.50", "Lunch")
        self.assertEqual(tx.id, 1)
        self.assertEqual(tracker.count(), 1)
        self.assertEqual(tx.amount, 12.50)

    def test_T02_add_boundary_amounts(self):
        """T2 (boundary): amounts 0.01 and 1,000,000.00 are both accepted."""
        tracker = core.FinanceTracker()
        tracker.add(PAST_DATE, "expense", "Food", "0.01", "min")
        tracker.add(PAST_DATE, "income", "Salary", "1000000.00", "max")
        self.assertEqual(tracker.count(), 2)

    def test_T03_add_boundary_dates(self):
        """T3 (boundary): the earliest date and today are both accepted."""
        tracker = core.FinanceTracker()
        tracker.add("2000-01-01", "expense", "Food", "5.00", "earliest")
        tracker.add(TODAY, "expense", "Food", "5.00", "today")
        self.assertEqual(tracker.count(), 2)

    def test_T04_add_invalid_amounts(self):
        """T4 (invalid): bad amounts are rejected and nothing is added."""
        tracker = core.FinanceTracker()
        for bad in ("abc", "0", "-5", "10.999"):
            with self.assertRaises(ValueError):
                tracker.add(PAST_DATE, "expense", "Food", bad, "x")
        self.assertEqual(tracker.count(), 0)

    def test_T05_add_invalid_dates(self):
        """T5 (invalid): wrong format, impossible and future dates are rejected."""
        tracker = core.FinanceTracker()
        for bad in ("24/11/2026", "2026-02-30", TOMORROW):
            with self.assertRaises(ValueError):
                tracker.add(bad, "expense", "Food", "5.00", "x")

    def test_T06_add_invalid_category_and_description(self):
        """T6 (invalid): unknown category and over-long description are rejected."""
        tracker = core.FinanceTracker()
        with self.assertRaises(ValueError):
            tracker.add(PAST_DATE, "expense", "Pets", "5.00", "x")
        with self.assertRaises(ValueError):
            tracker.add(PAST_DATE, "expense", "Food", "5.00", "x" * 51)


class TestView(unittest.TestCase):
    """FR2 - view all transactions."""

    def test_T07_view_newest_first(self):
        """T7 (normal): three records are returned newest date first."""
        tracker = core.FinanceTracker()
        tracker.add("2026-11-01", "expense", "Food", "1.00", "a")
        tracker.add("2026-11-20", "expense", "Food", "2.00", "b")
        tracker.add("2026-11-10", "expense", "Food", "3.00", "c")
        dates = [t.date.strftime(core.DATE_FORMAT) for t in tracker.get_all()]
        self.assertEqual(dates, ["2026-11-20", "2026-11-10", "2026-11-01"])

    def test_T08_view_empty(self):
        """T8 (boundary): an empty tracker returns an empty list."""
        self.assertEqual(core.FinanceTracker().get_all(), [])


class TestSearch(unittest.TestCase):
    """FR3 - search by category, kind and/or month."""

    def _tracker(self):
        tracker = core.FinanceTracker()
        tracker.add("2026-11-05", "expense", "Food", "10.00", "nov food")
        tracker.add("2026-10-05", "expense", "Food", "20.00", "oct food")
        tracker.add("2026-11-06", "expense", "Transport", "3.00", "nov bus")
        return tracker

    def test_T09_search_category_and_month(self):
        """T9 (normal): Food in 2026-11 returns only the November Food record."""
        results = self._tracker().search(category="Food", month="2026-11")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].category, "Food")
        self.assertEqual(results[0].date.strftime(core.MONTH_FORMAT), "2026-11")

    def test_T10_search_boundaries(self):
        """T10 (boundary): no filters returns all; an impossible filter returns []."""
        tracker = self._tracker()
        self.assertEqual(tracker.search(), tracker.get_all())
        self.assertEqual(tracker.search(category="Rent"), [])

    def test_T11_search_invalid_month(self):
        """T11 (invalid): a badly formatted month raises ValueError."""
        with self.assertRaises(ValueError):
            self._tracker().search(month="Nov 2026")


class TestSort(unittest.TestCase):
    """FR4 - sort the shown transactions."""

    def test_T12_sort_amount_descending(self):
        """T12 (normal): sorting by amount descending is non-increasing."""
        tracker = core.FinanceTracker()
        for amount in ("5.00", "20.00", "1.50"):
            tracker.add(PAST_DATE, "expense", "Food", amount, "x")
        amounts = [t.amount for t in tracker.sort(tracker.get_all(), "amount", descending=True)]
        self.assertEqual(amounts, sorted(amounts, reverse=True))

    def test_T13_sort_boundaries(self):
        """T13 (boundary): empty, single-item and equal-value lists are handled."""
        tracker = core.FinanceTracker()
        self.assertEqual(tracker.sort([], "amount"), [])
        one = tracker.add(PAST_DATE, "expense", "Food", "5.00", "one")
        self.assertEqual(tracker.sort([one], "amount"), [one])
        two = tracker.add(PAST_DATE, "expense", "Food", "5.00", "two")
        self.assertEqual(len(tracker.sort([one, two], "amount")), 2)

    def test_T14_sort_invalid_field(self):
        """T14 (invalid): an unknown sort field raises ValueError."""
        with self.assertRaises(ValueError):
            core.FinanceTracker().sort([], "colour")


class TestEdit(unittest.TestCase):
    """FR5 - edit a transaction chosen by id."""

    def test_T15_edit_normal(self):
        """T15 (normal): editing one record's amount leaves the others unchanged."""
        tracker = core.FinanceTracker()
        tracker.add(PAST_DATE, "expense", "Food", "10.00", "a")       # id 1
        tracker.add(PAST_DATE, "expense", "Transport", "3.00", "b")   # id 2
        tracker.edit(1, amount="20.00")
        self.assertEqual(tracker._require(1).amount, 20.00)
        self.assertEqual(tracker._require(2).amount, 3.00)

    def test_T16_edit_invalid(self):
        """T16 (invalid): unknown id raises KeyError; a bad value keeps the old one."""
        tracker = core.FinanceTracker()
        tracker.add(PAST_DATE, "expense", "Food", "10.00", "a")       # id 1
        with self.assertRaises(KeyError):
            tracker.edit(999, amount="5.00")
        with self.assertRaises(ValueError):
            tracker.edit(1, amount="-1")
        self.assertEqual(tracker._require(1).amount, 10.00)


class TestDelete(unittest.TestCase):
    """FR6 - delete a transaction chosen by id."""

    def test_T17_delete_normal(self):
        """T17 (normal): deleting a record drops the count and removes the id."""
        tracker = core.FinanceTracker()
        tracker.add(PAST_DATE, "expense", "Food", "10.00", "a")       # id 1
        tracker.add(PAST_DATE, "expense", "Transport", "3.00", "b")   # id 2
        tracker.delete(2)
        self.assertEqual(tracker.count(), 1)
        with self.assertRaises(KeyError):
            tracker._require(2)

    def test_T18_delete_invalid(self):
        """T18 (invalid): deleting an unknown id raises KeyError and keeps the count."""
        tracker = core.FinanceTracker()
        tracker.add(PAST_DATE, "expense", "Food", "10.00", "a")
        with self.assertRaises(KeyError):
            tracker.delete(999)
        self.assertEqual(tracker.count(), 1)


class TestSummary(unittest.TestCase):
    """FR7 - monthly summary of income, expenses, balance and categories."""

    def test_T19_summary_normal(self):
        """T19 (normal): totals and per-category expense totals are correct."""
        tracker = core.FinanceTracker()
        tracker.add("2026-11-01", "income", "Salary", "1000.00", "pay")
        tracker.add("2026-11-05", "expense", "Food", "250.00", "food")
        tracker.add("2026-11-06", "expense", "Transport", "50.00", "bus")
        summary = tracker.monthly_summary("2026-11")
        self.assertEqual(summary["income"], 1000.00)
        self.assertEqual(summary["expenses"], 300.00)
        self.assertEqual(summary["balance"], 700.00)
        self.assertEqual(summary["by_category"], {"Food": 250.00, "Transport": 50.00})

    def test_T20_summary_empty_month(self):
        """T20 (boundary): a month with no records totals 0.00 across the board."""
        summary = core.FinanceTracker().monthly_summary("2020-01")
        self.assertEqual(summary,
                         {"income": 0.0, "expenses": 0.0, "balance": 0.0, "by_category": {}})

    def test_T21_summary_month_boundary(self):
        """T21 (boundary): a record one day into the next month is excluded."""
        tracker = core.FinanceTracker()
        tracker.add("2026-10-31", "expense", "Food", "10.00", "in month")
        tracker.add("2026-11-01", "expense", "Food", "99.00", "next month")
        summary = tracker.monthly_summary("2026-10")
        self.assertEqual(summary["expenses"], 10.00)
        self.assertEqual(summary["by_category"], {"Food": 10.00})


if __name__ == "__main__":
    unittest.main()
