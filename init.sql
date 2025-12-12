CREATE TABLE Users (
  UsersID SERIAL,
  FirstName VARCHAR(30) NOT NULL,
  LastName VARCHAR(30) NOT NULL,
  Email VARCHAR(255) NOT NULL UNIQUE,
  HashedPassword TEXT NOT NULL,
  Salt TEXT NOT NULL,
  PasswordDate TIMESTAMP,
  PhoneNumber VARCHAR(25),
  BirthDate TIMESTAMP NOT NULL,
  Role VARCHAR(20),
  Nationality VARCHAR(20),
  PRIMARY KEY (UsersID),
  CONSTRAINT age_validation CHECK(
    EXTRACT(
      YEAR
      FROM
        age(BirthDate)
    ) >= 16
  )
);

CREATE TABLE SuperAdmin (
  UsersID INT,
  PRIMARY KEY (UsersID),
  FOREIGN KEY (UsersID) REFERENCES Users(UsersID) ON DELETE CASCADE
);

CREATE TABLE Admin (
  UsersID INT,
  PRIMARY KEY (UsersID),
  FOREIGN KEY (UsersID) REFERENCES Users(UsersID) ON DELETE CASCADE
);

CREATE TABLE Referee (
  UsersID INT,
  Certification VARCHAR(255) NOT NULL,
  PRIMARY KEY (UsersID),
  FOREIGN KEY (UsersID) REFERENCES Users(UsersID) ON DELETE CASCADE
);

CREATE TABLE TeamOwner (
  UsersID INT,
  NetWorth NUMERIC(12, 3),
  PRIMARY KEY (UsersID),
  FOREIGN KEY (UsersID) REFERENCES Users(UsersID) ON DELETE CASCADE,
  CONSTRAINT net_worth_check CHECK (NetWorth > 100000.000)
);

CREATE TABLE Team (
  TeamID SERIAL,
  OwnerID INT NOT NULL UNIQUE,
  TeamName VARCHAR(100) NOT NULL UNIQUE,
  EstablishedDate TIMESTAMP,
  HomeVenue VARCHAR(100) NOT NULL,
  PRIMARY KEY (TeamID),
  FOREIGN KEY (OwnerID) REFERENCES TeamOwner(UsersID) ON DELETE CASCADE
);

CREATE TABLE Employee (
  UsersID INT,
  TeamID INT,
  PRIMARY KEY (UsersID),
  FOREIGN KEY (UsersID) REFERENCES Users(UsersID) ON DELETE CASCADE,
  FOREIGN KEY (TeamID) REFERENCES Team(TeamID) ON DELETE
  SET
    NULL
);

CREATE TABLE Coach (
  UsersID INT,
  Certification VARCHAR(255) NOT NULL,
  PRIMARY KEY (UsersID),
  FOREIGN KEY (UsersID) REFERENCES Employee(UsersID) ON DELETE CASCADE
);

CREATE TABLE Player (
  UsersID INT,
  Height NUMERIC(5, 2),
  Weight NUMERIC(5, 2),
  Overall VARCHAR(255),
  Position VARCHAR(50),
  IsEligible VARCHAR(255) NOT NULL,
  PRIMARY KEY (UsersID),
  FOREIGN KEY (UsersID) REFERENCES Employee(UsersID) ON DELETE CASCADE
);

CREATE TABLE TrainingSession (
  SessionID SERIAL,
  CoachID INT NOT NULL,
  SessionDate TIMESTAMP NOT NULL,
  Location VARCHAR(255) NOT NULL,
  Focus VARCHAR(255) NOT NULL,
  PRIMARY KEY (SessionID),
  FOREIGN KEY (CoachID) REFERENCES Coach(UsersID) ON DELETE CASCADE
);

CREATE TABLE Match (
  MatchID SERIAL,
  HomeTeamID INT NOT NULL,
  AwayTeamID INT NOT NULL,
  MatchStartDatetime TIMESTAMP NOT NULL,
  MatchEndDatetime TIMESTAMP,
  VenuePlayed VARCHAR(100),
  HomeTeamName VARCHAR(100) NOT NULL,
  AwayTeamName VARCHAR(100) NOT NULL,
  HomeTeamScore INT,
  AwayTeamScore INT,
  WinnerTeam VARCHAR(100),
  IsLocked BOOLEAN NOT NULL,
  PRIMARY KEY (MatchID),
  FOREIGN KEY (HomeTeamID) REFERENCES Team(TeamID) ON DELETE CASCADE,
  FOREIGN KEY (AwayTeamID) REFERENCES Team(TeamID) ON DELETE CASCADE,
  CONSTRAINT positive_scores_match CHECK (
    (
      HomeTeamScore IS NULL
      OR HomeTeamScore >= 0
    )
    AND (
      AwayTeamScore IS NULL
      OR AwayTeamScore >= 0
    )
  )
);

CREATE TABLE Injury (
  InjuryID SERIAL,
  PlayerID INT NOT NULL,
  MatchID INT,
  TrainingID INT,
  InjuryDate TIMESTAMP NOT NULL,
  InjuryType VARCHAR(100) NOT NULL,
  Description VARCHAR(1000),
  RecoveryDate TIMESTAMP NOT NULL,
  PRIMARY KEY (InjuryID),
  FOREIGN KEY (PlayerID) REFERENCES Player(UsersID) ON DELETE CASCADE,
  FOREIGN KEY (MatchID) REFERENCES Match(MatchID) ON DELETE
  SET
    NULL,
    FOREIGN KEY (TrainingID) REFERENCES TrainingSession(SessionID) ON DELETE
  SET
    NULL
);

CREATE TABLE Ban (
  BanID SERIAL,
  PlayerID INT NOT NULL,
  BanStartDate TIMESTAMP NOT NULL,
  BanEndDate TIMESTAMP NOT NULL,
  PRIMARY KEY (BanID),
  FOREIGN KEY (PlayerID) REFERENCES Player(UsersID) ON DELETE CASCADE
);

CREATE TABLE Employment (
  EmploymentID SERIAL,
  StartDate TIMESTAMP NOT NULL,
  EndDate TIMESTAMP NOT NULL,
  Salary INT NOT NULL,
  PRIMARY KEY (EmploymentID)
);

CREATE TABLE Play (
  PlayID SERIAL,
  MatchID INT NOT NULL,
  PlayerID INT NOT NULL,
  SubstitutionID INT,
  StartTime INT,
  StopTime INT,
  SuccessfulPasses INT,
  GoalsScored INT,
  PenaltiesScored INT,
  AssistsMade INT,
  TotalPasses INT,
  YellowCards INT,
  RedCards INT,
  Saves INT,
  PRIMARY KEY (PlayID),
  FOREIGN KEY (MatchID) REFERENCES Match(MatchID) ON DELETE CASCADE,
  FOREIGN KEY (PlayerID) REFERENCES Player(UsersID) ON DELETE CASCADE,
  FOREIGN KEY (SubstitutionID) REFERENCES Player(UsersID) ON DELETE CASCADE,
  CONSTRAINT correct_substitution CHECK(PlayerID <> SubstitutionID),
  CONSTRAINT positive_scores_play CHECK (
    (
      GoalsScored IS NULL
      OR GoalsScored >= 0
    )
    AND (
      PenaltiesScored IS NULL
      OR PenaltiesScored >= 0
    )
  )
);

