# Database schema

## Table: deliveries (main table — one row per ball)

| Column | Type | Description |
|--------|------|-------------|
| match_id | TEXT | Match identifier |
| innings_num | INT | 1, 2, 3, 4 |
| over_num | INT | 0-indexed (0 = 1st over, 5 = 6th over) |
| batting_team | TEXT | Team batting this innings |
| bowling_team | TEXT | Team bowling |
| batter | TEXT | Striker (Cricsheet name e.g. V Kohli) |
| non_striker | TEXT | Partner at other end (partnership queries) |
| bowler | TEXT | Bowler (e.g. JJ Bumrah) |
| runs_batter | INT | Runs off the bat |
| runs_extras | INT | Extra runs on this ball |
| runs_total | INT | Total runs (for economy / conceded) |
| is_wide | BOOLEAN | True if wide — exclude from balls faced count |
| is_wicket | BOOLEAN | True if wicket fell |
| dismissal_kind | TEXT | bowled, caught, lbw, etc. |
| player_out | TEXT | Who got out |
| match_type | TEXT | ODI, Test, T20, IPL, etc. |
| match_date | DATE | Match date |

Legal ball for batter: `NOT is_wide`
Legal ball for bowler economy: usually all balls except some extras rules; use `NOT is_wide` for simplicity.

## Table: matches

match_id, match_date, match_type, gender, team1, team2, venue

## Table: players

player_name (PRIMARY KEY), player_id

## Table: innings_powerplays (raw Cricsheet only — optional join)

match_id, innings_num, pp_from, pp_to, pp_type (mandatory, batting, fielding)

Do NOT assume is_powerplay on deliveries. Compute phases from over_num:

- T20 powerplay (first 6 overs): match_type = 'T20' AND over_num <= 5
- ODI PP1 (first 10 overs): match_type = 'ODI' AND over_num <= 9
- ODI PP3 (last 10 overs): match_type = 'ODI' AND over_num >= 40
- ODI batting PP2: JOIN innings_powerplays WHERE pp_type = 'batting'

## Table: deliveries — T20 death overs

Death overs in T20 (overs 17-20): over_num >= 15 (0-indexed)
