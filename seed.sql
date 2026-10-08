-- =====================================================================
-- Flight Management Database - sample data
-- Run AFTER schema.sql (schema.sql drops and recreates the tables,
-- so schema + seed together always rebuild the database from scratch).
--
-- Assumptions (to state in the report)
--   * The airline ("Skybridge Air", flight prefix SB) and all pilots are
--     fictional. Emails use the reserved .example domain (RFC 2606).
--   * Airports are real; IATA codes and IANA timezones are accurate.
--   * All times are UTC. Statuses are a snapshot as of 08 Oct 2026 and are
--     maintained by staff - the database does not change them automatically.
--   * When a flight is Delayed, departure/arrival_datetime hold the current
--     expected times; the status flags that they differ from the original plan.
--   * IDs are given explicitly so FlightAssignment rows are easy to read.
--     New rows added later through the app get max(id) + 1 automatically.
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- Airport (12 rows)
-- FRA and DXB have no flights at all, and MAN and EDI are only used as
-- origins. All four show up with a count of 0 in the "flights per
-- destination" summary, which only works with a LEFT JOIN (an INNER JOIN
-- would drop them).
-- ---------------------------------------------------------------------
INSERT INTO Airport (airport_id, iata_code, airport_name, city, country, timezone) VALUES
    ( 1, 'LHR', 'London Heathrow Airport',               'London',     'United Kingdom',       'Europe/London'),
    ( 2, 'MAN', 'Manchester Airport',                    'Manchester', 'United Kingdom',       'Europe/London'),
    ( 3, 'EDI', 'Edinburgh Airport',                     'Edinburgh',  'United Kingdom',       'Europe/London'),
    ( 4, 'DUB', 'Dublin Airport',                        'Dublin',     'Ireland',              'Europe/Dublin'),
    ( 5, 'CDG', 'Paris Charles de Gaulle Airport',       'Paris',      'France',               'Europe/Paris'),
    ( 6, 'AMS', 'Amsterdam Airport Schiphol',            'Amsterdam',  'Netherlands',          'Europe/Amsterdam'),
    ( 7, 'FRA', 'Frankfurt Airport',                     'Frankfurt',  'Germany',              'Europe/Berlin'),
    ( 8, 'MUC', 'Munich Airport',                        'Munich',     'Germany',              'Europe/Berlin'),
    ( 9, 'MAD', 'Madrid-Barajas Airport',                'Madrid',     'Spain',                'Europe/Madrid'),
    (10, 'FCO', 'Rome Fiumicino Airport',                'Rome',       'Italy',                'Europe/Rome'),
    (11, 'JFK', 'John F. Kennedy International Airport', 'New York',   'United States',        'America/New_York'),
    (12, 'DXB', 'Dubai International Airport',           'Dubai',      'United Arab Emirates', 'Asia/Dubai');

-- ---------------------------------------------------------------------
-- Pilot (12 rows: 6 Captains, 6 First Officers)
-- O'Connor contains an apostrophe: in SQL a quote inside a string is
-- written twice (''). The Python app avoids this problem entirely by
-- using ? placeholders.
-- Oliver Bennett (12) is a new hire with no assignments, for the
-- "pilots with no assignments" LEFT JOIN query.
-- ---------------------------------------------------------------------
INSERT INTO Pilot (pilot_id, first_name, last_name, licence_number, rank, email, hire_date) VALUES
    ( 1, 'Sarah',  'Mitchell', 'UK-FCL-10231', 'Captain',       'sarah.mitchell@skybridge.example', '2012-03-15'),
    ( 2, 'James',  'O''Connor','UK-FCL-10544', 'Captain',       'james.oconnor@skybridge.example',  '2014-06-02'),
    ( 3, 'Priya',  'Sharma',   'UK-FCL-11087', 'Captain',       'priya.sharma@skybridge.example',   '2015-09-21'),
    ( 4, 'Daniel', 'Weber',    'UK-FCL-09872', 'Captain',       'daniel.weber@skybridge.example',   '2011-01-10'),
    ( 5, 'Elena',  'Rossi',    'UK-FCL-11650', 'Captain',       'elena.rossi@skybridge.example',    '2017-04-03'),
    ( 6, 'Tom',    'Hughes',   'UK-FCL-12318', 'First Officer', 'tom.hughes@skybridge.example',     '2019-07-29'),
    ( 7, 'Aisha',  'Khan',     'UK-FCL-12764', 'First Officer', 'aisha.khan@skybridge.example',     '2020-02-17'),
    ( 8, 'Lukas',  'Becker',   'UK-FCL-13105', 'First Officer', 'lukas.becker@skybridge.example',   '2021-10-04'),
    ( 9, 'Chloe',  'Martin',   'UK-FCL-13442', 'First Officer', 'chloe.martin@skybridge.example',   '2022-05-16'),
    (10, 'Marco',  'Bianchi',  'UK-FCL-13980', 'First Officer', 'marco.bianchi@skybridge.example',  '2023-03-06'),
    (11, 'Grace',  'Thompson', 'UK-FCL-11233', 'Captain',       'grace.thompson@skybridge.example', '2016-11-14'),
    (12, 'Oliver', 'Bennett',  'UK-FCL-14501', 'First Officer', 'oliver.bennett@skybridge.example', '2026-09-01');

