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
  SessionDate TIMESTAMPTZ NOT NULL,
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
  PlayerTeamAtOfferTime INT,
  RequestingTeamAtOfferTime INT,
  PRIMARY KEY (OfferID),
  FOREIGN KEY (RequestingCoach) REFERENCES Coach(UsersID) ON DELETE CASCADE,
  FOREIGN KEY (RequestedPlayer) REFERENCES Player(UsersID) ON DELETE CASCADE,
  FOREIGN KEY (PlayerTeamAtOfferTime) REFERENCES Team(TeamID) ON DELETE SET NULL,
  FOREIGN KEY (RequestingTeamAtOfferTime) REFERENCES Team(TeamID) ON DELETE SET NULL
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
  Status INT,
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
    m.HomeTeamID,
    m.AwayTeamID,
    home.TeamName AS HomeTeamName,
    away.TeamName AS AwayTeamName,
    m.hometeamscore,
    m.awayteamscore,
    m.winnerteam,
    m.MatchStartDatetime,
    l.Name AS CompetitionName,
    rma.RefereeID,
    TRUE AS IsLeague,
    m.IsLocked
  FROM Match m
  JOIN Team home ON m.HomeTeamID = home.TeamID
  JOIN Team away ON m.AwayTeamID = away.TeamID
  JOIN RefereeMatchAttendance rma ON m.MatchID = rma.MatchID
  JOIN SeasonalMatch sm ON m.MatchID = sm.MatchID
  JOIN League l USING (LeagueID)

  UNION

  SELECT
    m.MatchID,
    m.HomeTeamID,
    m.AwayTeamID,
    home.TeamName AS HomeTeamName,
    away.TeamName AS AwayTeamName,
    m.hometeamscore,
    m.awayteamscore,
    m.winnerteam,
    m.MatchStartDatetime,
    t.Name AS CompetitionName,
    rma.RefereeID,
    FALSE AS IsLeague,
    m.IsLocked
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

CREATE OR REPLACE VIEW teamCoaches AS
SELECT
  e.TeamID,
  c.UsersID AS CoachID
FROM Coach c
JOIN Employee e ON c.UsersID = e.UsersID
WHERE e.TeamID IS NOT NULL;

CREATE OR REPLACE VIEW TeamPlayers AS
SELECT
  e.TeamID,
  p.UsersID AS PlayerID
FROM Player p
JOIN Employee e ON p.UsersID = e.UsersID
WHERE e.TeamID IS NOT NULL;

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
    -- 6. Check if both children have winners AND are locked
    ----------------------------------------------------------------
    SELECT winnerteam INTO child1_winner
    FROM AllTournamentMatchInfo WHERE matchid = child1_match AND islocked = TRUE;

    SELECT winnerteam INTO child2_winner
    FROM AllTournamentMatchInfo WHERE matchid = child2_match AND islocked = TRUE;

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


-- Function to handle the logic of switching substitutes
CREATE OR REPLACE FUNCTION handle_substitution_change()
RETURNS TRIGGER AS $$
DECLARE
    target_play_id INT;
BEGIN
    -- Only proceed if the SubstitutionID has actually changed
    IF (OLD.SubstitutionID IS DISTINCT FROM NEW.SubstitutionID) THEN

        -- 1. Handle Removal of the OLD substitute (if one existed)
        IF OLD.SubstitutionID IS NOT NULL THEN
            -- Find the specific play record to delete based on the "closest start time" rule.
            -- We look for the play record where the PlayerID matches the OLD substitute.
            -- We assume the substitute's StartTime should have matched the original player's StopTime.
            SELECT PlayID INTO target_play_id
            FROM Play
            WHERE MatchID = OLD.MatchID
              AND PlayerID = OLD.SubstitutionID
            -- Calculate absolute difference to find the closest time match
            ORDER BY ABS(StartTime - COALESCE(OLD.StopTime, 0)) ASC
            LIMIT 1;

            -- If a matching record is found, delete it
            IF target_play_id IS NOT NULL THEN
                DELETE FROM Play WHERE PlayID = target_play_id;
            END IF;
        END IF;

        -- 2. Handle Insertion of the NEW substitute (if one is provided)
        IF NEW.SubstitutionID IS NOT NULL THEN
            -- Insert a new record for the new substitute
            -- They enter the game at the exact moment the original player leaves (NEW.StopTime)
            INSERT INTO Play (
                MatchID, 
                PlayerID, 
                SubstitutionID, 
                StartTime, 
                StopTime,
                GoalsScored, 
                PenaltiesScored, 
                AssistsMade, 
                TotalPasses, 
                YellowCards, 
                RedCards, 
                Saves
            )
            VALUES (
                NEW.MatchID,
                NEW.SubstitutionID,
                NULL, -- The incoming player is not yet substituted out
                COALESCE(NEW.StopTime, 0), -- StartTime = StopTime of player leaving
                NULL, -- StopTime is null (they are currently playing)
                0, 0, 0, 0, 0, 0, 0 -- Initialize stats to 0
            );
        END IF;

    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger definition
