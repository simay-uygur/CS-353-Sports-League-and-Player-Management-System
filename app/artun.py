from db import get_connection
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify, Blueprint, render_template

artunsPart = Blueprint("artunsPart", __name__, url_prefix="/")

# Check or add if these exists:
#


@artunsPart.route('/referee/edit_matches', methods=["GET"])
def view_referee_dashboard():
    # Corresponds to Figure 8
    return render_template('referee_matches.html')


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
            else:
                result = "success"

        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()

    except Exception as e:
        if commit:
            conn.rollback()
        print(f"Query Error: {e}")
        # result = {'error': str(e)}
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
    Supports multiple selections for teams, leagues, and tournaments.
    """
    ref_id = request.args.get('referee_id')
    team_ids = request.args.get('team_ids', '')
    league_ids = request.args.get('league_ids', '')
    tourn_ids = request.args.get('tournament_ids', '')

    if not ref_id:
        return jsonify({'error': 'Referee ID is required'}), 400

    query = """
        SELECT *
        FROM RefereeMatchView
        WHERE refereeid = %s
    """

    if 'today' in request.args:
        query += "AND matchstartdatetime::date = CURRENT_DATE"

    params = [ref_id]

    # [cite_start]Dynamic Filtering [cite: 991, 1002]
    # Handle multiple team selections
    if team_ids:
        team_list = [tid.strip() for tid in team_ids.split(',') if tid.strip()]
        if team_list:
            team_conditions = []
            for team_id in team_list:
                team_conditions.append("(hometeamid = %s OR awayteamid = %s)")
                params.extend([team_id, team_id])
            query += " AND (" + " OR ".join(team_conditions) + ")"

    # Competition filter (Multiple Leagues OR Multiple Tournaments)
    competition_conditions = []
    
    # Handle multiple league selections
    if league_ids:
        league_list = [lid.strip() for lid in league_ids.split(',') if lid.strip()]
        for league_id in league_list:
            competition_conditions.append("competitionname = (SELECT Name FROM League WHERE LeagueID = %s)")
            params.append(league_id)
    
    # Handle multiple tournament selections
    if tourn_ids:
        tourn_list = [tid.strip() for tid in tourn_ids.split(',') if tid.strip()]
        for tourn_id in tourn_list:
            competition_conditions.append("competitionname = (SELECT Name FROM Tournament WHERE TournamentID = %s)")
            params.append(tourn_id)
    
    # Join all competition conditions with OR
    if competition_conditions:
        query += " AND (" + " OR ".join(competition_conditions) + ")"

    query += ";"

    # Debug logging
    print(f"[DEBUG] Referee Matches Query: {query}")
    print(f"[DEBUG] Parameters: {params}")

    matches = execute_query(query, tuple(params), fetch_all=True)
    print(f"[DEBUG] Found {len(matches) if matches else 0} matches")
    return jsonify(matches if matches else [])


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
            M1.winnerteam, M1.hometeamscore, M1.awayteamscore,
            M1.hometeamname, M1.awayteamname, M1.matchstartdatetime,
            M1.IsLocked,
            A1.teamid
        FROM Match M1
            JOIN AllEmploymentInfo A1 ON (M1.hometeamid = A1.teamid)
            JOIN Users U1 USING (usersid)
            JOIN Player Per1 ON (Per1.usersid = U1.usersid)
            LEFT JOIN Play P1 ON P1.matchid = M1.matchid AND P1.playerid = U1.usersid
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
            M1.winnerteam, M1.hometeamscore, M1.awayteamscore,
            M1.hometeamname, M1.awayteamname, M1.matchstartdatetime,
            M1.IsLocked,
            A1.teamid
        FROM Match M1
            JOIN AllEmploymentInfo A1 ON (M1.awayteamid = A1.teamid)
            JOIN Users U1 USING (usersid)
            JOIN Player Per1 ON (Per1.usersid = U1.usersid)
            LEFT JOIN Play P1 ON (P1.matchid = M1.matchid AND P1.playerid = U1.usersid)
            LEFT JOIN Users U2 ON (P1.substitutionid = U2.usersid)
        WHERE M1.matchid = %s
        AND (M1.matchstartdatetime BETWEEN A1.startdate AND COALESCE(A1.enddate, NOW() + INTERVAL '1 year'))
        ORDER BY U1.firstname, U1.lastname;
    """
    roster = execute_query(query, (match_id,), fetch_all=True)
    return jsonify(roster)


