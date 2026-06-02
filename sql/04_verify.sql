-- Phase 1 verification — raw data, stats computed in SQL

\echo '=== Row counts ==='
SELECT 'matches' AS tbl, COUNT(*) FROM matches
UNION ALL SELECT 'players', COUNT(*) FROM players
UNION ALL SELECT 'deliveries', COUNT(*) FROM deliveries
UNION ALL SELECT 'innings_powerplays', COUNT(*) FROM innings_powerplays;

\echo ''
\echo '=== 1. Kohli ODI strike rate ==='
SELECT ROUND(100.0 * SUM(runs_batter) /
       NULLIF(COUNT(*) FILTER (WHERE NOT is_wide), 0), 1) AS strike_rate
FROM deliveries
WHERE batter = 'V Kohli' AND match_type = 'ODI';

\echo ''
\echo '=== 2. Bumrah T20 first 6 overs — economy (computed from over_num) ==='
SELECT
    COUNT(*) FILTER (WHERE NOT is_wide) AS balls,
    SUM(runs_total) AS runs_conceded,
    ROUND(SUM(runs_total)::numeric / (COUNT(*) FILTER (WHERE NOT is_wide) / 6.0), 2) AS economy
FROM deliveries
WHERE bowler = 'JJ Bumrah'
  AND match_type = 'T20'
  AND over_num <= 5;

\echo ''
\echo '=== 3. Sangakkara SR when Mahela at other end ==='
SELECT ROUND(100.0 * SUM(runs_batter) /
       NULLIF(COUNT(*) FILTER (WHERE NOT is_wide), 0), 1) AS strike_rate
FROM deliveries
WHERE batter = 'KC Sangakkara'
  AND non_striker = 'DPMD Jayawardene';

\echo ''
\echo '=== 4. Raw Cricsheet powerplay blocks (sample) ==='
SELECT match_id, innings_num, pp_from, pp_to, pp_type
FROM innings_powerplays
LIMIT 5;

\echo ''
\echo '=== 5. ODI PP1 only — first 10 overs (over_num 0-9) ==='
SELECT COUNT(*) AS balls
FROM deliveries
WHERE match_type = 'ODI' AND over_num <= 9;
