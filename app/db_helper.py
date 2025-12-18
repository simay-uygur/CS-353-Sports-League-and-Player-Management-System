# this is a mediator file that talks with the database and does common database tasks
import math
import random
from datetime import date, datetime, timedelta
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


def fetch_filtered_players(filters):
    conn = get_connection()
    try:
        name = filters.get("name")
        nationality = filters.get("nationality")
        min_age = filters.get("min_age")
        max_age = filters.get("max_age")
        current_team = filters.get("team")
        position = filters.get("position")

        min_birthdate = None
        max_birthdate = None
        if min_age and max_age:
            today = date.today()
            min_birthdate = date(today.year - max_age, today.month, today.day)
            max_birthdate = date(today.year - min_age, today.month, today.day)

        params = []
        conditions = []
        if name and name.strip() != "":
            stripped_name = name.strip()
            name_parts = stripped_name.split()
            if len(name_parts) == 2:
                conditions.append("(u.firstname ILIKE %s AND u.lastname ILIKE %s)")
                params.append(name_parts[0])
                params.append(name_parts[1])
            else:
                conditions.append("(u.firstname ILIKE %s OR u.lastname ILIKE %s)")
                params.append(stripped_name)
                params.append(stripped_name)
        if nationality:
            conditions.append("u.nationality = %s")
            params.append(nationality)
        if min_birthdate:
            conditions.append("u.birthdate <= %s")
            params.append(min_birthdate)
        if max_birthdate:
            conditions.append("u.birthdate >= %s")
            params.append(max_birthdate)
        if current_team:
            conditions.append("t.teamid = %s")
            params.append(current_team)
        if position:
            conditions.append("p.position = %s")
            params.append(position)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT u.usersid,
                   u.firstname,
                   u.lastname,
                   u.nationality,
                   u.birthdate,
                   p.height,
                   p.weight,
                   p.overall,
                   p.position,
                   p.iseligible,
                   t.teamid,
                   t.teamname
            FROM Player p
            JOIN Employee e ON p.usersid = e.usersid
            JOIN Users u ON p.usersid = u.usersid
            LEFT JOIN Team t ON e.teamid = t.teamid
            WHERE {where_clause}
            ORDER BY u.lastname, u.firstname;
        """  # Does not have salary information, which should exist
        # TODO: Make a view in init.sql that returns a player and their current employment

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()
    finally:
        conn.close()


def fetch_player_by_id(playerid):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT u.firstname,
                       u.lastname,
                       p.position,
                       aei.salary,
                       aei.enddate,
                       aei.teamname
                FROM Player p
                JOIN Users u ON p.usersid = u.usersid
                LEFT JOIN Employee e ON p.usersid = e.usersid
                LEFT JOIN AllEmploymentInfo aei ON p.usersid = aei.usersid
                WHERE u.usersid = %s
                """,
                (playerid,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def fetch_all_nationalities():
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT DISTINCT nationality
                FROM Users
                WHERE nationality IS NOT NULL
                ORDER BY nationality;
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_all_positions():
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT DISTINCT position
                FROM Player
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


def report_players(filters):
    """
    filters: {
      all_players: bool,
      currently_employed: bool,
      player_id: int|None,
      employed_before: datetime|None,
      employed_after: datetime|None,
      ended_before: datetime|None,
      ended_after: datetime|None,
    }
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            clauses = []
            params = []

            if filters.get("player_id"):
                clauses.append("p.UsersID = %s")
                params.append(filters["player_id"])

            if filters.get("currently_employed"):
                clauses.append("e.EndDate >= NOW()")

            if filters.get("employed_before"):
                clauses.append("e.StartDate <= %s")
                params.append(filters["employed_before"])

            if filters.get("employed_after"):
                clauses.append("e.StartDate >= %s")
                params.append(filters["employed_after"])

            if filters.get("ended_before"):
                clauses.append("e.EndDate <= %s")
                params.append(filters["ended_before"])

            if filters.get("ended_after"):
                clauses.append("e.EndDate >= %s")
                params.append(filters["ended_after"])

            where_sql = " WHERE " + " AND ".join(clauses) if clauses else ""

            cur.execute(
                f"""
                SELECT p.UsersID,
                       u.FirstName,
                       u.LastName,
                       u.Email,
                       p.Position,
                       p.Height,
                       p.Weight,
                       e.StartDate,
                       e.EndDate,
                       t.TeamName
                FROM Player p
                JOIN Users u ON u.UsersID = p.UsersID
                LEFT JOIN Employed em ON em.UsersID = p.UsersID
                LEFT JOIN Employment e ON e.EmploymentID = em.EmploymentID
                LEFT JOIN Team t ON t.TeamID = em.TeamID
                {where_sql}
                ORDER BY u.LastName, u.FirstName, e.StartDate NULLS LAST;
                """,
                tuple(params),
            )
            return cur.fetchall()
    finally:
        conn.close()


def report_league_standings(league_id, season_no, season_year):
    """Simple standings: wins/draws/losses/points from SeasonalMatch scores."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    m.HomeTeamID,
                    m.AwayTeamID,
                    m.HomeTeamName,
                    m.AwayTeamName,
                    m.HomeTeamScore,
                    m.AwayTeamScore
                FROM Match m
                JOIN SeasonalMatch sm ON m.MatchID = sm.MatchID
                WHERE sm.LeagueID = %s AND sm.SeasonNo = %s AND sm.SeasonYear = %s
                """,
                (league_id, season_no, season_year),
            )
            rows = cur.fetchall()

    finally:
        conn.close()

    stats = {}

    def ensure(team_id, name):
        if team_id not in stats:
            stats[team_id] = {
                "teamid": team_id,
                "teamname": name,
                "played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "gf": 0,
                "ga": 0,
                "points": 0,
            }

    for row in rows:
        home_id = row["hometeamid"]
        away_id = row["awayteamid"]
        home_name = row["hometeamname"]
        away_name = row["awayteamname"]
        hs = row["hometeamscore"]
        as_ = row["awayteamscore"]
        if hs is None or as_ is None:
            continue
        ensure(home_id, home_name)
        ensure(away_id, away_name)
        stats[home_id]["played"] += 1
        stats[away_id]["played"] += 1
        stats[home_id]["gf"] += hs
        stats[home_id]["ga"] += as_
        stats[away_id]["gf"] += as_
        stats[away_id]["ga"] += hs
        if hs > as_:
            stats[home_id]["wins"] += 1
            stats[home_id]["points"] += 3
            stats[away_id]["losses"] += 1
        elif hs < as_:
            stats[away_id]["wins"] += 1
            stats[away_id]["points"] += 3
            stats[home_id]["losses"] += 1
        else:
            stats[home_id]["draws"] += 1
            stats[away_id]["draws"] += 1
            stats[home_id]["points"] += 1
            stats[away_id]["points"] += 1

    return sorted(
        stats.values(), key=lambda s: (-s["points"], -(s["gf"] - s["ga"]), -s["wins"])
    )


def report_player_attendance(
    date_from=None, date_to=None, player_id=None, team_id=None, all_teams=False
):
    """
    Counts training attendance per player from TrainingAttendance table.
    Filters by training session dates, optionally by player_id, team_id, or all teams.
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            clauses = []
            params = []

            # Base query joins TrainingAttendance with TrainingSession, Coach, Employee, Team, and Users
            query = """
                SELECT 
                    u.UsersID AS PlayerID,
                    u.FirstName,
                    u.LastName,
                    COUNT(*) AS appearances
                FROM TrainingAttendance ta
                JOIN TrainingSession ts ON ta.SessionID = ts.SessionID
                JOIN Coach c ON ts.CoachID = c.UsersID
                JOIN Employee e ON c.UsersID = e.UsersID
                JOIN Team t ON e.TeamID = t.TeamID
                JOIN Users u ON ta.PlayerID = u.UsersID
                WHERE ta.Status = 1
            """

            # Filter by training session date range
            if date_from:
                clauses.append("ts.SessionDate >= %s")
                params.append(date_from)

            if date_to:
                clauses.append("ts.SessionDate <= %s")
                params.append(date_to)

            # Filter by specific player
            if player_id:
                clauses.append("ta.PlayerID = %s")
                params.append(player_id)

            # Filter by team (unless all_teams is True)
            if not all_teams and team_id:
                clauses.append("t.TeamID = %s")
                params.append(team_id)

            if clauses:
                query += " AND " + " AND ".join(clauses)

            query += """
                GROUP BY u.UsersID, u.FirstName, u.LastName
                ORDER BY appearances DESC, u.LastName, u.FirstName;
            """

            cur.execute(query, tuple(params))
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


def fetch_transferable_players(filters, coachid):
    conn = get_connection()
    try:
        name = filters.get("name")
        nationality = filters.get("nationality")

        min_age = None
        max_age = None
        if filters.get("min_age"):
            min_age = int(filters.get("min_age"))
        if filters.get("max_age"):
            max_age = int(filters.get("max_age"))
        current_team = filters.get("team")
        position = filters.get("position")
        contact_expiration_date = filters.get("contact_expiration_date")

        min_birthdate = None
        max_birthdate = None
        today = date.today()
        if max_age:
            max_birthdate = date(today.year - max_age, today.month, today.day)
        if min_age:
            min_birthdate = date(today.year - min_age, today.month, today.day)

        params = []
        conditions = []
        if name and name.strip() != "":
            stripped_name = name.strip()
            name_parts = stripped_name.split()
            if len(name_parts) == 2:
                conditions.append("(u.firstname ILIKE %s AND u.lastname ILIKE %s)")
                params.append(name_parts[0])
                params.append(name_parts[1])
            else:
                conditions.append("(u.firstname ILIKE %s OR u.lastname ILIKE %s)")
                params.append(stripped_name)
                params.append(stripped_name)
        if nationality:
            conditions.append("u.nationality = %s")
            params.append(nationality)
        if min_birthdate:
            conditions.append("u.birthdate <= %s")
            params.append(min_birthdate)
        if max_birthdate:
            conditions.append("u.birthdate >= %s")
            params.append(max_birthdate)
        if current_team:
            conditions.append("ce.teamid = %s")
            params.append(current_team)
        if position:
            conditions.append("p.position = %s")
            params.append(position)
        if contact_expiration_date:
            conditions.append("emp.EndDate < %s")
            params.append(contact_expiration_date)

        # Exclude players from the coach's own team
        conditions.append(
            "e.teamid <> (SELECT teamid FROM Employee WHERE usersid = %s)"
        )
        params.append(coachid)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT 
                    p.UsersID, 
                    u.FirstName, 
                    u.LastName, 
                    u.nationality,
                    u.Email, 
                    p.Position,
                    u.birthdate,
                    ce.Salary,
                    ce.EndDate,
                    ce.TeamName
                FROM Player p
                JOIN Users u ON p.UsersID = u.UsersID
                JOIN Employee e ON p.UsersID = e.UsersID
                LEFT JOIN CurrentEmployment ce ON p.UsersID = ce.UsersID
                WHERE {where_clause}
                """,
                (params),
            )
            rows = cur.fetchall()
            return rows
    finally:
        conn.close()


def fetch_player_transfer_offers(playerid):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM Offer
                WHERE RequestedPlayer = %s
                AND AvailableUntil > NOW()
                ORDER BY AvailableUntil DESC
                """,
                (playerid,),
            )
            rows = cur.fetchall()
            return rows
    finally:
        conn.close()


