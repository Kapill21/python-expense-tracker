"""
expense_tracker.py
Single-file CLI app: Personal Expense Tracker (JSON persistence)

What it does:
- Add expenses with amount, category, note, date
- List expenses (filter by category and/or date range)
- Summarize totals (overall + by category)
- Delete an expense by its ID
- Saves data to expenses.json (standard library only)
"""

from __future__ import annotations

import json
import os
from datetime import datetime, date
from typing import Any, Dict, List, Optional

DATA_FILE = "expenses.json"
DATE_FMT = "%Y-%m-%d"


def load_expenses(filepath: str) -> List[Dict[str, Any]]:
    """Load expenses from a JSON file. If missing/invalid, return an empty list."""
    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, list):
            return []
        return data
    except (json.JSONDecodeError, OSError):
        
        return []


def save_expenses(filepath: str, expenses: List[Dict[str, Any]]) -> None:
    """Save expenses to a JSON file safely (pretty-printed)."""
    try:
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(expenses, file, indent=2)
    except OSError:
        print("Error: Could not save data. Check file permissions or disk space.")


def parse_date(date_str: str) -> Optional[date]:
    """Parse YYYY-MM-DD into a date object. Return None if invalid."""
    try:
        return datetime.strptime(date_str.strip(), DATE_FMT).date()
    except ValueError:
        return None


def prompt_nonempty(prompt: str) -> str:
    """Prompt until the user enters a non-empty string."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Please enter a value (cannot be blank).")


def prompt_float(prompt: str) -> float:
    """Prompt until the user enters a valid positive float."""
    while True:
        raw = input(prompt).strip()
        try:
            value = float(raw)
            if value <= 0:
                print("Amount must be greater than 0.")
                continue
            return value
        except ValueError:
            print("Please enter a valid number (example: 12.50).")


def prompt_date(prompt: str, allow_blank: bool = False) -> Optional[date]:
    """Prompt for YYYY-MM-DD; optionally allow blank to mean None."""
    while True:
        raw = input(prompt).strip()
        if allow_blank and raw == "":
            return None

        parsed = parse_date(raw)
        if parsed is not None:
            return parsed

        print("Invalid date. Use YYYY-MM-DD (example: 2026-01-08).")


def next_id(expenses: List[Dict[str, Any]]) -> int:
    """Return the next integer ID based on current expenses."""
    if not expenses:
        return 1
    existing_ids = [e.get("id", 0) for e in expenses if isinstance(e.get("id"), int)]
    return (max(existing_ids) if existing_ids else 0) + 1


def add_expense(expenses: List[Dict[str, Any]]) -> None:
    """Collect input, validate it, append a new expense, and save."""
    amount = prompt_float("Amount (e.g., 12.50): ")
    category = prompt_nonempty("Category (e.g., food, gas, rent): ").lower()
    note = input("Note (optional): ").strip()
    when = prompt_date("Date (YYYY-MM-DD) [blank = today]: ", allow_blank=True)
    if when is None:
        when = date.today()

    new_item = {
        "id": next_id(expenses),
        "amount": round(amount, 2),
        "category": category,
        "note": note,
        "date": when.strftime(DATE_FMT),
    }

    expenses.append(new_item)
    save_expenses(DATA_FILE, expenses)
    print(f"Added expense #{new_item['id']} ✅")


def matches_filters(
    item: Dict[str, Any],
    category: Optional[str],
    start: Optional[date],
    end: Optional[date],
) -> bool:
    """Return True if an expense matches the chosen filters."""
    
    if category is not None and item.get("category") != category:
        return False


    item_date = parse_date(str(item.get("date", "")))
    if item_date is None:
        return False

    if start is not None and item_date < start:
        return False
    if end is not None and item_date > end:
        return False

    return True


def list_expenses(expenses: List[Dict[str, Any]]) -> None:
    """Print expenses, optionally filtered and sorted by date descending."""
    if not expenses:
        print("No expenses yet.")
        return

    category = input("Filter by category (blank = no filter): ").strip().lower() or None
    start = prompt_date("Start date YYYY-MM-DD (blank = none): ", allow_blank=True)
    end = prompt_date("End date YYYY-MM-DD (blank = none): ", allow_blank=True)

    filtered = [e for e in expenses if matches_filters(e, category, start, end)]


    def sort_key(e: Dict[str, Any]):
        d = parse_date(str(e.get("date", ""))) or date.min
        return (d, e.get("id", 0))

    filtered.sort(key=sort_key, reverse=True)

    if not filtered:
        print("No expenses matched your filters.")
        return

    print("\nID  Date        Amount   Category     Note")
    print("--  ----------  -------  ----------   -------------------------")
    for e in filtered:
        eid = str(e.get("id", "")).rjust(2)
        d = str(e.get("date", "")).ljust(10)
        amt = f"{float(e.get('amount', 0)):7.2f}"
        cat = str(e.get("category", "")).ljust(10)
        note = str(e.get("note", ""))[:25]
        print(f"{eid}  {d}  {amt}  {cat}   {note}")

    print(f"\nShown: {len(filtered)} expense(s)\n")


def summarize(expenses: List[Dict[str, Any]]) -> None:
    """Print total spending and totals per category (with optional date filtering)."""
    if not expenses:
        print("No expenses to summarize.")
        return

    start = prompt_date("Start date YYYY-MM-DD (blank = none): ", allow_blank=True)
    end = prompt_date("End date YYYY-MM-DD (blank = none): ", allow_blank=True)

    filtered = [e for e in expenses if matches_filters(e, None, start, end)]

    total = 0.0
    by_category: Dict[str, float] = {}

    for e in filtered:
        amount = float(e.get("amount", 0))
        total += amount
        cat = str(e.get("category", "uncategorized"))
        by_category[cat] = by_category.get(cat, 0.0) + amount

    print("\nSummary")
    print("-------")
    print(f"Total spent: ${total:.2f}")

    if not by_category:
        print("No category totals available.")
        return

   
    sorted_cats = sorted(by_category.items(), key=lambda x: x[1], reverse=True)
    print("\nBy category:")
    for cat, amt in sorted_cats:
        print(f"- {cat}: ${amt:.2f}")
    print("")


def delete_expense(expenses: List[Dict[str, Any]]) -> None:
    """Delete an expense by its ID."""
    if not expenses:
        print("No expenses to delete.")
        return

    raw = input("Enter expense ID to delete: ").strip()
    if not raw.isdigit():
        print("Please enter a valid integer ID.")
        return

    target_id = int(raw)
    for i, e in enumerate(expenses):
        if e.get("id") == target_id:
            removed = expenses.pop(i)
            save_expenses(DATA_FILE, expenses)
            print(f"Deleted expense #{removed.get('id')} ✅")
            return

    print(f"No expense found with ID {target_id}.")


def print_menu() -> None:
    """Display the main menu."""
    print("Personal Expense Tracker")
    print("------------------------")
    print("1) Add expense")
    print("2) List expenses")
    print("3) Summary")
    print("4) Delete expense")
    print("5) Exit")


def main() -> None:
    """Program entry point."""
    expenses = load_expenses(DATA_FILE)

    while True:
        print_menu()
        choice = input("Choose an option (1-5): ").strip()

        if choice == "1":
            add_expense(expenses)
        elif choice == "2":
            list_expenses(expenses)
        elif choice == "3":
            summarize(expenses)
        elif choice == "4":
            delete_expense(expenses)
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please choose 1-5.\n")


if __name__ == "__main__":
    main()
