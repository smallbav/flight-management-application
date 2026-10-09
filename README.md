# Flight Management Database

A command-line application for managing an airline's flights, pilots and destinations, built with Python and SQLite (`sqlite3`).

## How to run (GitHub Codespaces or any machine with Python 3)

No extra packages are needed — `sqlite3` is part of Python.

1. Build the database with the sample data (safe to re-run; it always restores the original data):

   ```
   python3 setup_db.py
   ```

2. Start the application:

   ```
   python3 main.py
   ```

3. Choose options by typing their number and pressing Enter. Choose `0` to exit.

## Files

| File | Purpose |
|---|---|
| `schema.sql` | Creates the tables, keys, constraints and indexes |
| `seed.sql` | Sample data: 12 airports, 12 pilots, 12 flights, 15 pilot assignments |
| `setup_db.py` | Builds `flights.db` from `schema.sql` and `seed.sql` |
| `db.py` | Opens a database connection with foreign keys switched on |
| `main.py` | Start here: shows the menu and calls the chosen option |
| `menus.py` | One function per menu option: asks questions, checks business rules, shows results |
| `repositories.py` | All SQL queries: one class per table, plus one for the summary reports |
| `ui.py` | Input and output helpers: validated questions and table printing |
| `flights.db` | The SQLite database file |

The code is in layers: `main.py` → `menus.py` → `repositories.py` → the database. Only `repositories.py` contains SQL, and only `ui.py` reads from the keyboard.

## Menu options

- **Flights:** add, view by criteria (destination, status, departure date), update times/status, delete
- **Pilots:** assign to / remove from a flight, view a pilot's schedule, view, add, update, delete
- **Destinations:** view/update, add, delete
- **Summary reports:** flights per destination, flights per pilot, flight hours per pilot, busiest airports, pilots with no assignments, flights without a full crew

## Notes

- All dates and times are in UTC, entered as `YYYY-MM-DD HH:MM`.
- Flight, pilot and airport details are fictional sample data for testing; airport codes and timezones are real.
