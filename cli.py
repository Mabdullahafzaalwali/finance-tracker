"""Text (command-line) front end for the Personal Finance Tracker.

Shows a numbered menu, collects one value at a time, calls the shared core
(core.py) and prints the results or the core's error messages. It holds no
business rules of its own, so it can never validate differently from the GUI.

Run with:  python cli.py
"""

import os
import sys

import core


# --- small helpers ------------------------------------------------------------
def _message(error):
    """Return the plain message from a core ValueError or KeyError."""
    return error.args[0] if error.args else str(error)


def _prompt_valid(prompt, validator):
    """Ask until the typed value passes the validator, then return that text."""
    while True:
        text = input(prompt)
        try:
            validator(text)
            return text
        except ValueError as error:
            print(_message(error))


def _prompt_optional(prompt, validator):
    """Like _prompt_valid, but an empty line returns None to mean 'keep as is'."""
    while True:
        text = input(prompt).strip()
        if text == "":
            return None
        try:
            validator(text)
            return text
        except ValueError as error:
            print(_message(error))


def _print_table(transactions):
    """Print transactions as an aligned table (FR2 columns)."""
    print(f"{'ID':>3}  {'Date':10}  {'Kind':7}  {'Category':13}  {'Amount':>11}  Description")
    for t in transactions:
        amount = f"£{t.amount:.2f}"
        print(f"{t.id:>3}  {t.date.strftime(core.DATE_FORMAT):10}  {t.kind:7}  "
              f"{t.category:13}  {amount:>11}  {t.description}")


def _print_menu():
    """Print the main menu (same order as the GUI, for a side-by-side demo)."""
    print()
    print("===== Personal Finance Tracker =====")
    print("1. Add transaction")
    print("2. View all transactions")
    print("3. Search transactions")
    print("4. Sort transactions")
    print("5. Edit a transaction")
    print("6. Delete a transaction")
    print("7. Monthly summary")
    print("8. Set a category budget")
    print("9. Save")
    print("0. Save and exit")


# --- menu actions -------------------------------------------------------------
def _load_at_startup(tracker):
    """Load the data file at start-up and report what happened (FR9)."""
    had_file = os.path.exists(core.DATA_FILE)
    skipped = tracker.load()
    tracker.load_budgets()
    if not had_file:
        print("No saved data found, starting a new file.")
        return
    rows = "row" if skipped == 1 else "rows"
    print(f"Loaded {tracker.count()} records, skipped {skipped} bad {rows}.")


def _add(tracker):
    """Add a transaction, asking again on any invalid field (FR1)."""
    date_text = _prompt_valid("Date (YYYY-MM-DD): ", core.validate_date)
    kind = _prompt_valid("Kind (income/expense): ", core.validate_kind)
    category = _prompt_valid("Category (" + ", ".join(core.CATEGORIES) + "): ",
                             core.validate_category)
    amount_text = _prompt_valid("Amount (£): ", core.validate_amount)
    description = _prompt_valid("Description (optional, max 50): ",
                                core.validate_description)
    transaction = tracker.add(date_text, kind, category, amount_text, description)
    print(f"Added ID {transaction.id}.")


def _view(tracker):
    """Show all transactions, newest first (FR2)."""
    transactions = tracker.get_all()
    if not transactions:
        print("No transactions yet.")
        return
    _print_table(transactions)


def _search(tracker):
    """Search by category, kind and/or month (FR3)."""
    category = input("Category (blank for all): ").strip() or None
    kind = input("Kind income/expense (blank for all): ").strip() or None
    month = input("Month YYYY-MM (blank for all): ").strip() or None
    try:
        results = tracker.search(category=category, kind=kind, month=month)
    except ValueError as error:
        print(_message(error))
        return
    if not results:
        print("No matching transactions.")
        return
    _print_table(results)


