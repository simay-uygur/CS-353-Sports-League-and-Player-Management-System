# this is a mediator file that talks with the database and does common database tasks 
import math
import random
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from collections import defaultdict

import os

from db import get_connection

def execute_query(query, params=None):
    conn = None
    cursor = None
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        if query.strip().upper().startswith("SELECT"):
            result = cursor.fetchall()
        else:
            conn.commit()
            result = None
        return result
    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
def fetch_one(query, params=None):
    conn = None
    cursor = None
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        return result
    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
            
            
def fetch_all_teams():
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT teamid,
                       teamname
                FROM Team
                ORDER BY teamname;
                """
            )
            return cur.fetchall()
    finally:
        conn.close()
        
        
def fetch_all_players():
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT playerid,
                       firstname,
                       lastname
                FROM Player
                ORDER BY lastname, firstname;
                """
            )
            return cur.fetchall()
    finally:
        conn.close()
        
        
def fetch_matches_grouped(tournament_id):
    """
    Fetch tournament bracket with all rounds (including those without matches).
    Returns rounds grouped by level (for display).
    """
    
    
    def _round_level(round_no):
        if round_no <= 0:
            return 1
        return math.floor(math.log2(round_no)) + 1
  
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT r.roundno,
                       r.child1roundno,
                       r.child2roundno,
                       r.parentroundno,
                       m.matchid,
                       m.hometeamname,
                       m.awayteamname,
                       m.hometeamscore,
                       m.awayteamscore,
                       m.matchstartdatetime
                FROM Round r
                LEFT JOIN Match m ON r.t_matchid = m.matchid
                WHERE r.tournamentid = %s
                ORDER BY r.roundno;
                """,
                (tournament_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    grouped = defaultdict(list)
    for row in rows:
        level = _round_level(row["roundno"])
        grouped[level].append(row)

    return dict(sorted(grouped.items()))


def create_tournament_with_bracket(form_data, admin_id, moderator_ids=None):
    if not admin_id:
        raise ValueError("You must be signed in as an admin to create tournaments.")

    name = (form_data.get("tournament_name") or "").strip()
    if not name:
        raise ValueError("Tournament name is required.")

    start_date_str = (form_data.get("tournament_start_date") or "").strip()
    if not start_date_str:
        raise ValueError("Tournament start date is required.")
    
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD format.")

    team_ids = [int(tid) for tid in form_data.getlist("team_ids") if tid]
    size = len(team_ids)

    if size < 2:
        raise ValueError("Please select at least two teams for this tournament.")

    # Check if size is power of 2
    if (size & (size - 1)) != 0:
        raise ValueError("Please select a power of 2 number of teams (2, 4, 8, 16, etc.).")

    if len(set(team_ids)) != len(team_ids):
        raise ValueError("Each team can only be selected once.")

    moderator_ids = [int(mid) for mid in (moderator_ids or []) if mid]
    if not moderator_ids:
        moderator_ids = [admin_id]
    moderator_ids = list(dict.fromkeys(moderator_ids))

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                for moderator_id in moderator_ids:
                    _ensure_admin_record(cur, moderator_id)
                cur.execute(
                    """
                    INSERT INTO Tournament (Name, Size)
                    VALUES (%s, %s)
                    RETURNING TournamentID;
                    """,
                    (name, size),
                )
                tournament_id = cur.fetchone()[0]

                for moderator_id in moderator_ids:
                    cur.execute(
                        """
                        INSERT INTO TournamentModeration (T_ID, AdminID)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING;
                        """,
                        (tournament_id, moderator_id),
                    )

                leaf_match_ids = _build_bracket_tree(cur, tournament_id, team_ids, start_date)

        return {"tournament_id": tournament_id, "match_ids": leaf_match_ids}
    finally:
        conn.close()        
        
        
def _build_bracket_tree(cur, tournament_id, team_ids, start_date):
    """
    Build complete binary bracket tree in memory, then INSERT all at once.
    
    Steps:
    1. Validate team_count is power of 2
    2. Calculate tree depth (leaf level)
    3. Generate all RoundNo's with parent-child links (no DB yet)
    4. INSERT all rounds into DB (single transaction)
    5. CREATE matches ONLY for leaf rounds
    6. UPDATE leaf rounds with MatchID
    
    Tree structure:
    - Root: RoundNo=1, ParentRoundNo=NULL
    - Level L: 2^L nodes, RoundNo from 2^L to 2^L + (2^L - 1)
    - Leaves: depth level, team_count/2 nodes
    - Each leaf has exactly 1 match
    """
    team_count = len(team_ids)
    
    # Validate power of 2 (already done in _create_tournament_with_bracket, but be safe)
    if (team_count & (team_count - 1)) != 0:
        raise ValueError("Team count must be a power of 2.")
    
    # Calculate depth
    # depth = level of leaves
    # leaf count = 2^depth = team_count / 2
    # So depth = log2(team_count) - 1
    depth = int(math.log2(team_count)) - 1
    
    # Helper functions
    def get_round_no(level, index):
        """Convert (level, index) to RoundNo. RoundNo = 2^level + index."""
        return (1 << level) + index
    
    def get_children(level, index):
        """Get (child1_round_no, child2_round_no) for node at (level, index)."""
        if level == depth:
            # Leaves have no children
            return None, None
        child_level = level + 1
        child1_no = get_round_no(child_level, index * 2)
        child2_no = get_round_no(child_level, index * 2 + 1)
        return child1_no, child2_no
    
    def get_parent(level, index):
        """Get parent_round_no for node at (level, index)."""
        if level == 0:
            # Root has no parent
            return None
        parent_level = level - 1
        parent_index = index // 2
        return get_round_no(parent_level, parent_index)
    
    # Generate all rounds in memory (no DB access yet)
    rounds_to_insert = []  # List of tuples: (tournament_id, round_no, child1_no, child2_no, parent_no)
    
    for level in range(depth + 1):
        nodes_at_level = 1 << level  # 2^level
        for index in range(nodes_at_level):
            round_no = get_round_no(level, index)
            child1, child2 = get_children(level, index)
            parent = get_parent(level, index)
            
            rounds_to_insert.append((tournament_id, round_no, child1, child2, parent))
    
    # INSERT all rounds with links left NULL, then set them after all rows exist
    for tournament_id_val, round_no, child1_no, child2_no, parent_no in rounds_to_insert:
        cur.execute(
            """
            INSERT INTO Round (TournamentID, RoundNo, T_MatchID, Child1RoundNo, Child2RoundNo, ParentRoundNo)
            VALUES (%s, %s, NULL, NULL, NULL, NULL);
            """,
            (tournament_id_val, round_no),
        )

    for tournament_id_val, round_no, child1_no, child2_no, parent_no in rounds_to_insert:
        cur.execute(
            """
            UPDATE Round
            SET Child1RoundNo = %s,
                Child2RoundNo = %s,
                ParentRoundNo = %s
            WHERE TournamentID = %s AND RoundNo = %s;
            """,
            (child1_no, child2_no, parent_no, tournament_id_val, round_no),
        )
    
    # CREATE matches for leaf rounds only
    # Shuffle teams and pair them
    shuffled_ids = team_ids[:]
    random.shuffle(shuffled_ids)
    team_names = lookup_team_names(cur, team_ids)
    
    # Create pairs: (team0, team1), (team2, team3), ...
    leaf_pairs = [
        (shuffled_ids[i], shuffled_ids[i + 1])
        for i in range(0, len(shuffled_ids), 2)
    ]
    
    created_match_ids = []
    
    for leaf_index, (home_team_id, away_team_id) in enumerate(leaf_pairs):
        leaf_round_no = get_round_no(depth, leaf_index)
        
        home_team_name = team_names.get(home_team_id)
        away_team_name = team_names.get(away_team_id)
        if not home_team_name or not away_team_name:
            raise ValueError("One or more selected teams no longer exist.")
        
        # Match datetime: start_date + (leaf_index * 1 day), 19:00
        match_datetime = start_date + timedelta(days=leaf_index)
        match_datetime = match_datetime.replace(hour=19, minute=0, second=0)
        
        # INSERT Match
        cur.execute(
            """
            INSERT INTO Match (
                HomeTeamID,
                AwayTeamID,
                MatchStartDatetime,
                MatchEndDatetime,
                VenuePlayed,
                HomeTeamName,
                AwayTeamName,
                HomeTeamScore,
                AwayTeamScore,
                WinnerTeam,
                IsLocked
            )
            VALUES (%s, %s, %s, NULL, NULL, %s, %s, NULL, NULL, NULL, FALSE)
            RETURNING MatchID;
            """,
            (home_team_id, away_team_id, match_datetime, home_team_name, away_team_name),
        )
        match_id = cur.fetchone()[0]
        created_match_ids.append(match_id)
        
        # INSERT into TournamentMatch
        cur.execute(
            "INSERT INTO TournamentMatch (MatchID) VALUES (%s);",
            (match_id,),
        )
        
        # UPDATE leaf round with match ID
        cur.execute(
            """
            UPDATE Round
            SET T_MatchID = %s
            WHERE TournamentID = %s AND RoundNo = %s;
            """,
            (match_id, tournament_id, leaf_round_no),
        )
    
    return created_match_ids        
  
  
  
def lookup_team_names(cur, team_ids):
    if not team_ids:
        return {}
    cur.execute(
        """
        SELECT TeamID, TeamName
        FROM Team
        WHERE TeamID = ANY(%s);
        """,
        (team_ids,),
    )
    return {row[0]: row[1] for row in cur.fetchall()}
  
  
def fetch_tournaments(admin_id):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT t.tournamentid,
                       t.name,
                       t.size
                FROM Tournament t
                JOIN TournamentModeration tm ON t.tournamentid = tm.t_id
                WHERE tm.adminid = %s
                ORDER BY t.name;
                """,
                (admin_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def delete_tournament_and_matches(tournament_id):
    """
    Delete a tournament and its associated tournament matches (and their Match rows) safely.
    Orders deletes to avoid FK issues:
    - collect match IDs from rounds
    - delete TournamentMatch entries for those matches (cascades Round rows via FK)
    - delete the Match rows
    - delete the Tournament
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    WITH match_ids AS (
                        SELECT r.t_matchid AS matchid
                        FROM Round r
                        WHERE r.tournamentid = %s
                          AND r.t_matchid IS NOT NULL
                    ),
                    deleted_tm AS (
                        DELETE FROM TournamentMatch tm
                        USING match_ids m
                        WHERE tm.matchid = m.matchid
                        RETURNING tm.matchid
                    ),
                    deleted_matches AS (
                        DELETE FROM Match m
                        USING match_ids mi
                        WHERE m.matchid = mi.matchid
                        RETURNING m.matchid
                    )
                    DELETE FROM Tournament
                    WHERE tournamentid = %s;
                    """,
                    (tournament_id, tournament_id),
                )
    finally:
        conn.close()

        
