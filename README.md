# CS-353-Sports-League-and-Player-Management-System

## Dev Environment
### Setup
Commands to run:

```bash
docker compose -f docker-compose.yml --build
docker compose up --build
```

## Teardown
Commands to run:
```bash
docker compose down
```

If you want to start from init.sql (delete you changes for the db volume):
```bash
docker compose down -v
```

## Database Views & Triggers
- `AllMatchInfo`: Matches with optional season/tournament context and tournament metadata.
- `AllSeasonMatchInfo`: Matches joined to their season and league.
- `AllTournamentMatchInfo`: Tournament matches with round info and tournament name/size.
- `AllEmploymentInfo`: Employment records joined through Employed → Employment → Team → Employee.
- `PlayerStatsAll`: Aggregate per-player stats across all matches (appearances, goals, penalties, minutes, cards, saves, passes, assists).
- `PlayerSeasonStats`: Aggregate per-player stats per league season.
- `PlayerTournamentStats`: Aggregate per-player stats per tournament.
- `RefereeMatchView`: All referee assignments with competition name, home/away teams, and a flag for league vs tournament.
- Trigger `trg_fill_parent_match` (function `fill_parent_match`): when a tournament match’s winner is set, auto-creates the parent round match and links it into the bracket.
- Trigger `play_insert`/`play_update` (functions `update_all_after_play_insertion`/`update_all_after_play_update`): on Play insert/update for non-tournament matches, increment/decrement the home/away scores based on the player’s team at the match time (using `AllEmploymentInfo`).
- Trigger `match_update` (function `update_match_winner`): on Match update for non-tournament matches, sets `WinnerTeam` based on the current scores.

## Notes
- All database interactions are implemented with raw SQL per project specification; no ORM is used.