def fetch_team_transfer_offers(coachid):
    """
    Fetch transfer offers for players on the coach's team.
    Returns a tuple: (pending_offers, past_offers)
    - pending_offers: offers with status NULL and AvailableUntil > NOW()
    - past_offers: accepted, rejected, or expired offers

    Uses PlayerTeamAtOfferTime to show offers based on which team the player was on
    when the offer was created. This ensures offers stay with the original team
    even if the player transfers to another team.
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get the coach's team ID
            cur.execute(
                """
                SELECT TeamID FROM Employee WHERE UsersID = %s
                """,
                (coachid,),
            )
            coach_team_result = cur.fetchone()
            if not coach_team_result or not coach_team_result.get("teamid"):
                return ([], [])
            coach_team_id = coach_team_result["teamid"]

            # Fetch all offers for this team (using PlayerTeamAtOfferTime)
            cur.execute(
                """
                SELECT 
                    o.OfferID,
                    o.OfferAmount,
                    o.AvailableUntil,
                    o.OfferedEndDate,
                    o.OfferStatus,
                    o.RequestingCoach,
                    o.RequestedPlayer,
                    u.FirstName AS PlayerFirstName,
                    u.LastName AS PlayerLastName,
                    u.Email AS PlayerEmail,
                    p.Position AS PlayerPosition,
                    COALESCE(t.TeamID, o.PlayerTeamAtOfferTime) AS PlayerTeamID,
                    COALESCE(t.TeamName, hist_team.TeamName) AS PlayerTeamName,
                    RC.FirstName AS RequestingCoachFirstName,
                    RC.LastName AS RequestingCoachLastName,
                    RC.Email AS RequestingCoachEmail,
                    RT.TeamID AS RequestingTeamID,
                    RT.TeamName AS RequestingTeamName
                FROM Offer o 
                JOIN Player p ON p.UsersID = o.RequestedPlayer
                JOIN Users u ON u.UsersID = p.UsersID
                JOIN Coach c ON o.RequestingCoach = c.UsersID
                JOIN Employee ec ON c.UsersID = ec.UsersID
                JOIN Team RT ON ec.TeamID = RT.TeamID
                JOIN Users RC ON o.RequestingCoach = RC.UsersID
                LEFT JOIN Employee e ON e.UsersID = p.UsersID
                LEFT JOIN Team t ON e.TeamID = t.TeamID
                LEFT JOIN Team hist_team ON o.PlayerTeamAtOfferTime = hist_team.TeamID
                WHERE
                    o.PlayerTeamAtOfferTime = %s
                ORDER BY o.AvailableUntil DESC
                """,
                (coach_team_id,),
            )
            all_offers = cur.fetchall()

            # Split into pending and past
            now = datetime.now()
            pending = []
            past = []

            for offer in all_offers:
                is_expired = offer["availableuntil"] < now
                is_pending = offer["offerstatus"] is None and not is_expired

                if is_pending:
                    pending.append(offer)
                else:
                    past.append(offer)

            return (pending, past)
    finally:
        conn.close()


def fetch_sent_transfer_offers(coachid):
    """
    Fetch transfer offers sent by coaches from the given coach's team.
    Returns all offers (pending, accepted, rejected, expired) sent by the team.
    Uses RequestingTeamAtOfferTime to show offers based on which team the coach was on
    when the offer was sent, not their current team.
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get the coach's team ID
            cur.execute(
                """
                SELECT TeamID FROM Employee WHERE UsersID = %s
                """,
                (coachid,),
            )
            coach_team_result = cur.fetchone()
            if not coach_team_result or not coach_team_result.get("teamid"):
                return []
            coach_team_id = coach_team_result["teamid"]

            # Fetch all offers sent by coaches from this team (using RequestingTeamAtOfferTime)
            cur.execute(
                """
                SELECT 
                    o.OfferID,
                    o.OfferAmount,
                    o.AvailableUntil,
                    o.OfferedEndDate,
                    o.OfferStatus,
                    o.RequestingCoach,
                    o.RequestedPlayer,
                    u.FirstName AS PlayerFirstName,
                    u.LastName AS PlayerLastName,
                    u.Email AS PlayerEmail,
                    p.Position AS PlayerPosition,
                    COALESCE(t.TeamID, o.PlayerTeamAtOfferTime) AS PlayerTeamID,
                    COALESCE(t.TeamName, hist_team.TeamName) AS PlayerTeamName,
                    RC.FirstName AS RequestingCoachFirstName,
                    RC.LastName AS RequestingCoachLastName,
                    RC.Email AS RequestingCoachEmail,
                    COALESCE(RT.TeamID, o.RequestingTeamAtOfferTime) AS RequestingTeamID,
                    COALESCE(RT.TeamName, req_hist_team.TeamName) AS RequestingTeamName
                FROM Offer o 
                JOIN Player p ON p.UsersID = o.RequestedPlayer
                JOIN Users u ON u.UsersID = p.UsersID
                JOIN Coach c ON o.RequestingCoach = c.UsersID
                JOIN Users RC ON o.RequestingCoach = RC.UsersID
                LEFT JOIN Employee ec ON c.UsersID = ec.UsersID
                LEFT JOIN Team RT ON ec.TeamID = RT.TeamID
                LEFT JOIN Employee e ON e.UsersID = p.UsersID
                LEFT JOIN Team t ON e.TeamID = t.TeamID
                LEFT JOIN Team hist_team ON o.PlayerTeamAtOfferTime = hist_team.TeamID
                LEFT JOIN Team req_hist_team ON o.RequestingTeamAtOfferTime = req_hist_team.TeamID
                WHERE
                    o.RequestingTeamAtOfferTime = %s
                ORDER BY o.AvailableUntil DESC
                """,
                (coach_team_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def make_transfer_offer(playerid, coachid, amount, available_until, contract_end_date):
    """
    Create a transfer offer for a player.
    Stores both the player's team and the coach's team when the offer was created for historical tracking.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Get the player's current team
            cur.execute(
                """
                SELECT TeamID FROM Employee WHERE UsersID = %s
                """,
                (playerid,),
            )
            team_result = cur.fetchone()
            player_team_id = team_result[0] if team_result else None

            # Get the coach's current team
            cur.execute(
                """
                SELECT TeamID FROM Employee WHERE UsersID = %s
                """,
                (coachid,),
            )
            coach_team_result = cur.fetchone()
            coach_team_id = coach_team_result[0] if coach_team_result else None

            cur.execute(
                """
                INSERT INTO Offer (RequestedPlayer, RequestingCoach, OfferAmount, AvailableUntil, OfferedEndDate, PlayerTeamAtOfferTime, RequestingTeamAtOfferTime)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    playerid,
                    coachid,
                    amount,
                    available_until,
                    contract_end_date,
                    player_team_id,
                    coach_team_id,
                ),
            )
            conn.commit()
    finally:
        conn.close()


