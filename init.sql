CREATE TABLE Users (
  UsersID SERIAL,
  FirstName VARCHAR(30) NOT NULL,
  LastName VARCHAR(30) NOT NULL,
  Email VARCHAR(255) NOT NULL UNIQUE,
  HashedPassword CHAR(255) NOT NULL,
  Salt CHAR(255) NOT NULL,
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
  MatchID INT NOT NULL,
  RequestingCoach INT NOT NULL,
  RequestedPlayer INT NOT NULL,
  ResponsibleCoach INT,
  OfferDate TIMESTAMP NOT NULL,
  AvailableUntil TIMESTAMP NOT NULL,
  OfferStatus INT NOT NULL,
  PRIMARY KEY (OfferID),
  FOREIGN KEY (RequestingCoach) REFERENCES Coach(UsersID) ON DELETE CASCADE,
  FOREIGN KEY (RequestedPlayer) REFERENCES Player(UsersID) ON DELETE CASCADE,
  FOREIGN KEY (ResponsibleCoach) REFERENCES Coach(UsersID) ON DELETE CASCADE
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

-- Seed data ---------------------------------------------------------------
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
  ('Ada', 'Admin', 'admin@example.com', REPEAT('a', 64), REPEAT('s', 32), NOW(), '555-0001', TO_DATE('1988-05-10','YYYY-MM-DD'), 'admin', 'USA'),
  ('Olivia', 'Owner', 'owner1@example.com', REPEAT('b', 64), REPEAT('t', 32), NOW(), '555-0011', TO_DATE('1990-03-22','YYYY-MM-DD'), 'team_owner', 'Spain'),
  ('Noah', 'Owner', 'owner2@example.com', REPEAT('c', 64), REPEAT('u', 32), NOW(), '555-0022', TO_DATE('1989-11-05','YYYY-MM-DD'), 'team_owner', 'Turkey'),
  ('Mia', 'Owner', 'owner3@example.com', REPEAT('d', 64), REPEAT('v', 32), NOW(), '555-0033', TO_DATE('1992-07-14','YYYY-MM-DD'), 'team_owner', 'Italy'),
  ('Elena', 'Owner', 'owner4@example.com', REPEAT('aa', 32), REPEAT('ww', 16), NOW(), '555-0044', TO_DATE('1987-02-19','YYYY-MM-DD'), 'team_owner', 'Germany'),
  ('Kenan', 'Owner', 'owner5@example.com', REPEAT('bb', 32), REPEAT('xx', 16), NOW(), '555-0055', TO_DATE('1991-09-07','YYYY-MM-DD'), 'team_owner', 'France'),
  ('Sara', 'Owner', 'owner6@example.com', REPEAT('cc', 32), REPEAT('yy', 16), NOW(), '555-0066', TO_DATE('1988-12-11','YYYY-MM-DD'), 'team_owner', 'Netherlands'),
  ('Omar', 'Owner', 'owner7@example.com', REPEAT('dd', 32), REPEAT('zz', 16), NOW(), '555-0077', TO_DATE('1993-04-03','YYYY-MM-DD'), 'team_owner', 'Morocco'),
  ('Priya', 'Owner', 'owner8@example.com', REPEAT('ee', 32), REPEAT('qq', 16), NOW(), '555-0088', TO_DATE('1986-08-29','YYYY-MM-DD'), 'team_owner', 'India'),
  -- Coaches
  ('John', 'Coach', 'coach1@example.com', REPEAT('e', 64), REPEAT('w', 32), NOW(), '555-0101', TO_DATE('1980-01-15','YYYY-MM-DD'), 'coach', 'USA'),
  ('Maria', 'Coach', 'coach2@example.com', REPEAT('f', 64), REPEAT('x', 32), NOW(), '555-0102', TO_DATE('1985-04-20','YYYY-MM-DD'), 'coach', 'Spain'),
  ('Carlos', 'Coach', 'coach3@example.com', REPEAT('g', 64), REPEAT('y', 32), NOW(), '555-0103', TO_DATE('1982-06-10','YYYY-MM-DD'), 'coach', 'Italy'),
  ('Sofia', 'Coach', 'coach4@example.com', REPEAT('h', 64), REPEAT('z', 32), NOW(), '555-0104', TO_DATE('1987-09-05','YYYY-MM-DD'), 'coach', 'Turkey'),
  -- Players
  ('Liam', 'Player', 'player1@example.com', REPEAT('i', 64), REPEAT('a', 32), NOW(), '555-0201', TO_DATE('2002-02-14','YYYY-MM-DD'), 'player', 'USA'),
  ('Emma', 'Player', 'player2@example.com', REPEAT('j', 64), REPEAT('b', 32), NOW(), '555-0202', TO_DATE('2003-03-22','YYYY-MM-DD'), 'player', 'Spain'),
  ('Lucas', 'Player', 'player3@example.com', REPEAT('k', 64), REPEAT('c', 32), NOW(), '555-0203', TO_DATE('2001-05-11','YYYY-MM-DD'), 'player', 'Italy'),
  ('Sophia', 'Player', 'player4@example.com', REPEAT('l', 64), REPEAT('d', 32), NOW(), '555-0204', TO_DATE('2002-07-19','YYYY-MM-DD'), 'player', 'Turkey'),
  ('James', 'Player', 'player5@example.com', REPEAT('m', 64), REPEAT('e', 32), NOW(), '555-0205', TO_DATE('2003-08-25','YYYY-MM-DD'), 'player', 'USA'),
  ('Olivia', 'Player', 'player6@example.com', REPEAT('n', 64), REPEAT('f', 32), NOW(), '555-0206', TO_DATE('2002-01-03','YYYY-MM-DD'), 'player', 'Spain'),
  ('Michael', 'Player', 'player7@example.com', REPEAT('o', 64), REPEAT('g', 32), NOW(), '555-0207', TO_DATE('2001-10-30','YYYY-MM-DD'), 'player', 'Italy'),
  ('Isabella', 'Player', 'player8@example.com', REPEAT('p', 64), REPEAT('h', 32), NOW(), '555-0208', TO_DATE('2003-12-12','YYYY-MM-DD'), 'player', 'Turkey'),
  -- real test users (can log in with password '123')
  ('Test', 'Player', 'p@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963', '555-1001', TO_DATE('2000-01-01','YYYY-MM-DD'), 'player', 'Local'),
  ('Tournament', 'Admin', 'ta@gmail.com', 'pbkdf2:sha256:260000$95IYv4bepWZLuX57$13e40434069c1e720f75f2b24a069f2adc2d345f0ba40bc2ea1e5aa3591db283', 'dd7ba3ba3009ae20ca6c8c4be0d22d3e','2025-11-28 15:05:59.408963','555-1002', TO_DATE('1990-01-01','YYYY-MM-DD'), 'tournament_admin', 'Local');

INSERT INTO Admin (UsersID)
SELECT UsersID FROM Users WHERE Email IN ('admin@example.com', 'ta@gmail.com');

INSERT INTO TeamOwner (UsersID, NetWorth)
SELECT u.UsersID, data.net_worth
FROM (
  VALUES
    ('owner1@example.com', 750000.000),
    ('owner2@example.com', 680000.000),
    ('owner3@example.com', 720000.000),
    ('owner4@example.com', 650000.000),
    ('owner5@example.com', 700000.000),
    ('owner6@example.com', 670000.000),
    ('owner7@example.com', 640000.000),
    ('owner8@example.com', 710000.000)
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
    ('owner1@example.com', 'Lions FC', '2015-03-12', 'Sunrise Stadium'),
    ('owner2@example.com', 'Falcons United', '2012-07-04', 'Riverfront Arena'),
    ('owner3@example.com', 'Harbor City Waves', '2018-09-18', 'Bayfront Dome'),
    ('owner4@example.com', 'Alpine Strikers', '2014-05-21', 'Summit Park'),
    ('owner5@example.com', 'Riviera Royals', '2016-11-02', 'Coastal Arena'),
    ('owner6@example.com', 'Canal City Crew', '2013-08-14', 'Harborfront Field'),
    ('owner7@example.com', 'Atlas Eagles', '2011-02-02', 'Mountain Crest'),
    ('owner8@example.com', 'Silk Route FC', '2017-06-09', 'Bazaar Stadium')
) AS data(email, team_name, established, venue)
JOIN Users u ON u.Email = data.email;

INSERT INTO Employee (UsersID, TeamID)
SELECT u.UsersID, t.TeamID
FROM Users u
JOIN Team t ON t.OwnerID = (SELECT UsersID FROM Users WHERE Email = CASE 
  WHEN u.Email = 'coach1@example.com' THEN 'owner1@example.com'
  WHEN u.Email = 'coach2@example.com' THEN 'owner2@example.com'
  WHEN u.Email = 'coach3@example.com' THEN 'owner3@example.com'
  WHEN u.Email = 'coach4@example.com' THEN 'owner1@example.com'
END)
WHERE u.Email IN ('coach1@example.com', 'coach2@example.com', 'coach3@example.com', 'coach4@example.com');

INSERT INTO Coach (UsersID, Certification)
SELECT u.UsersID, 'UEFA A License'
FROM Users u
WHERE u.Email IN ('coach1@example.com', 'coach2@example.com', 'coach3@example.com', 'coach4@example.com');


INSERT INTO Employee (UsersID, TeamID)
SELECT u.UsersID, t.TeamID
FROM Users u
JOIN Team t ON t.OwnerID = (SELECT UsersID FROM Users WHERE Email = CASE 
  WHEN u.Email IN ('player1@example.com', 'player2@example.com') THEN 'owner1@example.com'
  WHEN u.Email IN ('player3@example.com', 'player4@example.com') THEN 'owner2@example.com'
  WHEN u.Email IN ('player5@example.com', 'player6@example.com') THEN 'owner3@example.com'
  ELSE 'owner1@example.com'
END)
WHERE u.Email IN ('player1@example.com', 'player2@example.com', 'player3@example.com', 'player4@example.com',
                   'player5@example.com', 'player6@example.com', 'player7@example.com', 'player8@example.com');

INSERT INTO Player (UsersID, Height, Weight, Overall, Position, IsEligible)
SELECT u.UsersID, 
       180 + (ROW_NUMBER() OVER () % 20),
       75 + (ROW_NUMBER() OVER () % 10),
       '85',
       CASE (ROW_NUMBER() OVER () % 5)
         WHEN 0 THEN 'Forward'
         WHEN 1 THEN 'Midfielder'
         WHEN 2 THEN 'Defender'
         WHEN 3 THEN 'Goalkeeper'
         ELSE 'Forward'
       END,
       'Yes'
FROM Users u
WHERE u.Email IN ('player1@example.com', 'player2@example.com', 'player3@example.com', 'player4@example.com',
                   'player5@example.com', 'player6@example.com', 'player7@example.com', 'player8@example.com');


-- Migrate password storage away from CHAR padding
ALTER TABLE Users ALTER COLUMN HashedPassword TYPE TEXT;
ALTER TABLE Users ALTER COLUMN Salt TYPE TEXT;
UPDATE Users SET HashedPassword = RTRIM(HashedPassword);
UPDATE Users SET Salt = RTRIM(Salt);
