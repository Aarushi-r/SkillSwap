import os 
from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "local-development-only-key")


# ---------------- DATABASE CONNECTION ----------------

def get_db_connection():
    connection = sqlite3.connect("skillswap.db")
    connection.row_factory = sqlite3.Row
    return connection


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        college = request.form["college"]
        course = request.form["course"]
        year = request.form["year"]

        hashed_password = generate_password_hash(password)

        connection = get_db_connection()

        try:
            connection.execute("""
                INSERT INTO users
                (name, email, password, college, course, year)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                name,
                email,
                hashed_password,
                college,
                course,
                year
            ))

            connection.commit()

        except sqlite3.IntegrityError:
            connection.close()
            return "Email already registered."

        connection.close()

        return redirect("/login")

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()

        user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        connection.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["user_id"]
            session["user_name"] = user["name"]

            return redirect("/dashboard")

        return "Invalid email or password."

    return render_template("login.html")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        name=session["user_name"]
    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ---------------- MY SKILLS ----------------

@app.route("/skills")
def skills():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    connection = get_db_connection()

    teaching_skills = connection.execute("""
        SELECT skills.skill_id, skills.skill_name
        FROM skills
        JOIN user_skills
        ON skills.skill_id = user_skills.skill_id
        WHERE user_skills.user_id = ?
        AND user_skills.skill_type = 'TEACH'
    """, (user_id,)).fetchall()

    learning_skills = connection.execute("""
        SELECT skills.skill_id, skills.skill_name
        FROM skills
        JOIN user_skills
        ON skills.skill_id = user_skills.skill_id
        WHERE user_skills.user_id = ?
        AND user_skills.skill_type = 'LEARN'
    """, (user_id,)).fetchall()

    all_skills = connection.execute("""
        SELECT skill_id, skill_name
        FROM skills
        ORDER BY skill_name
    """).fetchall()

    connection.close()

    return render_template(
        "skills.html",
        teaching_skills=teaching_skills,
        learning_skills=learning_skills,
        all_skills=all_skills
    )


# ---------------- ADD SKILL ----------------

@app.route("/skills/add", methods=["POST"])
def add_skill():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    skill_id = request.form.get("skill_id")
    skill_type = request.form.get("skill_type")

    if not skill_id or not skill_type:
        return "Skill or skill type was not selected."

    connection = get_db_connection()

    existing_skill = connection.execute("""
        SELECT *
        FROM user_skills
        WHERE user_id = ?
        AND skill_id = ?
    """, (user_id, skill_id)).fetchone()

    if existing_skill:
        connection.close()
        return "You have already added this skill."

    connection.execute("""
        INSERT INTO user_skills
        (user_id, skill_id, skill_type)
        VALUES (?, ?, ?)
    """, (
        user_id,
        skill_id,
        skill_type
    ))

    connection.commit()
    connection.close()

    return redirect("/skills")


# ---------------- DELETE SKILL ----------------

@app.route("/skills/delete/<int:skill_id>/<skill_type>", methods=["POST"])
def delete_skill(skill_id, skill_type):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    connection = get_db_connection()

    connection.execute("""
        DELETE FROM user_skills
        WHERE user_id = ?
        AND skill_id = ?
        AND skill_type = ?
    """, (
        user_id,
        skill_id,
        skill_type
    ))

    connection.commit()
    connection.close()

    return redirect("/skills")


# ---------------- STUDENT PROFILE ----------------

@app.route("/profile/<int:user_id>")
def student_profile(user_id):

    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    user = connection.execute("""
        SELECT *
        FROM users
        WHERE user_id = ?
    """, (user_id,)).fetchone()

    if user is None:
        connection.close()
        return "User not found."

    teaching_skills = connection.execute("""
        SELECT skills.skill_name
        FROM skills
        JOIN user_skills
        ON skills.skill_id = user_skills.skill_id
        WHERE user_skills.user_id = ?
        AND user_skills.skill_type = 'TEACH'
    """, (user_id,)).fetchall()

    learning_skills = connection.execute("""
        SELECT skills.skill_name
        FROM skills
        JOIN user_skills
        ON skills.skill_id = user_skills.skill_id
        WHERE user_skills.user_id = ?
        AND user_skills.skill_type = 'LEARN'
    """, (user_id,)).fetchall()

    connection.close()

    return render_template(
        "studentprofile.html",
        user=user,
        teaching_skills=teaching_skills,
        learning_skills=learning_skills
    )


@app.route("/find-students")
def find_students():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    connection = get_db_connection()

    students = connection.execute("""
        SELECT
            users.user_id,
            users.name,
            users.college,
            users.course,
            users.year,
            skills.skill_name
        FROM users
        JOIN user_skills
        ON users.user_id = user_skills.user_id
        JOIN skills
        ON user_skills.skill_id = skills.skill_id
        WHERE user_skills.skill_type = 'TEACH'
        AND users.user_id != ?
        ORDER BY users.name
    """, (user_id,)).fetchall()

    connection.close()

    return render_template(
        "findstudents.html",
        students=students
    )

@app.route("/matches")
def matches():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    connection = get_db_connection()

    matches = connection.execute("""
        SELECT DISTINCT
            other.user_id,
            other.name,
            other.college,

            teach.skill_name AS their_teaching_skill,

            learn.skill_name AS their_learning_skill

        FROM users AS other

        JOIN user_skills AS other_teach
            ON other.user_id = other_teach.user_id

        JOIN skills AS teach
            ON other_teach.skill_id = teach.skill_id

        JOIN user_skills AS other_learn
            ON other.user_id = other_learn.user_id

        JOIN skills AS learn
            ON other_learn.skill_id = learn.skill_id

        JOIN user_skills AS my_learn
            ON my_learn.skill_id = other_teach.skill_id

        JOIN user_skills AS my_teach
            ON my_teach.skill_id = other_learn.skill_id

        WHERE other.user_id != ?

        AND other_teach.skill_type = 'TEACH'
        AND other_learn.skill_type = 'LEARN'

        AND my_learn.user_id = ?
        AND my_learn.skill_type = 'LEARN'

        AND my_teach.user_id = ?
        AND my_teach.skill_type = 'TEACH'

    """, (user_id, user_id, user_id)).fetchall()

    connection.close()

    return render_template(
        "matches.html",
        matches=matches
    )

# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    app.run(debug=True)