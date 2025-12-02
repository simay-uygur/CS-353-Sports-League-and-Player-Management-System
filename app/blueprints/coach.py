
import math
from datetime import datetime, timedelta

import psycopg2

from flask import Blueprint, render_template, request, redirect, url_for, session, abort
from psycopg2.extras import RealDictCursor

from db_helper import * 

from db import get_connection

coach_bp = Blueprint("coach", __name__, url_prefix="/coach")

@coach_bp.before_request
def require_coach_session():
    # Allow both full admins and tournament_admins to access admin routes
    if session.get("user_id") is None or session.get("role") not in ("coach", "superadmin"):
        session["next"] = request.path
        return redirect(url_for("login"))

@coach_bp.route("/transfer_market", methods=["GET"])
def view_transfer_market():
    name = request.args.get("name")
    nationality = request.args.get("nationality")
    position = request.args.get("position")
    min_age = request.args.get("minAge")
    max_age = request.args.get("maxAge")

    if name is not None:
        name = name.strip()
