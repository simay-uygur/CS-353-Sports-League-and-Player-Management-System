import math
import random
from collections import defaultdict
from datetime import datetime, timedelta

import psycopg2
from flask import Blueprint, render_template, request, redirect, url_for, session
from psycopg2.extras import RealDictCursor

from db import get_connection

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")



@admin_bp.before_request
def require_admin_session():
    if session.get("user_id") is None or session.get("role") != "admin":
        session["next"] = request.path
        return redirect(url_for("login"))


@admin_bp.route("/tournaments")
def view_tournaments():
    admin_id = session.get("user_id")
    if not admin_id:
        return redirect(url_for("login"))

    tournaments = _fetch_tournaments(admin_id)
    if not tournaments:
        return render_template(
            "admin_view_tournaments.html",
            tournaments=[],
            selected_tournament=None,
            matches_by_round={},
        )

    requested_tournament_id = request.args.get("tournament_id")
    selected_tournament = _select_tournament(requested_tournament_id, tournaments)
    matches_by_round = _fetch_matches_grouped(selected_tournament["tournamentid"])

    return render_template(
        "admin_view_tournaments.html",
        tournaments=tournaments,
        selected_tournament=selected_tournament,
        matches_by_round=matches_by_round,
    )


@admin_bp.route("/tournaments/create", methods=["GET", "POST"])
def create_tournament_form():
    teams = _fetch_all_teams()
    error_message = None
    form_data = request.form if request.method == "POST" else {}
    selected_team_ids = form_data.getlist("team_ids") if request.method == "POST" else []

    if request.method == "POST":
        try:
            result = _create_tournament_with_bracket(form_data, session.get("user_id"))
            return redirect(url_for("admin.view_tournaments", tournament_id=result["tournament_id"]))
        except ValueError as exc:
            error_message = str(exc)
        except psycopg2.Error as exc:
            error_message = getattr(exc.diag, "message_primary", str(exc))

    return render_template(
        "admin_create_tournament.html",
        teams=teams,
        error_message=error_message,
        form_data=form_data,
        selected_team_ids=set(selected_team_ids),
    )


def _fetch_tournaments(admin_id):
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


def _select_tournament(requested_id, tournaments):
    if requested_id:
        for tournament in tournaments:
            if str(tournament["tournamentid"]) == requested_id:
                return tournament
    return tournaments[0]


def _fetch_matches_grouped(tournament_id):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT r.roundno,
                       m.matchid,
                       m.hometeamname,
                       m.awayteamname,
                       m.hometeamscore,
                       m.awayteamscore,
                       m.matchstartdatetime
                FROM Round r
                JOIN Match m ON r.t_matchid = m.matchid
                WHERE r.tournamentid = %s
                """,
                #ORDER BY r.roundno, m.matchstartdatetime;
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


def _create_tournament_with_bracket(form_data, admin_id):
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

    if size % 2 != 0:
        raise ValueError("Please select an even number of teams so leaf rounds equal teams ÷ 2.")

    if len(set(team_ids)) != len(team_ids):
        raise ValueError("Each team can only be selected once.")

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO Tournament (Name, Size)
                    VALUES (%s, %s)
                    RETURNING TournamentID;
                    """,
                    (name, size),
                )
                tournament_id = cur.fetchone()[0]

                cur.execute(
                    """
                    INSERT INTO TournamentModeration (T_ID, AdminID)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING;
                    """,
                    (tournament_id, admin_id),
                )

                leaf_match_ids = _build_rounds_and_matches(cur, tournament_id, team_ids, start_date)

        return {"tournament_id": tournament_id, "match_ids": leaf_match_ids}
    finally:
        conn.close()


def _lookup_team_names(cur, team_ids):
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


def _build_rounds_and_matches(cur, tournament_id, team_ids, start_date):
    team_count = len(team_ids)
    total_matches = team_count - 1
    leaf_start_index = (total_matches // 2) + 1

    shuffled_ids = team_ids[:]
    random.shuffle(shuffled_ids)
    team_names = _lookup_team_names(cur, team_ids)

    leaf_pairs = [
        (shuffled_ids[i], shuffled_ids[i + 1])
        for i in range(0, len(shuffled_ids), 2)
    ]

    pair_iter = iter(leaf_pairs)
    created_matches = []
    match_counter = 0

    for round_no in range(1, total_matches + 1):
        if round_no >= leaf_start_index:
            try:
                home_id, away_id = next(pair_iter)
            except StopIteration:
                raise ValueError("Not enough team pairs to populate leaf matches.")

            home_name = team_names.get(home_id)
            away_name = team_names.get(away_id)
            if not home_name or not away_name:
                raise ValueError("One or more selected teams no longer exist.")

            # Her maç için 3 gün aralıkla saat 19:00'da tarih hesapla
            match_date = start_date + timedelta(days=match_counter * 3)
            match_datetime = match_date.replace(hour=19, minute=0, second=0)

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
                (home_id, away_id, match_datetime, home_name, away_name),
            )
            match_id = cur.fetchone()[0]
            created_matches.append(match_id)
            match_counter += 1

            cur.execute(
                "INSERT INTO TournamentMatch (MatchID) VALUES (%s);",
                (match_id,),
            )

            cur.execute(
                """
                INSERT INTO Round (TournamentID, RoundNo, T_MatchID)
                VALUES (%s, %s, %s);
                """,
                (tournament_id, round_no, match_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO Round (TournamentID, RoundNo, T_MatchID)
                VALUES (%s, %s, NULL);
                """,
                (tournament_id, round_no),
            )

    return created_matches


def _to_int(value, label, required=False, min_value=None):
    if value in (None, ""):
        if required:
            raise ValueError(f"{label} is required.")
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a valid number.")
    if min_value is not None and number < min_value:
        raise ValueError(f"{label} must be at least {min_value}.")
    return number


def _normalize_datetime(raw_value):
    if not raw_value:
        return None
    value = raw_value.replace("T", " ")
    if len(value) == 16:
        value += ":00"
    return value


def _fetch_all_teams():
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


def _round_level(round_no):
    if round_no <= 0:
        return 1
    return math.floor(math.log2(round_no)) + 1