CREATE TRIGGER trg_handle_substitution_change
AFTER UPDATE OF SubstitutionID ON Play
FOR EACH ROW
EXECUTE FUNCTION handle_substitution_change();


-- trigger to update scores on play insert
CREATE OR REPLACE FUNCTION update_all_after_play_insertion()
RETURNS TRIGGER AS $$
DECLARE
    player_team_id INT;
    match_time TIMESTAMP;
BEGIN
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

-- trigger to update scores on play update
CREATE OR REPLACE FUNCTION update_all_after_play_update()
RETURNS TRIGGER AS $$
DECLARE
    player_team_id INT;
    match_time TIMESTAMP;
    goal_delta INT;
BEGIN
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
-- CREATE OR REPLACE FUNCTION update_match_winner()
-- RETURNS TRIGGER AS $$
-- BEGIN
--     IF EXISTS (SELECT 1 FROM TournamentMatch WHERE MatchID = NEW.MatchID) THEN
--         RETURN NULL;
--     END IF;
-- 
--     IF NEW.HomeTeamScore IS NULL OR NEW.AwayTeamScore IS NULL THEN
--         RETURN NULL;
--     END IF;
-- 
--     IF NEW.HomeTeamScore <> OLD.HomeTeamScore OR NEW.AwayTeamScore <> OLD.AwayTeamScore THEN
--         UPDATE Match M
--         SET WinnerTeam = CASE
--             WHEN NEW.HomeTeamScore > NEW.AwayTeamScore THEN NEW.HomeTeamName
--             WHEN NEW.HomeTeamScore < NEW.AwayTeamScore THEN NEW.AwayTeamName
--             ELSE NULL
--         END
--         WHERE M.MatchID = NEW.MatchID;
--     END IF;
-- 
--     RETURN NULL;
-- END;
-- $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_match_winner()
RETURNS TRIGGER AS $$
DECLARE
    total_home_penalties INT := 0;
    total_away_penalties INT := 0;
BEGIN
    IF NEW.HomeTeamScore IS NULL OR NEW.AwayTeamScore IS NULL THEN
        NEW.WinnerTeam := NULL;
        RETURN NEW;
    END IF;

    -- 2. Decide Winner based on main scores
    IF NEW.HomeTeamScore > NEW.AwayTeamScore THEN
        NEW.WinnerTeam := NEW.HomeTeamName;
    ELSIF NEW.AwayTeamScore > NEW.HomeTeamScore THEN
        NEW.WinnerTeam := NEW.AwayTeamName;
    ELSE
        -- 3. It's a TIE: Culmination of penalty scores logic
        
        -- Calculate total penalties for the Home Team
        SELECT COALESCE(SUM(COALESCE(P.PenaltiesScored, 0)), 0)
        INTO total_home_penalties
        FROM Play P
        JOIN AllEmploymentInfo AE ON P.PlayerID = AE.UsersID
        WHERE P.MatchID = NEW.MatchID 
          AND AE.TeamID = NEW.HomeTeamID
          AND NEW.matchstartdatetime >= AE.StartDate
          AND (NEW.matchstartdatetime <= AE.EndDate OR AE.EndDate IS NULL);

        -- Calculate total penalties for the Away Team
        SELECT COALESCE(SUM(COALESCE(P.PenaltiesScored, 0)), 0)
        INTO total_away_penalties
        FROM Play P
        JOIN AllEmploymentInfo AE ON P.PlayerID = AE.UsersID
        WHERE P.MatchID = NEW.MatchID
          AND AE.TeamID = NEW.AwayTeamID
          AND NEW.matchstartdatetime >= AE.StartDate
          AND (NEW.matchstartdatetime <= AE.EndDate OR AE.EndDate IS NULL);

        -- Decide winner based on penalties
        IF COALESCE(total_home_penalties, 0) > COALESCE(total_away_penalties, 0) THEN
            NEW.WinnerTeam := NEW.HomeTeamName;
        ELSIF COALESCE(total_away_penalties, 0) > COALESCE(total_home_penalties, 0) THEN
            NEW.WinnerTeam := NEW.AwayTeamName;
        ELSE
            -- Still a tie after penalties
            NEW.WinnerTeam := NULL;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER match_update
BEFORE UPDATE ON Match
FOR EACH ROW
EXECUTE FUNCTION update_match_winner();

-- Trigger to trigger match winner update trigger when a play is updated
CREATE OR REPLACE FUNCTION trigger_match_recalc_from_play()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Match 
    SET MatchID = MatchID -- A "no-op" update that still fires triggers
    WHERE MatchID = COALESCE(NEW.MatchID, OLD.MatchID);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER play_change_recalc
AFTER INSERT OR UPDATE OR DELETE ON Play
FOR EACH ROW
EXECUTE FUNCTION trigger_match_recalc_from_play();

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
      VALUES (NOW(), NEW.OfferedEndDate, NEW.OfferAmount)
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

-- ===== TRIGGER: Update Play records when employment ends =====
-- Purpose: When a player's employment ends, delete their Play records for future matches
--          (only for matches where they were on the old team)
CREATE OR REPLACE FUNCTION handle_employment_end()
RETURNS TRIGGER AS $$
DECLARE
    v_player_id INT;
    v_team_id INT;