def finalize_transfer_offer(offerid, decision):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE Offer
                SET OfferStatus = %s
                WHERE OfferId = %s
                """,
                (
                    decision,
                    offerid,
                ),
            )
            conn.commit()
    finally:
        conn.close()


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
        raise ValueError(
            "Please select a power of 2 number of teams (2, 4, 8, 16, etc.)."
        )

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

                leaf_match_ids = _build_bracket_tree(
                    cur, tournament_id, team_ids, start_date
                )

        # NOTE: Play rows are now created automatically via the database trigger
        # trg_auto_create_plays_on_match_insert when matches are inserted.
        # The following code is commented out as the trigger handles this:
        # for match_id in leaf_match_ids:
        #     create_plays_for_match_players_on_insert(match_id)

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
    rounds_to_insert = (
        []
    )  # List of tuples: (tournament_id, round_no, child1_no, child2_no, parent_no)

    for level in range(depth + 1):
        nodes_at_level = 1 << level  # 2^level
        for index in range(nodes_at_level):
            round_no = get_round_no(level, index)
            child1, child2 = get_children(level, index)
            parent = get_parent(level, index)

            rounds_to_insert.append((tournament_id, round_no, child1, child2, parent))

    # INSERT all rounds with links left NULL, then set them after all rows exist
    for (
        tournament_id_val,
        round_no,
        child1_no,
        child2_no,
        parent_no,
    ) in rounds_to_insert:
        cur.execute(
            """
            INSERT INTO Round (TournamentID, RoundNo, T_MatchID, Child1RoundNo, Child2RoundNo, ParentRoundNo)
            VALUES (%s, %s, NULL, NULL, NULL, NULL);
            """,
            (tournament_id_val, round_no),
        )

    for (
        tournament_id_val,
        round_no,
        child1_no,
        child2_no,
        parent_no,
    ) in rounds_to_insert:
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
        (shuffled_ids[i], shuffled_ids[i + 1]) for i in range(0, len(shuffled_ids), 2)
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
            (
                home_team_id,
                away_team_id,
                match_datetime,
                home_team_name,
                away_team_name,
            ),
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

        # Seed Play rows for the tournament match (uses employment at match start)
        create_plays_for_match_players_on_insert(match_id)

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

                # checks also whether player is eligible _ _ _ at that date? or now  - i can delete is eligible
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


def fetch_admin_leagues(admin_id):
    """Fetch leagues and seasons moderated by a specific admin."""
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
                FROM SeasonModeration sm
                JOIN Season s
                    ON sm.leagueid = s.leagueid
                    AND sm.seasonno = s.seasonno
                    AND sm.seasonyear = s.seasonyear
                JOIN League l ON l.leagueid = sm.leagueid
                WHERE sm.adminid = %s
                ORDER BY l.name, s.seasonyear DESC, s.seasonno DESC;
                """,
                (admin_id,),
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


