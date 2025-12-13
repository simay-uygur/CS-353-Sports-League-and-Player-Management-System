from db import get_connection
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify, Blueprint, render_template

artunsPart = Blueprint("artunsPart", __name__, url_prefix="/")


@artunsPart.route('/ui/referee')
def view_referee_dashboard():
    # Corresponds to Figure 8
    return render_template('referee.html')


def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """Helper function to execute SQL queries safely."""
    conn = get_connection()
    if conn is None:
        return None

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    result = None
    try:
        cursor.execute(query, params)

        if commit:
            conn.commit()
            if 'RETURNING' in query.upper():
                result = cursor.fetchone()

        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()

    except Exception as e:
        if commit:
            conn.rollback()
        print(f"Query Error: {e}")
        result = {'error': str(e)}
    finally:
        cursor.close()
        conn.close()

    return result

# ==============================================================================
# 2. Topic Specific Functionalities
# ==============================================================================

# ------------------------------------------------------------------------------
# [cite_start]2.1 Referee Pages (Assigned Matches & Filtering) [cite: 944, 987, 1002]
# ------------------------------------------------------------------------------


@artunsPart.route('/referee/matches', methods=['GET'])
def get_referee_matches():
    """
    Corresponds to Figure 8 & Source [1002-1005].
    Retrieves assigned matches for the referee for the current day.
    """
    ref_id = request.args.get('referee_id')

    if not ref_id:
        return jsonify({'error': 'Referee ID is required'}), 400

    query = """
        SELECT *
        FROM RefereeMatchView
        WHERE matchstartdatetime::date = CURRENT_DATE
        AND refereeid = %s;
    """
    matches = execute_query(query, (ref_id,), fetch_all=True)
    return jsonify(matches)


@artunsPart.route('/referee/filters', methods=['GET'])
def get_referee_filter_options():
    """
    Corresponds to Source [992-1000].
    Populates dropdowns for Teams, Leagues, and Tournaments.
    """
    teams = execute_query(
        "SELECT teamid, teamname FROM Team ORDER BY teamname;", fetch_all=True)
    leagues = execute_query(
        "SELECT leagueid, name AS leaguename FROM League ORDER BY name;", fetch_all=True)
    tournaments = execute_query(
        "SELECT tournamentid, name AS tournamentname FROM Tournament ORDER BY name;", fetch_all=True)

    return jsonify({
        'teams': teams,
        'leagues': leagues,
        'tournaments': tournaments
    })

# ------------------------------------------------------------------------------
# [cite_start]2.2 Referee Pages (Match Roster & Info Entry) [cite: 1050, 1054, 1096]
# ------------------------------------------------------------------------------


@artunsPart.route('/match/<int:match_id>/roster/home', methods=['GET'])
def get_home_roster(match_id):
    """
    Corresponds to Source [1054-1094].
    Gets roster info, injury status, and ban status for the Home Team.
    """
    query = """
        SELECT
            P1.*,
            CASE
                WHEN (EXISTS(SELECT I1.injuryid FROM Injury I1
                    WHERE I1.playerid = U1.usersid
                    AND (M1.matchstartdatetime BETWEEN I1.injurydate AND I1.recoverydate))
                ) THEN TRUE ELSE FALSE
            END AS wasInjured,
            CASE
                WHEN (EXISTS(SELECT B1.banid FROM Ban B1
                    WHERE B1.playerid = U1.usersid
                    AND (M1.matchstartdatetime BETWEEN B1.banstartdate AND B1.banenddate))
                ) THEN TRUE ELSE FALSE
            END AS disciplinarilyPunished,
            U1.usersid, U1.firstname, U1.lastname,
            U2.usersid as sub_usersid, U2.firstname as sub_firstname, U2.lastname as sub_lastname,
            M1.winnerteam, M1.hometeamscore, M1.awayteamscore
        FROM ((((Match M1
            JOIN AllEmploymentInfo A1 ON (M1.hometeamid = A1.teamid))
            JOIN Users U1 USING (usersid))
            JOIN Player Per1 ON (Per1.usersid = U1.usersid))
            LEFT JOIN Play P1 USING (matchid))
            LEFT JOIN Users U2 ON (P1.substitutionid = U2.usersid)
        WHERE M1.matchid = %s
        AND (M1.matchstartdatetime BETWEEN A1.startdate AND COALESCE(A1.enddate, NOW() + INTERVAL '1 year'))
        ORDER BY U1.firstname, U1.lastname;
    """
    roster = execute_query(query, (match_id,), fetch_all=True)
    return jsonify(roster)