def _insert_play_rows_for_match(match_id, include_tournament_matches=False):
    """
    Shared insertion logic to add Play rows for a match.
    If include_tournament_matches is False, tournament matches are ignored.
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT HomeTeamID, AwayTeamID, MatchStartDatetime
                    FROM Match
                    WHERE MatchID = %s;
                    """,
                    (match_id,),
                )
                row = cur.fetchone()
                if not row:
                    return 0

                home_team_id, away_team_id, match_time = row

                if not include_tournament_matches:
                    cur.execute(
                        "SELECT 1 FROM TournamentMatch WHERE MatchID = %s;",
                        (match_id,),
                    )
                    if cur.fetchone():
                        return 0

                cur.execute(
                    """
                    WITH active_players AS (
                        SELECT em.UsersID AS player_id
                        FROM Employed em
                        JOIN Employment e ON e.EmploymentID = em.EmploymentID
                        JOIN Player p ON p.UsersID = em.UsersID
                        WHERE em.TeamID IN (%s, %s)
                          AND e.StartDate <= %s
                          AND e.EndDate >= %s
                          AND COALESCE(LOWER(p.IsEligible), '') = 'eligible'
                    ), to_insert AS (
                        SELECT %s AS match_id, ap.player_id
                        FROM active_players ap
                        WHERE NOT EXISTS (
                            SELECT 1 FROM Play pl
                            WHERE pl.MatchID = %s AND pl.PlayerID = ap.player_id
                        )
                    )
                    INSERT INTO Play (MatchID, PlayerID)
                    SELECT match_id, player_id FROM to_insert;
                    """,
                    (
                        home_team_id,
                        away_team_id,
                        match_time,
                        match_time,
                        match_id,
                        match_id,
                    ),
                )
                return cur.rowcount
    finally:
        conn.close()


