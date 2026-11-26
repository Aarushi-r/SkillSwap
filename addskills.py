import sqlite3


connection = sqlite3.connect("skillswap.db")

cursor = connection.cursor()


skills = [
    ("Python", "Programming"),
    ("Java", "Programming"),
    ("C++", "Programming"),
    ("C", "Programming"),
    ("JavaScript", "Programming"),
    ("SQL", "Database"),
    ("HTML", "Web Development"),
    ("CSS", "Web Development"),
    ("Graphic Design", "Design"),
    ("UI/UX Design", "Design"),
    ("Video Editing", "Creative"),
    ("Photography", "Creative"),
    ("Public Speaking", "Communication"),
    ("English", "Language"),
    ("Mathematics", "Academic"),
    ("Physics", "Academic"),
    ("Excel", "Productivity")
]


for skill in skills:

    cursor.execute("""
        INSERT OR IGNORE INTO skills
        (skill_name, category)
        VALUES (?, ?)
    """, skill)


connection.commit()
connection.close()

print("Skills added successfully!")