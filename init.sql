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
  PRIMARY KEY (TournamentID, RoundNo),
  FOREIGN KEY (T_MatchID) REFERENCES TournamentMatch(MatchID) ON DELETE CASCADE,
  FOREIGN KEY (TournamentID) REFERENCES Tournament(TournamentID) ON DELETE CASCADE
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
  ('Mia', 'Owner', 'owner3@example.com', REPEAT('d', 64), REPEAT('v', 32), NOW(), '555-0033', TO_DATE('1992-07-14','YYYY-MM-DD'), 'team_owner', 'Italy');

INSERT INTO Admin (UsersID)
SELECT UsersID FROM Users WHERE Email = 'admin@example.com';

INSERT INTO TeamOwner (UsersID, NetWorth)
SELECT u.UsersID, data.net_worth
FROM (
  VALUES
    ('owner1@example.com', 750000.000),
    ('owner2@example.com', 680000.000),
    ('owner3@example.com', 720000.000)
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
    ('owner3@example.com', 'Harbor City Waves', '2018-09-18', 'Bayfront Dome')
) AS data(email, team_name, established, venue)
JOIN Users u ON u.Email = data.email;



