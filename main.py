"""
main.py - Flight Management command-line application.

Run with:  python3 main.py
(Build the database first with:  python3 setup_db.py)

The program shows a menu, asks the user to choose an option, runs that
option, then shows the menu again until the user chooses 0 to exit.
Each menu option has its own function below.
"""

import sqlite3
from datetime import date

from db import get_connection

# The flight statuses allowed by the CHECK constraint in schema.sql.
# Kept here so the app can show them to the user and validate input
# before sending anything to the database.
STATUSES = ["Scheduled", "Delayed", "Departed", "Landed", "Cancelled"]


# ---------------------------------------------------------------------
# Display helper
# ---------------------------------------------------------------------

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


# ---------------------------------------------------------------------
# Input helpers - each one keeps asking until the input is valid,
# or returns "" if the user presses Enter to skip
# ---------------------------------------------------------------------

def ask_optional_airport(conn, prompt):
    """Ask for an IATA code. Returns the code, or "" if skipped."""
    while True:
        code = input(prompt).strip().upper()   # tidy spaces, make capitals
        if code == "":
            return ""

        # Check the airport exists, so a typo gets a helpful message
        # instead of silently returning no flights
        airport = conn.execute(
            "SELECT airport_name FROM Airport WHERE iata_code = ?", (code,)
        ).fetchone()
        if airport is None:
            print(f"No airport with code '{code}'. Please try again.")
        else:
            return code


def ask_optional_status():
    """Ask for a flight status. Returns the status, or "" if skipped."""
    print("Statuses: " + ", ".join(STATUSES))
    while True:
        status = input("Status (press Enter to skip): ").strip().title()
        if status == "" or status in STATUSES:
            return status
        print("That is not a valid status. Please choose one from the list.")


def ask_optional_date(prompt):
    """Ask for a date as YYYY-MM-DD. Returns it, or "" if skipped."""
    while True:
        text = input(prompt).strip()
        if text == "":
            return ""
        try:
            # fromisoformat() raises ValueError if this isn't a real date
            chosen = date.fromisoformat(text)
            # isoformat() gives it back in the exact form stored in the
            # database (e.g. 2026-10-09, with leading zeros)
            return chosen.isoformat()
        except ValueError:
            print("Please enter a real date as YYYY-MM-DD, e.g. 2026-10-09.")


# ---------------------------------------------------------------------
# Menu option 2: View Flights by Criteria
# ---------------------------------------------------------------------

def view_flights_by_criteria(conn):
    """Show flights filtered by any mix of destination, status and date."""
    print("\n--- View Flights by Criteria ---")
    print("Fill in any filters you want. Press Enter to skip a filter.")
    print("Skip them all to see every flight.\n")

    destination = ask_optional_airport(conn, "Destination airport code (e.g. CDG): ")
    status = ask_optional_status()
    departure_date = ask_optional_date("Departure date YYYY-MM-DD: ")

    # The Flight table stores airport IDs, not codes, so we JOIN the
    # Airport table twice: once as "o" for the origin and once as "d"
    # for the destination. Text in double quotes after AS sets the
    # column heading shown to the user.
    sql = """
        SELECT f.flight_id           AS "ID",
               f.flight_number       AS "Flight",
               o.iata_code           AS "From",
               d.iata_code           AS "To",
               f.departure_datetime  AS "Departs (UTC)",
               f.arrival_datetime    AS "Arrives (UTC)",
               f.status              AS "Status"
        FROM Flight AS f
        JOIN Airport AS o ON o.airport_id = f.origin_id
        JOIN Airport AS d ON d.airport_id = f.destination_id
    """

    # Build the WHERE clause from fixed pieces of SQL written here in the
    # code. The user's values never go into the SQL text - they go into
    # the "values" list and reach the database through the ? placeholders.
    conditions = []
    values = []

    if destination != "":
        conditions.append("d.iata_code = ?")
        values.append(destination)

    if status != "":
        conditions.append("f.status = ?")
        values.append(status)

    if departure_date != "":
        # Every time on that day falls between 00:00 and 23:59
        conditions.append("f.departure_datetime BETWEEN ? AND ?")
        values.append(departure_date + " 00:00")
        values.append(departure_date + " 23:59")

    if len(conditions) > 0:
        sql = sql + " WHERE " + " AND ".join(conditions)

    sql = sql + " ORDER BY f.departure_datetime"

    rows = conn.execute(sql, values).fetchall()
    print_table(rows)


# ---------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------

def show_menu():
    print("\n===== Flight Management System =====")
    print("1. Add a New Flight")
    print("2. View Flights by Criteria")
    print("3. Update Flight Information")
    print("4. Assign Pilot to Flight")
    print("5. View Pilot Schedule")
    print("6. View/Update Destination Information")
    print("7. Summary Reports")
    print("0. Exit")


def main():
    conn = get_connection()
    try:
        while True:
            show_menu()
            choice = input("Choose an option: ").strip()

            try:
                if choice == "2":
                    view_flights_by_criteria(conn)
                elif choice in ["1", "3", "4", "5", "6", "7"]:
                    print("\nThis option is not built yet.")
                elif choice == "0":
                    print("Goodbye.")
                    break
                else:
                    print("\nPlease enter a number from the menu.")
            except sqlite3.Error as error:
                # If the database rejects something, show the reason and
                # return to the menu instead of crashing the program
                print(f"\nDatabase error: {error}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