BEGIN
    -- Only process if EndDate is being set to NOW() or a past date
    -- and it wasn't already in the past
    IF NEW.EndDate <= NOW() AND (OLD.EndDate IS NULL OR OLD.EndDate > NOW()) THEN
        -- Get the player and team from the Employed table
        SELECT em.UsersID, em.TeamID
        INTO v_player_id, v_team_id
        FROM Employed em
        WHERE em.EmploymentID = NEW.EmploymentID
        LIMIT 1;
        
        -- Only proceed if we found the employment record
        IF v_player_id IS NOT NULL AND v_team_id IS NOT NULL THEN
            -- Delete Play records for future matches where the player was on this team
            DELETE FROM Play
            WHERE PlayerID = v_player_id
              AND MatchID IN (
                  SELECT MatchID
                  FROM Match
                  WHERE MatchStartDatetime > NOW()
                    AND (HomeTeamID = v_team_id OR AwayTeamID = v_team_id)
              );
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_employment_end
AFTER UPDATE OF EndDate ON Employment
FOR EACH ROW
EXECUTE FUNCTION handle_employment_end();

-- ===== TRIGGER: Update Play records when employment starts =====
-- Purpose: When a player starts new employment, create Play records for future matches
--          where their new team is involved
CREATE OR REPLACE FUNCTION handle_employment_start()
RETURNS TRIGGER AS $$
DECLARE
    v_player_id INT;
    v_team_id INT;
    v_start_date TIMESTAMP;
    v_end_date TIMESTAMP;
BEGIN
    -- Get employment details
    SELECT e.StartDate, e.EndDate
    INTO v_start_date, v_end_date
    FROM Employment e
    WHERE e.EmploymentID = NEW.EmploymentID;
    
    v_player_id := NEW.UsersID;
    v_team_id := NEW.TeamID;
    
    -- Only process if employment is active (not in the past)
    IF v_start_date IS NOT NULL AND v_end_date IS NOT NULL AND v_end_date >= NOW() THEN
        -- Insert Play records for future matches where the new team is involved
        INSERT INTO Play (MatchID, PlayerID)
        SELECT m.MatchID, v_player_id
        FROM Match m
        WHERE (m.HomeTeamID = v_team_id OR m.AwayTeamID = v_team_id)
          AND m.MatchStartDatetime > NOW()
          AND m.MatchStartDatetime >= v_start_date
          AND m.MatchStartDatetime <= v_end_date
          AND NOT EXISTS (
              SELECT 1
              FROM Play p
              WHERE p.MatchID = m.MatchID
                AND p.PlayerID = v_player_id
          );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_employment_start
AFTER INSERT ON Employed
FOR EACH ROW
EXECUTE FUNCTION handle_employment_start();

-- ===== TRIGGER: Set training attendance to Status=2 (Injured) when injury is added =====
CREATE OR REPLACE FUNCTION set_training_status_on_injury_insert()
RETURNS TRIGGER AS $$
DECLARE
    v_team_id INT;
BEGIN
    -- Get the player's team
    SELECT TeamID INTO v_team_id
    FROM Employee
    WHERE UsersID = NEW.PlayerID;

    -- If player has no team, nothing to do
    IF v_team_id IS NULL THEN
        RETURN NEW;
    END IF;

    -- Insert or update TrainingAttendance for all training sessions
    -- that fall within the injury period (InjuryDate to RecoveryDate)
    INSERT INTO TrainingAttendance (SessionID, PlayerID, Status)
    SELECT ts.SessionID, NEW.PlayerID, 2
    FROM TrainingSession ts
    JOIN Coach c ON ts.CoachID = c.UsersID
    JOIN Employee ec ON c.UsersID = ec.UsersID
    WHERE ec.TeamID = v_team_id
      AND ts.SessionDate >= NEW.InjuryDate
      AND ts.SessionDate <= NEW.RecoveryDate
    ON CONFLICT (SessionID, PlayerID) 
    DO UPDATE SET Status = 2;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_injury_insert_set_training_status
AFTER INSERT ON Injury
FOR EACH ROW
EXECUTE FUNCTION set_training_status_on_injury_insert();

-- ===== TRIGGER: Update training attendance when injury recovery date is updated =====
CREATE OR REPLACE FUNCTION update_training_status_on_injury_update()
RETURNS TRIGGER AS $$
DECLARE
    v_team_id INT;
