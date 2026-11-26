"""Tkinter (graphical) front end for the Personal Finance Tracker.

One window with an entry form, a filter bar, a table of transactions and action
buttons. It offers the same features as the text version and calls the shared
core (core.py) for all logic, so the two front ends can never behave differently.
Error messages come straight from the core and are shown in a message box.

Run with:  python gui.py
"""

import os
from datetime import date
import tkinter as tk
from tkinter import messagebox, ttk

import core

# The table columns, in the FR2 order. Only date, amount and category can be
# sorted, because those are the three fields FR4 defines.
COLUMNS = ("id", "date", "kind", "category", "amount", "description")
HEADINGS = {"id": "ID", "date": "Date", "kind": "Kind", "category": "Category",
            "amount": "Amount", "description": "Description"}
SORTABLE = ("date", "amount", "category")


class FinanceApp:
    """Builds the window and connects each widget to a core operation."""

    def __init__(self, root):
        """Build every part of the window and load the saved data."""
        self.root = root
        self.tracker = core.FinanceTracker()
        self.editing_id = None       # None means the form is in "add" mode
        self.shown = []              # the transactions currently in the table
        self.sort_field = None
        self.sort_descending = False

        root.title("Personal Finance Tracker")
        self._build_form()
        self._build_filter()
        self._build_table()
        self._build_actions()
        self._build_status()
        root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._load_at_startup()

    # --- building the widgets -------------------------------------------------
    def _build_form(self):
        """Build the add / edit entry form."""
        frame = ttk.LabelFrame(self.root, text="Add / edit transaction")
        frame.grid(row=0, column=0, sticky="ew", padx=8, pady=4)

        self.date_var = tk.StringVar(value=date.today().strftime(core.DATE_FORMAT))
        self.kind_var = tk.StringVar(value=core.KINDS[1])
        self.category_var = tk.StringVar(value=core.CATEGORIES[0])
        self.amount_var = tk.StringVar()
        self.description_var = tk.StringVar()

        ttk.Label(frame, text="Date (YYYY-MM-DD)").grid(row=0, column=0, padx=4, pady=2, sticky="w")
        ttk.Entry(frame, textvariable=self.date_var, width=14).grid(row=0, column=1, padx=4, pady=2)
        ttk.Label(frame, text="Kind").grid(row=0, column=2, padx=4, pady=2, sticky="w")
        ttk.Combobox(frame, textvariable=self.kind_var, values=core.KINDS,
                     state="readonly", width=10).grid(row=0, column=3, padx=4, pady=2)
        ttk.Label(frame, text="Category").grid(row=0, column=4, padx=4, pady=2, sticky="w")
        ttk.Combobox(frame, textvariable=self.category_var, values=core.CATEGORIES,
                     state="readonly", width=13).grid(row=0, column=5, padx=4, pady=2)

        ttk.Label(frame, text="Amount (£)").grid(row=1, column=0, padx=4, pady=2, sticky="w")
        ttk.Entry(frame, textvariable=self.amount_var, width=14).grid(row=1, column=1, padx=4, pady=2)
        ttk.Label(frame, text="Description").grid(row=1, column=2, padx=4, pady=2, sticky="w")
        ttk.Entry(frame, textvariable=self.description_var, width=40).grid(
            row=1, column=3, columnspan=3, padx=4, pady=2, sticky="w")

        ttk.Button(frame, text="Add", command=self._add).grid(row=0, column=6, padx=4, pady=2)
        ttk.Button(frame, text="Save changes", command=self._save_changes).grid(
            row=1, column=6, padx=4, pady=2)

    def _build_filter(self):
        """Build the search / filter bar."""
        frame = ttk.LabelFrame(self.root, text="Search")
        frame.grid(row=1, column=0, sticky="ew", padx=8, pady=4)

        self.filter_category = tk.StringVar()
        self.filter_kind = tk.StringVar()
        self.filter_month = tk.StringVar()

        ttk.Label(frame, text="Category").grid(row=0, column=0, padx=4, pady=4, sticky="w")
        ttk.Combobox(frame, textvariable=self.filter_category, values=("",) + core.CATEGORIES,
                     state="readonly", width=13).grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(frame, text="Kind").grid(row=0, column=2, padx=4, pady=4, sticky="w")
        ttk.Combobox(frame, textvariable=self.filter_kind, values=("",) + core.KINDS,
                     state="readonly", width=10).grid(row=0, column=3, padx=4, pady=4)
        ttk.Label(frame, text="Month (YYYY-MM)").grid(row=0, column=4, padx=4, pady=4, sticky="w")
        ttk.Entry(frame, textvariable=self.filter_month, width=10).grid(row=0, column=5, padx=4, pady=4)
        ttk.Button(frame, text="Search", command=self._search).grid(row=0, column=6, padx=4, pady=4)
        ttk.Button(frame, text="Clear", command=self._clear_filter).grid(row=0, column=7, padx=4, pady=4)

    def _build_table(self):
        """Build the transactions table (FR2 columns, sortable headings)."""
        frame = ttk.Frame(self.root)
        frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=4)
        self.root.rowconfigure(2, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(frame, columns=COLUMNS, show="headings", height=12)
        widths = {"id": 40, "date": 90, "kind": 70, "category": 110, "amount": 90, "description": 220}
        for column in COLUMNS:
            anchor = "e" if column == "amount" else "w"
            if column in SORTABLE:
                self.tree.heading(column, text=HEADINGS[column],
                                  command=lambda c=column: self._sort_by(c))
            else:
                self.tree.heading(column, text=HEADINGS[column])
            self.tree.column(column, width=widths[column], anchor=anchor)
        self.tree.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")

    def _build_actions(self):
        """Build the row of action buttons."""
        frame = ttk.Frame(self.root)
        frame.grid(row=3, column=0, sticky="ew", padx=8, pady=4)
        ttk.Button(frame, text="Edit selected", command=self._edit_selected).grid(row=0, column=0, padx=4)
        ttk.Button(frame, text="Delete selected", command=self._delete_selected).grid(row=0, column=1, padx=4)
        ttk.Button(frame, text="Monthly summary", command=self._show_summary).grid(row=0, column=2, padx=4)
        ttk.Button(frame, text="Set budget", command=self._set_budget).grid(row=0, column=3, padx=4)
        ttk.Button(frame, text="Save", command=self._save).grid(row=0, column=4, padx=4)

    def _build_status(self):
        """Build the status line at the bottom of the window."""
        self.status_var = tk.StringVar()
        ttk.Label(self.root, textvariable=self.status_var, relief="sunken",
                  anchor="w").grid(row=4, column=0, sticky="ew", padx=8, pady=(0, 6))

    # --- helpers --------------------------------------------------------------
    def _status(self, text):
        """Show a short message on the status line."""
        self.status_var.set(text)

    def _error(self, error):
        """Show a core error's plain message in a message box."""
        messagebox.showerror("Error", error.args[0] if error.args else str(error))

    def _show(self, transactions):
        """Replace the table contents with the given transactions."""
        self.shown = list(transactions)
        self.tree.delete(*self.tree.get_children())
        for t in self.shown:
            self.tree.insert("", "end", iid=str(t.id), values=(
                t.id, t.date.strftime(core.DATE_FORMAT), t.kind, t.category,
                f"£{t.amount:.2f}", t.description))

    def _selected_id(self):
        """Return the id of the selected row, or None if nothing is selected."""
        selection = self.tree.selection()
        return int(selection[0]) if selection else None

    def _clear_form(self):
        """Reset the entry form back to 'add' mode."""
        self.editing_id = None
        self.date_var.set(date.today().strftime(core.DATE_FORMAT))
        self.kind_var.set(core.KINDS[1])
        self.category_var.set(core.CATEGORIES[0])
        self.amount_var.set("")
        self.description_var.set("")

    # --- actions --------------------------------------------------------------
    def _load_at_startup(self):
        """Load the data file and report the result on the status line (FR9)."""
        had_file = os.path.exists(core.DATA_FILE)
        skipped = self.tracker.load()
        self.tracker.load_budgets()
        self._show(self.tracker.get_all())
        if not had_file:
            self._status("No saved data found, starting a new file.")
        else:
            rows = "row" if skipped == 1 else "rows"
            self._status(f"Loaded {self.tracker.count()} records, skipped {skipped} bad {rows}.")

    def _add(self):
        """Add a new transaction from the form (FR1)."""
        try:
            transaction = self.tracker.add(
                self.date_var.get(), self.kind_var.get(), self.category_var.get(),
                self.amount_var.get(), self.description_var.get())
        except ValueError as error:
            self._error(error)
            return
        self._clear_form()
        self._show(self.tracker.get_all())
        self._status(f"Added ID {transaction.id}.")

    def _save_changes(self):
        """Apply edits from the form to the record being edited (FR5)."""
        if self.editing_id is None:
            messagebox.showinfo("Edit", "Select a row and click 'Edit selected' first.")
            return
        try:
            self.tracker.edit(
                self.editing_id, date=self.date_var.get(), kind=self.kind_var.get(),
                category=self.category_var.get(), amount=self.amount_var.get(),
                description=self.description_var.get())
        except (ValueError, KeyError) as error:
            self._error(error)
            return
        edited_id = self.editing_id
        self._clear_form()
        self._show(self.tracker.get_all())
        self._status(f"Updated ID {edited_id}.")

    def _search(self):
        """Search by category, kind and/or month (FR3)."""
        try:
            results = self.tracker.search(
                category=self.filter_category.get() or None,
                kind=self.filter_kind.get() or None,
                month=self.filter_month.get().strip() or None)
        except ValueError as error:
            self._error(error)
            return
        self.sort_field = None
        self._show(results)
        self._status("No matching transactions." if not results
                     else f"Found {len(results)} matching transactions.")

    def _clear_filter(self):
        """Clear the filters and show every transaction again."""
        self.filter_category.set("")
        self.filter_kind.set("")
        self.filter_month.set("")
        self.sort_field = None
        self._show(self.tracker.get_all())
        self._status("Showing all transactions.")

    def _sort_by(self, field):
        """Sort the shown transactions by a column, reversing on a repeat click (FR4)."""
        self.sort_descending = not self.sort_descending if self.sort_field == field else False
        self.sort_field = field
        try:
            self._show(self.tracker.sort(self.shown, field, descending=self.sort_descending))
        except ValueError as error:
            self._error(error)
            return
        arrow = " ▼" if self.sort_descending else " ▲"
        for column in SORTABLE:
            self.tree.heading(column, text=HEADINGS[column] + (arrow if column == field else ""))

    def _edit_selected(self):
        """Load the selected row into the form for editing (FR5)."""
        tx_id = self._selected_id()
        if tx_id is None:
            messagebox.showinfo("Edit", "Select a row first.")
            return
        transaction = self.tracker.get(tx_id)
        self.editing_id = transaction.id
        self.date_var.set(transaction.date.strftime(core.DATE_FORMAT))
        self.kind_var.set(transaction.kind)
        self.category_var.set(transaction.category)
        self.amount_var.set(f"{transaction.amount:.2f}")
        self.description_var.set(transaction.description)
        self._status(f"Editing ID {transaction.id}; change fields and click 'Save changes'.")

    def _delete_selected(self):
        """Delete the selected row after a yes/no confirmation (FR6)."""
        tx_id = self._selected_id()
        if tx_id is None:
            messagebox.showinfo("Delete", "Select a row first.")
            return
        transaction = self.tracker.get(tx_id)
        if not messagebox.askyesno(
                "Delete", f"Delete ID {transaction.id} "
                          f"({transaction.category} £{transaction.amount:.2f})?"):
            self._status("Delete cancelled.")
            return
        self.tracker.delete(tx_id)
        self._show(self.tracker.get_all())
        self._status(f"Deleted ID {transaction.id}.")

    def _show_summary(self):
        """Open a small window with the monthly summary (FR7)."""
        window = tk.Toplevel(self.root)
        window.title("Monthly summary")
        month_var = tk.StringVar(value=date.today().strftime(core.MONTH_FORMAT))
        ttk.Label(window, text="Month (YYYY-MM)").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        ttk.Entry(window, textvariable=month_var, width=10).grid(row=0, column=1, padx=6, pady=6)
        output = tk.Text(window, width=40, height=14, state="disabled")
        output.grid(row=2, column=0, columnspan=2, padx=6, pady=6)

        def render():
            """Compute and display the summary for the chosen month."""
            try:
                summary = self.tracker.monthly_summary(month_var.get().strip())
            except ValueError as error:
                self._error(error)
                return
            lines = [f"Summary for {month_var.get().strip()}", "",
                     f"Income:   £{summary['income']:.2f}",
                     f"Expenses: £{summary['expenses']:.2f}",
                     f"Balance:  £{summary['balance']:.2f}", ""]
            if summary["by_category"]:
                lines.append("Expenses by category:")
                for category, total in sorted(summary["by_category"].items()):
                    lines.append(f"  {category:13} £{total:.2f}")
            else:
                lines.append("No expenses this month.")
            warnings = self.tracker.over_budget(month_var.get().strip())
            if warnings:
                lines.append("")
                for category, over in warnings:
                    lines.append(f"{category} over budget by £{over:.2f}")
            output.configure(state="normal")
            output.delete("1.0", "end")
            output.insert("1.0", "\n".join(lines))
            output.configure(state="disabled")

        ttk.Button(window, text="Show", command=render).grid(row=1, column=0, columnspan=2, pady=2)
        render()

    def _set_budget(self):
        """Open a small window to set a monthly budget for a category (FR10)."""
        window = tk.Toplevel(self.root)
        window.title("Set budget")
        category_var = tk.StringVar(value=core.CATEGORIES[0])
        limit_var = tk.StringVar()
        ttk.Label(window, text="Category").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        ttk.Combobox(window, textvariable=category_var, values=core.CATEGORIES,
                     state="readonly", width=13).grid(row=0, column=1, padx=6, pady=6)
        ttk.Label(window, text="Monthly limit (£)").grid(row=1, column=0, padx=6, pady=6, sticky="w")
        ttk.Entry(window, textvariable=limit_var, width=13).grid(row=1, column=1, padx=6, pady=6)

        def apply_budget():
            """Validate and store the budget, then close the window."""
            try:
                self.tracker.set_budget(category_var.get(), limit_var.get())
            except ValueError as error:
                self._error(error)
                return
            self._status(f"Budget set: {category_var.get()} £{float(limit_var.get()):.2f} per month.")
            window.destroy()

        ttk.Button(window, text="Set", command=apply_budget).grid(
            row=2, column=0, columnspan=2, pady=6)

    def _save(self):
        """Save all transactions and budgets to their data files (FR8, FR10)."""
        try:
            written = self.tracker.save()
            self.tracker.save_budgets()
        except OSError as error:
            messagebox.showerror("Error", f"Could not save: {error}")
            return
        self._status(f"Saved {written} records to {core.DATA_FILE}.")

    def _on_close(self):
        """Ask whether to save before the window closes."""
        answer = messagebox.askyesnocancel("Quit", "Save before closing?")
        if answer is None:
            return
        if answer:
            self._save()
        self.root.destroy()


def main():
    """Create the window and start the Tkinter event loop."""
    root = tk.Tk()
    FinanceApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
