# Personal Finance Tracker

A small personal finance tracker for a single user. Record income and expenses,
search and sort past transactions, and see monthly totals by category — so you
know where your money goes.

It runs entirely offline with **Python's standard library only** (no installs),
and comes in two versions that share one tested core:

- a **text / command-line** app (`cli.py`), and
- a **graphical** app (`gui.py`, Tkinter).

## Features

| ID | Feature |
|------|---------|
| FR1 | Add a transaction (date, kind, category, amount, description); auto id |
| FR2 | View all transactions in a table, newest first |
| FR3 | Search by category, kind and/or month (YYYY-MM) |
| FR4 | Sort by date, amount or category, ascending or descending |
| FR5 | Edit any field of a transaction, chosen by id |
| FR6 | Delete a transaction by id, after confirmation |
| FR7 | Monthly summary: income, expenses, balance, totals per category |
| FR8 | Save transactions to a CSV file |
| FR9 | Load transactions at start-up; skip and count bad rows |
| FR10 | Optional per-category monthly budget with an over-budget warning |

## Requirements

- Python **3.10 or newer**.
- No third-party packages. Only the standard library (`csv`, `datetime`,
  `tkinter`, `unittest`). Tkinter ships with most Python installations.

## How to run

From the project folder:

```bash
# Text version
python cli.py

# Graphical version
python gui.py
```

Both versions load `transactions.csv` from the project folder at start-up (or
start empty if it is missing) and save back to it.

## How to test

```bash
python -m unittest -v
```

There are 30 tests covering every requirement with normal, boundary and invalid
cases. They import only `core.py` and use a temporary file, so they never touch
your real `transactions.csv`.

## Data files

- `transactions.csv` — the data file (six columns: id, date, kind, category,
  amount, description). The copy in this repository is **synthetic sample data**;
  no real personal finances are stored here.
- `budgets.csv` — optional per-category monthly limits (only used by FR10).

## Project structure

```
core.py        Shared logic: Transaction, FinanceTracker, validation, CSV save/load
cli.py         Text front end
gui.py         Tkinter front end
test_core.py   Automated unittest tests for the core
transactions.csv  Sample data (synthetic)
```

All business rules live in `core.py`; the two front ends only collect input and
show results. This keeps the logic in one tested place.

## Use of AI assistance

This project was built with the help of an AI coding assistant (Anthropic's
Claude). The assistant worked under my direction: I set the requirements (the
FRD), reviewed each step, and I understand and can explain every part of the
code. The AI helped implement the code, write the tests, and keep the Git
history and planning notes tidy. All design decisions, the requirements, and the
final review are my own. The sample data is synthetic.

## Author

Abdullah Afzaal Wali — CSC-44102 coursework.
