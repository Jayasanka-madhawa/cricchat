# Data coverage (Cricsheet)

## Source
Ball-by-ball data from [Cricsheet](https://cricsheet.org/) (`all_json.zip`).

## Date range
- International men's matches: mostly **from 2003 onward** (varies slightly by format)
- Players who debuted **after 2003** (e.g. Kane Williamson, 2010) **should have data** in this database
- Career totals here are **only from matches in the dataset** — not all-time ICC records that include pre-2003 play

## When a user says "no data" for a recent player
1. Look up the exact Cricsheet name in `players` (e.g. Kane Williamson → **KS Williamson**)
2. Query `deliveries` with that exact name — do NOT use display names like "Kane Williamson"
3. If rows exist, report runs by `match_type` — the player IS in the database

## Common name mismatches
- Kane Williamson → KS Williamson
- Virat Kohli → V Kohli
- Use `player_aliases.md` and `SELECT player_name FROM players WHERE player_name ILIKE '%partial%';`

## What we cannot answer from this DB alone
- All-time career records before ~2003
- Live scores, future fixtures, opinions ("who is the GOAT")