BEGIN
    -- Only proceed if RecoveryDate changed
    IF OLD.RecoveryDate = NEW.RecoveryDate THEN
        RETURN NEW;
    END IF;

    -- Get the player's team
    SELECT TeamID INTO v_team_id
    FROM Employee
    WHERE UsersID = NEW.PlayerID;

    IF v_team_id IS NULL THEN
        RETURN NEW;
    END IF;

    -- If recovery date was EXTENDED: Mark additional trainings as Status=2
    IF NEW.RecoveryDate > OLD.RecoveryDate THEN
        INSERT INTO TrainingAttendance (SessionID, PlayerID, Status)
        SELECT ts.SessionID, NEW.PlayerID, 2
        FROM TrainingSession ts
        JOIN Coach c ON ts.CoachID = c.UsersID
        JOIN Employee ec ON c.UsersID = ec.UsersID
        WHERE ec.TeamID = v_team_id
          AND ts.SessionDate > OLD.RecoveryDate
          AND ts.SessionDate <= NEW.RecoveryDate
        ON CONFLICT (SessionID, PlayerID) 
        DO UPDATE SET Status = 2;
    END IF;

    -- If recovery date was SHORTENED: Reset trainings outside the new period to NULL (only future ones)
    IF NEW.RecoveryDate < OLD.RecoveryDate THEN
        UPDATE TrainingAttendance ta
        SET Status = NULL
        FROM TrainingSession ts
        WHERE ta.SessionID = ts.SessionID
          AND ta.PlayerID = NEW.PlayerID
          AND ta.Status = 2
          AND ts.SessionDate > NEW.RecoveryDate
          AND ts.SessionDate <= OLD.RecoveryDate
          AND ts.SessionDate > NOW();  -- Only future trainings
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_injury_update_training_status
AFTER UPDATE OF RecoveryDate ON Injury
FOR EACH ROW
EXECUTE FUNCTION update_training_status_on_injury_update();

-- ===== TRIGGER: Reset training attendance when injury is deleted =====
CREATE OR REPLACE FUNCTION reset_training_status_on_injury_delete()
RETURNS TRIGGER AS $$
BEGIN
    -- Reset Status to NULL for future trainings that were marked as injured (Status=2)
    UPDATE TrainingAttendance ta
    SET Status = NULL
    FROM TrainingSession ts
    WHERE ta.SessionID = ts.SessionID
      AND ta.PlayerID = OLD.PlayerID
      AND ta.Status = 2
      AND ts.SessionDate > NOW();  -- Only future trainings

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_injury_delete_reset_training_status
AFTER DELETE ON Injury
FOR EACH ROW
EXECUTE FUNCTION reset_training_status_on_injury_delete();

-- Trigger to auto-mark training attendance as NULL when training time arrives
CREATE OR REPLACE FUNCTION auto_mark_training_skipped()
RETURNS TRIGGER AS $$
BEGIN
    -- For each player on the coach's team who doesn't have a TrainingAttendance record
    INSERT INTO TrainingAttendance (SessionID, PlayerID, Status)
    SELECT 
        NEW.SessionID,
        e_player.UsersID,
        NULL  -- Status NULL = Not set yet
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
WHERE u.Email IN ('c1@gmail.com', 'c2@gmail.com', 'c3@gmail.com' , 'c4@gmail.com' );

INSERT INTO Coach (UsersID, Certification)
SELECT u.UsersID, 'UEFA A License'
FROM Users u
WHERE u.Email IN ('c1@gmail.com', 'c2@gmail.com', 'c3@gmail.com', 'c4@gmail.com');

-- Additional coaches (unassigned to teams)
INSERT INTO Employee (UsersID, TeamID)
SELECT u.UsersID, NULL
FROM Users u
WHERE u.Email IN ( 'c5@gmail.com', 'c6@gmail.com', 'c7@gmail.com', 'c8@gmail.com');

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
    (ARRAY['USA', 'Canada', 'UK', 'Spain', 'France', 'Germany', 'Italy', 'Brazil', 'Argentina', 'Mexico', 'Japan', 'South Korea', 'Australia', 'Netherlands', 'Portugal', 'Turkey', 'Russia', 'Poland', 'Sweden', 'Norway', 'Denmark', 'Belgium', 'Switzerland', 'Greece', 'Egypt', 'Morocco', 'Nigeria', 'South Africa', 'India', 'China'])[1 + floor(random() * 30)::int]
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




---------------------------------------------------------------------------------------------------------------------------
-- Test referees
-- 1. Create a Test Referee
-- Email: ref_test@example.com, Password: (Matches your hashed sample)
INSERT INTO Users (FirstName, LastName, Email, HashedPassword, Salt, BirthDate, Role, Nationality)
VALUES ('Test', 'Referee', 'ref_test@example.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e', '1985-05-20', 'referee', 'USA');

INSERT INTO Referee (UsersID, Certification)
SELECT UsersID, 'FIFA Pro' FROM Users WHERE Email = 'ref_test@example.com';

-- 2. Create Team Owners
INSERT INTO Users (FirstName, LastName, Email, HashedPassword, Salt, BirthDate, Role, Nationality)
VALUES 
('Owner', 'Red', 'owner_red@example.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e', '1970-01-01', 'team_owner', 'USA'),
('Owner', 'Blue', 'owner_blue@example.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e', '1972-01-01', 'team_owner', 'UK');

INSERT INTO TeamOwner (UsersID, NetWorth)
SELECT UsersID, 5000000 FROM Users WHERE Email IN ('owner_red@example.com', 'owner_blue@example.com');

