import sqlite3
import datetime


class DB:
    def __init__(self):
        self.connection = sqlite3.connect("questionnaire.db")
        self.cursor = self.connection.cursor()

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            name TEXT,
            nickname TEXT,
            datetime timestamp)"""
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS answers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)"""
        )

    def add_users_db(self, id, name, nickname):
        now = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
        self.cursor.execute(
            """INSERT INTO users(id, name, nickname, datetime)
            VALUES(?, ?, ?, ?)""",
            [id, name, nickname, now],
        )
        self.connection.commit()

    def add_answers_db(self, data_answers, user_id):
        data_to_insert = [(question, answer, user_id) for question, answer in data_answers.items()]

        query = ("INSERT INTO answers "
                 "(question, answer, user_id) VALUES (?, ?, ?)")
        self.cursor.executemany(query, data_to_insert)
        self.connection.commit()

    def fetch_all(self):
        query = """SELECT users.id AS user_id,
                    users.name AS user_name,
                    users.nickname AS user_nickname,
                    users.datetime AS user_datetime,
                    answers.id AS answer_id,
                    answers.question AS answer_question,
                    answers.answer AS answer_value
                FROM users
                LEFT JOIN answers ON users.id = answers.user_id
                ORDER BY answers.id"""

        return self.cursor.execute(query).fetchall()

    def delete_user(self, user_id):
        self.cursor.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,))
        self.connection.commit()

    def __del__(self):
        self.connection.close()