@artunsPart.route('/match/substitute_roster', methods=['GET'])
def get_substitute_roster():

    matchid = request.args.get('matchid')
    teamid = request.args.get('teamid')
    usersid = request.args.get('usersid')

    query = """
        WITH playdate AS (SELECT matchstartdatetime AS value FROM Match WHERE matchid = %s )
        SELECT U.usersid, U.firstname, U.lastname
        FROM AllEmploymentInfo AE
        JOIN Users U USING (usersid)
        CROSS JOIN playdate PD
        WHERE AE.teamid = %s AND AE.usersid <> %s
        AND ( PD.value BETWEEN AE.startdate AND AE.enddate )
        AND NOT EXISTS (SELECT injuryid FROM Injury
                WHERE playerid = U.usersid
                AND (PD.value BETWEEN injurydate AND recoverydate))
        AND NOT EXISTS (SELECT banid FROM Ban
                WHERE playerid = U.usersid
                AND (PD.value BETWEEN banstartdate AND banenddate));
    """

    params = (
        matchid,
        teamid,
        usersid,
    )

    result = execute_query(query=query, params=params,
                           fetch_all=True, commit=False)

    return jsonify(result)

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

    # 1. Try UPDATE first
    update_query = """
        UPDATE Play
        SET SubstitutionID = %s, StartTime = %s, StopTime = %s,
            SuccessfulPasses = %s, GoalsScored = %s, AssistsMade = %s,
            TotalPasses = %s, YellowCards = %s, RedCards = %s,
            Saves = %s, PenaltiesScored = %s
        WHERE playid = %s
    """

    substitutionId = data.get('substitutionid')
    if substitutionId == '':
        substitutionId = None

    update_params = (
        substitutionId,
        data.get('starttime'),
        data.get('stoptime'),
        data.get('successfulpasses'),
        data.get('goalsscored'),
        data.get('assistsmade'),
        data.get('totalpasses'),
        data.get('yellowcards'),
        data.get('redcards'),
        data.get('saves'),
        data.get('penaltiesscored'),
        data.get('playid'),
    )

    result = execute_query(update_query, update_params, commit=True)

    # According to the design play shouldn't be inserted manually
    # if not result:
    #    insert_query = """
    #        INSERT INTO Play (
    #            MatchID, PlayerID, SubstitutionID, StartTime, StopTime,
    #            SuccessfulPasses, GoalsScored, PenaltiesScored, AssistsMade,
    #            TotalPasses, YellowCards, RedCards, Saves
    #        ) VALUES (
    #            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    #        ) RETURNING PlayID;
    #    """
    #    insert_params = (
    #        data.get('matchid'), data.get(
    #            'playerid'), data.get('substitutionid'),
    #        data.get('starttime'), data.get(
    #            'stoptime'), data.get('successfulpasses'),
    #        data.get('goalsscored'), data.get('penaltiesscored', 0),
    #        data.get('assistsmade'), data.get(
    #            'totalpasses'), data.get('yellowcards'),
    #        data.get('redcards'), data.get('saves')
    #    )
    #    result = execute_query(insert_query, insert_params, commit=True)

    return jsonify(result)

# ------------------------------------------------------------------------------
# [cite_start]2.4 Injury and Disciplinary Punishment Endpoints [cite: 1302, 1304, 1312, 1333]
# ------------------------------------------------------------------------------