CREATE TABLE League (
  LeagueID SERIAL,
  Name VARCHAR(100) NOT NULL UNIQUE,
  PRIMARY KEY (LeagueID)
);

CREATE TABLE LeagueTeam (
  LeagueID INT,
  TeamID INT,
  PRIMARY KEY (LeagueID, TeamID),
  FOREIGN KEY (LeagueID) REFERENCES League(LeagueID) ON DELETE CASCADE,
  FOREIGN KEY (TeamID) REFERENCES Team(TeamID) ON DELETE CASCADE
);

CREATE TABLE Season (
  LeagueID INT,
  SeasonNo INT,
  SeasonYear DATE,
  StartDate TIMESTAMP NOT NULL,
  EndDate TIMESTAMP NOT NULL,
  PrizePool BIGINT NOT NULL,
  PRIMARY KEY (LeagueID, SeasonNo, SeasonYear),
  FOREIGN KEY (LeagueID) REFERENCES League(LeagueID) ON DELETE CASCADE
);

CREATE TABLE SeasonalMatch (
  MatchID INT,
  LeagueID INT,
  SeasonNo INT,
  SeasonYear DATE,
  PRIMARY KEY (MatchID),
  FOREIGN KEY (MatchID) REFERENCES Match(MatchID) ON DELETE CASCADE,
  FOREIGN KEY (LeagueID, SeasonNo, SeasonYear) REFERENCES Season(LeagueID, SeasonNo, SeasonYear) ON DELETE CASCADE
);

CREATE TABLE TournamentMatch (
  MatchID INT,
  PRIMARY KEY (MatchID),
  FOREIGN KEY (MatchID) REFERENCES Match(MatchID) ON DELETE CASCADE
);

CREATE TABLE Tournament (
  TournamentID SERIAL,
  Name VARCHAR(255) UNIQUE,
  Size INT,
  PRIMARY KEY (TournamentID)
);

CREATE TABLE Round (
  TournamentID INT,
  RoundNo INT,
  T_MatchID INT UNIQUE,
  Child1RoundNo INT,
  Child2RoundNo INT,
  ParentRoundNo INT,
  PRIMARY KEY (TournamentID, RoundNo),
  FOREIGN KEY (T_MatchID) REFERENCES TournamentMatch(MatchID) ON DELETE CASCADE,
  FOREIGN KEY (TournamentID) REFERENCES Tournament(TournamentID) ON DELETE CASCADE,
  FOREIGN KEY (TournamentID, Child1RoundNo) REFERENCES Round(TournamentID, RoundNo) ON DELETE SET NULL,
  FOREIGN KEY (TournamentID, Child2RoundNo) REFERENCES Round(TournamentID, RoundNo) ON DELETE SET NULL,
  FOREIGN KEY (TournamentID, ParentRoundNo) REFERENCES Round(TournamentID, RoundNo) ON DELETE CASCADE
);

CREATE TABLE Offer (
  OfferID SERIAL,
  RequestingCoach INT NOT NULL,
  RequestedPlayer INT NOT NULL,
  OfferedEndDate TIMESTAMP NOT NULL,
  AvailableUntil TIMESTAMP NOT NULL,
  OfferAmount INT NOT NULL,
  OfferStatus BOOLEAN,
  PRIMARY KEY (OfferID),
  FOREIGN KEY (RequestingCoach) REFERENCES Coach(UsersID) ON DELETE CASCADE,
  FOREIGN KEY (RequestedPlayer) REFERENCES Player(UsersID) ON DELETE CASCADE
);

CREATE TABLE Employed (
  EmploymentID INT,
  UsersID INT,
  TeamID INT,
  PRIMARY KEY (EmploymentID, UsersID, TeamID),
  FOREIGN KEY (EmploymentID) REFERENCES Employment(EmploymentID) ON DELETE CASCADE,
  FOREIGN KEY (UsersID) REFERENCES Employee(UsersID) ON DELETE CASCADE,
  FOREIGN KEY (TeamID) REFERENCES Team(TeamID) ON DELETE CASCADE
);

CREATE TABLE TrainingAttendance (
  SessionID SERIAL,
  PlayerID INT,
  Status INT NOT NULL,
  PRIMARY KEY (SessionID, PlayerID),
  FOREIGN KEY (SessionID) REFERENCES TrainingSession(SessionID) ON DELETE CASCADE,
  FOREIGN KEY (PlayerID) REFERENCES Player(UsersID) ON DELETE CASCADE
);

CREATE TABLE TournamentModeration (
  T_ID INT,
  AdminID INT,
  PRIMARY KEY (T_ID, AdminID),
  FOREIGN KEY (T_ID) REFERENCES Tournament(TournamentID) ON DELETE CASCADE,
  FOREIGN KEY (AdminID) REFERENCES Admin(UsersID) ON DELETE CASCADE
);

CREATE TABLE SeasonModeration (
  LeagueID INT,
  SeasonNo INT,
  SeasonYear DATE,
  AdminID INT,
  PRIMARY KEY (LeagueID, SeasonNo, SeasonYear, AdminID),
  FOREIGN KEY (LeagueID, SeasonNo, SeasonYear) REFERENCES Season(LeagueID, SeasonNo, SeasonYear) ON DELETE CASCADE,
  FOREIGN KEY (AdminID) REFERENCES Admin(UsersID) ON DELETE CASCADE
);

CREATE TABLE CoachMatchAttendance (
  MatchID INT,
  CoachID INT,
  PRIMARY KEY (MatchID, CoachID),
  FOREIGN KEY (MatchID) REFERENCES Match(MatchID) ON DELETE CASCADE,
  FOREIGN KEY (CoachID) REFERENCES Coach(UsersID) ON DELETE CASCADE
);

CREATE TABLE RefereeMatchAttendance (
  MatchID INT,
  RefereeID INT,
  PRIMARY KEY (MatchID, RefereeID),
  FOREIGN KEY (MatchID) REFERENCES Match(MatchID) ON DELETE CASCADE,
  FOREIGN KEY (RefereeID) REFERENCES Referee(UsersID) ON DELETE CASCADE
);

-- --views -----------------------------------------------------------------------------
-- view for all matches with seasonal and tournament info 
CREATE OR REPLACE VIEW AllMatchInfo AS
SELECT
  M1.*,
  SMa1.LeagueID,
  SMa1.SeasonNo,
  SMa1.SeasonYear,
  T1.TournamentID,
  T1.Name AS TournamentName,
  T1.Size AS TournamentSize
FROM Match M1
LEFT JOIN SeasonalMatch SMa1 USING (MatchID)
LEFT JOIN TournamentMatch TM1 USING (MatchID)
LEFT JOIN Round R1 ON R1.T_MatchID = TM1.MatchID
LEFT JOIN Tournament T1 USING (TournamentID)
ORDER BY M1.MatchStartDatetime;

CREATE OR REPLACE VIEW AllSeasonMatchInfo AS
SELECT
  M1.*,
  SMa1.LeagueID,
  L1.Name AS LeagueName,
  SMa1.SeasonNo,
  SMa1.SeasonYear
