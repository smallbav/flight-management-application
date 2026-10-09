"""
repositories.py - the data access layer: ALL of the app's SQL lives here.

There is one class per table (plus one for the summary reports). Each
class is given the database connection when it is created and keeps it
in self.conn, so its methods can run queries.

Rules for this layer:
  * Repositories only talk to the database. They never print anything
    or ask the user anything - that is the job of menus.py and ui.py.
  * Every value from the user is passed in through ? placeholders,
    never pasted into the SQL text, to prevent SQL injection.
  * Methods that change data call self.conn.commit() so the change is
    saved. If the database rejects a change (e.g. a UNIQUE rule is
    broken) it raises sqlite3.IntegrityError, which menus.py catches
    and turns into a friendly message.
"""


# =====================================================================
# Flight table
# =====================================================================

class FlightRepository:

    # The SELECT used whenever flights are shown to the user. The Flight
    # table stores airport IDs, so it JOINs the Airport table twice:
    # once as "o" (origin) and once as "d" (destination), to show airport
    # codes instead. Text in double quotes after AS is the column heading.
    # Defined once here so every flight list looks the same.
    FLIGHT_SELECT = """
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

    def __init__(self, conn):
        self.conn = conn

    def get(self, flight_id):
        """Return one flight's stored values, or None if it doesn't exist."""
        return self.conn.execute(
            "SELECT * FROM Flight WHERE flight_id = ?", (flight_id,)
        ).fetchone()

    def list_all(self):
        """Every flight, ready to display, in departure order."""
        return self.conn.execute(
            self.FLIGHT_SELECT + " ORDER BY f.departure_datetime"
        ).fetchall()

    def list_one(self, flight_id):
        """One flight, ready to display."""
        return self.conn.execute(
            self.FLIGHT_SELECT + " WHERE f.flight_id = ?", (flight_id,)
        ).fetchall()

    def search(self, destination, status, departure_date):
        """Flights matching any mix of the three filters.

        An empty string ("") means "don't filter on this". The WHERE
        clause is built from fixed pieces of SQL written here; the user's
        values only ever go into the "values" list for the ? placeholders.
        """
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

        sql = self.FLIGHT_SELECT
        if len(conditions) > 0:
            sql = sql + " WHERE " + " AND ".join(conditions)
        sql = sql + " ORDER BY f.departure_datetime"

        return self.conn.execute(sql, values).fetchall()

    def add(self, flight_number, origin_code, destination_code, departure, arrival):
        """Insert a new flight and return its new ID.

        The table stores airport IDs, so each (SELECT ...) subquery looks
        up the ID for an airport code. Status is left out, so the
        table's DEFAULT 'Scheduled' is used.
        """
        cursor = self.conn.execute("""
            INSERT INTO Flight (flight_number, origin_id, destination_id,
                                departure_datetime, arrival_datetime)
            VALUES (?,
                    (SELECT airport_id FROM Airport WHERE iata_code = ?),
                    (SELECT airport_id FROM Airport WHERE iata_code = ?),
                    ?, ?)
        """, (flight_number, origin_code, destination_code, departure, arrival))
        self.conn.commit()
        return cursor.lastrowid   # the ID SQLite gave the new row

    def update(self, flight_id, departure, arrival, status):
        """Change a flight's times and status."""
        self.conn.execute("""
            UPDATE Flight
            SET departure_datetime = ?, arrival_datetime = ?, status = ?
            WHERE flight_id = ?
        """, (departure, arrival, status, flight_id))
        self.conn.commit()

    def delete(self, flight_id):
        """Delete a flight. ON DELETE CASCADE in the schema also removes
        its rows in FlightAssignment."""
        self.conn.execute("DELETE FROM Flight WHERE flight_id = ?", (flight_id,))
        self.conn.commit()


# =====================================================================
# Pilot table
# =====================================================================

