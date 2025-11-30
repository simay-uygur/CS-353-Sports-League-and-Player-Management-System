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
        
        
        
