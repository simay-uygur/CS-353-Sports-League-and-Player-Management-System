import psycopg2

from db import get_connection


def update_play(playid, form):
    cur = get_connection().cursor()

    cur.execute(
        """
        UPDATE Play
        SET
          SubstitutionID = %s,
          StartTime = %s,
          StopTime = %s,
          SuccessfulPasses = %s,
          GoalsScored = %s,
          PenaltiesScored = %s,
          AssistsMade = %s,
          TotalPasses = %s,
          YellowCards = %s,
          RedCards = %s,
          Saves = %s
        WHERE MatchID = %s
          AND PlayerID = %s
        """,
        (
            form["substitutionid"],
            form["starttime"],
            form["stoptime"],
            form["successfulpasses"],
            form["goalsscored"],
            form["penaltiesscored"],
            form["assistsmade"],
            form["totalpasses"],
            form["yellowcards"],
            form["redcards"],
            form["saves"],
            form["matchid"],
            form["playerid"],
        )
    )

    if cur.fetchone() is not None:
        cur.commit()

    else:
        cur.execute(
            """
            INSERT INTO Play (
              MatchID,
              PlayerID,
              SubstitutionID,
              StartTime,
              StopTime,
              SuccessfulPasses,
              GoalsScored,
              PenaltiesScored,
              AssistsMade,
              TotalPasses,
              YellowCards,
              RedCards,
              Saves
            )
            VALUES (
              %s,
              %s,
              %s,
              %s,
              %s,
              %s,
              %s,
              %s,
              %s,
              %s,
              %s,
              %s,
              %s
            )
            """,
            (
                form["matchid"],
                form["playerid"],
                form["substitutionid"],
                form["starttime"],
                form["stoptime"],
                form["successfulpasses"],
                form["goalsscored"],
                form["penaltiesscored"],
                form["assistsmade"],
                form["totalpasses"],
                form["yellowcards"],
                form["redcards"],
                form["saves"],
            )
        )
        cur.commit()


def match_hometeam_info(matchid):

    cur = get_connection().cursor()

    cur.execute(
        """
        SELECT
        P1.*,
        CASE
            WHEN (EXISTS( SELECT I1.injuryid FROM Injury I1
                WHERE I1.playerid = U1.usersid
                AND
                (M1.matchstartdatetime
                BETWEEN I1.injurydate AND I1.recoverydate)
                )
            )
            THEN TRUE
            ELSE FALSE
        END
        AS wasInjured,
        CASE
            WHEN (EXISTS( SELECT B1.banid FROM Ban B1
            WHERE B1.playerid = U1.usersid
            AND
            (M1.matchstartdatetime
            BETWEEN B1.banstartdate AND B1.banenddate)
            )
        )
            THEN TRUE
            ELSE FALSE
        END
        AS disciplinarilyPunished,
        U1.usersid,
        U1.firstname,
        U1.lastname,
        U2.usersid,
        U2.firstname,
        U2.lastname,
        M1.winnerteam,
        M1.hometeamscore,
        M1.awayteamscore
        FROM ( ( ( ( Match M1
        JOIN AllEmploymentInfo A1 ON (M1.hometeamid = A1.teamid) )
        JOIN Users U1 USING (usersid) )
        JOIN Player Per1 ON (Per1.usersid = U1.usersid) )
        LEFT JOIN Play P1 USING (matchid) )
        LEFT JOIN Users U2 ON (P1.substitutionid = U2.usersid)
        WHERE M1.matchid = %s
        AND (M1.matchstartdatetime BETWEEN
        A1.startdate AND COALESCE(A1.enddate, NOW() + INTERVAL '1 year') )
        ORDER BY U1.firstname, U1.lastname;
        """,
        (matchid, )
    )

    return cur.fetchall()


def match_awayteam_info(matchid):

    cur = get_connection().cursor()

    cur.execute(
        """
        SELECT
        P1.*,
        CASE
            WHEN (EXISTS( SELECT I1.injuryid FROM Injury I1
                WHERE I1.playerid = U1.usersid
                AND
                (M1.matchstartdatetime
                BETWEEN I1.injurydate AND I1.recoverydate)
                )
            )
            THEN TRUE
            ELSE FALSE
        END
        AS wasInjured,
        CASE
            WHEN (EXISTS( SELECT B1.banid FROM Ban B1
            WHERE B1.playerid = U1.usersid
            AND
            (M1.matchstartdatetime
            BETWEEN B1.banstartdate AND B1.banenddate)
            )
        )
            THEN TRUE
            ELSE FALSE
        END
        AS disciplinarilyPunished,
        U1.usersid,
        U1.firstname,
        U1.lastname,
        U2.usersid,
        U2.firstname,
        U2.lastname,
        M1.winnerteam,
        M1.hometeamscore,
        M1.awayteamscore
        FROM ( ( ( ( Match M1
        JOIN AllEmploymentInfo A1 ON (M1.awayteamid = A1.teamid) )
        JOIN Users U1 USING (usersid) )
        JOIN Player Per1 ON (Per1.usersid = U1.usersid) )
        LEFT JOIN Play P1 USING (matchid) )
        LEFT JOIN Users U2 ON (P1.substitutionid = U2.usersid)
        WHERE M1.matchid = %s
        AND (M1.matchstartdatetime BETWEEN
        A1.startdate AND COALESCE(A1.enddate, NOW() + INTERVAL '1 year') )
        ORDER BY U1.firstname, U1.lastname;
        """,
        (matchid, )
    )

    return cur.fetchall()
