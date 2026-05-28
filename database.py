import sqlite3

DB_PATH = "ponchik.db"

def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            habit_name TEXT,
            habit_time TEXT,
            done_today INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            last_done DATE
        )
    ''')
    conn.commit()
    conn.close()
    print("База данных готова")

def add_habit(user_id, habit_name, habit_time):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM habits WHERE user_id = ? AND habit_name = ?', (user_id, habit_name))
    if cursor.fetchone():
        conn.close()
        return False
    cursor.execute('INSERT INTO habits (user_id, habit_name, habit_time) VALUES (?, ?, ?)', (user_id, habit_name, habit_time))
    conn.commit()
    conn.close()
    return True

def get_habits(user_id):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute('SELECT habit_name, habit_time, done_today, streak FROM habits WHERE user_id = ? ORDER BY habit_time ASC', (user_id,))
    habits = cursor.fetchall()
    conn.close()
    return habits

def delete_habit(user_id, habit_name):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM habits WHERE user_id = ? AND habit_name = ?', (user_id, habit_name))
    conn.commit()
    conn.close()

def delete_all_habits(user_id):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM habits WHERE user_id = ?', (user_id,))
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

def mark_done(user_id, habit_name):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute('UPDATE habits SET done_today = 1, streak = streak + 1 WHERE user_id = ? AND habit_name = ? AND done_today = 0', (user_id, habit_name))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def get_all_habits_for_time(check_time):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, habit_name FROM habits WHERE habit_time = ?', (check_time,))
    habits = cursor.fetchall()
    conn.close()
    return habits

def reset_done_today():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute('UPDATE habits SET streak = 0, done_today = 0 WHERE done_today = 0')
    cursor.execute('UPDATE habits SET done_today = 0 WHERE done_today = 1')
    conn.commit()
    conn.close()
    print("Серии обновлены")

def get_progress(user_id):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as total, COALESCE(SUM(done_today), 0) as completed FROM habits WHERE user_id = ?', (user_id,))
    total, completed = cursor.fetchone()
    
    cursor.execute('SELECT habit_name, streak FROM habits WHERE user_id = ? ORDER BY streak DESC LIMIT 1', (user_id,))
    best_row = cursor.fetchone()
    best_streak = best_row[1] if best_row else 0
    best_streak_name = best_row[0] if best_row else "—"

    cursor.execute('SELECT habit_name, streak FROM habits WHERE user_id = ? AND streak > 0 ORDER BY streak DESC', (user_id,))
    active_streaks = cursor.fetchall()
    
    conn.close()
    return {
        "total": total,
        "completed": completed,
        "best_streak": best_streak,
        "best_streak_name": best_streak_name,
        "active_streaks": active_streaks
    }

def get_progress_detailed(user_id):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute('SELECT habit_name, done_today, streak FROM habits WHERE user_id = ?', (user_id,))
    habits = cursor.fetchall()
    conn.close()
    return habits