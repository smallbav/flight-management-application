"""
main.py - Flight Management command-line application. Start here.

Run with:  python3 main.py
(Build the database first with:  python3 setup_db.py)

How the program is organised:
  main.py          this file: opens the database, shows the menu,
                   calls the chosen option
  menus.py         one function per menu option
  repositories.py  all the SQL, one class per table
  ui.py            input and output (questions and tables)
  db.py            opens the database connection
"""

import sqlite3

import menus
from db import get_connection
from repositories import (
    FlightRepository,
    PilotRepository,
    AssignmentRepository,
    AirportRepository,
    ReportRepository,
)


def show_menu():
    print("\n========== Flight Management System ==========")
    print(" Flights")
    print("   1. Add a New Flight")
    print("   2. View Flights by Criteria")
    print("   3. Update Flight Information")
    print("   4. Delete a Flight")
    print(" Pilots")
    print("   5. Assign Pilot to Flight")
    print("   6. Remove Pilot from Flight")
    print("   7. View Pilot Schedule")
    print("   8. View All Pilots")
    print("   9. Add a Pilot")
    print("  10. Update a Pilot")
    print("  11. Delete a Pilot")
    print(" Destinations")
    print("  12. View/Update Destination Information")
    print("  13. Add a Destination")
    print("  14. Delete a Destination")
    print(" Reports")
    print("  15. Summary Reports")
    print("\n   0. Exit")


def main():
    conn = get_connection()

    # Create one repository object per table. They all share the same
    # connection, and are passed to the menu functions that need them.
    flights = FlightRepository(conn)
    pilots = PilotRepository(conn)
    assignments = AssignmentRepository(conn)
    airports = AirportRepository(conn)
    reports = ReportRepository(conn)

    try:
        while True:
            show_menu()
            choice = input("Choose an option: ").strip()

            try:
                if choice == "1":
                    menus.add_flight(flights, airports)
                elif choice == "2":
                    menus.view_flights_by_criteria(flights, airports)
                elif choice == "3":
                    menus.update_flight(flights)
                elif choice == "4":
                    menus.delete_flight(flights, assignments)
                elif choice == "5":
                    menus.assign_pilot(flights, pilots, assignments)
                elif choice == "6":
                    menus.remove_pilot(flights, pilots, assignments)
                elif choice == "7":
                    menus.view_pilot_schedule(pilots, assignments)
                elif choice == "8":
                    menus.view_pilots(pilots)
                elif choice == "9":
                    menus.add_pilot(pilots)
                elif choice == "10":
                    menus.update_pilot(pilots, assignments)
                elif choice == "11":
                    menus.delete_pilot(pilots)
                elif choice == "12":
                    menus.view_update_destination(airports)
                elif choice == "13":
                    menus.add_destination(airports)
                elif choice == "14":
                    menus.delete_destination(airports)
                elif choice == "15":
                    menus.summary_reports(reports)
                elif choice == "0":
                    print("Goodbye.")
                    break
                else:
                    print("\nPlease enter a number from the menu.")
            except sqlite3.Error as error:
                # Safety net: if the database rejects something we didn't
                # expect, undo any half-finished change, show the reason
                # and return to the menu instead of crashing
                conn.rollback()
                print(f"\nDatabase error: {error}")
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C or Ctrl+D: leave politely instead of showing an error
        print("\nGoodbye.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