FROM Match M1
JOIN SeasonalMatch SMa1 USING (MatchID)
JOIN League L1 USING (LeagueID)
ORDER BY M1.MatchStartDatetime;

-- view for all tournament matches with round info - WORKS
CREATE OR REPLACE VIEW AllTournamentMatchInfo AS
SELECT
  M1.*,
  R1.*,
  T1.Name,
  T1.Size
FROM Match M1
JOIN TournamentMatch TM1 USING (MatchID)
JOIN Round R1 ON R1.T_MatchID = TM1.MatchID
JOIN Tournament T1 USING (TournamentID)
ORDER BY M1.MatchStartDatetime;

CREATE OR REPLACE VIEW RefereeMatchView AS
SELECT *
FROM (
  SELECT
    m.MatchID,
    home.TeamName AS HomeTeamName,
    away.TeamName AS AwayTeamName,
    m.MatchStartDatetime,
    l.Name AS CompetitionName,
    rma.RefereeID,
    TRUE AS IsLeague
  FROM Match m
  JOIN Team home ON m.HomeTeamID = home.TeamID
  JOIN Team away ON m.AwayTeamID = away.TeamID
  JOIN RefereeMatchAttendance rma ON m.MatchID = rma.MatchID
  JOIN SeasonalMatch sm ON m.MatchID = sm.MatchID
  JOIN League l USING (LeagueID)

  UNION

  SELECT
    m.MatchID,
    home.TeamName AS HomeTeamName,
    away.TeamName AS AwayTeamName,
    m.MatchStartDatetime,
    t.Name AS CompetitionName,
    rma.RefereeID,
    FALSE AS IsLeague
  FROM Match m
  JOIN Team home ON m.HomeTeamID = home.TeamID
  JOIN Team away ON m.AwayTeamID = away.TeamID
  JOIN RefereeMatchAttendance rma ON m.MatchID = rma.MatchID
  JOIN TournamentMatch tm ON m.MatchID = tm.MatchID
  JOIN Round r ON r.T_MatchID = tm.MatchID
  JOIN Tournament t USING (TournamentID)
) AS combined
ORDER BY MatchStartDatetime;

CREATE OR REPLACE VIEW AllEmploymentInfo AS
SELECT
  em.EmploymentID,
  em.UsersID,
  em.TeamID,
  e.StartDate,
  e.EndDate,
  e.Salary,
  t.TeamName,
  t.OwnerID,
  t.EstablishedDate,
  t.HomeVenue
FROM Employed em
JOIN Employment e ON e.EmploymentID = em.EmploymentID
JOIN Team t ON t.TeamID = em.TeamID
JOIN Employee emp ON emp.UsersID = em.UsersID;

CREATE OR REPLACE VIEW PlayerStatsAll AS
SELECT
  U1.UsersID,
  U1.FirstName,
  U1.LastName,
  COUNT(DISTINCT M1.MatchID) AS total_appearances,
  SUM(P1.GoalsScored) AS total_goals,
  SUM(P1.PenaltiesScored) AS total_penalties,
  SUM(COALESCE(P1.StopTime, 0) - COALESCE(P1.StartTime, 0)) / 60 AS total_minutes,
  SUM(P1.YellowCards) AS total_yellowcards,
  SUM(P1.RedCards) AS total_redcards,
  SUM(P1.Saves) AS total_saves,
  SUM(P1.SuccessfulPasses) AS total_successfulpasses,
  SUM(P1.TotalPasses) AS total_totalpasses,
  SUM(P1.AssistsMade) AS total_assistsmade
FROM Match M1
JOIN Play P1 USING (MatchID)
JOIN Users U1 ON U1.UsersID = P1.PlayerID
LEFT JOIN SeasonalMatch SMa1 USING (MatchID)
LEFT JOIN TournamentMatch TM1 USING (MatchID)
LEFT JOIN Round R1 ON R1.T_MatchID = TM1.MatchID
LEFT JOIN Tournament T1 USING (TournamentID)
GROUP BY U1.UsersID, U1.FirstName, U1.LastName;

CREATE OR REPLACE VIEW PlayerSeasonStats AS
SELECT
  U1.UsersID,
  U1.FirstName,
  U1.LastName,
  L1.Name,
  SMa1.LeagueID,
  SMa1.SeasonNo,
  SMa1.SeasonYear,
  COUNT(DISTINCT M1.MatchID) AS total_appearances,
  SUM(P1.GoalsScored) AS total_goals,
  SUM(P1.PenaltiesScored) AS total_penalties,
  SUM(COALESCE(P1.StopTime, 0) - COALESCE(P1.StartTime, 0)) / 60 AS total_minutes,
  SUM(P1.YellowCards) AS total_yellowcards,
  SUM(P1.RedCards) AS total_redcards,
  SUM(P1.Saves) AS total_saves,
  SUM(P1.SuccessfulPasses) AS total_successfulpasses,
  SUM(P1.TotalPasses) AS total_totalpasses,
  SUM(P1.AssistsMade) AS total_assistsmade
FROM SeasonalMatch SMa1
JOIN Match M1 USING (MatchID)
JOIN Play P1 USING (MatchID)
JOIN Users U1 ON U1.UsersID = P1.PlayerID
JOIN League L1 USING (LeagueID)
GROUP BY
  U1.UsersID, U1.FirstName, U1.LastName,
  L1.Name, SMa1.LeagueID, SMa1.SeasonNo, SMa1.SeasonYear;

CREATE OR REPLACE VIEW PlayerTournamentStats AS
SELECT
  U1.UsersID,
  U1.FirstName,
  U1.LastName,
  T1.TournamentID,
  T1.Name,
  COUNT(DISTINCT M1.MatchID) AS total_appearances,
  SUM(P1.GoalsScored) AS total_goals,
  SUM(P1.PenaltiesScored) AS total_penalties,
  SUM(COALESCE(P1.StopTime, 0) - COALESCE(P1.StartTime, 0)) / 60 AS total_minutes,
  SUM(P1.YellowCards) AS total_yellowcards,
  SUM(P1.RedCards) AS total_redcards,
  SUM(P1.Saves) AS total_saves,
  SUM(P1.SuccessfulPasses) AS total_successfulpasses,
  SUM(P1.TotalPasses) AS total_totalpasses,
  SUM(P1.AssistsMade) AS total_assistsmade
FROM TournamentMatch TM1
JOIN Match M1 USING (MatchID)
JOIN Play P1 USING (MatchID)
JOIN Users U1 ON U1.UsersID = P1.PlayerID
JOIN Round R1 ON R1.T_MatchID = TM1.MatchID
JOIN Tournament T1 USING (TournamentID)
GROUP BY U1.UsersID, U1.FirstName, U1.LastName, T1.TournamentID, T1.Name;

CREATE OR REPLACE VIEW CurrentEmployment AS (
  SELECT DISTINCT ON (UsersID) 
   *
  FROM AllEmploymentInfo
  WHERE EndDate > NOW()
  ORDER BY UsersID, StartDate DESC
);

-- functions 

