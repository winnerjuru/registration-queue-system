import sqlite3

DATABASE = "database.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def generate_queue_number(student_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT MAX(queue_number) FROM queue")
    last_number = cursor.fetchone()[0]

    new_number = 1 if last_number is None else last_number + 1

    cursor.execute("""
        INSERT INTO queue (student_id, queue_number)
        VALUES (?, ?)
    """, (student_id, new_number))

    connection.commit()
    connection.close()

    return new_number