-- 3. Create Teams
INSERT INTO Team (OwnerID, TeamName, EstablishedDate, HomeVenue)
VALUES 
((SELECT UsersID FROM Users WHERE Email = 'owner_red@example.com'), 'Red Dragons', '2020-01-01', 'Dragon Pit'),
((SELECT UsersID FROM Users WHERE Email = 'owner_blue@example.com'), 'Blue Knights', '2020-01-01', 'Castle Arena');

-- 4. Create Players, Employees, and Contracts
-- We perform a bulk insert logic here to ensure they are "Employed" BEFORE the match is created.

WITH new_players AS (
    INSERT INTO Users (FirstName, LastName, Email, HashedPassword, Salt, BirthDate, Role, Nationality)
    VALUES 
    -- Red Team Players
    ('John', 'Striker', 'p_red1@example.com', 'hash', 'salt', '1998-01-01', 'player', 'USA'),
    ('Mike', 'Mid', 'p_red2@example.com', 'hash', 'salt', '1999-01-01', 'player', 'USA'),
    ('Steve', 'Defender', 'p_red3@example.com', 'hash', 'salt', '1997-01-01', 'player', 'USA'),
    ('Dave', 'Goalie', 'p_red4@example.com', 'hash', 'salt', '1996-01-01', 'player', 'USA'),
    ('Tom', 'Bench', 'p_red5@example.com', 'hash', 'salt', '2000-01-01', 'player', 'USA'),
    -- Blue Team Players
    ('Alex', 'Forward', 'p_blue1@example.com', 'hash', 'salt', '1998-05-01', 'player', 'UK'),
    ('Ben', 'Winger', 'p_blue2@example.com', 'hash', 'salt', '1999-05-01', 'player', 'UK'),
    ('Chris', 'Back', 'p_blue3@example.com', 'hash', 'salt', '1997-05-01', 'player', 'UK'),
    ('Dan', 'Keeper', 'p_blue4@example.com', 'hash', 'salt', '1996-05-01', 'player', 'UK'),
    ('Eric', 'Sub', 'p_blue5@example.com', 'hash', 'salt', '2000-05-01', 'player', 'UK')
    RETURNING UsersID, Email
),
-- Insert into Player Subtype
player_subtype AS (
    INSERT INTO Player (UsersID, Height, Weight, Overall, Position, IsEligible)
    SELECT UsersID, 180, 75, '80', 'Midfielder', 'Yes' FROM new_players
    RETURNING UsersID
),
-- Insert into Employee Subtype and Assign Team
employee_assign AS (
    INSERT INTO Employee (UsersID, TeamID)
    SELECT 
        np.UsersID, 
        CASE 
            WHEN np.Email LIKE '%red%' THEN (SELECT TeamID FROM Team WHERE TeamName = 'Red Dragons')
            ELSE (SELECT TeamID FROM Team WHERE TeamName = 'Blue Knights')
        END
    FROM new_players np
    RETURNING UsersID, TeamID
),
-- Create Employment Contract (Must be active NOW for trigger to work)
employment_contract AS (
    INSERT INTO Employment (StartDate, EndDate, Salary)
    SELECT '2023-01-01', '2030-12-31', 100000
    FROM new_players
    RETURNING EmploymentID
),
-- Link Employment to Employee
employed_link AS (
    INSERT INTO Employed (EmploymentID, UsersID, TeamID)
    SELECT 
        ec.EmploymentID, 
        ea.UsersID, 
        ea.TeamID
    FROM 
        (SELECT EmploymentID, ROW_NUMBER() OVER () as rn FROM employment_contract) ec
    JOIN 
        (SELECT UsersID, TeamID, ROW_NUMBER() OVER () as rn FROM employee_assign) ea
    ON ec.rn = ea.rn
)
SELECT count(*) as players_created FROM new_players;

-- 5. Create League and Season
INSERT INTO League (Name) VALUES ('Premier Test League') ON CONFLICT DO NOTHING;

INSERT INTO Season (LeagueID, SeasonNo, SeasonYear, StartDate, EndDate, PrizePool)
VALUES (
    (SELECT LeagueID FROM League WHERE Name = 'Premier Test League'),
    1,
    '2025-01-01',
    '2025-01-01',
    '2025-12-31',
    1000000
) ON CONFLICT DO NOTHING;

-- 6. Create the MATCH
-- IMPORTANT: Because the players are already inserted and have active Employment records,
-- the trigger 'trg_auto_create_plays_on_match_insert' will fire immediately after this INSERT.
-- It will populate the 'Play' table for the 10 players created above.

INSERT INTO Match (
    HomeTeamID, AwayTeamID, MatchStartDatetime, MatchEndDatetime, 
    VenuePlayed, HomeTeamName, AwayTeamName, 
    HomeTeamScore, AwayTeamScore, WinnerTeam, IsLocked
)
VALUES (
    (SELECT TeamID FROM Team WHERE TeamName = 'Red Dragons'),
    (SELECT TeamID FROM Team WHERE TeamName = 'Blue Knights'),
    NOW(),
    NOW() + INTERVAL '2 hours',
    'Dragon Pit',
    'Red Dragons',
    'Blue Knights',
    0, 0, NULL, FALSE
);

