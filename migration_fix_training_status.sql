-- Migration: Allow NULL status in TrainingAttendance table
-- Run this SQL command to fix the NOT NULL constraint issue

ALTER TABLE TrainingAttendance ALTER COLUMN Status DROP NOT NULL;

-- Update trigger function to use NULL instead of 0
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

-- Update process_past_trainings function to use NULL instead of 0
CREATE OR REPLACE FUNCTION process_past_trainings()
RETURNS void AS $$
BEGIN
    -- Mark all players as NULL for trainings that have passed and don't have attendance records
    INSERT INTO TrainingAttendance (SessionID, PlayerID, Status)
    SELECT DISTINCT
        ts.SessionID,
        e_player.UsersID,
        NULL  -- Status NULL = Not set yet
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