@artunsPart.route('/match/<int:match_id>/roster/away', methods=['GET'])
def get_away_roster(match_id):
    """
    Corresponds to Source [1096-1134].
    Gets roster info, injury status, and ban status for the Away Team.
    """
    query = """
        SELECT
            P1.*,
            CASE
                WHEN (EXISTS(SELECT I1.injuryid FROM Injury I1
                    WHERE I1.playerid = U1.usersid
                    AND (M1.matchstartdatetime BETWEEN I1.injurydate AND I1.recoverydate))
                ) THEN TRUE ELSE FALSE
            END AS wasInjured,
            CASE
                WHEN (EXISTS(SELECT B1.banid FROM Ban B1
                    WHERE B1.playerid = U1.usersid
                    AND (M1.matchstartdatetime BETWEEN B1.banstartdate AND B1.banenddate))
                ) THEN TRUE ELSE FALSE
            END AS disciplinarilyPunished,
            U1.usersid, U1.firstname, U1.lastname,
            U2.usersid as sub_usersid, U2.firstname as sub_firstname, U2.lastname as sub_lastname,
            M1.winnerteam, M1.hometeamscore, M1.awayteamscore
        FROM ((((Match M1
            JOIN AllEmploymentInfo A1 ON (M1.awayteamid = A1.teamid))
            JOIN Users U1 USING (usersid))
            JOIN Player Per1 ON (Per1.usersid = U1.usersid))
            LEFT JOIN Play P1 USING (matchid))
            LEFT JOIN Users U2 ON (P1.substitutionid = U2.usersid)
        WHERE M1.matchid = %s
        AND (M1.matchstartdatetime BETWEEN A1.startdate AND COALESCE(A1.enddate, NOW() + INTERVAL '200 year'))
        ORDER BY U1.firstname, U1.lastname;
    """
    roster = execute_query(query, (match_id,), fetch_all=True)
    return jsonify(roster)

# ------------------------------------------------------------------------------
# [cite_start]2.3 Referee Pages (Saving Match Play Data) [cite: 1181, 1187, 1204]
# ------------------------------------------------------------------------------


@artunsPart.route('/match/play/save', methods=['POST'])
def save_play_info():
    """
    Corresponds to Source [1187-1234].
    Updates or Inserts play data (Goals, Cards, Passes, etc.) for a player.
    """
    data = request.json

    # 1. Try UPDATE first (Source 1187)
    update_query = """
        UPDATE Play
        SET SubstitutionID = %s, StartTime = %s, StopTime = %s,
            SuccessfulPasses = %s, GoalsScored = %s, AssistsMade = %s,
            TotalPasses = %s, YellowCards = %s, RedCards = %s, Saves = %s
        WHERE MatchID = %s AND PlayerID = %s
        RETURNING PlayID;
    """
    update_params = (
        data.get('substitutionid'), data.get(
            'starttime'), data.get('stoptime'),
        data.get('successfulpasses'), data.get(
            'goalsscored'), data.get('assistsmade'),
        data.get('totalpasses'), data.get('yellowcards'), data.get('redcards'),
        data.get('saves'), data.get('matchid'), data.get('playerid')
    )
    result = execute_query(update_query, update_params, commit=True)

    # 2. If Update returns nothing, perform INSERT (Source 1201-1204)
    if not result:
        insert_query = """
            INSERT INTO Play (
                MatchID, PlayerID, SubstitutionID, StartTime, StopTime,
                SuccessfulPasses, GoalsScored, PenaltiesScored, AssistsMade,
                TotalPasses, YellowCards, RedCards, Saves
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING PlayID;
        """
        insert_params = (
            data.get('matchid'), data.get(
                'playerid'), data.get('substitutionid'),
            data.get('starttime'), data.get(
                'stoptime'), data.get('successfulpasses'),
            data.get('goalsscored'), data.get('penaltiesscored', 0),
            data.get('assistsmade'), data.get(
                'totalpasses'), data.get('yellowcards'),
            data.get('redcards'), data.get('saves')
        )
        result = execute_query(insert_query, insert_params, commit=True)

    return jsonify(result)

# ------------------------------------------------------------------------------
# [cite_start]2.4 Referee Pages (Injury Management) [cite: 1302, 1304, 1312, 1333]
# ------------------------------------------------------------------------------


@artunsPart.route('/injury', methods=['GET', 'POST', 'DELETE'])
def manage_injury():
    """
    Handles fetching, recording, and deleting injuries for a player/match.
    """
    # GET: Fetch existing injury (Source 1302)
    if request.method == 'GET':
        pid = request.args.get('playerid')
        mid = request.args.get('matchid')
        query = "SELECT * FROM Injury WHERE playerid=%s AND matchid=%s;"
        result = execute_query(query, (pid, mid), fetch_all=True)
        return jsonify(result)

    # POST: Update or Insert Injury (Source 1304, 1312)
    if request.method == 'POST':
        data = request.json

        # Try Update
        update_query = """
            UPDATE Injury
            SET MatchID = %s, TrainingID = %s, InjuryDate = %s,
                InjuryType = %s, Description = %s, RecoveryDate = %s
            WHERE PlayerID = %s
            RETURNING InjuryID;
        """
        params = (
            data.get('matchid'), data.get(
                'trainingid'), data.get('injurydate'),
            data.get('injurytype'), data.get(
                'description'), data.get('recoverydate'),
            data.get('playerid')
        )
        result = execute_query(update_query, params, commit=True)

        # If no update happened, Insert
        if not result:
            insert_query = """
                INSERT INTO Injury (
                    PlayerID, MatchID, TrainingID, InjuryDate,
                    InjuryType, Description, RecoveryDate
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING InjuryID;
            """
            insert_params = (
                data.get('playerid'), data.get(
                    'matchid'), data.get('trainingid'),
                data.get('injurydate'), data.get('injurytype'),
                data.get('description'), data.get('recoverydate')
            )
            result = execute_query(insert_query, insert_params, commit=True)
        return jsonify(result)

    # DELETE: Delete Injury (Source 1333)
    if request.method == 'DELETE':
        mid = request.args.get('matchid')
        query = "DELETE FROM Injury WHERE MatchID = %s AND TrainingID IS NULL RETURNING InjuryID;"
        result = execute_query(query, (mid,), commit=True)
        return jsonify(result)

