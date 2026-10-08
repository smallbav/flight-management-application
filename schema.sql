-- =====================================================================
-- Flight Management Database - schema
-- Target: SQLite 3 (via Python's sqlite3 module)
--
-- Conventions
--   * All date-times are stored as TEXT in ISO-8601 'YYYY-MM-DD HH:MM', in UTC.
--     Fixed-width ISO strings sort and compare correctly as text.
--   * Foreign keys are only enforced if every connection runs
--     PRAGMA foreign_keys = ON;
-- =====================================================================

PRAGMA foreign_keys = ON;

-- Drop in reverse dependency order so the script can be re-run cleanly
DROP TABLE IF EXISTS FlightAssignment;
DROP TABLE IF EXISTS Flight;
DROP TABLE IF EXISTS Pilot;
DROP TABLE IF EXISTS Airport;

-- ---------------------------------------------------------------------
-- Airport: an airport the airline flies from or to.
-- Holds the brief's "destination" information; named Airport because
-- each row can be referenced as a flight's origin OR its destination.
-- ---------------------------------------------------------------------
CREATE TABLE Airport (
    airport_id      INTEGER PRIMARY KEY,                 -- surrogate key (alias of ROWID)
    iata_code       TEXT    NOT NULL UNIQUE
                            CHECK (iata_code GLOB '[A-Z][A-Z][A-Z]'),
    airport_name    TEXT    NOT NULL,
    city            TEXT    NOT NULL,
    country         TEXT    NOT NULL,
    timezone        TEXT    NOT NULL                     -- IANA name, e.g. 'Europe/London'
);

-- ---------------------------------------------------------------------
-- Pilot: a member of flight crew who can be assigned to flights
-- ---------------------------------------------------------------------
CREATE TABLE Pilot (
    pilot_id        INTEGER PRIMARY KEY,
    first_name      TEXT    NOT NULL,
    last_name       TEXT    NOT NULL,
    licence_number  TEXT    NOT NULL UNIQUE,
    rank            TEXT    NOT NULL
                            CHECK (rank IN ('Captain', 'First Officer')),
    email           TEXT    NOT NULL UNIQUE,
    hire_date       TEXT    NOT NULL
                            CHECK (date(hire_date) IS hire_date)   -- valid 'YYYY-MM-DD'
);

-- ---------------------------------------------------------------------
-- Flight: one scheduled operation of a flight number on a given date-time
-- ---------------------------------------------------------------------
CREATE TABLE Flight (
    flight_id           INTEGER PRIMARY KEY,
    flight_number       TEXT    NOT NULL,                -- e.g. 'BA117'; repeats daily
    origin_id           INTEGER NOT NULL                 -- FK1: departure airport
                                REFERENCES Airport (airport_id) ON DELETE RESTRICT,
    destination_id      INTEGER NOT NULL                 -- FK2: arrival airport
                                REFERENCES Airport (airport_id) ON DELETE RESTRICT,
    departure_datetime  TEXT    NOT NULL
                                CHECK (strftime('%Y-%m-%d %H:%M', departure_datetime) IS departure_datetime),
    arrival_datetime    TEXT    NOT NULL
                                CHECK (strftime('%Y-%m-%d %H:%M', arrival_datetime) IS arrival_datetime),
    status              TEXT    NOT NULL DEFAULT 'Scheduled'
                                CHECK (status IN ('Scheduled', 'Delayed', 'Departed', 'Landed', 'Cancelled')),

    CHECK (origin_id <> destination_id),
    CHECK (arrival_datetime > departure_datetime),
    UNIQUE (flight_number, departure_datetime)           -- same flight number can't depart twice at once
);

-- ---------------------------------------------------------------------
-- FlightAssignment: resolves the many-to-many between Pilot and Flight
-- ---------------------------------------------------------------------
CREATE TABLE FlightAssignment (
    flight_id   INTEGER NOT NULL                         -- FK1
                        REFERENCES Flight (flight_id) ON DELETE CASCADE,
    pilot_id    INTEGER NOT NULL                         -- FK2
                        REFERENCES Pilot (pilot_id) ON DELETE RESTRICT,
    role        TEXT    NOT NULL
                        CHECK (role IN ('Captain', 'First Officer')),

    PRIMARY KEY (flight_id, pilot_id),                   -- a pilot appears once per flight
    UNIQUE (flight_id, role)                             -- at most one Captain and one First Officer,
                                                         -- so a flight has 0..2 pilots
);

-- ---------------------------------------------------------------------
-- Indexes: SQLite does not index foreign keys automatically.
-- These support the Task 2 filters (destination, status, date) and the
-- pilot-schedule / flights-per-pilot queries.
-- ---------------------------------------------------------------------
CREATE INDEX idx_flight_destination ON Flight (destination_id);
CREATE INDEX idx_flight_origin      ON Flight (origin_id);
CREATE INDEX idx_flight_departure   ON Flight (departure_datetime);
CREATE INDEX idx_flight_status      ON Flight (status);
CREATE INDEX idx_assignment_pilot   ON FlightAssignment (pilot_id);
