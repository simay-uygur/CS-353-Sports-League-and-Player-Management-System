from flask import Flask, jsonify, render_template, request
import os
import psycopg2

app = Flask(__name__)

# ENV variable from docker-compose
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route("/")
def home():
    return "Flask + PostgreSQL is running!"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if email:
            message = f"Authentication for {email} is not set up yet, but the form is wired!"
            # TODO: Implement authentication logic
        else:
            message = "Please enter a valid email address."
        return render_template("login.html", message=message)

    return render_template("login.html")

@app.route("/register/player", methods=["GET", "POST"])
def register_player():
    if request.method == "POST":
        role = request.form.get("role", "player")
        # TODO: Implement player registration logic
        message = f"Player registration (role: {role}) is not set up yet, but the form is wired!"
        return render_template("register_player.html", message=message)
    return render_template("register_player.html")

@app.route("/register/coach", methods=["GET", "POST"])
def register_coach():
    if request.method == "POST":
        role = request.form.get("role", "coach")
        # TODO: Implement coach registration logic
        message = f"Coach registration (role: {role}) is not set up yet, but the form is wired!"
        return render_template("register_coach.html", message=message)
    return render_template("register_coach.html")

@app.route("/register/referee", methods=["GET", "POST"])
def register_referee():
    if request.method == "POST":
        role = request.form.get("role", "referee")
        # TODO: Implement referee registration logic
        message = f"Referee registration (role: {role}) is not set up yet, but the form is wired!"
        return render_template("register_referee.html", message=message)
    return render_template("register_referee.html")

@app.route("/register/team-owner", methods=["GET", "POST"])
def register_team_owner():
    if request.method == "POST":
        role = request.form.get("role", "team_owner")
        # TODO: Implement team owner registration logic
        message = f"Team owner registration (role: {role}) is not set up yet, but the form is wired!"
        return render_template("register_team_owner.html", message=message)
    return render_template("register_team_owner.html")

@app.route("/register/tournament-admin", methods=["GET", "POST"])
def register_tournament_admin():
    if request.method == "POST":
        role = request.form.get("role", "tournament_admin")
        # TODO: Implement tournament admin registration logic
        message = f"Tournament admin registration (role: {role}) is not set up yet, but the form is wired!"
        return render_template("register_tournament_admin.html", message=message)
    return render_template("register_tournament_admin.html")

@app.route("/register", methods=["GET"])
def register_select():
    return render_template("register_select.html")


@app.route("/users")
def users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM users;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    data = [{"id": r[0], "name": r[1]} for r in rows]
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)