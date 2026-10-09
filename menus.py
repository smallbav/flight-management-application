"""
menus.py - one function for each menu option.

Each function:
  1. asks the user for what it needs   (using ui.py)
  2. checks the business rules         (here, in Python)
  3. reads or changes the data         (using the repositories)
  4. shows the result                  (using ui.py)

There is no SQL in this file - it is all in repositories.py.
Each function is given only the repositories it needs as parameters.
"""

import sqlite3

import ui

# The values allowed by the CHECK constraints in schema.sql. Kept here so
# the app can show the choices and validate input before it reaches the
# database.
STATUSES = ["Scheduled", "Delayed", "Departed", "Landed", "Cancelled"]
RANKS = ["Captain", "First Officer"]


# =====================================================================
# Helpers that check the user's answer against the database
# (they live here, not in ui.py, because ui.py never uses the database)
# =====================================================================

def ask_existing_flight(flights, prompt):
    """Ask for a flight ID until it matches a flight. Returns the ID."""
    while True:
        flight_id = ui.ask_number(prompt)
        if flights.get(flight_id) is not None:
            return flight_id
        print(f"No record with ID {flight_id}. Please try again.")


def ask_existing_pilot(pilots, prompt):
    """Ask for a pilot ID until it matches a pilot. Returns the ID."""
    while True:
        pilot_id = ui.ask_number(prompt)
        if pilots.get(pilot_id) is not None:
            return pilot_id
        print(f"No record with ID {pilot_id}. Please try again.")


def ask_existing_airport(airports, prompt, optional):
    """Ask for the IATA code of an airport in the database."""
    while True:
        code = ui.ask_text(prompt, optional).upper()
        if code == "":   # only possible when optional is True
            return ""
        if airports.get(code) is not None:
            return code
        print(f"No airport with code '{code}'. Please try again.")


# =====================================================================
# FLIGHTS
# =====================================================================

# ---- Option 1: Add a New Flight (CREATE) ----------------------------

def add_flight(flights, airports):
    print("\n--- Add a New Flight ---")

    # Flight number: letters and digits only, e.g. SB123
    while True:
        flight_number = ui.ask_text("Flight number (e.g. SB123): ", optional=False).upper()
        if flight_number.isalnum():   # True if only letters and digits
            break
        print("Use letters and digits only, with no spaces.")

    origin = ask_existing_airport(airports, "Origin airport code (e.g. LHR): ", optional=False)

    # The schema also blocks origin = destination, but checking here
    # lets us give a clear message and ask again straight away
    while True:
        destination = ask_existing_airport(airports, "Destination airport code (e.g. CDG): ", optional=False)
        if destination != origin:
            break
        print("The destination must be different from the origin.")

    # Same idea: the schema checks arrival > departure, but we check
    # first so the user can simply re-enter the arrival time
    departure = ui.ask_datetime("Departure (UTC) YYYY-MM-DD HH:MM: ", optional=False)
    while True:
        arrival = ui.ask_datetime("Arrival (UTC) YYYY-MM-DD HH:MM: ", optional=False)
        if arrival > departure:   # works because the format sorts in time order
            break
        print("Arrival must be after departure.")

    print(f"\nNew flight: {flight_number}  {origin} -> {destination}")
    print(f"Departs {departure} UTC, arrives {arrival} UTC, status Scheduled")
    if not ui.ask_yes_no("Save this flight?"):
        print("Cancelled - nothing was saved.")
        return

    try:
        new_id = flights.add(flight_number, origin, destination, departure, arrival)
    except sqlite3.IntegrityError:
        # The UNIQUE (flight_number, departure_datetime) rule was broken
        print(f"\nNot saved: flight {flight_number} already departs at {departure}.")
        return

    print(f"\nFlight {flight_number} added with ID {new_id}.")


# ---- Option 2: View Flights by Criteria (READ) ----------------------

def view_flights_by_criteria(flights, airports):
    print("\n--- View Flights by Criteria ---")
    print("Fill in any filters you want. Press Enter to skip a filter.")
    print("Skip them all to see every flight.\n")

    destination = ask_existing_airport(airports, "Destination airport code (e.g. CDG): ", optional=True)
    status = ui.ask_from_list("Status (press Enter to skip): ", STATUSES, optional=True)
    departure_date = ui.ask_date("Departure date YYYY-MM-DD (press Enter to skip): ", optional=True)

    ui.print_table(flights.search(destination, status, departure_date))


