# SQL examples — question to query

## Example 1: Kohli ODI strike rate (career — all overs, no powerplay filter)
Question: What is Kohli's strike rate in ODIs?
```sql
SELECT ROUND(100.0 * SUM(runs_batter) /
       NULLIF(COUNT(*) FILTER (WHERE NOT is_wide), 0), 1) AS strike_rate
FROM deliveries
WHERE batter = 'V Kohli' AND match_type = 'ODI';
```

## Example 2: Bumrah T20 economy in first 6 overs
Question: Bumrah economy in powerplay T20 (first 6 overs)
```sql
SELECT ROUND(SUM(runs_total)::numeric /
       (COUNT(*) FILTER (WHERE NOT is_wide) / 6.0), 2) AS economy
FROM deliveries
WHERE bowler = 'JJ Bumrah'
  AND match_type = 'T20'
  AND over_num <= 5;
```

## Example 3: Bumrah T20 bowling average in first 6 overs
Question: Bumrah bowling average in T20 powerplay
```sql
SELECT ROUND(SUM(runs_total)::numeric /
       NULLIF(COUNT(*) FILTER (WHERE is_wicket), 0), 1) AS bowling_avg
FROM deliveries
WHERE bowler = 'JJ Bumrah'
  AND match_type = 'T20'
  AND over_num <= 5;
```

## Example 4: Sangakkara strike rate when Mahela at other end
Question: Sangakkara strike rate when Mahela is non-striker
```sql
SELECT ROUND(100.0 * SUM(runs_batter) /
       NULLIF(COUNT(*) FILTER (WHERE NOT is_wide), 0), 1) AS strike_rate
FROM deliveries
WHERE batter = 'KC Sangakkara'
  AND non_striker = 'DPMD Jayawardene';
```

## Example 5: Kohli ODI total runs
Question: How many ODI runs has Kohli scored?
```sql
SELECT SUM(runs_batter) AS total_runs
FROM deliveries
WHERE batter = 'V Kohli' AND match_type = 'ODI';
```

## Example 6: Maxwell T20 strike rate
Question: Maxwell strike rate in T20
```sql
SELECT ROUND(100.0 * SUM(runs_batter) /
       NULLIF(COUNT(*) FILTER (WHERE NOT is_wide), 0), 1) AS strike_rate
FROM deliveries
WHERE batter = 'GJ Maxwell' AND match_type = 'T20';
```

## Example 7: Top run scorers in IPL 2023
Question: Most runs in IPL 2023
```sql
SELECT batter, SUM(runs_batter) AS runs
FROM deliveries
WHERE match_type = 'IPL'
  AND match_date >= '2023-01-01'
  AND match_date < '2024-01-01'
GROUP BY batter
ORDER BY runs DESC
LIMIT 10;
```

## Example 8: Death overs runs in T20 (overs 17-20)
Question: Most runs in death overs T20
```sql
SELECT batter, SUM(runs_batter) AS runs
FROM deliveries
WHERE match_type = 'T20' AND over_num >= 15
GROUP BY batter
ORDER BY runs DESC
LIMIT 10;
```

## Example 9: Head to head batter vs bowler
Question: Kohli runs against Anderson in Tests
```sql
SELECT SUM(runs_batter) AS runs,
       COUNT(*) FILTER (WHERE NOT is_wide) AS balls
FROM deliveries
WHERE batter = 'V Kohli'
  AND bowler = 'JM Anderson'
  AND match_type = 'Test';
```

## Example 10: ODI PP1 bowling economy (first 10 overs)
Question: Bumrah economy in first 10 overs of ODI
```sql
SELECT ROUND(SUM(runs_total)::numeric /
       (COUNT(*) FILTER (WHERE NOT is_wide) / 6.0), 2) AS economy
FROM deliveries
WHERE bowler = 'JJ Bumrah'
  AND match_type = 'ODI'
  AND over_num <= 9;
```

## Example 11: Find player name
Question: What is the Cricsheet name for Kohli?
```sql
SELECT player_name FROM players WHERE player_name ILIKE '%kohli%';
```

## Example 12: Balls to 50 in an innings (window function)
Question: Kohli balls to reach 50 in each ODI innings
```sql
WITH balls AS (
    SELECT match_id, innings_num,
           ROW_NUMBER() OVER (PARTITION BY match_id, innings_num ORDER BY over_num) AS ball_num,
           SUM(runs_batter) OVER (
               PARTITION BY match_id, innings_num ORDER BY over_num
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
           ) AS cumulative_runs
    FROM deliveries
    WHERE batter = 'V Kohli' AND match_type = 'ODI' AND NOT is_wide
)
SELECT match_id, MIN(ball_num) AS balls_to_50
FROM balls WHERE cumulative_runs >= 50
GROUP BY match_id, innings_num;
```

## Example 13: Centuries for a batter
Question: How many centuries has Kusal Mendis scored?
```sql
WITH innings AS (
    SELECT match_id, innings_num, SUM(runs_batter) AS runs
    FROM deliveries
    WHERE batter = 'MDKJ Mendis'
    GROUP BY match_id, innings_num
)
SELECT COUNT(*) AS centuries
FROM innings
WHERE runs >= 100;
```

## Example 14: Find player by partial name
Question: What is the Cricsheet name for Kusal Mendis?
```sql
SELECT player_name FROM players
WHERE player_name ILIKE '%mendis%' AND player_name ILIKE '%k%';
```

## Example 15: Half-centuries (50–99, excluding 100+)
Question: How many half centuries has Kusal Mendis scored?
```sql
WITH innings AS (
    SELECT match_id, innings_num, SUM(runs_batter) AS runs
    FROM deliveries
    WHERE batter = 'MDKJ Mendis'
    GROUP BY match_id, innings_num
)
SELECT COUNT(*) AS half_centuries
FROM innings
WHERE runs >= 50 AND runs < 100;
```