def _sort(tracker):
    """Sort the current transactions by a field and direction (FR4)."""
    field = input("Sort by (date/amount/category): ").strip().lower()
    descending = input("Direction (asc/desc): ").strip().lower().startswith("d")
    try:
        results = tracker.sort(tracker.get_all(), field, descending=descending)
    except ValueError as error:
        print(_message(error))
        return
    if not results:
        print("No transactions yet.")
        return
    _print_table(results)


def _edit(tracker):
    """Edit any field of a transaction chosen by id; blank keeps a field (FR5)."""
    id_text = input("ID to edit: ").strip()
    try:
        current = tracker.get(id_text)
    except KeyError as error:
        print(_message(error))
        return
    print("Leave a field blank to keep its current value.")
    changes = {}
    for field, validator, shown in (
        ("date", core.validate_date, current.date.strftime(core.DATE_FORMAT)),
        ("kind", core.validate_kind, current.kind),
        ("category", core.validate_category, current.category),
        ("amount", core.validate_amount, f"{current.amount:.2f}"),
        ("description", core.validate_description, current.description),
    ):
        new_value = _prompt_optional(f"{field} [{shown}]: ", validator)
        if new_value is not None:
            changes[field] = new_value
    if not changes:
        print("No changes made.")
        return
    tracker.edit(id_text, **changes)
    print(f"Updated ID {current.id}.")


def _delete(tracker):
    """Delete a transaction chosen by id, after confirmation (FR6)."""
    id_text = input("ID to delete: ").strip()
    try:
        transaction = tracker.get(id_text)
    except KeyError as error:
        print(_message(error))
        return
    answer = input(f"Delete ID {transaction.id} "
                   f"({transaction.category} £{transaction.amount:.2f})? (y/n): ")
    if answer.strip().lower() in ("y", "yes"):
        tracker.delete(id_text)
        print(f"Deleted ID {transaction.id}.")
    else:
        print("Delete cancelled.")


def _summary(tracker):
    """Show the monthly summary for a chosen month (FR7)."""
    month = _prompt_valid("Month (YYYY-MM): ", core.validate_month)
    summary = tracker.monthly_summary(month)
    print(f"Summary for {month}")
    print(f"  Income:   £{summary['income']:.2f}")
    print(f"  Expenses: £{summary['expenses']:.2f}")
    print(f"  Balance:  £{summary['balance']:.2f}")
    if summary["by_category"]:
        print("  Expenses by category:")
        for category, total in sorted(summary["by_category"].items()):
            print(f"    {category:13} £{total:.2f}")
    else:
        print("  No expenses this month.")
    for category, over in tracker.over_budget(month):
        print(f"  {category} over budget by £{over:.2f}")


def _set_budget(tracker):
    """Set a monthly spending limit for a category (FR10)."""
    category = _prompt_valid("Budget category (" + ", ".join(core.CATEGORIES) + "): ",
                             core.validate_category)
    limit = _prompt_valid("Monthly limit (£): ", core.validate_amount)
    tracker.set_budget(category, limit)
    print(f"Budget set: {category} £{float(limit):.2f} per month.")


def _save(tracker):
    """Save all transactions to the data file (FR8)."""
    try:
        written = tracker.save()
        tracker.save_budgets()
        print(f"Saved {written} records to {core.DATA_FILE}.")
    except OSError as error:
        print(f"Could not save: {error}")


# --- main loop ----------------------------------------------------------------
def main():
    """Run the menu loop until the user chooses to exit."""
    # Never crash on a console whose codepage cannot show a character (e.g. £).
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    tracker = core.FinanceTracker()
    _load_at_startup(tracker)
    actions = {
        "1": _add, "2": _view, "3": _search, "4": _sort,
        "5": _edit, "6": _delete, "7": _summary, "8": _set_budget, "9": _save,
    }
    while True:
        _print_menu()
        try:
            choice = input("Choose an option (0-9): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if choice == "0":
            _save(tracker)
            print("Goodbye.")
            break
        action = actions.get(choice)
        if action is None:
            print("Invalid choice. Enter a number from 0 to 9.")
        else:
            action(tracker)


if __name__ == "__main__":
    main()