# ---- Option 3: Update Flight Information (UPDATE) -------------------

def update_flight(flights):
    print("\n--- Update Flight Information ---")
    ui.print_table(flights.list_all())
    flight_id = ask_existing_flight(flights, "\nFlight ID to update: ")
    flight = flights.get(flight_id)

    print("\nPress Enter to keep the current value shown in [brackets].")
    departure = ui.ask_datetime(f"Departure (UTC) [{flight['departure_datetime']}]: ", optional=True)
    arrival = ui.ask_datetime(f"Arrival (UTC) [{flight['arrival_datetime']}]: ", optional=True)
    status = ui.ask_from_list(f"Status [{flight['status']}]: ", STATUSES, optional=True)

    # An empty answer means "keep the current value"
    if departure == "":
        departure = flight["departure_datetime"]
    if arrival == "":
        arrival = flight["arrival_datetime"]
    if status == "":
        status = flight["status"]

    if arrival <= departure:
        print("\nNot saved: arrival must be after departure.")
        return

    try:
        flights.update(flight_id, departure, arrival, status)
    except sqlite3.IntegrityError:
        # The new departure time clashes with the same flight number
        # already departing at that time (the UNIQUE rule)
        print(f"\nNot saved: flight {flight['flight_number']} already departs at {departure}.")
        return

    print(f"\nFlight {flight_id} updated:")
    ui.print_table(flights.list_one(flight_id))


# ---- Option 4: Delete a Flight (DELETE) -----------------------------

def delete_flight(flights, assignments):
    print("\n--- Delete a Flight ---")
    ui.print_table(flights.list_all())
    flight_id = ask_existing_flight(flights, "\nFlight ID to delete: ")
    ui.print_table(flights.list_one(flight_id))

    crew_count = assignments.count_for_flight(flight_id)
    if crew_count > 0:
        print(f"This flight has {crew_count} pilot assignment(s), which will also be removed.")

    if not ui.ask_yes_no("Delete this flight?"):
        print("Cancelled - nothing was deleted.")
        return

    flights.delete(flight_id)   # CASCADE removes its assignments
    print(f"\nFlight {flight_id} deleted.")


# =====================================================================
# PILOTS
# =====================================================================

# ---- Option 5: Assign Pilot to Flight (CREATE assignment) -----------

def assign_pilot(flights, pilots, assignments):
    print("\n--- Assign Pilot to Flight ---")
    ui.print_table(flights.list_all())
    flight_id = ask_existing_flight(flights, "\nFlight ID: ")
    ui.print_table(pilots.list_all())
    pilot_id = ask_existing_pilot(pilots, "\nPilot ID: ")
    role = ui.ask_from_list("Role on this flight: ", RANKS, optional=False)

    flight = flights.get(flight_id)
    pilot = pilots.get(pilot_id)
    pilot_name = pilot["first_name"] + " " + pilot["last_name"]

    # Business rules the schema cannot check, so Python checks them:
    if flight["status"] == "Cancelled":
        print("\nNot assigned: this flight is cancelled.")
        return
    if role == "Captain" and pilot["rank"] == "First Officer":
        print(f"\nNot assigned: {pilot_name} is a First Officer and cannot fly as Captain.")
        return

    # These two are also enforced by the schema (primary key and UNIQUE),
    # but checking first lets us explain exactly what the problem is
    if assignments.is_assigned(flight_id, pilot_id):
        print(f"\nNot assigned: {pilot_name} is already on this flight.")
        return
    current_holder = assignments.role_holder(flight_id, role)
    if current_holder is not None:
        print(f"\nNot assigned: {current_holder} is already the {role} on this flight.")
        return

    assignments.add(flight_id, pilot_id, role)
    print(f"\n{pilot_name} assigned to flight {flight['flight_number']} (ID {flight_id}) as {role}.")


# ---- Option 6: Remove Pilot from Flight (DELETE assignment) ---------

