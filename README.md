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

## User Roles & Functionalities

### Superadmin
- **Tournament Management**: Create tournaments with bracket generation and assign tournament admins
- **League Management**: Create leagues with multiple seasons, assign teams, and assign admins to seasons
- **Admin Assignment**: Assign admins to all seasons at once or individually per season
- **Delete Operations**: Delete tournaments, leagues, and seasons with cascading cleanup

### Admin / Tournament Admin
- **Tournament Management**: View assigned tournaments and their bracket structures
- **League Management**: View assigned leagues with teams, seasons, and matches
- **Team Management**: Add/remove teams from leagues they manage
- **Match Creation**: Create seasonal matches for leagues with validation (team availability, date conflicts)
- **Referee Assignment**: Assign referees to tournament and league matches
- **Match Locking**: Lock/unlock league matches to prevent modifications
- **Match Filtering**: Filter all matches by season year (year only), league, or tournament
- **Reports**: Generate and download player reports, league standings, and attendance reports as PDFs

### Team Owner
- View owned teams and their rosters
- Manage team information

### Coach
- View team information
- Manage training and player development

### Player
- View personal statistics and match history
- View team and match information

### Referee
- View assigned matches
- Access match details for officiating
