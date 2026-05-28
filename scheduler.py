import schedule
import time
import threading
from datetime import datetime
import database
import json
from vk_api import VkApi
from vk_api.utils import get_random_id

TOKEN = "vk1.a.i45ijVNBtDAeu7NhrHS6ClLltgQWbWFVUi0Gvs8U1Eeh2wppBAT1hcXwIx0F16CfUCgGIoJCPIHYi26SqcvNtDmyw6a1Hpqrtf48zU6r_K86LhX0H_39FluXjB9UITcWMkME-kwM7Ghfus5655tgSpmkYZ_rVGYc0JSdLxXU4Q3_IR2QmlhuoqN0iuSLaxQZuPoHSxQOBDLOaEI9BggGMg"

vk_session = VkApi(token=TOKEN)
vk = vk_session.get_api()

RESET_TIME = "04:00"

def send_reminder(user_id, habit_name):
    try:
        payload_data = {"cmd": "done", "habit": habit_name}
        keyboard_dict = {
            "one_time": True,
            "buttons": [
               [{"action": {"type": "text", "payload": json.dumps(payload_data), "label": f"✅ Выполнить: {habit_name}" }, "color": "positive"}]
            ]
        }
        vk.messages.send(
            user_id=user_id,
            message=f"🐶🕙 Напоминание от Пончика!\n\nПора выполнить привычку: {habit_name}\n\nНажми кнопку ниже, чтобы отметить выполнение",
            random_id=get_random_id(),
            keyboard=json.dumps(keyboard_dict)
        )
        print(f"Отправлено напоминание")
    except Exception as e:
        print(f"Ошибка отправки напоминания: {e}")

def check_and_send():
    now = datetime.now().strftime("%H:%M")
    habits = database.get_all_habits_for_time(now)
    if habits:
        print(f"Найдено {len(habits)} напоминаний на {now}")
        for user_id, habit_name in habits:
            send_reminder(user_id, habit_name)
    else:
        pass

def reset_habits_job():
    print(f"Наступило время сброса ({RESET_TIME})")
    database.reset_done_today()

def run_scheduler():
    schedule.every(1).minutes.do(check_and_send)
    schedule.every().day.at(RESET_TIME).do(reset_habits_job)
    
    print(f"Планировщик запущен")
    while True:
        schedule.run_pending()
        time.sleep(30)

def start_scheduler():
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()