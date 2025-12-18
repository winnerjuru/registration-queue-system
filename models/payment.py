import sqlite3

DATABASE = "database.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_payment(student_id, amount, proof):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO payments (student_id, amount, proof)
        VALUES (?, ?, ?)
    """, (student_id, amount, proof))

    connection.commit()
    connection.close()


def get_all_payments():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT payments.id, users.name, payments.amount,
               payments.proof, payments.status
        FROM payments
        JOIN users ON payments.student_id = users.id
    """)

    payments = cursor.fetchall()
    connection.close()
    return payments