def remove_pilot(flights, pilots, assignments):
    print("\n--- Remove Pilot from Flight ---")
    flight_id = ask_existing_flight(flights, "Flight ID: ")

    crew = assignments.crew_for_flight(flight_id)
    if len(crew) == 0:
        print("\nThis flight has no pilots assigned.")
        return
    ui.print_table(crew)

    pilot_id = ask_existing_pilot(pilots, "\nPilot ID to remove: ")
    if not ui.ask_yes_no("Remove this pilot from the flight?"):
        print("Cancelled - nothing was changed.")
        return

    # remove() returns how many rows it deleted: 0 if that pilot
    # wasn't on this flight
    if assignments.remove(flight_id, pilot_id) == 0:
        print("\nThat pilot is not on this flight - nothing was changed.")
    else:
        print("\nPilot removed from the flight.")


# ---- Option 7: View Pilot Schedule (READ) ---------------------------

def view_pilot_schedule(pilots, assignments):
    print("\n--- View Pilot Schedule ---")
    ui.print_table(pilots.list_all())
    pilot_id = ask_existing_pilot(pilots, "\nPilot ID: ")
    pilot = pilots.get(pilot_id)

    print(f"\nSchedule for {pilot['first_name']} {pilot['last_name']}:")
    ui.print_table(assignments.schedule_for_pilot(pilot_id))


# ---- Option 8: View All Pilots (READ) -------------------------------

def view_pilots(pilots):
    print("\n--- All Pilots ---")
    ui.print_table(pilots.list_all())


# ---- Option 9: Add a Pilot (CREATE) ---------------------------------

def add_pilot(pilots):
    print("\n--- Add a Pilot ---")
    first_name = ui.ask_text("First name: ", optional=False)
    last_name = ui.ask_text("Last name: ", optional=False)
    licence = ui.ask_text("Licence number (e.g. UK-FCL-12345): ", optional=False).upper()
    rank = ui.ask_from_list("Rank: ", RANKS, optional=False)
    email = ui.ask_email("Email: ", optional=False)
    hire_date = ui.ask_date("Hire date YYYY-MM-DD: ", optional=False)

    try:
        new_id = pilots.add(first_name, last_name, licence, rank, email, hire_date)
    except sqlite3.IntegrityError:
        # Licence number and email are both UNIQUE in the schema
        print("\nNot saved: another pilot already has that licence number or email.")
        return

    print(f"\n{first_name} {last_name} added with pilot ID {new_id}.")


# ---- Option 10: Update a Pilot (UPDATE) -----------------------------

def update_pilot(pilots, assignments):
    print("\n--- Update a Pilot ---")
    ui.print_table(pilots.list_all())
    pilot_id = ask_existing_pilot(pilots, "\nPilot ID to update: ")
    pilot = pilots.get(pilot_id)

    print("\nPress Enter to keep the current value shown in [brackets].")
    first_name = ui.ask_text(f"First name [{pilot['first_name']}]: ", optional=True)
    last_name = ui.ask_text(f"Last name [{pilot['last_name']}]: ", optional=True)
    rank = ui.ask_from_list(f"Rank [{pilot['rank']}]: ", RANKS, optional=True)
    email = ui.ask_email(f"Email [{pilot['email']}]: ", optional=True)

    if first_name == "":
        first_name = pilot["first_name"]
    if last_name == "":
        last_name = pilot["last_name"]
    if rank == "":
        rank = pilot["rank"]
    if email == "":
        email = pilot["email"]

    # Same rule as Assign Pilot: a First Officer cannot fly as Captain.
    # So a pilot can't become a First Officer while still rostered as Captain.
    if rank == "First Officer":
        captain_flights = assignments.count_as_captain(pilot_id)
        if captain_flights > 0:
            print(f"\nNot saved: this pilot is Captain on {captain_flights} flight(s). "
                  "Remove them from those flights first.")
            return

    try:
        pilots.update(pilot_id, first_name, last_name, rank, email)
    except sqlite3.IntegrityError:
        print("\nNot saved: another pilot already has that email.")
        return

    print(f"\nPilot {pilot_id} updated.")


# ---- Option 11: Delete a Pilot (DELETE) -----------------------------