@artunsPart.route('/injury', methods=['GET', 'POST', 'DELETE'])
def manage_injury():
    """
    Handles fetching, recording, and deleting injuries for a player/match.
    """
    # GET: Fetch existing injury
    if request.method == 'GET':
        pid = request.args.get('playerid')
        mid = request.args.get('matchid')
        query = "SELECT * FROM Injury WHERE playerid=%s AND matchid=%s;"
        result = execute_query(query, (pid, mid, ), fetch_one=True)
        return jsonify(result)

    # POST: Update or Insert Injury
    if request.method == 'POST':
        data = request.json

        matchid = None
        if (data.get('matchid')):
            matchid = data.get('matchid')

        trainingid = None
        if (data.get('trainingid')):
            trainingid = data.get('trainingid')

        # Try Update
        update_query = """
            UPDATE Injury
            SET MatchID = %s, TrainingID = %s,
                InjuryDate = TO_DATE(%s, 'YYYY-MM-DD') + INTERVAL '1 DAY',
                InjuryType = %s, Description = %s,
                RecoveryDate = TO_DATE(%s, 'YYYY-MM-DD')
            WHERE InjuryID = %s
        """
        params = (
            matchid, trainingid, data.get('injurydate'),
            data.get('injurytype'), data.get(
                'description'), data.get('recoverydate'),
            data.get('injuryid'),
        )
        result = execute_query(update_query, params, commit=True)

        # If no update happened, Insert
        if not result:
            insert_query = """
                INSERT INTO Injury (
                    PlayerID, MatchID, TrainingID, InjuryDate,
                    InjuryType, Description, RecoveryDate
                ) VALUES (%s, %s, %s, TO_DATE(%s, 'YYYY-MM-DD') + INTERVAL '1 DAY', %s, %s, TO_DATE(%s, 'YYYY-MM-DD'))
            """
            insert_params = (
                data.get('playerid'), matchid, trainingid,
                data.get('injurydate'), data.get('injurytype'),
                data.get('description'), data.get('recoverydate'),
            )
            result = execute_query(insert_query, insert_params, commit=True)
        return jsonify(result)

    # DELETE: Delete Injury
    if request.method == 'DELETE':
        iid = request.args.get('injuryid')
        query = "DELETE FROM Injury WHERE InjuryID = %s;"
        result = execute_query(query, (iid,), commit=True)
        return jsonify(result)


@artunsPart.route('/ban', methods=['GET', 'POST', 'DELETE'])
def manage_ban():

    if request.method == 'GET':
        pid = request.args.get('playerid')
        mdt = request.args.get('matchdatetime')
        query = "SELECT * FROM Ban WHERE playerid=%s AND BanStartDate = TO_DATE(%s, 'YYYY-MM-DD') + INTERVAL '1 DAY';"
        result = execute_query(query, (pid, mdt, ), fetch_one=True)
        return jsonify(result)

    # POST: Update or Insert Injury
    if request.method == 'POST':
        data = request.json

        # Try Update
        update_query = """
            UPDATE Ban
            SET BanEndDate = TO_DATE(%s, 'YYYY-MM-DD'),
            WHERE banid = %s
        """
        params = (request.args.get('banenddate'), request.args.get('banid'),)
        result = execute_query(update_query, params, commit=True)

        # If no update happened, Insert
        if not result:
            insert_query = """
                INSERT INTO Ban (
                    playerid, banstartdate, banenddate
                ) VALUES (%s, TO_DATE(%s, 'YYYY-MM-DD') + INTERVAL '1 DAY', TO_DATE(%s, 'YYYY-MM-DD'))
            """
            insert_params = (
                data.get('playerid'),
                data.get('banstartdate'),
                data.get('banenddate'),
            )
            result = execute_query(insert_query, insert_params, commit=True)
        return jsonify(result)

    # DELETE: Delete Injury
    if request.method == 'DELETE':
        bid = data.get('banid')
        query = "DELETE FROM Ban WHERE banid = %s;"
        result = execute_query(query, (bid,), commit=True)
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


@artunsPart.route('/match/lock', methods=['POST'])
def lock_match():
    """
    Corresponds to Source [1386-1406].
    Toggles the lock status of a match. Checks permission for Season Admin or Tournament Admin.
    """
    data = request.json
    mid = data.get('matchid')

    if 'adminid' in data:
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

    if 'refereeid' in data:
        rid = data.get('refereeid')

        # 1. Attempt lock for Seasonal Match (Source 1386)
        query_season = """
            UPDATE Match M1
            SET IsLocked = TRUE
            WHERE M1.MatchID = %s
            AND EXISTS (
                SELECT 1
                FROM RefereeMatchAttendance RMa1
                WHERE RMa1.MatchID = M1.MatchID
                AND RMa1.RefereeID = %s
            ) RETURNING MatchID;
        """
        result = execute_query(query_season, (mid, rid), commit=True)

        if result:
            return jsonify({'status': 'success', 'type': 'season', 'matchid': result['matchid']})

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