-- triggers
-- trigger to fill parent match when both child matches have winners -  WORKS
CREATE OR REPLACE FUNCTION fill_parent_match()
RETURNS TRIGGER AS $$
DECLARE
    child_round INT;
    tournament_id INT;

    parent_round INT;
    child1_round INT;
    child2_round INT;

    child1_match INT;
    child2_match INT;

    child1_winner VARCHAR(100);
    child2_winner VARCHAR(100);

    new_parent_match_id INT;
BEGIN
    ----------------------------------------------------------------
    -- 0. Ignore matches that are NOT part of tournaments
    ----------------------------------------------------------------
    IF NOT EXISTS (SELECT 1 FROM TournamentMatch WHERE MatchID = NEW.MatchID) THEN
        RETURN NULL;
    END IF;

    ----------------------------------------------------------------
    -- 1. Identify the round for the updated tournament match
    ----------------------------------------------------------------
    SELECT RoundNo, TournamentID
    INTO child_round, tournament_id
    FROM Round
    WHERE T_MatchID = NEW.MatchID;

    IF child_round IS NULL THEN
        -- Match not assigned to any round
        RETURN NULL;
    END IF;

    ----------------------------------------------------------------
    -- 2. Find parent round
    ----------------------------------------------------------------
    SELECT ParentRoundNo
    INTO parent_round
    FROM Round
    WHERE TournamentID = tournament_id
      AND RoundNo = child_round;

    IF parent_round IS NULL THEN
        -- This is the FINAL round (root). No parent to fill.
        RETURN NULL;
    END IF;

    ----------------------------------------------------------------
    -- 3. Check if parent round already has a match
    ----------------------------------------------------------------
    SELECT T_MatchID
    INTO new_parent_match_id
    FROM Round
    WHERE TournamentID = tournament_id
      AND RoundNo = parent_round;

    IF new_parent_match_id IS NOT NULL THEN
        RETURN NULL;  -- Parent already created
    END IF;

    ----------------------------------------------------------------
    -- 4. Get the two child rounds of the parent
    ----------------------------------------------------------------
    SELECT Child1RoundNo, Child2RoundNo
    INTO child1_round, child2_round
    FROM Round
    WHERE TournamentID = tournament_id
      AND RoundNo = parent_round;

    IF child1_round IS NULL OR child2_round IS NULL THEN
        RETURN NULL;
    END IF;

    ----------------------------------------------------------------
    -- 5. Get match IDs of the two child rounds
    ----------------------------------------------------------------
    SELECT T_MatchID INTO child1_match
    FROM Round WHERE TournamentID = tournament_id AND RoundNo = child1_round;

    SELECT T_MatchID INTO child2_match
    FROM Round WHERE TournamentID = tournament_id AND RoundNo = child2_round;

    IF child1_match IS NULL OR child2_match IS NULL THEN
        RETURN NULL;
    END IF;

    ----------------------------------------------------------------
    -- 6. Check if both children have winners
    ----------------------------------------------------------------
    SELECT winnerteam INTO child1_winner
    FROM AllTournamentMatchInfo WHERE matchid = child1_match;

    SELECT winnerteam INTO child2_winner
    FROM AllTournamentMatchInfo WHERE matchid = child2_match;

    IF child1_winner IS NULL OR child2_winner IS NULL THEN
        RETURN NULL;
    END IF;

    ----------------------------------------------------------------
    -- 7. Create parent match
    ----------------------------------------------------------------
    INSERT INTO Match (
        HomeTeamID, AwayTeamID, MatchStartDatetime,
        HomeTeamName, AwayTeamName,
        HomeTeamScore, AwayTeamScore, WinnerTeam, IsLocked
    )
    VALUES (
        (SELECT TeamID FROM Team WHERE TeamName = child1_winner),
        (SELECT TeamID FROM Team WHERE TeamName = child2_winner),
        NOW() + INTERVAL '1 week',
        child1_winner, child2_winner,
        NULL, NULL, NULL, TRUE
    )
    RETURNING MatchID INTO new_parent_match_id;

    ----------------------------------------------------------------
    -- 8. Insert into TournamentMatch first to satisfy FK
    ----------------------------------------------------------------
    INSERT INTO TournamentMatch (MatchID)
    VALUES (new_parent_match_id);

    ----------------------------------------------------------------
    -- 9. Attach match to parent round
    ----------------------------------------------------------------
    UPDATE Round
    SET T_MatchID = new_parent_match_id
    WHERE TournamentID = tournament_id
      AND RoundNo = parent_round;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trg_fill_parent_match
AFTER UPDATE OF winnerteam ON Match
FOR EACH ROW
EXECUTE FUNCTION fill_parent_match();


-- ===== TRIGGER: Auto-create Play rows when a Match is inserted =====
-- Purpose: Whenever a Match is created (league or tournament), automatically 
--          populate Play rows for all current active players on both teams.
-- Logic:
--   1. Get the HomeTeamID and AwayTeamID from the new Match
--   2. Find all players actively employed by both teams at the match time
--   3. Insert Play rows for each player (without eligibility check for now)
-- Note: This runs for BOTH seasonal matches and tournament matches
-- Note: IsEligible filtering is currently bypassed
CREATE OR REPLACE FUNCTION auto_create_plays_on_match_insert()
RETURNS TRIGGER AS $$
DECLARE
    home_team_id INT;
    away_team_id INT;
    match_time TIMESTAMP;
BEGIN
    home_team_id := NEW.HomeTeamID;
    away_team_id := NEW.AwayTeamID;
    match_time := NEW.MatchStartDatetime;

    -- Insert Play rows for all active players from both teams
    WITH active_players AS (
        SELECT em.UsersID AS player_id
        FROM Employed em
        JOIN Employment e ON e.EmploymentID = em.EmploymentID
        JOIN Player p ON p.UsersID = em.UsersID
        WHERE em.TeamID IN (home_team_id, away_team_id)
          AND e.StartDate <= match_time
          AND e.EndDate >= match_time
          -- NOTE: Skipping IsEligible check for now (see TODO in create_tournament_with_bracket)
    ),
    to_insert AS (
        SELECT NEW.MatchID AS match_id, ap.player_id
        FROM active_players ap
        WHERE NOT EXISTS (
            SELECT 1 FROM Play pl
            WHERE pl.MatchID = NEW.MatchID AND pl.PlayerID = ap.player_id
        )
    )
    INSERT INTO Play (MatchID, PlayerID)
    SELECT match_id, player_id FROM to_insert;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_auto_create_plays_on_match_insert
AFTER INSERT ON Match
FOR EACH ROW
EXECUTE FUNCTION auto_create_plays_on_match_insert();






-- trigger to update scores on play insert, excluding tournament matches
CREATE OR REPLACE FUNCTION update_all_after_play_insertion()
RETURNS TRIGGER AS $$
DECLARE
    player_team_id INT;
    match_time TIMESTAMP;
