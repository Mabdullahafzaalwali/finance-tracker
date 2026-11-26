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
