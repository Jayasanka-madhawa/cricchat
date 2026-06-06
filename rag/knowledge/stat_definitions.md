# Cricket stat definitions (SQL formulas)

## Batting strike rate
100 * SUM(runs_batter) / COUNT(*) FILTER (WHERE NOT is_wide)

## Batting average
SUM(runs_batter) / COUNT(DISTINCT (match_id, innings_num))  -- per innings, need dismissal logic for proper avg

Simple innings count for runs:
SUM(runs_batter) grouped by batter, match_type

## Balls faced
COUNT(*) FILTER (WHERE NOT is_wide) WHERE batter = 'X'

## Centuries (100+ in an innings)
Sum runs_batter per (match_id, innings_num), then COUNT innings WHERE total >= 100.
NOT runs_total = 100 on one ball — that is wrong.

```sql
WITH innings AS (
  SELECT match_id, innings_num, SUM(runs_batter) AS runs
  FROM deliveries WHERE batter = 'X'
  GROUP BY match_id, innings_num
)
SELECT COUNT(*) AS centuries FROM innings WHERE runs >= 100;
```

## Bowling economy (runs per over)
SUM(runs_total) / (COUNT(*) FILTER (WHERE NOT is_wide) / 6.0)

## Bowling average
SUM(runs_total) / NULLIF(COUNT(*) FILTER (WHERE is_wicket), 0)

## Bowling strike rate
COUNT(*) FILTER (WHERE NOT is_wide) / NULLIF(COUNT(*) FILTER (WHERE is_wicket), 0)

## Partnership — batter SR when specific non-striker at other end
Filter: batter = 'A' AND non_striker = 'B'
Then batting strike rate formula on those rows only.

## Partnership — either direction (both batters together)
(batter = 'A' AND non_striker = 'B') OR (batter = 'B' AND non_striker = 'A')

## Cricsheet player names
Always use exact names from players table. Examples:
- V Kohli (not Virat Kohli)
- JJ Bumrah (not Bumrah)
- KC Sangakkara
- DPMD Jayawardene (Mahela)
- GJ Maxwell
- LRPL Taylor (Ross Taylor)

## over_num is 0-indexed
over_num 0 = 1st over. First 6 overs T20 powerplay = over_num <= 5.

## When to filter by over_num
- "strike rate in ODI" / "economy in T20" = ALL overs — do NOT filter over_num
- Only filter when user says powerplay, first 6/10 overs, death overs, etc.