BEGIN
-- if it is a tournament match, do nothing - SKIP 
    IF EXISTS (SELECT 1 FROM TournamentMatch WHERE MatchID = NEW.MatchID) THEN
        RETURN NULL;
    END IF;

    IF NEW.StartTime IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT MatchStartDatetime INTO match_time
    FROM Match
    WHERE MatchID = NEW.MatchID;

    IF match_time IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT TeamID INTO player_team_id
    FROM AllEmploymentInfo
    WHERE UsersID = NEW.PlayerID
      AND match_time BETWEEN StartDate AND EndDate
    LIMIT 1;

    IF player_team_id IS NULL THEN
        RETURN NULL;
    END IF;

    UPDATE Match
    SET HomeTeamScore = COALESCE(HomeTeamScore, 0) +
                        CASE WHEN HomeTeamID = player_team_id THEN COALESCE(NEW.GoalsScored, 0) ELSE 0 END,
        AwayTeamScore = COALESCE(AwayTeamScore, 0) +
                        CASE WHEN AwayTeamID = player_team_id THEN COALESCE(NEW.GoalsScored, 0) ELSE 0 END
    WHERE MatchID = NEW.MatchID;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER play_insert
AFTER INSERT ON Play
FOR EACH ROW
EXECUTE FUNCTION update_all_after_play_insertion();

-- trigger to update scores on play update, excluding tournament matches
CREATE OR REPLACE FUNCTION update_all_after_play_update()
RETURNS TRIGGER AS $$
DECLARE
    player_team_id INT;
    match_time TIMESTAMP;
    goal_delta INT;
BEGIN
    IF EXISTS (SELECT 1 FROM TournamentMatch WHERE MatchID = NEW.MatchID) THEN
        RETURN NULL;
    END IF;

    IF NEW.StartTime IS NULL THEN
        RETURN NULL;
    END IF;

    goal_delta := COALESCE(NEW.GoalsScored, 0) - COALESCE(OLD.GoalsScored, 0);
    IF goal_delta = 0 THEN
        RETURN NULL;
    END IF;

    SELECT MatchStartDatetime INTO match_time
    FROM Match
    WHERE MatchID = NEW.MatchID;

    IF match_time IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT TeamID INTO player_team_id
    FROM AllEmploymentInfo
    WHERE UsersID = NEW.PlayerID
      AND match_time BETWEEN StartDate AND EndDate
    LIMIT 1;

    IF player_team_id IS NULL THEN
        RETURN NULL;
    END IF;

    UPDATE Match
    SET HomeTeamScore = COALESCE(HomeTeamScore, 0) +
                        CASE WHEN HomeTeamID = player_team_id THEN goal_delta ELSE 0 END,
        AwayTeamScore = COALESCE(AwayTeamScore, 0) +
                        CASE WHEN AwayTeamID = player_team_id THEN goal_delta ELSE 0 END
    WHERE MatchID = NEW.MatchID;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER play_update
AFTER UPDATE ON Play
FOR EACH ROW
EXECUTE FUNCTION update_all_after_play_update();

-- trigger to update match winner when scores change, excluding tournament matches
CREATE OR REPLACE FUNCTION update_match_winner()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM TournamentMatch WHERE MatchID = NEW.MatchID) THEN
        RETURN NULL;
    END IF;

    IF NEW.HomeTeamScore IS NULL OR NEW.AwayTeamScore IS NULL THEN
        RETURN NULL;
    END IF;

    IF NEW.HomeTeamScore <> OLD.HomeTeamScore OR NEW.AwayTeamScore <> OLD.AwayTeamScore THEN
        UPDATE Match M
        SET WinnerTeam = CASE
            WHEN NEW.HomeTeamScore > NEW.AwayTeamScore THEN NEW.HomeTeamName
            WHEN NEW.HomeTeamScore < NEW.AwayTeamScore THEN NEW.AwayTeamName
            ELSE NULL
        END
        WHERE M.MatchID = NEW.MatchID;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER match_update
AFTER UPDATE ON Match
FOR EACH ROW
EXECUTE FUNCTION update_match_winner();

-- trigger to update a player's employment after accepting an offer ----------
CREATE OR REPLACE FUNCTION handle_accepted_transfer_offer()
RETURNS TRIGGER AS $$
DECLARE
  v_requesting_coach_team INT;
  v_current_employment_id INT;
  v_current_employment_salary INT;
  v_new_employment_id INT;
BEGIN
  -- Only process when OfferStatus changes to 1 (accepted)
  IF NEW.OfferStatus = TRUE AND (OLD.OfferStatus IS NULL OR OLD.OfferStatus != TRUE) THEN
    
    -- Get the requesting coach's team
    SELECT TeamID INTO v_requesting_coach_team
    FROM Employee
    WHERE UsersID = NEW.RequestingCoach;
    
    -- Only proceed if the coach has a team
    IF v_requesting_coach_team IS NOT NULL THEN
      
      -- Get the player's most recent employment
      SELECT em.EmploymentID, emp.Salary
      INTO v_current_employment_id, v_current_employment_salary
      FROM Employed em
      JOIN Employment emp ON em.EmploymentID = emp.EmploymentID
      WHERE em.UsersID = NEW.RequestedPlayer
      AND emp.EndDate > NOW()
      ORDER BY emp.StartDate DESC
      LIMIT 1;
      
      -- If player has active employment, end it
      IF v_current_employment_id IS NOT NULL THEN
        UPDATE Employment
        SET EndDate = NOW()
        WHERE EmploymentID = v_current_employment_id;
      END IF;
      
      -- Update the player's team in Employee table
      UPDATE Employee
      SET TeamID = v_requesting_coach_team
      WHERE UsersID = NEW.RequestedPlayer;
      
      -- Create new employment record with OfferedEndDate
      INSERT INTO Employment (StartDate, EndDate, Salary)
      VALUES (NOW(), NEW.OfferedEndDate, COALESCE(v_current_employment_salary, 60000))
      RETURNING EmploymentID INTO v_new_employment_id;
      
      -- Create new employed record
      INSERT INTO Employed (EmploymentID, UsersID, TeamID)
      VALUES (v_new_employment_id, NEW.RequestedPlayer, v_requesting_coach_team);
    END IF;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_accepted_transfer_offer
AFTER UPDATE ON Offer
FOR EACH ROW
EXECUTE FUNCTION handle_accepted_transfer_offer();

