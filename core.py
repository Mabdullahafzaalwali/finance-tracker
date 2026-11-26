"""Core logic for the Personal Finance Tracker.

This module holds every class, data structure, algorithm, calculation and the
CSV save/load code. It is the single place where data is validated.

Layer rule (FRD section 6.1): the core contains no print(), no input() and no
tkinter. The front ends (cli.py, gui.py) and the tests call the core; the core
never calls them. Bad data raises ValueError and an unknown id raises KeyError,
both with a clear message that the front ends show to the user.
"""

import csv
from datetime import date, datetime

# --- Named constants (no magic numbers) ---------------------------------------
CATEGORIES = ("Food", "Rent", "Transport", "Bills", "Shopping",
              "Entertainment", "Salary", "Gift", "Other")
KINDS = ("income", "expense")
MAX_AMOUNT = 1_000_000.00
MAX_DESCRIPTION_LENGTH = 50
EARLIEST_DATE = date(2000, 1, 1)
DATE_FORMAT = "%Y-%m-%d"
MONTH_FORMAT = "%Y-%m"
DATA_FILE = "transactions.csv"
CSV_HEADER = ("id", "date", "kind", "category", "amount", "description")


# --- Field validators ---------------------------------------------------------
# Each validator takes the raw text the user typed, returns a clean value, and
# raises ValueError with a clear message if the value breaks a section 3 rule.
# They are shared by Transaction.from_row and FinanceTracker so the CLI, the GUI
# and the saved file can never validate differently.

def validate_date(date_text):
    """Return date_text as a datetime.date between 2000-01-01 and today."""
    text = str(date_text).strip()
    parts = text.split("-")
    if (len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2
            or len(parts[2]) != 2 or not all(part.isdigit() for part in parts)):
        raise ValueError("Date must be in the format YYYY-MM-DD.")
    try:
        value = datetime.strptime(text, DATE_FORMAT).date()
    except ValueError:
        raise ValueError("That date does not exist.")
    if value < EARLIEST_DATE or value > date.today():
        raise ValueError("Date must be between 2000-01-01 and today.")
    return value


def validate_kind(kind_text):
    """Return the kind in its standard lower-case spelling, or raise ValueError."""
    text = str(kind_text).strip().lower()
    if text not in KINDS:
        raise ValueError("Kind must be income or expense.")
    return text


def validate_category(category_text):
    """Return the category in its standard spelling, or raise ValueError."""
    text = str(category_text).strip()
    for category in CATEGORIES:
        if category.lower() == text.lower():
            return category
    raise ValueError("Category must be one of: " + ", ".join(CATEGORIES) + ".")


def validate_amount(amount_text):
    """Return amount_text as a float > 0, <= 1,000,000.00 and <= 2 dp."""
    text = str(amount_text).strip()
    try:
        value = float(text)
    except ValueError:
        raise ValueError("Amount must be a number, for example 12.50.")
    if value <= 0:
        raise ValueError("Amount must be greater than 0.")
    if value > MAX_AMOUNT:
        raise ValueError("Amount must be at most 1,000,000.00.")
    if "." in text and len(text.split(".")[1]) > 2:
        raise ValueError("Amount can have at most 2 decimal places.")
    return round(value, 2)


def validate_description(description_text):
    """Return the trimmed description (may be empty), or raise ValueError."""
    text = str(description_text).strip()
    if len(text) > MAX_DESCRIPTION_LENGTH:
        raise ValueError("Description can be at most 50 characters.")
    return text


def validate_month(month_text):
    """Return month_text if it is a valid YYYY-MM string, or raise ValueError."""
    text = str(month_text).strip()
    parts = text.split("-")
    if (len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 2
            or not all(part.isdigit() for part in parts)
            or not 1 <= int(parts[1]) <= 12):
        raise ValueError("Month must be in the format YYYY-MM.")
    return text


# --- Transaction --------------------------------------------------------------
class Transaction:
    """One income or expense record with six fields (see FRD section 3)."""

    def __init__(self, id, date, kind, category, amount, description):
        """Store already-validated field values for one transaction."""
        self.id = id
        self.date = date
        self.kind = kind
        self.category = category
        self.amount = amount
        self.description = description

    def to_row(self):
        """Return this transaction as a list of strings for one CSV row."""
        return [str(self.id), self.date.strftime(DATE_FORMAT), self.kind,
                self.category, f"{self.amount:.2f}", self.description]

    @classmethod
    def from_row(cls, row):
        """Build a Transaction from a CSV row, raising ValueError if it is bad."""
        if len(row) != 6:
            raise ValueError("A row must have exactly 6 columns.")
        id_text, date_text, kind_text, category_text, amount_text, description = row
        try:
            id = int(id_text)
        except ValueError:
            raise ValueError("ID must be a whole number.")
        return cls(
            id,
            validate_date(date_text),
            validate_kind(kind_text),
            validate_category(category_text),
            validate_amount(amount_text),
            validate_description(description),
        )


# --- FinanceTracker -----------------------------------------------------------
class FinanceTracker:
    """Owns every transaction and all operations on them (see FRD section 6.4).

    Transactions are stored in a dictionary keyed by id, so find, edit and delete
    by id are O(1) on average. Views are built as a fresh list each time, so the
    stored data has a single source of truth.
    """

    def __init__(self):
        """Start with no transactions."""
        self._transactions = {}

    def _next_id(self):
        """Return the next free id: highest existing id + 1, or 1 if empty."""
        return max(self._transactions) + 1 if self._transactions else 1

    def _require(self, tx_id):
        """Return the transaction with tx_id, or raise KeyError with a message."""
        try:
            key = int(tx_id)
        except (ValueError, TypeError):
            raise KeyError(f"No transaction with ID {tx_id}.")
        if key not in self._transactions:
            raise KeyError(f"No transaction with ID {key}.")
        return self._transactions[key]

    def add(self, date_text, kind, category, amount_text, description=""):
        """Validate the inputs, store a new transaction and return it (FR1)."""
        transaction = Transaction(
            self._next_id(),
            validate_date(date_text),
            validate_kind(kind),
            validate_category(category),
            validate_amount(amount_text),
            validate_description(description),
        )
        self._transactions[transaction.id] = transaction
        return transaction

    def get_all(self):
        """Return all transactions as a list, newest date first (FR2)."""
        return sorted(self._transactions.values(),
                      key=lambda t: (t.date, t.id), reverse=True)

    def count(self):
        """Return how many transactions are stored."""
        return len(self._transactions)