def fetch_league_teams(league_id):
    """Teams currently associated to a league."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT t.teamid, t.teamname
                FROM LeagueTeam lt
                JOIN Team t ON lt.teamid = t.teamid
                WHERE lt.leagueid = %s
                ORDER BY t.teamname;
                """,
                (league_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_league_available_teams(league_id):
    """Teams not yet associated to this league."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT t.teamid, t.teamname
                FROM Team t
                WHERE NOT EXISTS (
                    SELECT 1 FROM LeagueTeam lt
                    WHERE lt.teamid = t.teamid AND lt.leagueid = %s
                )
                ORDER BY t.teamname;
                """,
                (league_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def add_team_to_league(league_id, team_id):
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO LeagueTeam (LeagueID, TeamID)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING;
                    """,
                    (league_id, team_id),
                )
    finally:
        conn.close()


def delete_season(league_id, season_no, season_year):
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM Season
                    WHERE LeagueID = %s AND SeasonNo = %s AND SeasonYear = %s;
                    """,
                    (league_id, season_no, season_year),
                )
    finally:
        conn.close()


def delete_league(league_id):
    """Delete a league and all associated data."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM League
                    WHERE LeagueID = %s;
                    """,
                    (league_id,),
                )
    finally:
        conn.close()


def create_season_match(
    league_id, season_no, season_year, home_team_id, away_team_id, start_dt, venue
):
    """Create a Match and link it to SeasonalMatch for the given season."""
    if home_team_id == away_team_id:
        raise ValueError("Home and away team cannot be the same.")

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO Match (
                        HomeTeamID, AwayTeamID,
                        MatchStartDatetime, MatchEndDatetime,
                        VenuePlayed,
                        HomeTeamName, AwayTeamName,
                        HomeTeamScore, AwayTeamScore, WinnerTeam, IsLocked
                    )
                    SELECT %s, %s, %s, NULL, %s, ht.teamname, at.teamname, NULL, NULL, NULL, FALSE
                    FROM Team ht, Team at
                    WHERE ht.teamid = %s AND at.teamid = %s
                    RETURNING MatchID;
                    """,
                    (
                        home_team_id,
                        away_team_id,
                        start_dt,
                        venue,
                        home_team_id,
                        away_team_id,
                    ),
                )
                match_id = cur.fetchone()[0]

                cur.execute(
                    """
                    INSERT INTO SeasonalMatch (MatchID, LeagueID, SeasonNo, SeasonYear)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (match_id, league_id, season_no, season_year),
                )

                return match_id
    finally:
        conn.close()


def team_has_match_on_date(team_id, date_str):
    """
    Check if a team already has any match scheduled on the given date (YYYY-MM-DD).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM Match
                WHERE DATE(matchstartdatetime) = %s
                  AND (hometeamid = %s OR awayteamid = %s)
                LIMIT 1;
                """,
                (date_str, team_id, team_id),
            )
            return cur.fetchone() is not None
    finally:
        conn.close()


def fetch_league_matches(league_id):
    """All seasonal matches for a league with season info."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT m.matchid,
                       m.hometeamname,
                       m.awayteamname,
                       m.matchstartdatetime,
                       m.islocked,
                       m.winnerteam,
                       s.seasonno,
                       s.seasonyear
                FROM Match m
                JOIN SeasonalMatch sm ON m.matchid = sm.matchid
                JOIN Season s ON sm.leagueid = s.leagueid
                    AND sm.seasonno = s.seasonno
                    AND sm.seasonyear = s.seasonyear
                WHERE sm.leagueid = %s
                ORDER BY s.seasonyear DESC, s.seasonno DESC, m.matchstartdatetime DESC;
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
            raise ValueError(
                f"Season {season_no}: Start date and end date are required."
            )

        try:
            start_datetime = datetime.strptime(
                f"{start_date_str} {start_time_str}", "%Y-%m-%d %H:%M"
            )
            end_datetime = datetime.strptime(
                f"{end_date_str} {end_time_str}", "%Y-%m-%d %H:%M"
            )
        except ValueError:
            raise ValueError(
                f"Season {season_no}: Invalid date or time format. Use YYYY-MM-DD for dates and HH:MM for times."
            )

        if start_datetime >= end_datetime:
            raise ValueError(
                f"Season {season_no}: Start datetime must be before end datetime."
            )

        if int(prize_pool) <= 0:
            raise ValueError(f"Season {season_no}: Prize pool must be greater than 0.")

        validated_seasons.append(
            {
                "season_no": season_no,
                "season_year": start_datetime.date(),
                "start_datetime": start_datetime,
                "end_datetime": end_datetime,
                "prize_pool": int(prize_pool),
            }
        )

    # Ensure seasons do not overlap
    sorted_seasons = sorted(validated_seasons, key=lambda s: s["start_datetime"])
    for i in range(len(sorted_seasons) - 1):
        current = sorted_seasons[i]
        nxt = sorted_seasons[i + 1]
        if current["end_datetime"] > nxt["start_datetime"]:
            raise ValueError(
                f"Season {current['season_no']} and Season {nxt['season_no']} overlap. "
                "Please adjust the start/end dates and times."
            )

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
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
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
                            (
                                league_id,
                                season["seasonno"],
                                season["seasonyear"],
                                admin_id,
                            ),
                        )
    finally:
        conn.close()


def fetch_available_coaches():
    """Fetch coaches who don't have a team assigned (TeamID IS NULL)."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT 
                    c.UsersID,
                    u.FirstName,
                    u.LastName,
                    u.Email,
                    c.Certification
                FROM Coach c
                JOIN Users u ON c.UsersID = u.UsersID
                JOIN Employee e ON c.UsersID = e.UsersID
                WHERE e.TeamID IS NULL
                ORDER BY u.LastName, u.FirstName;
                """,
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_all_coaches():
    """Fetch all coaches with their current team info."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT 
                    c.UsersID,
                    u.FirstName,
                    u.LastName,
                    u.Email,
                    c.Certification,
                    e.TeamID,
                    t.TeamName
                FROM Coach c
                JOIN Users u ON c.UsersID = u.UsersID
                JOIN Employee e ON c.UsersID = e.UsersID
                LEFT JOIN Team t ON e.TeamID = t.TeamID
                ORDER BY u.LastName, u.FirstName;
                """,
            )
            return cur.fetchall()
    finally:
        conn.close()


def employ_coach_to_team(coach_id, team_id, owner_id):
    """
    Assign a coach to a team. Validates that:
    - Coach exists
    - Team belongs to the owner
    - Ends new coach's previous employment if switching teams
    - Creates new employment record for the new coach
    - Updates Employee.TeamID for backward compatibility
    - Does NOT terminate existing coaches on the team (allows multiple coaches)
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # Verify team belongs to owner
                cur.execute(
                    """
                    SELECT TeamID FROM Team WHERE TeamID = %s AND OwnerID = %s;
                    """,
                    (team_id, owner_id),
                )
                if not cur.fetchone():
                    raise ValueError("Team does not belong to you.")

                # Verify coach exists
                cur.execute(
                    """
                    SELECT e.UsersID, e.TeamID
                    FROM Employee e
                    JOIN Coach c ON e.UsersID = c.UsersID
                    WHERE e.UsersID = %s;
                    """,
                    (coach_id,),
                )
                coach_row = cur.fetchone()
                if not coach_row:
                    raise ValueError("Coach not found.")

                # End new coach's current active employment if they have one (switching teams)
                cur.execute(
                    """
                    SELECT em.EmploymentID, emp.Salary
                    FROM Employed em
                    JOIN Employment emp ON em.EmploymentID = emp.EmploymentID
                    WHERE em.UsersID = %s
                    AND emp.EndDate > NOW()
                    ORDER BY emp.StartDate DESC
                    LIMIT 1;
                    """,
                    (coach_id,),
                )
                current_employment = cur.fetchone()
                current_salary = (
                    current_employment[1] if current_employment else 80000
                )  # Default coach salary

                if current_employment:
                    cur.execute(
                        """
                        UPDATE Employment
                        SET EndDate = NOW()
                        WHERE EmploymentID = %s;
                        """,
                        (current_employment[0],),
                    )

                # Create new employment record (1 year contract)
                start_date = datetime.now()
                end_date = start_date + timedelta(days=365)

                cur.execute(
                    """
                    INSERT INTO Employment (StartDate, EndDate, Salary)
                    VALUES (%s, %s, %s)
                    RETURNING EmploymentID;
                    """,
                    (start_date, end_date, current_salary),
                )
                new_employment_id = cur.fetchone()[0]

                # Create new employed record
                cur.execute(
                    """
                    INSERT INTO Employed (EmploymentID, UsersID, TeamID)
                    VALUES (%s, %s, %s);
                    """,
                    (new_employment_id, coach_id, team_id),
                )

                # Update Employee table for backward compatibility (shows latest team)
                # Note: Multiple coaches per team are supported via the teamCoaches view
                cur.execute(
                    """
                    UPDATE Employee
                    SET TeamID = %s
                    WHERE UsersID = %s;
                    """,
                    (team_id, coach_id),
                )

                if cur.rowcount == 0:
                    raise ValueError("Failed to assign coach to team.")
    finally:
        conn.close()


