# Player name aliases (user input → Cricsheet name)

kohli → V Kohli
virat → V Kohli
virat kohli → V Kohli

bumrah → JJ Bumrah
j bumrah → JJ Bumrah

sangakkara → KC Sangakkara
sanga → KC Sangakkara

mahela → DPMD Jayawardene
jayawardene → DPMD Jayawardene
mahela jayawardene → DPMD Jayawardene

maxwell → GJ Maxwell
glenn maxwell → GJ Maxwell

ross taylor → LRPL Taylor
taylor → LRPL Taylor

dhoni → MS Dhoni
rohit → RG Sharma
rohit sharma → RG Sharma

smith → SPD Smith
steve smith → SPD Smith

root → JE Root
williamson → KS Williamson
babar → Babar Azam

anderson → JM Anderson
jadeja → RA Jadeja
bumrah → JJ Bumrah

kusal mendis → MDKJ Mendis
mendis → MDKJ Mendis

When unsure, search: SELECT player_name FROM players WHERE player_name ILIKE '%kohli%';