def delete_pilot(pilots):
    print("\n--- Delete a Pilot ---")
    ui.print_table(pilots.list_all())
    pilot_id = ask_existing_pilot(pilots, "\nPilot ID to delete: ")

    if not ui.ask_yes_no("Delete this pilot?"):
        print("Cancelled - nothing was deleted.")
        return

    try:
        pilots.delete(pilot_id)
    except sqlite3.IntegrityError:
        # ON DELETE RESTRICT blocks deleting a pilot with assignments
        print("\nNot deleted: this pilot is assigned to flights. "
              "Remove them from those flights first (option 6).")
        return

    print(f"\nPilot {pilot_id} deleted.")


# =====================================================================
# DESTINATIONS (the Airport table)
# =====================================================================

# ---- Option 12: View/Update Destination Information (READ + UPDATE) --

def view_update_destination(airports):
    print("\n--- View/Update Destination Information ---")
    ui.print_table(airports.list_all())

    if not ui.ask_yes_no("\nUpdate one of these destinations?"):
        return

    code = ask_existing_airport(airports, "Airport code to update: ", optional=False)
    airport = airports.get(code)

    print("\nPress Enter to keep the current value shown in [brackets].")
    name = ui.ask_text(f"Airport name [{airport['airport_name']}]: ", optional=True)
    city = ui.ask_text(f"City [{airport['city']}]: ", optional=True)
    country = ui.ask_text(f"Country [{airport['country']}]: ", optional=True)
    timezone = ui.ask_text(f"Timezone [{airport['timezone']}]: ", optional=True)

    if name == "":
        name = airport["airport_name"]
    if city == "":
        city = airport["city"]
    if country == "":
        country = airport["country"]
    if timezone == "":
        timezone = airport["timezone"]

    airports.update(code, name, city, country, timezone)
    print(f"\n{code} updated.")


# ---- Option 13: Add a Destination (CREATE) --------------------------

def add_destination(airports):
    print("\n--- Add a Destination ---")

    # IATA codes are exactly three letters, e.g. LIS
    while True:
        code = ui.ask_text("IATA code (3 letters, e.g. LIS): ", optional=False).upper()
        if len(code) == 3 and code.isalpha():   # isalpha(): letters only
            break
        print("The code must be exactly 3 letters.")

    name = ui.ask_text("Airport name: ", optional=False)
    city = ui.ask_text("City: ", optional=False)
    country = ui.ask_text("Country: ", optional=False)
    timezone = ui.ask_text("Timezone (e.g. Europe/Lisbon): ", optional=False)

    try:
        airports.add(code, name, city, country, timezone)
    except sqlite3.IntegrityError:
        # iata_code is UNIQUE in the schema
        print(f"\nNot saved: an airport with code {code} already exists.")
        return

    print(f"\n{code} ({city}) added.")


# ---- Option 14: Delete a Destination (DELETE) -----------------------

def delete_destination(airports):
    print("\n--- Delete a Destination ---")
    ui.print_table(airports.list_all())
    code = ask_existing_airport(airports, "\nAirport code to delete: ", optional=False)

    if not ui.ask_yes_no(f"Delete {code}?"):
        print("Cancelled - nothing was deleted.")
        return

    try:
        airports.delete(code)
    except sqlite3.IntegrityError:
        # ON DELETE RESTRICT blocks deleting an airport that flights use
        print(f"\nNot deleted: flights still use {code}. "
              "Delete or change those flights first.")
        return

    print(f"\n{code} deleted.")


# =====================================================================
# REPORTS
# =====================================================================

# ---- Option 15: Summary Reports -------------------------------------

def summary_reports(reports):
    print("\n=== Flights to each destination ===")
    ui.print_table(reports.flights_per_destination())

    print("\n=== Flights assigned to each pilot ===")
    ui.print_table(reports.flights_per_pilot())

    print("\n=== Flight hours per pilot (excluding cancelled flights) ===")
    ui.print_table(reports.hours_per_pilot())

    print("\n=== Busiest airports (departures + arrivals) ===")
    ui.print_table(reports.busiest_airports())

    print("\n=== Pilots with no flight assignments ===")
    ui.print_table(reports.pilots_without_flights())

    print("\n=== Flights without a full crew (excluding cancelled) ===")
    ui.print_table(reports.flights_without_full_crew())