-- Link Match to Season
INSERT INTO SeasonalMatch (MatchID, LeagueID, SeasonNo, SeasonYear)
VALUES (
    (SELECT MAX(MatchID) FROM Match),
    (SELECT LeagueID FROM League WHERE Name = 'Premier Test League'),
    1,
    '2025-01-01'
);

-- 7. Assign Referee to Match
-- This allows the UI to filter "My Matches" for the logged-in referee
INSERT INTO RefereeMatchAttendance (MatchID, RefereeID)
VALUES (
    (SELECT MAX(MatchID) FROM Match),
    (SELECT UsersID FROM Users WHERE Email = 'ref_test@example.com'));


-- Players without teams (no employment records)
-- These players exist as Users, Employees (with NULL TeamID), and Players, but have no Employment records
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
  ('Jake', 'Freeman', 'free1@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-2001', TO_DATE('1995-03-15','YYYY-MM-DD'), 'player', 'USA'),
  ('Marcus', 'Wilder', 'free2@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-2002', TO_DATE('1996-07-22','YYYY-MM-DD'), 'player', 'Canada'),
  ('Oscar', 'Mitchell', 'free3@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-2003', TO_DATE('1994-11-08','YYYY-MM-DD'), 'player', 'UK'),
  ('Ryan', 'Bennett', 'free4@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-2004', TO_DATE('1997-02-14','YYYY-MM-DD'), 'player', 'Australia'),
  ('Victor', 'Garcia', 'free5@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-2005', TO_DATE('1993-09-30','YYYY-MM-DD'), 'player', 'Spain');

-- Insert these players as Employees with NULL TeamID (no team assignment)
INSERT INTO Employee (UsersID, TeamID)
SELECT u.UsersID, NULL
FROM Users u
WHERE u.Email IN ('free1@gmail.com', 'free2@gmail.com', 'free3@gmail.com', 'free4@gmail.com', 'free5@gmail.com');

-- Insert these players into the Player table
INSERT INTO Player (UsersID, Height, Weight, Overall, Position, IsEligible)
SELECT 
  u.UsersID,
  CASE u.Email
    WHEN 'free1@gmail.com' THEN 182
    WHEN 'free2@gmail.com' THEN 185
    WHEN 'free3@gmail.com' THEN 178
    WHEN 'free4@gmail.com' THEN 188
    ELSE 192
  END,
  CASE u.Email
    WHEN 'free1@gmail.com' THEN 76
    WHEN 'free2@gmail.com' THEN 79
    WHEN 'free3@gmail.com' THEN 74
    WHEN 'free4@gmail.com' THEN 82
    ELSE 85
  END,
  '82',
  CASE u.Email
    WHEN 'free1@gmail.com' THEN 'Forward'
    WHEN 'free2@gmail.com' THEN 'Midfielder'
    WHEN 'free3@gmail.com' THEN 'Defender'
    WHEN 'free4@gmail.com' THEN 'Midfielder'
    ELSE 'Goalkeeper'
  END,
  'eligible'
FROM Users u
WHERE u.Email IN ('free1@gmail.com', 'free2@gmail.com', 'free3@gmail.com', 'free4@gmail.com', 'free5@gmail.com');



-- Artun match with injured and banned player seeding
-- ==================================================================
-- 1. SETUP OWNERS AND TEAMS
-- ==================================================================

BEGIN;

INSERT INTO Users (FirstName, LastName, Email, HashedPassword, Salt, BirthDate, Role, Nationality)
VALUES 
('Leonidas', 'Sparta', 'owner.sparta@test.com', 'hash', 'salt', '1980-01-01', 'team_owner', 'Greece'),
('Priam', 'Troy', 'owner.troy@test.com', 'hash', 'salt', '1980-01-01', 'team_owner', 'Turkey')
ON CONFLICT (Email) DO NOTHING;

INSERT INTO TeamOwner (UsersID, NetWorth)
VALUES 
((SELECT UsersID FROM Users WHERE Email='owner.sparta@test.com'), 5000000),
((SELECT UsersID FROM Users WHERE Email='owner.troy@test.com'), 5000000)
ON CONFLICT (UsersID) DO NOTHING;

INSERT INTO Team (OwnerID, TeamName, EstablishedDate, HomeVenue)
VALUES 
((SELECT UsersID FROM Users WHERE Email='owner.sparta@test.com'), 'Spartans FC', '1950-01-01', 'Thermopylae Arena'),
((SELECT UsersID FROM Users WHERE Email='owner.troy@test.com'), 'Trojans United', '1950-01-01', 'Wall Stadium')
ON CONFLICT (TeamName) DO NOTHING;

-- ==================================================================
-- 2. CREATE FULL ROSTERS (11 Players per team)
-- ==================================================================

