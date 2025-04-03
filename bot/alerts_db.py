import sqlite3

def init_db():
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS alerts
                 (user_id INTEGER, token TEXT, threshold REAL)''')
    conn.commit()
    conn.close()

def add_alert(user_id, token, threshold):
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    c.execute("INSERT INTO alerts VALUES (?, ?, ?)", (user_id, token, threshold))
    conn.commit()
    conn.close()

def get_user_alerts(user_id):
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    c.execute("SELECT * FROM alerts WHERE user_id=?", (user_id,))
    alerts = c.fetchall()
    conn.close()
    return alerts

init_db()