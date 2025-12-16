import psycopg2
from flask import Blueprint, render_template, request, redirect, url_for, session

from db import get_connection

from db_helper import (
    fetch_all_teams,
    fetch_all_tournaments,
    fetch_matches_grouped,
)

from db_helper_match import match_hometeam_info, match_awayteam_info, update_play

match_bp = Blueprint("match", __name__, url_prefix="/")


@match_bp.route("/match_edit/<matchid>", ["GET", "POST"])
def match_edit(matchid):

    if request.method == "GET" and session['role'] == "referee":
        ht_result = match_hometeam_info(matchid)
        at_result = match_awayteam_info(matchid)
        return render_template("match_edit.html", hometeaminfo=ht_result, awayteaminfo=at_result)

    return redirect(url_for("login"))


@match_bp.route("/play_update", ["POST"])
def play_update(playid):

    if request.method == "POST" and session['role'] == "referee":
        update_play(playid, request.form)