def remove_coach_from_team(coach_id, team_id, owner_id):
    """
    Remove a coach from a team by terminating their employment.
    Validates that:
    - Coach exists and is on the team
    - Team belongs to the owner
    - Ends the coach's active employment
    - Sets Employee.TeamID to NULL
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # Verify team belongs to owner
                cur.execute(
                    """
                    SELECT TeamID FROM Team WHERE TeamID = %s AND OwnerID = %s;
                    """,
                    (team_id, owner_id),
                )
                if not cur.fetchone():
                    raise ValueError("Team does not belong to you.")

                # Verify coach exists and is on this team
                cur.execute(
                    """
                    SELECT e.UsersID, e.TeamID
                    FROM Employee e
                    JOIN Coach c ON e.UsersID = c.UsersID
                    WHERE e.UsersID = %s;
                    """,
                    (coach_id,),
                )
                coach_row = cur.fetchone()
                if not coach_row:
                    raise ValueError("Coach not found.")

                # Find and end the coach's active employment for this team
                cur.execute(
                    """
                    SELECT em.EmploymentID
                    FROM Employed em
                    JOIN Employment emp ON em.EmploymentID = emp.EmploymentID
                    WHERE em.UsersID = %s
                    AND em.TeamID = %s
                    AND emp.EndDate > NOW()
                    ORDER BY emp.StartDate DESC
                    LIMIT 1;
                    """,
                    (coach_id, team_id),
                )
                active_employment = cur.fetchone()

                if active_employment:
                    cur.execute(
                        """
                        UPDATE Employment
                        SET EndDate = NOW()
                        WHERE EmploymentID = %s;
                        """,
                        (active_employment[0],),
                    )

                # Update Employee table to remove team assignment
                # Only set to NULL if they're currently on this team
                cur.execute(
                    """
                    UPDATE Employee
                    SET TeamID = NULL
                    WHERE UsersID = %s AND TeamID = %s;
                    """,
                    (coach_id, team_id),
                )

                if cur.rowcount == 0:
                    raise ValueError("Coach is not currently assigned to this team.")
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


def fetch_team_players(team_id):
    """Fetch all players currently on a team using TeamPlayers view."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # SQL SORGUSUNU GÜNCELLİYORUZ: IsEligible ve RecoveryDate eklendi
            cur.execute(
                """
                SELECT 
                    u.UsersID,
                    u.FirstName,
                    u.LastName,
                    u.Email,
                    p.Position,
                    p.Height,
                    p.Weight,
                    p.Overall,
                    p.IsEligible,
                    (SELECT RecoveryDate FROM Injury 
                     WHERE PlayerID = u.UsersID 
                     ORDER BY InjuryDate DESC LIMIT 1) as RecoveryDate
                FROM TeamPlayers tp
                JOIN Player p ON tp.PlayerID = p.UsersID
                JOIN Users u ON tp.PlayerID = u.UsersID
                WHERE tp.TeamID = %s
                ORDER BY u.LastName, u.FirstName;
                """,
                (team_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_team_coaches(team_id):
    """Fetch all coaches currently on a team using teamCoaches view."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT 
                    c.UsersID,
                    u.FirstName,
                    u.LastName,
                    u.Email,
                    c.Certification
                FROM teamCoaches tc
                JOIN Coach c ON tc.CoachID = c.UsersID
                JOIN Users u ON tc.CoachID = u.UsersID
                WHERE tc.TeamID = %s
                ORDER BY u.LastName, u.FirstName;
                """,
                (team_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_team_by_coach(coach_id):
    """Return the team assigned to the given coach."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT t.TeamID, t.TeamName, t.EstablishedDate, t.HomeVenue, t.OwnerID,
                       u.FirstName as OwnerFirstName, u.LastName as OwnerLastName, u.Email as OwnerEmail
                FROM Employee e
                JOIN Team t ON e.TeamID = t.TeamID
                JOIN TeamOwner to_owner ON t.OwnerID = to_owner.UsersID
                JOIN Users u ON to_owner.UsersID = u.UsersID
                WHERE e.UsersID = %s AND e.TeamID IS NOT NULL;
                """,
                (coach_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def fetch_team_by_player(player_id):
    """Return the team assigned to the given player."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (t.TeamID)
                       t.TeamID, t.TeamName, t.EstablishedDate, t.HomeVenue, t.OwnerID,
                       u.FirstName as OwnerFirstName, u.LastName as OwnerLastName, u.Email as OwnerEmail,
                       c.UsersID as CoachID,
                       uc.FirstName as CoachFirstName, uc.LastName as CoachLastName, uc.Email as CoachEmail
                FROM Employee e
                JOIN Team t ON e.TeamID = t.TeamID
                JOIN TeamOwner to_owner ON t.OwnerID = to_owner.UsersID
                JOIN Users u ON to_owner.UsersID = u.UsersID
                LEFT JOIN Employee ec ON ec.TeamID = t.TeamID
                LEFT JOIN Coach c ON ec.UsersID = c.UsersID
                LEFT JOIN Users uc ON c.UsersID = uc.UsersID
                WHERE e.UsersID = %s AND e.TeamID IS NOT NULL
                ORDER BY t.TeamID, c.UsersID NULLS LAST;
                """,
                (player_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def fetch_teams_by_owner(owner_id):
    """Return teams owned by the given owner."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT TeamID, TeamName, EstablishedDate, HomeVenue
                FROM Team
                WHERE OwnerID = %s
                ORDER BY TeamName;
                """,
                (owner_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_other_team_owners(current_owner_id):
    """Return other owners who don't have teams (available for transfer)."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT towner.UsersID,
                       u.FirstName,
                       u.LastName,
                       u.Email,
                       towner.NetWorth
                FROM TeamOwner towner
                JOIN Users u ON u.UsersID = towner.UsersID
                LEFT JOIN Team t ON t.OwnerID = towner.UsersID
                WHERE towner.UsersID <> %s
                  AND t.TeamID IS NULL
                ORDER BY u.LastName, u.FirstName;
                """,
                (current_owner_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def transfer_team_owner(team_id, current_owner_id, new_owner_id):
    """Transfer ownership of a team to a different owner."""
    if current_owner_id == new_owner_id:
        raise ValueError("New owner must be different.")

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # Verify team belongs to current owner
                cur.execute(
                    """
                    SELECT TeamID FROM Team WHERE TeamID = %s AND OwnerID = %s;
                    """,
                    (team_id, current_owner_id),
                )
                if not cur.fetchone():
                    raise ValueError(
                        "Transfer failed; team not owned by current owner."
                    )

                # Check if new owner already has a team
                cur.execute(
                    """
                    SELECT TeamID, TeamName FROM Team WHERE OwnerID = %s;
                    """,
                    (new_owner_id,),
                )
                existing_team = cur.fetchone()
                if existing_team:
                    raise ValueError(
                        f"Transfer failed; the new owner already owns a team ({existing_team[1]}). Each owner can only own one team."
                    )

                # Perform the transfer
                cur.execute(
                    """
                    UPDATE Team
                    SET OwnerID = %s
                    WHERE TeamID = %s AND OwnerID = %s;
                    """,
                    (new_owner_id, team_id, current_owner_id),
                )
                if cur.rowcount == 0:
                    raise ValueError(
                        "Transfer failed; team not owned by current owner."
                    )
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


def finalize_tournament_match_from_plays(match_id):
    """
    Recompute scores for a tournament match from Play rows, set winner, and lock the match.
    Seasonal matches are ignored (handled by DB triggers elsewhere).
    Returns True if the match was updated, False otherwise.
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT m.matchid,
                           m.hometeamid,
                           m.awayteamid,
                           m.matchstartdatetime
                    FROM Match m
                    JOIN TournamentMatch tm ON tm.matchid = m.matchid
                    WHERE m.matchid = %s;
                    """,
                    (match_id,),
                )
                match = cur.fetchone()
                if not match:
                    return False

                match_start = match["matchstartdatetime"]
                home_team_id = match["hometeamid"]
                away_team_id = match["awayteamid"]

                def _score_for_team(team_id):
                    cur.execute(
                        """
                        SELECT COALESCE(SUM(COALESCE(pl.GoalsScored, 0) + COALESCE(pl.PenaltiesScored, 0)), 0) AS goals
                        FROM Play pl
                        JOIN Employed em ON em.UsersID = pl.PlayerID
                        JOIN Employment e ON e.EmploymentID = em.EmploymentID
                        WHERE pl.MatchID = %s
                          AND em.TeamID = %s
                          AND e.StartDate <= %s
                          AND e.EndDate >= %s;
                        """,
                        (match_id, team_id, match_start, match_start),
                    )
                    row = cur.fetchone()
                    return row["goals"] if row and row["goals"] is not None else 0

                home_score = _score_for_team(home_team_id)
                away_score = _score_for_team(away_team_id)

                winner_team = None
                if home_score > away_score:
                    winner_team = home_team_id
                elif away_score > home_score:
                    winner_team = away_team_id

                cur.execute(
                    """
                    UPDATE Match
                    SET HomeTeamScore = %s,
                        AwayTeamScore = %s,
                        WinnerTeam = %s,
                        IsLocked = TRUE
                    WHERE MatchID = %s;
                    """,
                    (home_score, away_score, winner_team, match_id),
                )
                return True
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


def fetch_seasons_for_dropdown():
    """Fetch distinct season years for dropdown."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT DISTINCT EXTRACT(YEAR FROM SeasonYear)::INT AS seasonyear
                FROM Season
                ORDER BY seasonyear DESC;
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_leagues_for_dropdown():
    """Fetch all leagues for dropdown."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT leagueid, name AS leaguename
                FROM League
                ORDER BY name;
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_tournaments_for_dropdown():
    """Fetch all tournaments for dropdown."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT tournamentid, name AS tournamentname
                FROM Tournament
                ORDER BY name;
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_all_matches_with_filters(
    admin_id, season_year=None, league_id=None, tournament_id=None
):
    """
    Fetch all matches (league and tournament) that the admin can manage,
    with optional filters for season year, league, or tournament.
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Build the query dynamically based on filters
            query = """
                -- League matches (seasonal matches)
                SELECT DISTINCT
                    m.matchid,
                    m.hometeamname,
                    m.awayteamname,
                    m.matchstartdatetime,
                    m.hometeamscore,
                    m.awayteamscore,
                    m.islocked,
                    'league' as match_type,
                    l.leagueid,
                    l.name as league_name,
                    s.seasonno,
                    s.seasonyear,
                    NULL::INT as tournamentid,
                    NULL::VARCHAR as tournament_name
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
            """
            params = [admin_id]

            if season_year:
                query += " AND EXTRACT(YEAR FROM s.seasonyear) = %s"
                params.append(season_year)

            if league_id:
                query += " AND l.leagueid = %s"
                params.append(int(league_id))

            query += """
                UNION ALL
                
                -- Tournament matches
                SELECT DISTINCT
                    m.matchid,
                    m.hometeamname,
                    m.awayteamname,
                    m.matchstartdatetime,
                    m.hometeamscore,
                    m.awayteamscore,
                    m.islocked,
                    'tournament' as match_type,
                    NULL::INT as leagueid,
                    NULL::VARCHAR as league_name,
                    NULL::INT as seasonno,
                    NULL::DATE as seasonyear,
                    t.tournamentid,
                    t.name as tournament_name
                FROM Match m
                JOIN TournamentMatch tm ON m.matchid = tm.matchid
                JOIN Round r ON r.t_matchid = tm.matchid
                JOIN Tournament t ON r.tournamentid = t.tournamentid
                JOIN TournamentModeration tmod ON t.tournamentid = tmod.t_id
                WHERE tmod.adminid = %s
            """
            params.append(admin_id)

            if tournament_id:
                query += " AND t.tournamentid = %s"
                params.append(int(tournament_id))

            query += " ORDER BY matchstartdatetime DESC;"

            cur.execute(query, params)
            return cur.fetchall()
    finally:
        conn.close()


def toggle_league_match_lock_by_admin(match_id, admin_id):
    """
    Toggle lock/unlock for a league match with admin permission check.
    Returns the number of rows affected (0 if no permission, 1 if successful).
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # Try to update league match
                cur.execute(
                    """
                    UPDATE Match M1
                    SET IsLocked = NOT IsLocked
                    WHERE EXISTS (
                        SELECT 1
                        FROM SeasonModeration SMo1
                        JOIN Season S1 USING (LeagueID, SeasonNo, SeasonYear)
                        JOIN SeasonalMatch SMa1 USING (LeagueID, SeasonNo, SeasonYear)
                        WHERE SMa1.MatchID = %s
                        AND M1.MatchID = SMa1.MatchID
                        AND SMo1.AdminID = %s
                    );
                    """,
                    (match_id, admin_id),
                )
                rows_affected = cur.rowcount
                return rows_affected
    finally:
        conn.close()


def toggle_tournament_match_lock_by_admin(match_id, admin_id):
    """
    Toggle lock/unlock for a tournament match with admin permission check.
    Returns the number of rows affected (0 if no permission, 1 if successful).
    NOTE: Based on requirements, tournament matches should NOT be locked via this page.
    This method is provided for completeness but may not be used.
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # Try to update tournament match
                cur.execute(
                    """
                    UPDATE Match M1
                    SET IsLocked = NOT IsLocked
                    WHERE EXISTS (
                        SELECT 1
                        FROM TournamentModeration TMOD
                        JOIN Tournament T ON TMOD.T_ID = T.TournamentID
                        JOIN Round R ON T.TournamentID = R.TournamentID
                        JOIN TournamentMatch TM ON R.T_MatchID = TM.MatchID
                        WHERE TM.MatchID = %s
                        AND M1.MatchID = TM.MatchID
                        AND TMOD.AdminID = %s
                    );
                    """,
                    (match_id, admin_id),
                )
                rows_affected = cur.rowcount
                return rows_affected
    finally:
        conn.close()


def fetch_player_stats_all(player_id):
    """Fetch overall statistics for a player from PlayerStatsAll view."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM PlayerStatsAll
                WHERE UsersID = %s;
                """,
                (player_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def fetch_player_season_stats(
    player_id, league_id=None, season_no=None, season_year=None
):
    """
    Fetch season-specific statistics for a player.
    If all parameters are provided, returns stats for that specific season.
    If only player_id is provided, returns all seasons the player participated in.
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT *
                FROM PlayerSeasonStats
                WHERE UsersID = %s
            """
            params = [player_id]

            if league_id is not None:
                query += " AND LeagueID = %s"
                params.append(league_id)

            if season_no is not None:
                query += " AND SeasonNo = %s"
                params.append(season_no)

            if season_year is not None:
                query += " AND SeasonYear = %s"
                params.append(season_year)

            query += " ORDER BY SeasonYear DESC, SeasonNo DESC, Name;"

            cur.execute(query, params)
            return cur.fetchall()
    finally:
        conn.close()


def fetch_player_tournament_stats(player_id):
    """Fetch tournament statistics for a player from PlayerTournamentStats view."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM PlayerTournamentStats
                WHERE UsersID = %s
                ORDER BY TournamentID DESC;
                """,
                (player_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_player_available_seasons(player_id):
    """Fetch distinct league/season combinations that a player has participated in."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT DISTINCT
                    LeagueID,
                    Name AS LeagueName,
                    SeasonNo,
                    SeasonYear
                FROM PlayerSeasonStats
                WHERE UsersID = %s
                ORDER BY SeasonYear DESC, SeasonNo DESC, Name;
                """,
                (player_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_player_available_leagues(player_id):
    """Fetch distinct leagues that a player has participated in."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT DISTINCT
                    LeagueID,
                    Name AS LeagueName
                FROM PlayerSeasonStats
                WHERE UsersID = %s
                ORDER BY Name;
                """,
                (player_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_player_trainings(player_id):
    """
    Fetch all training sessions for a player, including attendance status.
    Returns trainings from coaches on the same team, ordered by date (upcoming first).
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT 
                    TS.SessionID,
                    TS.SessionDate,
                    TS.Location,
                    TS.Focus,
                    TS.CoachID,
                    UC.FirstName AS CoachFirstName,
                    UC.LastName AS CoachLastName,
                    TA.Status AS AttendanceStatus,
                    T.TeamID,
                    T.TeamName
                FROM TrainingSession TS
                JOIN Coach CO ON TS.CoachID = CO.UsersID
                JOIN Employee E ON CO.UsersID = E.UsersID
                JOIN Team T ON E.TeamID = T.TeamID
                JOIN Users UC ON CO.UsersID = UC.UsersID
                LEFT JOIN TrainingAttendance TA ON TS.SessionID = TA.SessionID AND TA.PlayerID = %s
                WHERE EXISTS (
                    SELECT 1
                    FROM Employee E2
                    WHERE E2.UsersID = %s
                    AND E2.TeamID = T.TeamID
                )
                ORDER BY TS.SessionDate DESC;
                """,
                (player_id, player_id),
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_player_offers(player_id):
    """
    Fetch all offers and invites for a player.
    Returns offers ordered by date (newest first).
    Only returns offers when the player has no responsible coach (no team or team has no coach).
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT 
                    O.OfferID,
                    O.AvailableUntil,
                    O.OfferedEndDate,
                    O.OfferStatus,
                    O.RequestingCoach,
                    RC.FirstName AS RequestingCoachFirstName,
                    RC.LastName AS RequestingCoachLastName,
                    E.TeamID,
                    T.TeamName
                FROM Offer O
                JOIN Coach C ON O.RequestingCoach = C.UsersID
                JOIN Employee E ON C.UsersID = E.UsersID
                JOIN Team T ON E.TeamID = T.TeamID
                JOIN Users RC ON O.RequestingCoach = RC.UsersID
                WHERE O.RequestedPlayer = %s
                  AND NOT EXISTS (
                      -- Check if player has a team with a coach
                      SELECT 1
                      FROM Employee PE
                      JOIN Employee CE ON CE.TeamID = PE.TeamID
                      JOIN Coach C2 ON CE.UsersID = C2.UsersID
                      WHERE PE.UsersID = O.RequestedPlayer
                        AND PE.TeamID IS NOT NULL
                  )
                ORDER BY O.AvailableUntil DESC;
                """,
                (player_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def update_training_attendance(player_id, session_id, status):
    """
    Update or insert training attendance for a player.
    Status: 1 = Attended/Joined, 0 = Skipped/Absent
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # Check if training session exists and is in the future
                cur.execute(
                    """
                    SELECT SessionDate FROM TrainingSession WHERE SessionID = %s;
                    """,
                    (session_id,),
                )
                session_row = cur.fetchone()
                if not session_row:
                    raise ValueError("Training session not found.")

                # Verify player is on the same team as the coach
                cur.execute(
                    """
                    SELECT 1
                    FROM TrainingSession ts
                    JOIN Coach c ON ts.CoachID = c.UsersID
                    JOIN Employee e_coach ON c.UsersID = e_coach.UsersID
                    JOIN Employee e_player ON e_player.UsersID = %s
                    WHERE ts.SessionID = %s
                    AND e_coach.TeamID = e_player.TeamID;
                    """,
                    (player_id, session_id),
                )
                if not cur.fetchone():
                    raise ValueError(
                        "You are not on the same team as this training's coach."
                    )

                # Insert or update attendance
                cur.execute(
                    """
                    INSERT INTO TrainingAttendance (SessionID, PlayerID, Status)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (SessionID, PlayerID)
                    DO UPDATE SET Status = EXCLUDED.Status;
                    """,
                    (session_id, player_id, status),
                )
    finally:
        conn.close()


from psycopg2.extras import RealDictCursor


def create_training_session(coach_id, session_date, location, focus):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO TrainingSession (CoachID, SessionDate, Location, Focus)
                VALUES (%s, %s, %s, %s)
            """,
                (coach_id, session_date, location, focus),
            )
            conn.commit()
    finally:
        conn.close()


def fetch_coach_sessions(coach_id):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM TrainingSession 
                WHERE CoachID = %s 
                ORDER BY SessionDate ASC
            """,
                (coach_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_session_details(session_id):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Oturum detayları + Katılan oyuncular
            cur.execute(
                """
                SELECT 
                    ts.*, 
                    p.FirstName, p.LastName, p.Position,
                    ta.Status
                FROM TrainingSession ts
                LEFT JOIN TrainingAttendance ta ON ts.SessionID = ta.SessionID
                LEFT JOIN Users p ON ta.PlayerID = p.UsersID
                WHERE ts.SessionID = %s
            """,
                (session_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def log_player_injury_db(
    player_id,
    match_id,
    training_id,
    injury_date,
    injury_type,
    description,
    recovery_date,
):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Injury tablosuna ekle
            cur.execute(
                """
                INSERT INTO Injury (PlayerID, MatchID, TrainingID, InjuryDate, InjuryType, Description, RecoveryDate)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    player_id,
                    match_id,
                    training_id,
                    injury_date,
                    injury_type,
                    description,
                    recovery_date,
                ),
            )

            # 2. Oyuncuyu "Ineligible" yap (Player tablosundaki IsEligible alanı)
            cur.execute(
                """
                UPDATE Player 
                SET IsEligible = 'Injured' 
                WHERE UsersID = %s
            """,
                (player_id,),
            )

            conn.commit()
    finally:
        conn.close()


def is_player_eligible(player_id):
    """Oyuncunun sakat olup olmadığını kontrol eder (Eligible = 'eligible')."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Player tablosunda IsEligible sütununu kontrol et (büyük/küçük harf duyarsız yapalım)
            cur.execute(
                "SELECT IsEligible FROM Player WHERE UsersID = %s", (player_id,)
            )
            result = cur.fetchone()

            # Eğer kayıt varsa ve durumu 'eligible' ise True döner
            if result and str(result[0]).lower() == "eligible":
                return True
            return False
    finally:
        conn.close()


def get_player_injury_status(player_id):
    """
    Oyuncunun uygunluk durumunu ve varsa son iyileşme tarihini döndürür.
    Return: (is_eligible (bool), recovery_date (datetime or None))
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Oyuncunun statüsünü ve son sakatlık kaydındaki iyileşme tarihini çek
            cur.execute(
                """
                SELECT 
                    p.IsEligible,
                    (SELECT RecoveryDate FROM Injury i 
                     WHERE i.PlayerID = p.UsersID 
                     ORDER BY i.InjuryDate DESC LIMIT 1) as RecoveryDate
                FROM Player p
                WHERE p.UsersID = %s
            """,
                (player_id,),
            )
            row = cur.fetchone()

            if not row:
                return (False, None)

            is_eligible_str = str(row[0]).lower() if row[0] else ""
            is_currently_eligible = is_eligible_str == "eligible"
            recovery_date = row[1]

            return (is_currently_eligible, recovery_date)
    finally:
        conn.close()


def fetch_session_date(session_id):
    """Antrenman tarihini döndürür."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT SessionDate FROM TrainingSession WHERE SessionID = %s",
                (session_id,),
            )
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


def clear_player_injury_db(player_id):
    """Oyuncunun sakatlığını manuel olarak kaldırır (Eligible yapar)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE Player SET IsEligible = 'Eligible' WHERE UsersID = %s",
                (player_id,),
            )
            conn.commit()
    finally:
        conn.close()


def update_expired_injuries():
    """
    Otomatik Bakım: İyileşme tarihi gelmiş veya geçmiş olan oyuncuların
    statüsünü 'Injured' durumundan 'Eligible' durumuna çeker.
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # Mantık:
                # 1. Oyuncu şu an 'Injured' (veya Eligible değil) OLMALI.
                # 2. Son sakatlık kaydındaki RecoveryDate BUGÜN veya GEÇMİŞ OLMALI.
                cur.execute(
                    """
                    UPDATE Player p
                    SET IsEligible = 'Eligible'
                    WHERE (p.IsEligible IS NULL OR LOWER(p.IsEligible) != 'eligible')
                    AND EXISTS (
                        SELECT 1 FROM Injury i
                        WHERE i.PlayerID = p.UsersID
                        -- En son girilen sakatlık kaydına bakıyoruz
                        AND i.InjuryDate = (
                            SELECT MAX(InjuryDate) FROM Injury sub_i WHERE sub_i.PlayerID = p.UsersID
                        )
                        -- İyileşme tarihi bugün veya geçmiş mi?
                        AND i.RecoveryDate <= CURRENT_DATE
                    );
                """
                )
    finally:
        conn.close()