class PilotRepository:

    def __init__(self, conn):
        self.conn = conn

    def get(self, pilot_id):
        """Return one pilot's stored values, or None if they don't exist."""
        return self.conn.execute(
            "SELECT * FROM Pilot WHERE pilot_id = ?", (pilot_id,)
        ).fetchone()

    def list_all(self):
        """Every pilot, ready to display, sorted by name."""
        return self.conn.execute("""
            SELECT pilot_id                       AS "ID",
                   first_name || ' ' || last_name AS "Name",
                   rank                           AS "Rank",
                   licence_number                 AS "Licence",
                   email                          AS "Email",
                   hire_date                      AS "Hired"
            FROM Pilot
            ORDER BY last_name, first_name
        """).fetchall()

    def add(self, first_name, last_name, licence, rank, email, hire_date):
        """Insert a new pilot and return their new ID."""
        cursor = self.conn.execute("""
            INSERT INTO Pilot (first_name, last_name, licence_number, rank, email, hire_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (first_name, last_name, licence, rank, email, hire_date))
        self.conn.commit()
        return cursor.lastrowid

    def update(self, pilot_id, first_name, last_name, rank, email):
        """Change a pilot's name, rank and email."""
        self.conn.execute("""
            UPDATE Pilot
            SET first_name = ?, last_name = ?, rank = ?, email = ?
            WHERE pilot_id = ?
        """, (first_name, last_name, rank, email, pilot_id))
        self.conn.commit()

    def delete(self, pilot_id):
        """Delete a pilot. ON DELETE RESTRICT in the schema blocks this
        (IntegrityError) if the pilot still has flight assignments."""
        self.conn.execute("DELETE FROM Pilot WHERE pilot_id = ?", (pilot_id,))
        self.conn.commit()


# =====================================================================
# FlightAssignment table (which pilots fly which flights)
# =====================================================================

class AssignmentRepository:

    def __init__(self, conn):
        self.conn = conn

    def add(self, flight_id, pilot_id, role):
        """Put a pilot on a flight's crew."""
        self.conn.execute(
            "INSERT INTO FlightAssignment (flight_id, pilot_id, role) VALUES (?, ?, ?)",
            (flight_id, pilot_id, role),
        )
        self.conn.commit()

    def remove(self, flight_id, pilot_id):
        """Take a pilot off a flight. Returns how many rows were deleted:
        1 if they were on the flight, 0 if they weren't."""
        cursor = self.conn.execute(
            "DELETE FROM FlightAssignment WHERE flight_id = ? AND pilot_id = ?",
            (flight_id, pilot_id),
        )
        self.conn.commit()
        return cursor.rowcount

    def crew_for_flight(self, flight_id):
        """The pilots on one flight, ready to display."""
        return self.conn.execute("""
            SELECT p.pilot_id                         AS "Pilot ID",
                   p.first_name || ' ' || p.last_name AS "Name",
                   fa.role                            AS "Role"
            FROM FlightAssignment AS fa
            JOIN Pilot AS p ON p.pilot_id = fa.pilot_id
            WHERE fa.flight_id = ?
        """, (flight_id,)).fetchall()

    def count_for_flight(self, flight_id):
        """How many pilots are on a flight."""
        return self.conn.execute(
            "SELECT COUNT(*) FROM FlightAssignment WHERE flight_id = ?", (flight_id,)
        ).fetchone()[0]

    def is_assigned(self, flight_id, pilot_id):
        """True if the pilot is already on this flight."""
        row = self.conn.execute(
            "SELECT 1 FROM FlightAssignment WHERE flight_id = ? AND pilot_id = ?",
            (flight_id, pilot_id),
        ).fetchone()
        return row is not None

    def role_holder(self, flight_id, role):
        """The name of whoever holds this role on the flight, or None."""
        row = self.conn.execute("""
            SELECT p.first_name || ' ' || p.last_name AS name
            FROM FlightAssignment AS fa
            JOIN Pilot AS p ON p.pilot_id = fa.pilot_id
            WHERE fa.flight_id = ? AND fa.role = ?
        """, (flight_id, role)).fetchone()
        if row is None:
            return None
        return row["name"]

    def count_as_captain(self, pilot_id):
        """How many flights this pilot is rostered on as Captain."""
        return self.conn.execute(
            "SELECT COUNT(*) FROM FlightAssignment WHERE pilot_id = ? AND role = 'Captain'",
            (pilot_id,),
        ).fetchone()[0]

    def schedule_for_pilot(self, pilot_id):
        """Every flight a pilot is assigned to, in time order.

        Starts from this pilot's FlightAssignment rows, then JOINs Flight
        for the details and Airport twice for the codes.
        """
        return self.conn.execute("""
            SELECT f.flight_id           AS "ID",
                   f.flight_number       AS "Flight",
                   o.iata_code           AS "From",
                   d.iata_code           AS "To",
                   f.departure_datetime  AS "Departs (UTC)",
                   f.arrival_datetime    AS "Arrives (UTC)",
                   f.status              AS "Status",
                   fa.role               AS "Role"
            FROM FlightAssignment AS fa
            JOIN Flight  AS f ON f.flight_id  = fa.flight_id
            JOIN Airport AS o ON o.airport_id = f.origin_id
            JOIN Airport AS d ON d.airport_id = f.destination_id
            WHERE fa.pilot_id = ?
            ORDER BY f.departure_datetime
        """, (pilot_id,)).fetchall()


# =====================================================================
# Airport table (the brief's "destinations")
# =====================================================================

class AirportRepository:

    def __init__(self, conn):
        self.conn = conn

    def get(self, code):
        """Return one airport by its IATA code, or None if it doesn't exist."""
        return self.conn.execute(
            "SELECT * FROM Airport WHERE iata_code = ?", (code,)
        ).fetchone()

    def list_all(self):
        """Every airport, ready to display."""
        return self.conn.execute("""
            SELECT iata_code     AS "Code",
                   airport_name  AS "Airport",
                   city          AS "City",
                   country       AS "Country",
                   timezone      AS "Timezone"
            FROM Airport
            ORDER BY iata_code
        """).fetchall()

    def add(self, code, name, city, country, timezone):
        """Insert a new airport."""
        self.conn.execute("""
            INSERT INTO Airport (iata_code, airport_name, city, country, timezone)
            VALUES (?, ?, ?, ?, ?)
        """, (code, name, city, country, timezone))
        self.conn.commit()

    def update(self, code, name, city, country, timezone):
        """Change an airport's details (the code itself stays the same)."""
        self.conn.execute("""
            UPDATE Airport
            SET airport_name = ?, city = ?, country = ?, timezone = ?
            WHERE iata_code = ?
        """, (name, city, country, timezone, code))
        self.conn.commit()

    def delete(self, code):
        """Delete an airport. ON DELETE RESTRICT in the schema blocks this
        (IntegrityError) if any flight uses it as origin or destination."""
        self.conn.execute("DELETE FROM Airport WHERE iata_code = ?", (code,))
        self.conn.commit()


# =====================================================================
# Summary reports (read-only queries across several tables)
# =====================================================================

class ReportRepository:

    def __init__(self, conn):
        self.conn = conn

    def flights_per_destination(self):
        """Number of flights to each destination.

        LEFT JOIN keeps airports with no flights; a plain JOIN would drop
        them. COUNT(f.flight_id) counts only real matches, so those
        airports show 0 rather than 1.
        """
        return self.conn.execute("""
            SELECT a.iata_code         AS "Code",
                   a.city              AS "City",
                   COUNT(f.flight_id)  AS "Flights"
            FROM Airport AS a
            LEFT JOIN Flight AS f ON f.destination_id = a.airport_id
            GROUP BY a.airport_id
            ORDER BY COUNT(f.flight_id) DESC, a.iata_code
        """).fetchall()

    def flights_per_pilot(self):
        """Number of flights assigned to each pilot (0 for none, via LEFT JOIN)."""
        return self.conn.execute("""
            SELECT p.first_name || ' ' || p.last_name  AS "Pilot",
                   p.rank                              AS "Rank",
                   COUNT(fa.flight_id)                 AS "Flights"
            FROM Pilot AS p
            LEFT JOIN FlightAssignment AS fa ON fa.pilot_id = p.pilot_id
            GROUP BY p.pilot_id
            ORDER BY COUNT(fa.flight_id) DESC, p.last_name
        """).fetchall()

    def hours_per_pilot(self):
        """Total flight hours per pilot, excluding cancelled flights.

        julianday() turns a date-time into a number of days, so
        (arrival - departure) is the length in days and * 24 makes it
        hours. ROUND(..., 2) keeps two decimal places (with one, tiny
        rounding errors could turn 3.75 into 3.7). Hours are calculated,
        not stored, so they always match the flight times.
        """
        return self.conn.execute("""
            SELECT p.first_name || ' ' || p.last_name  AS "Pilot",
                   ROUND(SUM(julianday(f.arrival_datetime)
                             - julianday(f.departure_datetime)) * 24, 2) AS "Hours"
            FROM Pilot AS p
            JOIN FlightAssignment AS fa ON fa.pilot_id = p.pilot_id
            JOIN Flight AS f ON f.flight_id = fa.flight_id
            WHERE f.status <> 'Cancelled'
            GROUP BY p.pilot_id
            ORDER BY "Hours" DESC
        """).fetchall()

    def busiest_airports(self):
        """Airports ranked by departures + arrivals.

        The inner query counts each airport's departures and arrivals
        with two small subqueries; the outer query adds them up and sorts.
        """
        return self.conn.execute("""
            SELECT code AS "Code", city AS "City",
                   departures AS "Departures", arrivals AS "Arrivals",
                   departures + arrivals AS "Total"
            FROM (
                SELECT a.iata_code AS code,
                       a.city      AS city,
                       (SELECT COUNT(*) FROM Flight AS f WHERE f.origin_id = a.airport_id)      AS departures,
                       (SELECT COUNT(*) FROM Flight AS f WHERE f.destination_id = a.airport_id) AS arrivals
                FROM Airport AS a
            )
            WHERE departures + arrivals > 0
            ORDER BY departures + arrivals DESC, code
        """).fetchall()

    def pilots_without_flights(self):
        """Pilots with no assignments: LEFT JOIN, then keep only pilots
        where no matching FlightAssignment row was found (NULL)."""
        return self.conn.execute("""
            SELECT p.pilot_id                          AS "ID",
                   p.first_name || ' ' || p.last_name  AS "Pilot",
                   p.rank                              AS "Rank"
            FROM Pilot AS p
            LEFT JOIN FlightAssignment AS fa ON fa.pilot_id = p.pilot_id
            WHERE fa.pilot_id IS NULL
        """).fetchall()

    def flights_without_full_crew(self):
        """Flights with fewer than 2 pilots, ignoring cancelled flights.

        WHERE filters rows before they are counted; HAVING filters the
        groups after counting.
        """
        return self.conn.execute("""
            SELECT f.flight_id           AS "ID",
                   f.flight_number       AS "Flight",
                   f.departure_datetime  AS "Departs (UTC)",
                   f.status              AS "Status",
                   COUNT(fa.pilot_id)    AS "Pilots"
            FROM Flight AS f
            LEFT JOIN FlightAssignment AS fa ON fa.flight_id = f.flight_id
            WHERE f.status <> 'Cancelled'
            GROUP BY f.flight_id
            HAVING COUNT(fa.pilot_id) < 2
            ORDER BY f.departure_datetime
        """).fetchall()