-- ---------------------------------------------------------------------
-- Flight (12 rows)
-- Covers all five statuses. Points worth noticing:
--   * SB101 appears twice on different days -> allowed by
--     UNIQUE (flight_number, departure_datetime).
--   * Out-and-back pairs (SB101/SB102, SB301/SB302) let one crew fly both
--     legs, which makes the pilot-schedule view realistic.
--   * Flight 12 departs on the 10th and lands on the 11th: the text
--     comparison arrival > departure still holds because ISO strings
--     sort in date order.
-- Columns: id, number, origin, destination, departure, arrival, status
-- ---------------------------------------------------------------------
INSERT INTO Flight (flight_id, flight_number, origin_id, destination_id, departure_datetime, arrival_datetime, status) VALUES
    ( 1, 'SB101',  1,  5, '2026-10-06 07:00', '2026-10-06 08:15', 'Landed'),     -- LHR -> CDG
    ( 2, 'SB102',  5,  1, '2026-10-06 09:30', '2026-10-06 10:45', 'Landed'),     -- CDG -> LHR
    ( 3, 'SB201',  1, 11, '2026-10-07 10:00', '2026-10-07 18:00', 'Landed'),     -- LHR -> JFK
    ( 4, 'SB301',  1,  8, '2026-10-08 05:00', '2026-10-08 06:50', 'Departed'),   -- LHR -> MUC
    ( 5, 'SB401',  2,  6, '2026-10-08 06:45', '2026-10-08 08:00', 'Delayed'),    -- MAN -> AMS
    ( 6, 'SB501',  1,  9, '2026-10-08 08:00', '2026-10-08 10:20', 'Scheduled'),  -- LHR -> MAD
    ( 7, 'SB302',  8,  1, '2026-10-08 08:00', '2026-10-08 09:55', 'Scheduled'),  -- MUC -> LHR
    ( 8, 'SB601',  1, 10, '2026-10-09 07:15', '2026-10-09 09:45', 'Scheduled'),  -- LHR -> FCO
    ( 9, 'SB101',  1,  5, '2026-10-09 07:00', '2026-10-09 08:15', 'Scheduled'),  -- LHR -> CDG
    (10, 'SB701',  3,  1, '2026-10-09 12:00', '2026-10-09 13:25', 'Scheduled'),  -- EDI -> LHR
    (11, 'SB801',  1,  4, '2026-10-08 14:00', '2026-10-08 15:15', 'Cancelled'),  -- LHR -> DUB
    (12, 'SB202', 11,  1, '2026-10-10 22:00', '2026-10-11 05:00', 'Scheduled');  -- JFK -> LHR (overnight)

-- ---------------------------------------------------------------------
-- FlightAssignment (15 rows)
--   * Flights 1-7: full crew (Captain + First Officer)  -> 14 rows
--   * Flight 8:    Captain only (partly crewed)         ->  1 row
--   * Flights 9-12: no crew at all (incl. the cancelled flight)
-- Every role matches the pilot's rank, and no pilot is on two flights
-- whose times overlap. Seed data bypasses the Python checks, so these
-- rules were checked by hand (and by queries) rather than by the app.
-- Columns: flight_id, pilot_id, role
-- ---------------------------------------------------------------------
INSERT INTO FlightAssignment (flight_id, pilot_id, role) VALUES
    (1,  1, 'Captain'),        -- Mitchell, SB101 LHR->CDG
    (1,  6, 'First Officer'),  -- Hughes
    (2,  1, 'Captain'),        -- same crew flies the return SB102
    (2,  6, 'First Officer'),
    (3,  4, 'Captain'),        -- Weber, SB201 LHR->JFK
    (3,  8, 'First Officer'),  -- Becker
    (4,  3, 'Captain'),        -- Sharma, SB301 LHR->MUC
    (4,  7, 'First Officer'),  -- Khan
    (5,  2, 'Captain'),        -- O'Connor, SB401 MAN->AMS
    (5,  9, 'First Officer'),  -- Martin
    (6,  5, 'Captain'),        -- Rossi, SB501 LHR->MAD
    (6, 10, 'First Officer'),  -- Bianchi
    (7,  3, 'Captain'),        -- Sharma and Khan fly the return SB302
    (7,  7, 'First Officer'),
    (8, 11, 'Captain');        -- Thompson, SB601 LHR->FCO (no FO yet)