def create_plays_for_match_players(match_id):
    """
    For a given match, auto-insert Play rows for all players on the home and away teams
    whose employment is active at the match start time. Skips tournaments and existing plays.
    Returns the number of Play rows inserted.
    """
    return _insert_play_rows_for_match(match_id, include_tournament_matches=False)


def create_plays_for_match_players_on_insert(match_id):
    """
    Call immediately after inserting any match to add Play rows for all eligible players
    on the home and away teams at the match start time. Works for league and tournament matches.
    Returns the number of Play rows inserted.
    """
    return _insert_play_rows_for_match(match_id, include_tournament_matches=True)


def fetch_all_admins():
    """
    Returns all admins (including superadmins persisted in Admin) with names and emails.
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT u.usersid,
                       u.firstname,
                       u.lastname,
                       u.email
                FROM Admin a
                JOIN Users u ON a.usersid = u.usersid
                ORDER BY u.firstname, u.lastname;
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_all_tournaments():
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT tournamentid,
                       name,
                       size
                FROM Tournament
                ORDER BY name;
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


def _ensure_admin_record(cur, admin_id):
    cur.execute(
        """
        INSERT INTO Admin (UsersID)
        VALUES (%s)
        ON CONFLICT DO NOTHING;
        """,
        (admin_id,),
    )


def fetch_all_leagues():
    """Fetch all leagues with their seasons."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT l.leagueid,
                       l.name,
                       s.seasonno,
                       s.seasonyear,
                       s.startdate,
                       s.enddate,
                       s.prizepool
                FROM League l
                LEFT JOIN Season s ON l.leagueid = s.leagueid
                ORDER BY l.name, s.seasonyear DESC, s.seasonno DESC;
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_league_by_id(league_id):
    """Fetch a single league with all its seasons and admin assignments."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT l.leagueid,
                       l.name,
                       s.seasonno,
                       s.seasonyear,
                       s.startdate,
                       s.enddate,
                       s.prizepool,
                       sm.adminid
                FROM League l
                LEFT JOIN Season s ON l.leagueid = s.leagueid
                LEFT JOIN SeasonModeration sm ON l.leagueid = sm.leagueid 
                    AND s.seasonno = sm.seasonno 
                    AND s.seasonyear = sm.seasonyear
                WHERE l.leagueid = %s
                ORDER BY s.seasonyear DESC, s.seasonno DESC;
                """,
                (league_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def create_league_with_seasons(league_name, seasons_data, team_ids=None):
    """
    Create a league and its seasons in a single transaction.
    
    seasons_data: List of dicts with keys:
        - start_date: Start date (YYYY-MM-DD format)
        - start_time: Start time (HH:MM format)
        - end_date: End date (YYYY-MM-DD format)
        - end_time: End time (HH:MM format)
        - prize_pool: Prize pool amount (int)
    
    team_ids: List of team IDs to associate with this league (optional)
    
    Returns: {'league_id': int}
    """
    if not league_name or not league_name.strip():
        raise ValueError("League name is required.")
    
    if not seasons_data:
        raise ValueError("At least one season is required.")
    
    validated_seasons = []
    for i, season in enumerate(seasons_data):
        season_no = i + 1
        start_date_str = season.get("start_date", "").strip()
        start_time_str = season.get("start_time", "00:00").strip()
        end_date_str = season.get("end_date", "").strip()
        end_time_str = season.get("end_time", "23:59").strip()
        prize_pool = season.get("prize_pool", 0)
        
        if not start_date_str or not end_date_str:
            raise ValueError(f"Season {season_no}: Start date and end date are required.")
        
        try:
            start_datetime = datetime.strptime(f"{start_date_str} {start_time_str}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.strptime(f"{end_date_str} {end_time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError(f"Season {season_no}: Invalid date or time format. Use YYYY-MM-DD for dates and HH:MM for times.")
        
        if start_datetime >= end_datetime:
            raise ValueError(f"Season {season_no}: Start datetime must be before end datetime.")
        
        if int(prize_pool) <= 0:
            raise ValueError(f"Season {season_no}: Prize pool must be greater than 0.")
        
        validated_seasons.append({
            "season_no": season_no,
            "season_year": start_datetime.date(),
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "prize_pool": int(prize_pool),
        })
    
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # Insert league
                cur.execute(
                    """
                    INSERT INTO League (Name)
                    VALUES (%s)
                    RETURNING LeagueID;
                    """,
                    (league_name.strip(),),
                )
                league_id = cur.fetchone()[0]
                
                # Insert seasons using validated data
                for season in validated_seasons:
                    cur.execute(
                        """
                        INSERT INTO Season (LeagueID, SeasonNo, SeasonYear, StartDate, EndDate, PrizePool)
                        VALUES (%s, %s, %s, %s, %s, %s);
                        """,
                        (
                            league_id,
                            season["season_no"],
                            season["season_year"],
                            season["start_datetime"],
                            season["end_datetime"],
                            season["prize_pool"],
                        ),
                    )
                
                # Insert team-league associations if provided
                if team_ids:
                    for team_id in team_ids:
                        cur.execute(
                            """
                            INSERT INTO LeagueTeam (LeagueID, TeamID)
                            VALUES (%s, %s);
                            """,
                            (league_id, int(team_id)),
                        )
        
        return {"league_id": league_id}
    finally:
        conn.close()


def assign_admins_to_season(league_id, season_no, season_year, admin_ids):
    """
    Assign admins to a specific season.
    Replaces all existing admin assignments for that season.
    
    admin_ids: List of admin user IDs
    """
    if not admin_ids:
        raise ValueError("At least one admin must be assigned.")
    
    admin_ids = [int(aid) for aid in admin_ids if aid]
    admin_ids = list(dict.fromkeys(admin_ids))  # Remove duplicates
    
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # Ensure all admins exist in Admin table
                for admin_id in admin_ids:
                    _ensure_admin_record(cur, admin_id)
                
                # Delete existing assignments for this season
                cur.execute(
                    """
                    DELETE FROM SeasonModeration
                    WHERE LeagueID = %s AND SeasonNo = %s AND SeasonYear = %s;
                    """,
                    (league_id, season_no, season_year),
                )
                
                # Insert new assignments
                for admin_id in admin_ids:
                    cur.execute(
                        """
                        INSERT INTO SeasonModeration (LeagueID, SeasonNo, SeasonYear, AdminID)
                        VALUES (%s, %s, %s, %s);
                        """,
                        (league_id, season_no, season_year, admin_id),
                    )
    finally:
        conn.close()


def assign_same_admins_to_all_seasons(league_id, admin_ids):
    """
    Assign the same set of admins to all seasons of a league.
    Replaces all existing admin assignments for all seasons.
    """
    if not admin_ids:
        raise ValueError("At least one admin must be assigned.")
    
    admin_ids = [int(aid) for aid in admin_ids if aid]
    admin_ids = list(dict.fromkeys(admin_ids))  # Remove duplicates
    
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # Ensure all admins exist in Admin table
                for admin_id in admin_ids:
                    _ensure_admin_record(cur, admin_id)
                
                # Get all seasons for this league
                cur.execute(
                    """
                    SELECT seasonno, seasonyear
                    FROM Season
                    WHERE leagueid = %s;
                    """,
                    (league_id,),
                )
                seasons = cur.fetchall()
                
                if not seasons:
                    raise ValueError("League has no seasons.")
                
                # Delete existing assignments for this league
                cur.execute(
                    """
                    DELETE FROM SeasonModeration
                    WHERE LeagueID = %s;
                    """,
                    (league_id,),
                )
                
                # Insert new assignments for all seasons
                for season in seasons:
                    for admin_id in admin_ids:
                        cur.execute(
                            """
                            INSERT INTO SeasonModeration (LeagueID, SeasonNo, SeasonYear, AdminID)
                            VALUES (%s, %s, %s, %s);
                            """,
                            (league_id, season["seasonno"], season["seasonyear"], admin_id),
                        )
    finally:
        conn.close()


def fetch_all_referees():
    """Fetch all referees."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT r.usersid,
                       u.firstname,
                       u.lastname,
                       u.email
                FROM Referee r
                JOIN Users u ON r.usersid = u.usersid
                ORDER BY u.lastname, u.firstname;
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_admin_tournament_matches(admin_id):
    """
    Fetch all tournament and seasonal matches that this admin manages.
    Returns matches with their basic info and any assigned referees.
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT DISTINCT
                       m.matchid,
                       m.hometeamname,
                       m.awayteamname,
                       m.matchstartdatetime,
                       m.matchenddatetime,
                       m.hometeamscore,
                       m.awayteamscore,
                       m.winnerteam,
                       m.islocked,
                       CASE 
                           WHEN tm.matchid IS NOT NULL THEN 'tournament'
                           WHEN sm.matchid IS NOT NULL THEN 'seasonal'
                           ELSE 'unknown'
                       END as match_type,
                       t.tournamentid,
                       t.name as tournament_name,
                       l.leagueid,
                       l.name as league_name
                FROM Match m
                LEFT JOIN TournamentMatch tm ON m.matchid = tm.matchid
                LEFT JOIN Tournament t ON t.tournamentid = (
                    SELECT tournamentid FROM Round WHERE t_matchid = m.matchid
                )
                LEFT JOIN SeasonalMatch sm ON m.matchid = sm.matchid
                LEFT JOIN League l ON sm.leagueid = l.leagueid
                WHERE t.tournamentid IN (
                    SELECT t_id FROM TournamentModeration WHERE adminid = %s
                ) OR sm.leagueid IN (
                    SELECT leagueid FROM SeasonModeration WHERE adminid = %s
                )
                ORDER BY m.matchstartdatetime DESC;
                """,
                (admin_id, admin_id),
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_match_with_referees(match_id):
    """Fetch a specific match with its assigned referees."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT m.matchid,
                       m.hometeamname,
                       m.awayteamname,
                       m.matchstartdatetime,
                       m.matchenddatetime,
                       m.hometeamscore,
                       m.awayteamscore,
                       m.winnerteam,
                       m.islocked,
                       CASE 
                           WHEN tm.matchid IS NOT NULL THEN 'tournament'
                           WHEN sm.matchid IS NOT NULL THEN 'seasonal'
                           ELSE 'unknown'
                       END as match_type
                FROM Match m
                LEFT JOIN TournamentMatch tm ON m.matchid = tm.matchid
                LEFT JOIN SeasonalMatch sm ON m.matchid = sm.matchid
                WHERE m.matchid = %s;
                """,
                (match_id,),
            )
            match = cur.fetchone()
            
            if not match:
                return None
            
            # Fetch assigned referees for this match
            cur.execute(
                """
                SELECT r.usersid,
                       u.firstname,
                       u.lastname,
                       u.email
                FROM RefereeMatchAttendance rma
                JOIN Referee r ON rma.refereeid = r.usersid
                JOIN Users u ON r.usersid = u.usersid
                WHERE rma.matchid = %s
                ORDER BY u.lastname, u.firstname;
                """,
                (match_id,),
            )
            match_dict = dict(match)
            match_dict["referees"] = cur.fetchall()
            return match_dict
    finally:
        conn.close()


def assign_referee_to_match(match_id, referee_id):
    """Assign a referee to a match (in RefereeMatchAttendance)."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO RefereeMatchAttendance (MatchID, RefereeID)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING;
                    """,
                    (match_id, referee_id),
                )
    finally:
        conn.close()


def remove_referee_from_match(match_id, referee_id):
    """Remove a referee from a match."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM RefereeMatchAttendance
                    WHERE MatchID = %s AND RefereeID = %s;
                    """,
                    (match_id, referee_id),
                )
    finally:
        conn.close()


def fetch_seasonal_matches_for_admin(admin_id):
    """
    Fetch all seasonal matches that this admin manages (for locking/unlocking).
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT m.matchid,
                       m.hometeamname,
                       m.awayteamname,
                       m.matchstartdatetime,
                       m.hometeamscore,
                       m.awayteamscore,
                       m.islocked,
                       l.leagueid,
                       l.name as league_name,
                       s.seasonno,
                       s.seasonyear
                FROM Match m
                JOIN SeasonalMatch sm ON m.matchid = sm.matchid
                JOIN Season s ON sm.leagueid = s.leagueid 
                    AND sm.seasonno = s.seasonno 
                    AND sm.seasonyear = s.seasonyear
                JOIN League l ON s.leagueid = l.leagueid
                JOIN SeasonModeration smod ON s.leagueid = smod.leagueid 
                    AND s.seasonno = smod.seasonno 
                    AND s.seasonyear = smod.seasonyear
                WHERE smod.adminid = %s
                ORDER BY m.matchstartdatetime DESC;
                """,
                (admin_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def toggle_match_lock(match_id, lock_state):
    """Toggle the lock state of a match."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE Match
                    SET IsLocked = %s
                    WHERE MatchID = %s;
                    """,
                    (lock_state, match_id),
                )
    finally:
        conn.close()

        
        
        

        
        

        
        
        

        
        
