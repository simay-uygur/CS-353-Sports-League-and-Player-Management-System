from flask import Blueprint, session, redirect, url_for, request, jsonify

from db_helper import finalize_tournament_match_from_plays
from db import get_connection
import psycopg2
from psycopg2.extras import RealDictCursor

referee_bp = Blueprint("referee", __name__, url_prefix="/referee")


@referee_bp.before_request
def require_referee():
    if session.get("role") != "referee":
        return redirect(url_for("login"))


@referee_bp.route("/matches/<int:match_id>/plays/save", methods=["POST"])
def save_plays(match_id):
    """
    Save/update plays for a match. 
    - For seasonal matches: Updates plays and returns early (triggers handle score updates automatically).
    - For tournament matches: Updates plays and then automatically finalizes the match 
      (recalculates scores, sets winner, locks match).
    """
    referee_id = session.get("user_id")
    if not referee_id:
        return jsonify({"error": "Not authenticated"}), 401

    # Verify referee is assigned to this match
    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if referee is assigned to this match
                cur.execute(
                    """
                    SELECT 1
                    FROM RefereeMatchAttendance
                    WHERE MatchID = %s AND RefereeID = %s;
                    """,
                    (match_id, referee_id),
                )
                if not cur.fetchone():
                    return jsonify({"error": "You are not assigned to this match"}), 403

                # Check if match is locked
                cur.execute(
                    """
                    SELECT IsLocked FROM Match WHERE MatchID = %s;
                    """,
                    (match_id,),
                )
                match_row = cur.fetchone()
                if not match_row or match_row["islocked"]:
                    return jsonify({"error": "Match is locked or does not exist"}), 400

                # Check if it's a tournament match
                cur.execute(
                    """
                    SELECT 1 FROM TournamentMatch WHERE MatchID = %s;
                    """,
                    (match_id,),
                )
                is_tournament = cur.fetchone() is not None

                # Process play updates from form data
                # Expected format: play_data = {play_id: {field: value, ...}, ...}
                # or new plays as {new_play_<index>: {player_id: X, field: value, ...}}
                play_updates = {}
                for key, value in request.form.items():
                    if key.startswith("play_"):
                        # Format: play_<play_id>_<field>
                        parts = key.split("_")
                        if len(parts) >= 3:
                            play_id = parts[1]
                            field = "_".join(parts[2:])
                            if play_id not in play_updates:
                                play_updates[play_id] = {}
                            play_updates[play_id][field] = value

                # Update existing plays
                for play_id, updates in play_updates.items():
                    if play_id.startswith("new"):
                        continue  # Skip new plays for now (can be added later)
                    
                    try:
                        play_id_int = int(play_id)
                    except ValueError:
                        continue

                    # Build UPDATE query dynamically
                    set_clauses = []
                    params = []
                    for field, val in updates.items():
                        # Map form field names to DB column names
                        field_map = {
                            "start_time": "StartTime",
                            "stop_time": "StopTime",
                            "successful_passes": "SuccessfulPasses",
                            "goals_scored": "GoalsScored",
                            "penalties_scored": "PenaltiesScored",
                            "assists_made": "AssistsMade",
                            "total_passes": "TotalPasses",
                            "yellow_cards": "YellowCards",
                            "red_cards": "RedCards",
                            "saves": "Saves",
                            "substitution_id": "SubstitutionID",
                        }
                        db_field = field_map.get(field)
                        if db_field:
                            set_clauses.append(f"{db_field} = %s")
                            # Convert to int if not empty, else NULL
                            if val and val.strip():
                                try:
                                    params.append(int(val))
                                except ValueError:
                                    params.append(None)
                            else:
                                params.append(None)

                    if set_clauses:
                        params.append(play_id_int)
                        params.append(match_id)  # Ensure play belongs to this match
                        cur.execute(
                            f"""
                            UPDATE Play
                            SET {', '.join(set_clauses)}
                            WHERE PlayID = %s AND MatchID = %s;
                            """,
                            tuple(params),
                        )

        # For seasonal matches, just update plays and let triggers handle it
        if not is_tournament:
            return jsonify({"success": True, "finalized": False})

        # After all plays are saved, if it's a tournament match, finalize it
        finalize_tournament_match_from_plays(match_id)

        return jsonify({"success": True, "finalized": True})
    except psycopg2.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()