-- --- SPARTANS (Home) ---
INSERT INTO Users (FirstName, LastName, Email, HashedPassword, Salt, BirthDate, Role, Nationality) VALUES 
('Achilles', 'Hero', 'achilles@sparta.com', 'hash', 'salt', '1998-01-01', 'player', 'Greece'),
('Odysseus', 'Tactician', 'odysseus@sparta.com', 'hash', 'salt', '1998-01-01', 'player', 'Greece'),
('Ajax', 'Greater', 'ajax1@sparta.com', 'hash', 'salt', '1995-01-01', 'player', 'Greece'),
('Menelaus', 'King', 'menelaus@sparta.com', 'hash', 'salt', '1994-01-01', 'player', 'Greece'),
('Agamemnon', 'Commander', 'agamemnon@sparta.com', 'hash', 'salt', '1993-01-01', 'player', 'Greece'),
('Patroclus', 'Loyal', 'patroclus@sparta.com', 'hash', 'salt', '1996-01-01', 'player', 'Greece'),
('Diomedes', 'Strong', 'diomedes@sparta.com', 'hash', 'salt', '1997-01-01', 'player', 'Greece'),
('Nestor', 'Elder', 'nestor@sparta.com', 'hash', 'salt', '1980-01-01', 'player', 'Greece'),
('Teucer', 'Archer', 'teucer@sparta.com', 'hash', 'salt', '1998-01-01', 'player', 'Greece'),
('Antilochus', 'Swift', 'antilochus@sparta.com', 'hash', 'salt', '1999-01-01', 'player', 'Greece'),
('Idomeneus', 'Spear', 'idomeneus@sparta.com', 'hash', 'salt', '1992-01-01', 'player', 'Greece');

-- --- TROJANS (Away) ---
INSERT INTO Users (FirstName, LastName, Email, HashedPassword, Salt, BirthDate, Role, Nationality) VALUES 
('Hector', 'Prince', 'hector@troy.com', 'hash', 'salt', '1998-01-01', 'player', 'Turkey'),
('Paris', 'Archer', 'paris@troy.com', 'hash', 'salt', '1998-01-01', 'player', 'Turkey'),
('Aeneas', 'Founder', 'aeneas@troy.com', 'hash', 'salt', '1995-01-01', 'player', 'Turkey'),
('Sarpedon', 'Leader', 'sarpedon@troy.com', 'hash', 'salt', '1994-01-01', 'player', 'Turkey'),
('Glaucus', 'Noble', 'glaucus@troy.com', 'hash', 'salt', '1997-01-01', 'player', 'Turkey'),
('Pandarus', 'Bowman', 'pandarus@troy.com', 'hash', 'salt', '1998-01-01', 'player', 'Turkey'),
('Helenus', 'Seer', 'helenus@troy.com', 'hash', 'salt', '1990-01-01', 'player', 'Turkey'),
('Deiphobus', 'Warrior', 'deiphobus@troy.com', 'hash', 'salt', '1993-01-01', 'player', 'Turkey'),
('Polydamas', 'Wise', 'polydamas@troy.com', 'hash', 'salt', '1996-01-01', 'player', 'Turkey'),
('Agenor', 'Stout', 'agenor@troy.com', 'hash', 'salt', '1997-01-01', 'player', 'Turkey'),
('Dolon', 'Spy', 'dolon@troy.com', 'hash', 'salt', '1999-01-01', 'player', 'Turkey');

-- Link all to Employee and Team
INSERT INTO Employee (UsersID, TeamID) 
SELECT UsersID, (SELECT TeamID FROM Team WHERE TeamName='Spartans FC') FROM Users WHERE Email LIKE '%@sparta.com' AND Role='player';

INSERT INTO Employee (UsersID, TeamID) 
SELECT UsersID, (SELECT TeamID FROM Team WHERE TeamName='Trojans United') FROM Users WHERE Email LIKE '%@troy.com' AND Role='player';

-- Link all to Player
INSERT INTO Player (UsersID, Height, Weight, Overall, Position, IsEligible)
SELECT UsersID, 180, 75, '85', 'Midfielder', 'eligible' FROM Users WHERE (Email LIKE '%@sparta.com' OR Email LIKE '%@troy.com') AND Role='player';

-- ==================================================================
-- 3. EMPLOYMENT CONTRACTS (22 total)
-- ==================================================================

-- Create 22 active contracts
INSERT INTO Employment (StartDate, EndDate, Salary)
SELECT '2024-01-01', '2026-01-01', 1000000 FROM generate_series(1, 22);

-- Link them manually to the players
-- Spartans
INSERT INTO Employed (EmploymentID, UsersID, TeamID)
SELECT 
    (SELECT MIN(EmploymentID) + rn - 1 FROM Employment WHERE StartDate = '2024-01-01'),
    u.UsersID,
    (SELECT TeamID FROM Team WHERE TeamName='Spartans FC')
FROM (SELECT UsersID, ROW_NUMBER() OVER (ORDER BY UsersID) as rn FROM Users WHERE Email LIKE '%@sparta.com' AND Role='player') u;

-- Trojans
INSERT INTO Employed (EmploymentID, UsersID, TeamID)
SELECT 
    (SELECT MIN(EmploymentID) + 11 + rn - 1 FROM Employment WHERE StartDate = '2024-01-01'),
    u.UsersID,
    (SELECT TeamID FROM Team WHERE TeamName='Trojans United')
