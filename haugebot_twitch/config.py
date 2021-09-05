import sqlite3


def get_value(column):
    conn = sqlite3.connect("db.sqlite3")

    c = conn.cursor()
    c.execute(f"SELECT {column} FROM haugebot_web_setting")
    value = c.fetchone()[0]
    conn.close()

    return value


def get_int(column):
    return get_value(column)


def get_float(column):
    return get_value(column)


def get_bool(column):
    return get_value(column) == "1"