-- sample data ---------------------------------------------------------------
INSERT INTO Users (
  FirstName,
  LastName,
  Email,
  HashedPassword,
  Salt,
  PasswordDate,
  PhoneNumber,
  BirthDate,
  Role,
  Nationality
) VALUES
  ('Alice', 'Smith', 'a1@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'admin', 'USA'),
  ('Aaron', 'Lee', 'a2@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'admin', 'Canada'),
  ('Sam', 'Super', 'sa@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'superadmin', 'USA'),
  -- Owners
  ('Olivia', 'Ortiz', 'o1@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'team_owner', 'Spain'),
  ('Noah', 'Novak', 'o2@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'team_owner', 'Turkey'),
  ('Mia', 'Marino', 'o3@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'team_owner', 'Italy'),
  ('Elena', 'Evans', 'o4@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'team_owner', 'Germany'),
  ('Kenan', 'Kaya', 'o5@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'team_owner', 'France'),
  ('Sara', 'Sato', 'o6@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'team_owner', 'Netherlands'),
  ('Omar', 'Ochoa', 'o7@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'team_owner', 'Morocco'),
  ('Priya', 'Patel', 'o8@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'team_owner', 'India'),
  -- Additional team owners without teams
  ('David', 'Thompson', 'o9@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'team_owner', 'UK'),
  ('Emma', 'Wilson', 'o10@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'team_owner', 'Australia'),
  ('James', 'Anderson', 'o11@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'team_owner', 'New Zealand'),
  ('Sophie', 'Martin', 'o12@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'team_owner', 'Belgium'),
  -- Coaches
  ('John', 'Carter', 'c1@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'coach', 'USA'),
  ('Maria', 'Lopez', 'c2@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'coach', 'Spain'),
  ('Carlos', 'Silva', 'c3@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'coach', 'Italy'),
  ('Sofia', 'Rossi', 'c4@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'coach', 'Turkey'),
  ('Ivy', 'Chen', 'c5@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'coach', 'Canada'),
  ('Mateo', 'Diaz', 'c6@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'coach', 'Argentina'),
  ('Keiko', 'Tanaka', 'c7@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'coach', 'Japan'),
  ('Jonas', 'Berg', 'c8@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'coach', 'Norway'),
  -- Referees
  ('Ryan', 'Cole', 'r1@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'referee', 'USA'),
  ('Elena', 'Ruiz', 'r2@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'referee', 'Spain'),
  ('Marco', 'Conte', 'r3@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'referee', 'Italy'),
  ('Deniz', 'Arslan', 'r4@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'referee', 'Turkey'),
  ('Pierre', 'Dupont', 'r5@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'referee', 'France'),
  ('Hans', 'Weber', 'r6@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'referee', 'Germany'),
  ('Bruno', 'Costa', 'r7@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'referee', 'Brazil'),
  ('Javier', 'Mendez', 'r8@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'referee', 'Argentina'),
  ('Kenji', 'Sato', 'r9@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'referee', 'Japan'),
  ('Liam', 'OBrien', 'r10@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'referee', 'Ireland');

INSERT INTO SuperAdmin (UsersID)
SELECT UsersID FROM Users WHERE Email = 'sa@gmail.com';


INSERT INTO Admin (UsersID)
SELECT UsersID FROM Users WHERE Email IN ('a1@gmail.com', 'a2@gmail.com');

INSERT INTO TeamOwner (UsersID, NetWorth)
SELECT u.UsersID, data.net_worth
FROM (
  VALUES
    ('o1@gmail.com', 750000.000),
    ('o2@gmail.com', 680000.000),
    ('o3@gmail.com', 720000.000),
    ('o4@gmail.com', 650000.000),
    ('o5@gmail.com', 700000.000),
    ('o6@gmail.com', 670000.000),
    ('o7@gmail.com', 640000.000),
    ('o8@gmail.com', 710000.000),
    ('o9@gmail.com', 690000.000),
    ('o10@gmail.com', 660000.000),
    ('o11@gmail.com', 680000.000),
    ('o12@gmail.com', 700000.000)
) AS data(email, net_worth)
JOIN Users u ON u.Email = data.email;

INSERT INTO Team (
  OwnerID,
  TeamName,
  EstablishedDate,
  HomeVenue
)
SELECT u.UsersID,
       data.team_name,
       TO_DATE(data.established, 'YYYY-MM-DD'),
       data.venue
FROM (
  VALUES
    ('o1@gmail.com', 'Lions FC', '2015-03-12', 'Sunrise Stadium'),
    ('o2@gmail.com', 'Falcons United', '2012-07-04', 'Riverfront Arena'),
    ('o3@gmail.com', 'Harbor City Waves', '2018-09-18', 'Bayfront Dome'),
    ('o4@gmail.com', 'Alpine Strikers', '2014-05-21', 'Summit Park'),
    ('o5@gmail.com', 'Riviera Royals', '2016-11-02', 'Coastal Arena'),
    ('o6@gmail.com', 'Canal City Crew', '2013-08-14', 'Harborfront Field'),
    ('o7@gmail.com', 'Atlas Eagles', '2011-02-02', 'Mountain Crest'),
    ('o8@gmail.com', 'Silk Route FC', '2017-06-09', 'Bazaar Stadium')
) AS data(email, team_name, established, venue)
JOIN Users u ON u.Email = data.email;

INSERT INTO Employee (UsersID, TeamID)
SELECT u.UsersID, t.TeamID
FROM Users u
JOIN Team t ON t.OwnerID = (SELECT UsersID FROM Users WHERE Email = CASE 
  WHEN u.Email = 'c1@gmail.com' THEN 'o1@gmail.com'
  WHEN u.Email = 'c2@gmail.com' THEN 'o2@gmail.com'
  WHEN u.Email = 'c3@gmail.com' THEN 'o3@gmail.com'
  WHEN u.Email = 'c4@gmail.com' THEN 'o1@gmail.com'
END)
WHERE u.Email IN ('c1@gmail.com', 'c2@gmail.com', 'c3@gmail.com', 'c4@gmail.com');

INSERT INTO Coach (UsersID, Certification)
SELECT u.UsersID, 'UEFA A License'
FROM Users u
WHERE u.Email IN ('c1@gmail.com', 'c2@gmail.com', 'c3@gmail.com', 'c4@gmail.com');

-- Additional coaches (unassigned to teams)
INSERT INTO Employee (UsersID, TeamID)
SELECT u.UsersID, NULL
FROM Users u
WHERE u.Email IN ('c5@gmail.com', 'c6@gmail.com', 'c7@gmail.com', 'c8@gmail.com');

INSERT INTO Coach (UsersID, Certification)
SELECT u.UsersID, 'UEFA B License'
FROM Users u
WHERE u.Email IN ('c5@gmail.com', 'c6@gmail.com', 'c7@gmail.com', 'c8@gmail.com');

-- Referees
INSERT INTO Referee (UsersID, Certification)
SELECT u.UsersID, 'FIFA Elite'
FROM Users u
WHERE u.Email LIKE 'r%@gmail.com';

-- 112 players (14 per team) with ongoing employment
WITH player_data AS (
  SELECT * FROM (VALUES
    ('Lions FC','Noah','Keller','p1@gmail.com','Forward',183,77),
    ('Lions FC','Liam','Brooks','p2@gmail.com','Midfielder',180,74),
    ('Lions FC','Ethan','Miles','p3@gmail.com','Defender',185,79),
    ('Lions FC','Mason','Carter','p4@gmail.com','Goalkeeper',191,84),
    ('Lions FC','Henry','Doyle','p5@gmail.com','Forward',182,76),
    ('Lions FC','Owen','Blake','p6@gmail.com','Midfielder',179,73),
    ('Lions FC','Isaac','Turner','p7@gmail.com','Defender',186,81),
    ('Lions FC','Julian','Hayes','p8@gmail.com','Forward',181,75),
    ('Lions FC','Caleb','Foster','p9@gmail.com','Midfielder',178,72),
    ('Lions FC','Adrian','Pierce','p10@gmail.com','Defender',187,82),
    ('Lions FC','Miles','Barrett','p11@gmail.com','Forward',184,78),
    ('Lions FC','Felix','Rowe','p12@gmail.com','Midfielder',180,74),
    ('Lions FC','Leo','Harmon','p13@gmail.com','Defender',188,83),
    ('Lions FC','Nolan','Pratt','p14@gmail.com','Goalkeeper',192,86),
    ('Falcons United','Aiden','Walsh','p15@gmail.com','Forward',182,76),
    ('Falcons United','Logan','Hart','p16@gmail.com','Midfielder',179,72),
    ('Falcons United','Gavin','Rhodes','p17@gmail.com','Defender',187,81),
    ('Falcons United','Connor','Tate','p18@gmail.com','Goalkeeper',190,85),
    ('Falcons United','Parker','Vance','p19@gmail.com','Forward',183,77),
    ('Falcons United','Cole','Mercer','p20@gmail.com','Midfielder',181,74),
    ('Falcons United','Dylan','Briggs','p21@gmail.com','Defender',186,80),
    ('Falcons United','Ryder','Flynn','p22@gmail.com','Forward',182,75),
    ('Falcons United','Chase','Dalton','p23@gmail.com','Midfielder',180,73),
    ('Falcons United','Tyler','McKee','p24@gmail.com','Defender',188,82),
    ('Falcons United','Max','Holden','p25@gmail.com','Forward',184,78),
    ('Falcons United','Evan','Draper','p26@gmail.com','Midfielder',179,72),
    ('Falcons United','Blake','Sutton','p27@gmail.com','Defender',186,81),
    ('Falcons United','Reid','Lowry','p28@gmail.com','Goalkeeper',191,85),
    ('Harbor City Waves','Luca','Marino','p29@gmail.com','Forward',181,75),
    ('Harbor City Waves','Mateo','Costa','p30@gmail.com','Midfielder',178,72),
    ('Harbor City Waves','Diego','Alvarez','p31@gmail.com','Defender',185,79),
    ('Harbor City Waves','Marco','Russo','p32@gmail.com','Goalkeeper',190,84),
    ('Harbor City Waves','Rafael','Silva','p33@gmail.com','Forward',183,77),
    ('Harbor City Waves','Bruno','Santos','p34@gmail.com','Midfielder',180,74),
    ('Harbor City Waves','Thiago','Ramos','p35@gmail.com','Defender',187,81),
    ('Harbor City Waves','Enzo','Ferreira','p36@gmail.com','Forward',182,76),
    ('Harbor City Waves','Gabriel','Mendes','p37@gmail.com','Midfielder',179,73),
    ('Harbor City Waves','Santiago','Rios','p38@gmail.com','Defender',186,80),
    ('Harbor City Waves','Julian','Herrera','p39@gmail.com','Forward',184,78),
    ('Harbor City Waves','Adrian','Vargas','p40@gmail.com','Midfielder',180,74),
    ('Harbor City Waves','Nicolas','Duarte','p41@gmail.com','Defender',188,82),
    ('Harbor City Waves','Martin','Paredes','p42@gmail.com','Goalkeeper',192,86),
    ('Alpine Strikers','Lukas','Steiner','p43@gmail.com','Forward',183,77),
    ('Alpine Strikers','Leon','Schneider','p44@gmail.com','Midfielder',179,72),
    ('Alpine Strikers','Jonas','Keller','p45@gmail.com','Defender',186,81),
    ('Alpine Strikers','Fabian','Vogel','p46@gmail.com','Goalkeeper',191,85),
    ('Alpine Strikers','Simon','Weber','p47@gmail.com','Forward',182,76),
    ('Alpine Strikers','Moritz','Brandt','p48@gmail.com','Midfielder',180,74),
    ('Alpine Strikers','Felix','Kruger','p49@gmail.com','Defender',187,82),
    ('Alpine Strikers','Emil','Hofmann','p50@gmail.com','Forward',183,77),
    ('Alpine Strikers','Niklas','Berger','p51@gmail.com','Midfielder',179,73),
    ('Alpine Strikers','Tobias','Frank','p52@gmail.com','Defender',186,80),
    ('Alpine Strikers','Marcel','Winkler','p53@gmail.com','Forward',184,78),
    ('Alpine Strikers','Pascal','Neumann','p54@gmail.com','Midfielder',180,74),
    ('Alpine Strikers','Dennis','Koch','p55@gmail.com','Defender',188,82),
    ('Alpine Strikers','Oliver','Busch','p56@gmail.com','Goalkeeper',192,86),
    ('Riviera Royals','Antoine','Laurent','p57@gmail.com','Forward',182,76),
    ('Riviera Royals','Lucas','Bernard','p58@gmail.com','Midfielder',179,72),
    ('Riviera Royals','Hugo','Moreau','p59@gmail.com','Defender',186,81),
    ('Riviera Royals','Maxime','Girard','p60@gmail.com','Goalkeeper',190,85),
    ('Riviera Royals','Julien','Lefevre','p61@gmail.com','Forward',183,77),
    ('Riviera Royals','Theo','Dubois','p62@gmail.com','Midfielder',180,74),
    ('Riviera Royals','Pierre','Lambert','p63@gmail.com','Defender',187,82),
    ('Riviera Royals','Adrien','Roche','p64@gmail.com','Forward',182,76),
    ('Riviera Royals','Clement','Faure','p65@gmail.com','Midfielder',179,73),
    ('Riviera Royals','Leo','Marchand','p66@gmail.com','Defender',186,80),
    ('Riviera Royals','Baptiste','Noel','p67@gmail.com','Forward',184,78),
    ('Riviera Royals','Arthur','Perrot','p68@gmail.com','Midfielder',180,74),
    ('Riviera Royals','Remy','Colin','p69@gmail.com','Defender',188,83),
    ('Riviera Royals','Paul','Garnier','p70@gmail.com','Goalkeeper',192,86),
    ('Canal City Crew','Mehmet','Arslan','p71@gmail.com','Forward',183,77),
    ('Canal City Crew','Emir','Demir','p72@gmail.com','Midfielder',179,72),
    ('Canal City Crew','Kerem','Yilmaz','p73@gmail.com','Defender',186,81),
    ('Canal City Crew','Can','Kaya','p74@gmail.com','Goalkeeper',190,85),
    ('Canal City Crew','Deniz','Aydin','p75@gmail.com','Forward',182,76),
    ('Canal City Crew','Burak','Sahin','p76@gmail.com','Midfielder',180,74),
    ('Canal City Crew','Alp','Yildiz','p77@gmail.com','Defender',187,82),
    ('Canal City Crew','Eren','Kaplan','p78@gmail.com','Forward',182,76),
    ('Canal City Crew','Serkan','Kurt','p79@gmail.com','Midfielder',179,73),
    ('Canal City Crew','Mert','Ozdemir','p80@gmail.com','Defender',186,80),
    ('Canal City Crew','Onur','Tekin','p81@gmail.com','Forward',184,78),
    ('Canal City Crew','Baran','Aksoy','p82@gmail.com','Midfielder',180,74),
    ('Canal City Crew','Arda','Ceylan','p83@gmail.com','Defender',188,82),
    ('Canal City Crew','Furkan','Gunes','p84@gmail.com','Goalkeeper',192,86),
    ('Atlas Eagles','Carlos','Navarro','p85@gmail.com','Forward',182,76),
    ('Atlas Eagles','Miguel','Torres','p86@gmail.com','Midfielder',179,72),
    ('Atlas Eagles','Javier','Castillo','p87@gmail.com','Defender',186,81),
    ('Atlas Eagles','Luis','Herrera','p88@gmail.com','Goalkeeper',190,85),
    ('Atlas Eagles','Sergio','Molina','p89@gmail.com','Forward',183,77),
    ('Atlas Eagles','Andres','Cabrera','p90@gmail.com','Midfielder',180,74),
    ('Atlas Eagles','Pedro','Salas','p91@gmail.com','Defender',187,82),
    ('Atlas Eagles','Diego','Campos','p92@gmail.com','Forward',182,76),
    ('Atlas Eagles','Raul','Dominguez','p93@gmail.com','Midfielder',179,73),
    ('Atlas Eagles','Ignacio','Ponce','p94@gmail.com','Defender',186,80),
    ('Atlas Eagles','Esteban','Flores','p95@gmail.com','Forward',184,78),
    ('Atlas Eagles','Mateo','Serrano','p96@gmail.com','Midfielder',180,74),
    ('Atlas Eagles','Bruno','Aguilar','p97@gmail.com','Defender',188,83),
    ('Atlas Eagles','Tomas','Rojas','p98@gmail.com','Goalkeeper',192,86),
    ('Silk Route FC','Aarav','Patel','p99@gmail.com','Forward',182,76),
    ('Silk Route FC','Rohan','Sharma','p100@gmail.com','Midfielder',179,72),
    ('Silk Route FC','Vihaan','Kapoor','p101@gmail.com','Defender',186,81),
    ('Silk Route FC','Arjun','Mehta','p102@gmail.com','Goalkeeper',190,85),
    ('Silk Route FC','Ishaan','Nair','p103@gmail.com','Forward',183,77),
    ('Silk Route FC','Reyansh','Gupta','p104@gmail.com','Midfielder',180,74),
    ('Silk Route FC','Advait','Khanna','p105@gmail.com','Defender',187,82),
    ('Silk Route FC','Kabir','Bose','p106@gmail.com','Forward',182,76),
    ('Silk Route FC','Arnav','Malhotra','p107@gmail.com','Midfielder',179,73),
    ('Silk Route FC','Dhruv','Verma','p108@gmail.com','Defender',186,80),
    ('Silk Route FC','Vivaan','Iyer','p109@gmail.com','Forward',184,78),
    ('Silk Route FC','Kian','Desai','p110@gmail.com','Midfielder',180,74),
    ('Silk Route FC','Shaan','Batra','p111@gmail.com','Defender',188,82),
    ('Silk Route FC','Ayaan','Sethi','p112@gmail.com','Goalkeeper',192,86)
  ) AS v(team_name, first_name, last_name, email, position, height_cm, weight_kg)
),
numbered_players AS (
  SELECT pd.*, ROW_NUMBER() OVER () AS rn
  FROM player_data pd
),
insert_users AS (
  INSERT INTO Users (
    FirstName, LastName, Email, HashedPassword, Salt, PasswordDate,
    PhoneNumber, BirthDate, Role, Nationality
  )
  SELECT
    first_name,
    last_name,
    email,
    'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'),
    'player',
    'Local'
  FROM numbered_players
  RETURNING UsersID, Email
),
players_with_ids AS (
  SELECT np.*, iu.UsersID
  FROM numbered_players np
  JOIN insert_users iu ON iu.Email = np.email
),
player_employees AS (
  INSERT INTO Employee (UsersID, TeamID)
  SELECT pwi.UsersID, t.TeamID
  FROM players_with_ids pwi
  JOIN Team t ON t.TeamName = pwi.team_name
  RETURNING UsersID, TeamID
),
numbered_employee AS (
  SELECT pe.*, ROW_NUMBER() OVER (ORDER BY pe.UsersID) AS rn
  FROM player_employees pe
),
insert_employment AS (
  INSERT INTO Employment (StartDate, EndDate, Salary)
  SELECT DATE '2024-01-01', TIMESTAMP '2026-12-30 00:00:00', 60000 + ((rn - 1) % 5) * 2000
  FROM numbered_employee
  ORDER BY rn
  RETURNING EmploymentID
),
employment_with_rn AS (
  SELECT ie.EmploymentID, ROW_NUMBER() OVER (ORDER BY ie.EmploymentID) AS rn
  FROM insert_employment ie
),
insert_employed AS (
  INSERT INTO Employed (EmploymentID, UsersID, TeamID)
  SELECT ewr.EmploymentID, ne.UsersID, ne.TeamID
  FROM employment_with_rn ewr
  JOIN numbered_employee ne USING (rn)
)
INSERT INTO Player (UsersID, Height, Weight, Overall, Position, IsEligible)
SELECT pwi.UsersID, pwi.height_cm, pwi.weight_kg, '85', pwi.position, 'eligible'
FROM players_with_ids pwi;

-- Trigger to auto-mark training attendance as skipped when training time arrives
CREATE OR REPLACE FUNCTION auto_mark_training_skipped()
RETURNS TRIGGER AS $$
BEGIN
    -- For each player on the coach's team who doesn't have a TrainingAttendance record
    INSERT INTO TrainingAttendance (SessionID, PlayerID, Status)
    SELECT 
        NEW.SessionID,
        e_player.UsersID,
        0  -- Status 0 = Skipped
    FROM Employee e_coach
    JOIN Employee e_player ON e_coach.TeamID = e_player.TeamID
    JOIN Player p ON e_player.UsersID = p.UsersID
    WHERE e_coach.UsersID = NEW.CoachID
      AND e_player.UsersID != e_coach.UsersID  -- Don't include the coach
      AND NOT EXISTS (
          SELECT 1 
          FROM TrainingAttendance ta 
          WHERE ta.SessionID = NEW.SessionID 
          AND ta.PlayerID = e_player.UsersID
      )
    ON CONFLICT (SessionID, PlayerID) DO NOTHING;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_auto_mark_training_skipped
AFTER INSERT OR UPDATE OF SessionDate ON TrainingSession
FOR EACH ROW
WHEN (NEW.SessionDate <= NOW())
EXECUTE FUNCTION auto_mark_training_skipped();

-- Function to process existing trainings that have passed
CREATE OR REPLACE FUNCTION process_past_trainings()
RETURNS void AS $$
BEGIN
    -- Mark all players as skipped for trainings that have passed and don't have attendance records
    INSERT INTO TrainingAttendance (SessionID, PlayerID, Status)
    SELECT DISTINCT
        ts.SessionID,
        e_player.UsersID,
        0  -- Status 0 = Skipped
    FROM TrainingSession ts
    JOIN Employee e_coach ON ts.CoachID = e_coach.UsersID
    JOIN Employee e_player ON e_coach.TeamID = e_player.TeamID
    JOIN Player p ON e_player.UsersID = p.UsersID
    WHERE ts.SessionDate <= NOW()
      AND e_player.UsersID != e_coach.UsersID
      AND NOT EXISTS (
          SELECT 1 
          FROM TrainingAttendance ta 
          WHERE ta.SessionID = ts.SessionID 
          AND ta.PlayerID = e_player.UsersID
      )
    ON CONFLICT (SessionID, PlayerID) DO NOTHING;
END;
$$ LANGUAGE plpgsql;
