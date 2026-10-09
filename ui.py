"""
ui.py - everything that touches the screen or the keyboard.

Plain functions, not classes: they don't need to remember anything
between calls, so there is no state for an object to hold.
This file never talks to the database.

The ask_... functions keep asking until the answer is valid.
Where "optional" is True, pressing Enter skips the question and the
function returns "" - used for search filters, and for updates where
Enter means "keep the current value".
"""

from datetime import date, datetime


# =====================================================================
# Output
# =====================================================================

def print_table(rows):
    """Print query results as a simple table with column headings."""
    if len(rows) == 0:
        print("\nNo results found.")
        return

    # Column headings come from the query itself (the names after AS)
    headings = rows[0].keys()

    # Work out how wide each column needs to be: the longest of the
    # heading and every value in that column
    widths = []
    for heading in headings:
        widest = len(heading)
        for row in rows:
            value_length = len(str(row[heading]))
            if value_length > widest:
                widest = value_length
        widths.append(widest)

    # Print the heading line, a separator line, then one line per row.
    # ljust(n) pads text with spaces on the right to make it n characters.
    print()
    heading_cells = []
    for i in range(len(headings)):
        heading_cells.append(headings[i].ljust(widths[i]))
    print(" | ".join(heading_cells))

    separator_cells = []
    for width in widths:
        separator_cells.append("-" * width)
    print("-+-".join(separator_cells))

    for row in rows:
        value_cells = []
        for i in range(len(headings)):
            value_cells.append(str(row[headings[i]]).ljust(widths[i]))
        print(" | ".join(value_cells))

    print(f"\n{len(rows)} row(s)")


# =====================================================================
# Input
# =====================================================================

def ask_text(prompt, optional):
    """Ask for any text. Returns it with spaces trimmed."""
    while True:
        text = input(prompt).strip()
        if text != "" or optional:
            return text
        print("This field is required.")


def ask_number(prompt):
    """Ask for a whole number, e.g. an ID. Returns it as an int."""
    while True:
        text = input(prompt).strip()
        if text.isdigit():   # isdigit() is True only for 0-9 characters
            return int(text)
        print("Please enter a number.")


def ask_yes_no(prompt):
    """Ask a y/n question. Returns True for yes, False for no."""
    while True:
        answer = input(prompt + " (y/n): ").strip().lower()
        if answer == "y":
            return True
        if answer == "n":
            return False
        print("Please type y or n.")


def ask_from_list(prompt, choices, optional):
    """Ask for one of a fixed list of values, e.g. a status or a rank.

    Accepts any capitalisation: "first officer" becomes "First Officer".
    """
    print("Choices: " + ", ".join(choices))
    while True:
        text = input(prompt).strip().title()
        if text == "" and optional:
            return ""
        if text in choices:
            return text
        print("Please type one of the choices shown.")


def ask_date(prompt, optional):
    """Ask for a date as YYYY-MM-DD."""
    while True:
        text = input(prompt).strip()
        if text == "" and optional:
            return ""
        try:
            # fromisoformat() raises ValueError if this isn't a real date
            chosen = date.fromisoformat(text)
            # isoformat() gives it back in the exact stored form,
            # e.g. 2026-10-09 with leading zeros
            return chosen.isoformat()
        except ValueError:
            print("Please enter a real date as YYYY-MM-DD, e.g. 2026-10-09.")


def ask_datetime(prompt, optional):
    """Ask for a date and time as YYYY-MM-DD HH:MM."""
    while True:
        text = input(prompt).strip()
        if text == "" and optional:
            return ""
        try:
            # strptime() reads the text using the pattern given and raises
            # ValueError if it doesn't match or isn't a real date/time.
            # %Y year, %m month, %d day, %H hour (24h), %M minute.
            chosen = datetime.strptime(text, "%Y-%m-%d %H:%M")
            # strftime() writes it back out in exactly the stored format,
            # so "2026-10-9 7:05" becomes "2026-10-09 07:05"
            return chosen.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            print("Please use YYYY-MM-DD HH:MM in 24-hour UTC time, e.g. 2026-10-12 14:30.")


def ask_email(prompt, optional):
    """Ask for an email address (a simple check: it must contain @)."""
    while True:
        email = input(prompt).strip().lower()
        if email == "" and optional:
            return ""
        if "@" in email and " " not in email:
            return email
        print("Please enter a valid email address, e.g. name@example.com.")