FROM (SELECT UsersID, ROW_NUMBER() OVER (ORDER BY UsersID) as rn FROM Users WHERE Email LIKE '%@troy.com' AND Role='player') u;

-- ==================================================================
-- 4. CREATE MATCH (Date: CURRENT_DATE - scheduled for today at 20:00)
-- ==================================================================

INSERT INTO Match (
    HomeTeamID, AwayTeamID, MatchStartDatetime, MatchEndDatetime, 
    VenuePlayed, HomeTeamName, AwayTeamName, 
    HomeTeamScore, AwayTeamScore, WinnerTeam, IsLocked
)
VALUES (
    (SELECT TeamID FROM Team WHERE TeamName='Spartans FC'),
    (SELECT TeamID FROM Team WHERE TeamName='Trojans United'),
    CURRENT_DATE + INTERVAL '20 hours',
    CURRENT_DATE + INTERVAL '22 hours',
    'Thermopylae Arena',
    'Spartans FC',
    'Trojans United',
    0, 0, NULL, FALSE
);

-- Link to Season
INSERT INTO League (Name) VALUES ('Ancient League') ON CONFLICT DO NOTHING;
INSERT INTO Season (LeagueID, SeasonNo, SeasonYear, StartDate, EndDate, PrizePool)
VALUES ((SELECT LeagueID FROM League WHERE Name='Ancient League' LIMIT 1), 1, '2025-01-01', '2025-01-01', '2025-12-31', 1000000)
ON CONFLICT DO NOTHING;

INSERT INTO SeasonalMatch (MatchID, LeagueID, SeasonNo, SeasonYear)
VALUES (
    (SELECT MAX(MatchID) FROM Match),
    (SELECT LeagueID FROM League WHERE Name='Ancient League' LIMIT 1),
    1,
    '2025-01-01'
);

-- Assign an admin to the Ancient League season so it appears in admin views
INSERT INTO SeasonModeration (LeagueID, SeasonNo, SeasonYear, AdminID)
VALUES (
    (SELECT LeagueID FROM League WHERE Name='Ancient League' LIMIT 1),
    1,
    '2025-01-01',
    (SELECT UsersID FROM Users WHERE Email='a1@gmail.com' LIMIT 1)
)
ON CONFLICT DO NOTHING;

-- ==================================================================
-- 5. INJECT OVERLAPPING INJURIES AND BANS
-- ==================================================================

-- Spartans: Achilles Injured, Odysseus Banned
INSERT INTO Injury (PlayerID, MatchID, InjuryDate, InjuryType, Description, RecoveryDate)
VALUES ((SELECT UsersID FROM Users WHERE Email='achilles@sparta.com'), NULL, '2025-06-10', 'Heel Strain', 'Classic weak point injury', '2025-07-01');

INSERT INTO Ban (PlayerID, BanStartDate, BanEndDate)
VALUES ((SELECT UsersID FROM Users WHERE Email='odysseus@sparta.com'), '2025-06-01', '2025-06-30');

-- Trojans: Hector Injured, Paris Banned
INSERT INTO Injury (PlayerID, MatchID, InjuryDate, InjuryType, Description, RecoveryDate)
VALUES ((SELECT UsersID FROM Users WHERE Email='hector@troy.com'), NULL, '2025-06-14', 'Concussion', 'Collision with chariot', '2025-06-20');

INSERT INTO Ban (PlayerID, BanStartDate, BanEndDate)
VALUES ((SELECT UsersID FROM Users WHERE Email='paris@troy.com'), '2025-06-15', '2025-06-22');

-- ==================================================================
-- 6. SETUP REFEREE
-- ==================================================================
INSERT INTO Users (FirstName, LastName, Email, HashedPassword, Salt, BirthDate, Role, Nationality)
VALUES ('Homer', 'Referee', 'ref.ancient@test.com', 'hash', 'salt', '1985-05-20', 'referee', 'Ionia')
ON CONFLICT (Email) DO NOTHING;

INSERT INTO Referee (UsersID, Certification)
SELECT UsersID, 'Legendary' FROM Users WHERE Email='ref.ancient@test.com'
ON CONFLICT (UsersID) DO NOTHING;

INSERT INTO RefereeMatchAttendance (MatchID, RefereeID)
VALUES (
    (SELECT MAX(MatchID) FROM Match),
    (SELECT UsersID FROM Users WHERE Email='ref.ancient@test.com')
);
INSERT INTO RefereeMatchAttendance (MatchID, RefereeID)
VALUES (
    (SELECT MAX(MatchID) FROM Match),
    (SELECT UsersID FROM Users WHERE Email='ref_test@example.com')
);
INSERT INTO RefereeMatchAttendance (MatchID, RefereeID)
VALUES (
    (SELECT MAX(MatchID) FROM Match),
    (SELECT UsersID FROM Users WHERE Email='r1@gmail.com')
)
ON CONFLICT DO NOTHING;

COMMIT;