# ------------------------------------------------------------------------------
# [cite_start]2.5 Admin Page (Viewing & Locking Matches) [cite: 1373, 1386, 1397]
# ------------------------------------------------------------------------------


@artunsPart.route('/admin/matches/filters', methods=['GET'])
def get_admin_filter_options():
    """
    Corresponds to Source [1374-1382].
    Dropdowns for Admin Match View (Season, League, Tournament).
    """
    seasons = execute_query(
        "SELECT DISTINCT SeasonYear FROM Season ORDER BY SeasonYear;", fetch_all=True)
    leagues = execute_query(
        "SELECT leagueid, name AS leaguename FROM League ORDER BY name;", fetch_all=True)
    tournaments = execute_query(
        "SELECT tournamentid, name AS tournamentname FROM Tournament ORDER BY name;", fetch_all=True)

    return jsonify({'seasons': seasons, 'leagues': leagues, 'tournaments': tournaments})


@artunsPart.route('/admin/match/lock', methods=['POST'])
def lock_match():
    """
    Corresponds to Source [1386-1406].
    Toggles the lock status of a match. Checks permission for Season Admin or Tournament Admin.
    """
    data = request.json
    mid = data.get('matchid')
    aid = data.get('adminid')

    # 1. Attempt lock/unlock for Seasonal Match (Source 1386)
    query_season = """
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
        ) RETURNING MatchID;
    """
    result = execute_query(query_season, (mid, aid), commit=True)

    if result:
        return jsonify({'status': 'success', 'type': 'season', 'matchid': result['matchid']})

    # 2. Attempt lock/unlock for Tournament Match (Source 1397)
    query_tournament = """
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
        ) RETURNING MatchID;
    """
    result = execute_query(query_tournament, (mid, aid), commit=True)

    if result:
        return jsonify({'status': 'success', 'type': 'tournament', 'matchid': result['matchid']})

    return jsonify({'status': 'failed', 'message': 'Match not found or Admin unauthorized'}), 403

# ------------------------------------------------------------------------------
# [cite_start]2.6 Player Statistics [cite: 1431, 1440, 1469]
# ------------------------------------------------------------------------------


@artunsPart.route('/stats/player/season', methods=['GET'])
def get_player_season_stats():
    """
    Corresponds to Source [1440].
    Get stats for a specific player in a specific season.
    """
    pid = request.args.get('playerid')
    lid = request.args.get('leagueid')
    sno = request.args.get('seasonno')
    syear = request.args.get('seasonyear')

    query = """
        SELECT *
        FROM PlayerSeasonStats PS1
        WHERE PS1.usersid = %s
        AND PS1.leagueid = %s
        AND PS1.seasonno = %s
        AND PS1.seasonyear = %s;
    """
    stats = execute_query(query, (pid, lid, sno, syear), fetch_all=True)
    return jsonify(stats)


@artunsPart.route('/stats/player/tournament', methods=['GET'])
def get_player_tournament_stats():
    """
    Corresponds to Source [1470].
    Get stats for a player in a specific tournament.
    """
    uid = request.args.get('usersid')
    query = "SELECT * FROM PlayerTournamentStats WHERE usersid = %s;"
    stats = execute_query(query, (uid,), fetch_all=True)
    return jsonify(stats)


@artunsPart.route('/stats/season/top_scorer', methods=['GET'])
def get_season_top_scorer():
    """
    Corresponds to Source [1457-1468].
    Get the top scorer of a season.
    """
    lid = request.args.get('leagueid')
    sno = request.args.get('seasonno')
    syear = request.args.get('seasonyear')

    query = """
        SELECT *
        FROM PlayerSeasonStats PS1
        WHERE PS1.leagueid = %s
        AND PS1.seasonno = %s
        AND PS1.seasonyear = %s
        AND PS1.totalgoals = (
            SELECT MAX(totalgoals)
            FROM PlayerSeasonStats PS2
            WHERE PS2.leagueid = %s
            AND PS2.seasonno = %s
            AND PS2.seasonyear = %s
        );
    """
    # Note: Params must be repeated for the subquery
    params = (lid, sno, syear, lid, sno, syear)
    result = execute_query(query, params, fetch_all=True)
    return jsonify(result)


if __name__ == '__main__':
    artunsPart.run(debug=True)
