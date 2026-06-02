-- CricChat schema — raw facts only
-- Stats (powerplay, death overs, balls to 50) are computed in SQL at query time.

CREATE TABLE matches (
    match_id    TEXT PRIMARY KEY,
    match_date  DATE,
    match_type  TEXT,
    gender      TEXT,
    team1       TEXT,
    team2       TEXT,
    venue       TEXT
);

CREATE TABLE players (
    player_name TEXT PRIMARY KEY,
    player_id   TEXT
);

-- One row per ball
CREATE TABLE deliveries (
    match_id        TEXT,
    innings_num     INT,
    over_num        INT,        -- 0-indexed (0 = 1st over) — use for phase filters
    batting_team    TEXT,
    bowling_team    TEXT,
    batter          TEXT,
    non_striker     TEXT,
    bowler          TEXT,
    runs_batter     INT,
    runs_extras     INT,
    runs_total      INT,
    is_wide         BOOLEAN,
    is_wicket       BOOLEAN,
    dismissal_kind  TEXT,
    player_out      TEXT,
    match_type      TEXT,
    match_date      DATE
);

-- Raw Cricsheet powerplay blocks (only when present in JSON — not forced)
CREATE TABLE innings_powerplays (
    match_id     TEXT,
    innings_num  INT,
    pp_from      TEXT,          -- e.g. "0.1"
    pp_to        TEXT,          -- e.g. "5.6"
    pp_type      TEXT           -- mandatory, batting, fielding
);

-- Phase filters (computed at query time, NOT stored):
--   T20 powerplay (1st 6 overs) : match_type = 'T20' AND over_num <= 5
--   ODI PP1 (1st 10 overs)      : match_type = 'ODI' AND over_num <= 9
--   ODI PP3 (last 10 overs)     : match_type = 'ODI' AND over_num >= 40
--   ODI batting PP2             : JOIN innings_powerplays WHERE pp_type = 'batting'
