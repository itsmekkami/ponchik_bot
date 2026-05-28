import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.upload import VkUpload
import json
import database
import scheduler 
import threading
import os
import random
import matplotlib.pyplot as plt
import time

TOKEN = "***"
GROUP_ID = ***

database.init_db()
scheduler.start_scheduler()

vk_session = vk_api.VkApi(token=TOKEN)
longpoll = VkBotLongPoll(vk_session, GROUP_ID)
vk = vk_session.get_api()
upload = VkUpload(vk_session)

MEMES_DIR = "memes"
os.makedirs(MEMES_DIR, exist_ok=True)
CHARTS_DIR = "charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

print("Пончик запущен")

MAIN_MENU_KEYBOARD = json.dumps({
    "one_time": False,
    "buttons": [
        [{"action": {"type": "text", "payload": json.dumps({"cmd": "menu", "action": "my_habits"}), "label": "📋 Мои привычки"}, "color": "primary"},
         {"action": {"type": "text", "payload": json.dumps({"cmd": "menu", "action": "add_habit"}), "label": "➕ Добавить"}, "color": "positive"}],
        [{"action": {"type": "text", "payload": json.dumps({"cmd": "menu", "action": "del_habit"}), "label": "️🗑️ Удалить"}, "color": "negative"},
         {"action": {"type": "text", "payload": json.dumps({"cmd": "menu", "action": "meme"}), "label": "🐶🍩 Мем"}, "color": "secondary"}],
        [{"action": {"type": "text", "payload": json.dumps({"cmd": "menu", "action": "progress"}), "label": "📊 Прогресс"}, "color": "secondary"},
         {"action": {"type": "text", "payload": json.dumps({"cmd": "menu", "action": "help"}), "label": "❓ Помощь"}, "color": "secondary"}]
    ]
})

user_states = {}

def send_message(peer_id, text, keyboard=None):
    try:
        vk.messages.send(peer_id=peer_id, message=text, random_id=get_random_id(), keyboard=keyboard)
        print("Сообщение отправлено")
    except Exception as e:
        print(f"ОШИБКА: {e}")

def get_motivation(percent):
    if percent == 0:
        return random.choice(["🎯 Первый шаг — самый важный!", "🌱 Всё начинается с малого!", "💪 Ты можешь начать прямо сейчас!"])
    elif percent < 30:
        return random.choice([" Хороший старт! Не останавливайся!", "🚀 Уже начало! Продолжай в том же духе!", "🐶 Гав-гав! Ты на верном пути!"])
    elif percent < 60:
        return random.choice([" Больше половины! Это круто!", "💪 Серьёзный прогресс!", "🌟 Осталось чуть-чуть, ты справишься!"])
    elif percent < 80:
        return random.choice(["🎯 Финиш уже близко!", "🏃 Почти у цели! Рывок!", "💫 Ты почти сделал(-а) всё!"])
    elif percent < 100:
        return random.choice(["🎯 Шикарный результат!", "⭐ Это успех!", "🍩 Ты молодец! Заслужил(-а) пончик!"])
    else:
        return random.choice(["🎉 Всё выполнено! Ты легенда!", "🏆 100%! Пончик гордится тобой!", "🌟 Идеальный день! Ты молодец!"])

def send_random_meme(peer_id):
    try:
        files = [f for f in os.listdir(MEMES_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
        if not files:
            return
        
        chosen_file = os.path.join(MEMES_DIR, random.choice(files))
        filename = os.path.basename(chosen_file)
        meme_text = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').capitalize()
        
        photo = upload.photo_messages(photos=[chosen_file])[0]
        attachment = f"photo{photo['owner_id']}_{photo['id']}"
        
        vk.messages.send(
            peer_id=peer_id,
            attachment=attachment,
            message=f"🐶🍩 Мем от Пончика:\n\n{meme_text}",
            random_id=get_random_id()
        )
        print("Мем отправлен")
        
    except Exception as e:
        print(f"Ошибка отправки мема: {e}")
        send_message(peer_id, "🐶🍩 Ой, мем убежал! Попробуй позже", keyboard=MAIN_MENU_KEYBOARD)

def generate_progress_chart(user_id, filename="progress_chart.png", pct=0):
    habits = database.get_progress_detailed(user_id)
    if not habits: return None
    done = sum(1 for h in habits if h[1] == 1)
    pending = len(habits) - done
    if len(habits) == 0: return None
    
    plt.figure(figsize=(6, 6), facecolor="#ffffff")
    colors = ["#3ECF43", "#E31E1E"]
    labels = [f'Выполнено: {done}', f'Осталось: {pending}']
    sizes = [done, pending] if done > 0 else [pending]
    
    if done > 0: 
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 10})
    else: 
        plt.pie(sizes, labels=['Осталось: ' + str(pending)], colors=['#E31E1E'], autopct='%1.1f%%', textprops={'fontsize': 10})
    
    plt.title('Прогресс на сегодня', fontsize=14, fontweight='bold', pad=20)
    plt.axis('equal')
    filepath = os.path.join(CHARTS_DIR, filename)
    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor="#ffffff")
    plt.close()
    return filepath

def send_full_progress(peer_id):
    try:
        stats = database.get_progress(peer_id)
        if stats["total"] == 0:
            send_message(peer_id, "📊 Пока нет привычек. Добавь первую через ➕ Добавить!", keyboard=MAIN_MENU_KEYBOARD)
            return

        pct = int((stats["completed"] / stats["total"]) * 100)
        motivation = get_motivation(pct)

        filepath = generate_progress_chart(user_id=peer_id, pct=pct)
        
        text_msg = f"📊 Твой прогресс на сегодня:\n\n"
        text_msg += f" Выполнено: {stats['completed']} из {stats['total']} ({pct}%)\n\n" 
        text_msg += f"💬 {motivation}\n\n"
        
        if stats["active_streaks"]:
            text_msg += "🔥 Активные серии:\n"
            for name, streak in stats["active_streaks"]:
                text_msg += f"  • {name}: {streak} дн.\n"
        else:
            text_msg += "🔥 Серии пока не начаты. Начни сегодня!\n"
            
        if stats["best_streak"] > 0:
            text_msg += f"\n Лучшая серия: {stats['best_streak_name']} ({stats['best_streak']} дн.)"
        else:
            text_msg += f"\n🏆 Лучшая серия: пока нет"

        if filepath and os.path.exists(filepath):
            photo = upload.photo_messages(photos=[filepath])[0]
            attachment = f"photo{photo['owner_id']}_{photo['id']}"
            vk.messages.send(peer_id=peer_id, attachment=attachment, message=text_msg, random_id=get_random_id())
            if os.path.exists(filepath): os.remove(filepath)
            print("Полный прогресс отправлен")
        else:
            send_message(peer_id, text_msg, keyboard=MAIN_MENU_KEYBOARD)
            print("Прогресс отправлен текст")
            
    except Exception as e:
        print(f"Ошибка прогресса: {e}")
        send_message(peer_id, "📊 Ошибка при формировании отчёта. Попробуй позже", keyboard=MAIN_MENU_KEYBOARD)

def show_main_menu(peer_id):
    send_message(peer_id, "🐶🍩 Пончик - трекер привычек\n\nВыбери действие:", keyboard=MAIN_MENU_KEYBOARD)

def run_bot():
    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    message_data = event.obj.get('message', event.obj)
                    text = message_data.get('text', '').strip()
                    payload = message_data.get('payload')
                    peer_id = message_data.get('peer_id')
                    user_id = message_data.get('from_id')

                    if not peer_id: continue

                    if payload:
                        try:
                            p_data = json.loads(payload) if isinstance(payload, str) else payload
                            if p_data.get('cmd') == 'confirm_yes':
                                if user_states.get(user_id) == 'confirm_delete_all':
                                    count = database.delete_all_habits(user_id)
                                    del user_states[user_id]
                                    send_message(peer_id, f"🗑️ Удалено привычек: {count}\nТеперь всё чисто!", keyboard=MAIN_MENU_KEYBOARD)
                                continue
                            elif p_data.get('cmd') == 'confirm_no':
                                if user_id in user_states: del user_states[user_id]
                                send_message(peer_id, "Отмена. Привычки остались", keyboard=MAIN_MENU_KEYBOARD)
                                continue

                            if p_data.get('cmd') == 'menu':
                                action = p_data.get('action')
                                if action in ['my_habits', 'del_habit', 'meme', 'help', 'back', 'delete_all_confirm', 'progress']:
                                    if user_id in user_states: del user_states[user_id]

                                if action == 'my_habits':
                                    habits = database.get_habits(user_id)
                                    if habits:
                                        msg = "📋 Твои привычки:\n\n"
                                        kb = {"one_time": False, "buttons": []}
                                        for h in habits:
                                            n, t, d, s = h
                                            msg += f"{'✅' if d else '⭕'} {n} — {t} | серия: {s}\n"
                                            if not d: kb["buttons"].append([{"action": {"type": "text", "payload": json.dumps({"cmd": "done", "habit": n}), "label": f"✓ {n}"}, "color": "positive"}])
                                        kb["buttons"].append([{"action": {"type": "text", "payload": json.dumps({"cmd": "menu", "action": "back"}), "label": "🔙 Назад"}, "color": "secondary"}])
                                        send_message(peer_id, msg, keyboard=json.dumps(kb))
                                    else: send_message(peer_id, "📋 Нет привычек. Нажми ➕ Добавить", keyboard=MAIN_MENU_KEYBOARD)

                                elif action == 'add_habit':
                                    user_states[user_id] = 'adding_habit'
                                    send_message(peer_id, "➕ Напиши: [название] [время]\n(Пример: Вода 09:00)\n\n", 
                                               keyboard=json.dumps({"one_time": False, "buttons": [[{"action": {"type": "text", "payload": json.dumps({"cmd": "cancel"}), "label": "❌ Отмена"}, "color": "negative"}]]}))

                                elif action == 'del_habit':
                                    habits = database.get_habits(user_id)
                                    if habits:
                                        msg = "🗑️ Удаление привычек:\n"
                                        kb = {"one_time": False, "buttons": []}
                                        for h in habits:
                                            n, t, d, s = h
                                            msg += f"⏰ {t} — {n}\n"
                                            kb["buttons"].append([{"action": {"type": "text", "payload": json.dumps({"cmd": "delete", "habit": n}), "label": f"❌ {n} ({t})"}, "color": "negative"}])
                                        kb["buttons"].append([{"action": {"type": "text", "payload": json.dumps({"cmd": "menu", "action": "delete_all_confirm"}), "label": " Удалить ВСЕ привычки"}, "color": "negative"}])
                                        kb["buttons"].append([{"action": {"type": "text", "payload": json.dumps({"cmd": "menu", "action": "back"}), "label": " Назад"}, "color": "secondary"}])
                                        send_message(peer_id, msg, keyboard=json.dumps(kb))
                                    else: send_message(peer_id, "📋 Нечего удалять", keyboard=MAIN_MENU_KEYBOARD)

                                elif action == 'delete_all_confirm':
                                    if not database.get_habits(user_id):
                                        send_message(peer_id, " У тебя и так нет привычек!", keyboard=MAIN_MENU_KEYBOARD)
                                    else:
                                        user_states[user_id] = 'confirm_delete_all'
                                        send_message(peer_id, "⚠️ Удалить ВСЕ привычки?\nЭто нельзя отменить\n\nНапиши 'да' или нажми кнопку",
                                                   keyboard=json.dumps({"one_time": False, "buttons": [
                                                       [{"action": {"type": "text", "payload": json.dumps({"cmd": "confirm_yes"}), "label": "✅ Да, удалить"}, "color": "negative"}],
                                                       [{"action": {"type": "text", "payload": json.dumps({"cmd": "confirm_no"}), "label": " Нет, отмена"}, "color": "secondary"}]
                                                   ]}))

                                elif action == 'meme':
                                    send_random_meme(peer_id)
                                    continue

                                elif action == 'progress':
                                    send_full_progress(user_id)
                                    continue

                                elif action == 'help':
                                    send_message(peer_id, 
                                        "🐶 Я Пончик - помогаю следить за твоими привычками!\n\n"
                                        "Как начать работу:\n"
                                        "1. Нажми ➕ Добавить\n"
                                        "2. Напиши: Вода 09:00\n"
                                        "3. Нажми 📋 Мои привычки\n"
                                        "4. Кликай на кнопки для отметки выполнения и жди следующих уведоилений\n"
                                        "5. Нажми 📊 Прогресс, чтобы увидеть свои достижения за день\n"
                                        "6. Кликай 🐶🍩 Мем и улыбайся\n\n"
                                        "Команды:\n"
                                        "/add [название] [время] - добавить привычку\n"
                                        "/my - открыть список привычек\n"
                                        "/done [название] - выполнить привычку\n"
                                        "/del [название] - удалить привычку\n"
                                        "/meme - получить мем\n"
                                        "/progress - посмотреть прогресс",
                                        keyboard=MAIN_MENU_KEYBOARD
                                    )

                                elif action == 'back':
                                    show_main_menu(peer_id)
                                continue

                            elif p_data.get('cmd') == 'done':
                                success = database.mark_done(user_id, p_data.get('habit'))
                                send_message(peer_id, f"✅ Отлично! +1 к серии! Так держать!" if success else "🐶 Уже выполнял!", keyboard=MAIN_MENU_KEYBOARD)
                                continue
                            elif p_data.get('cmd') == 'delete':
                                database.delete_habit(user_id, p_data.get('habit'))
                                send_message(peer_id, "️🗑️ Привычка удалена", keyboard=MAIN_MENU_KEYBOARD)
                                continue
                            elif p_data.get('cmd') == 'cancel':
                                if user_id in user_states: del user_states[user_id]
                                send_message(peer_id, "❌ Отменено", keyboard=MAIN_MENU_KEYBOARD)
                                continue
                        except Exception as e:
                            print(f"Ошибка кнопки: {e}")

                    if user_id in user_states and user_states[user_id] == 'adding_habit':
                        if text.lower() in ['назад', 'отмена', 'cancel']:
                            del user_states[user_id]
                            send_message(peer_id, "❌ Отменено", keyboard=MAIN_MENU_KEYBOARD)
                            continue
                        parts = text.split()
                        if len(parts) >= 2:
                            t_str = parts[-1]
                            name = ' '.join(parts[:-1])
                            if len(t_str) == 5 and t_str[2] == ':':
                                try:
                                    h, m = t_str.split(':')
                                    if len(h)==2 and len(m)==2 and 0<=int(h)<=23 and 0<=int(m)<=59:
                                        if database.add_habit(user_id, name, t_str):
                                            del user_states[user_id]
                                            send_message(peer_id, f"✅ Добавлено: {name} на {t_str}\n\nНе забудь отметить!", keyboard=MAIN_MENU_KEYBOARD)
                                        else:
                                            send_message(peer_id, f"⚠️ '{name}' уже есть!", keyboard=MAIN_MENU_KEYBOARD)
                                        continue
                                except: pass
                        send_message(peer_id, "Ошибка формата\nПиши: Вода 09:00\nИли 'назад'", keyboard=MAIN_MENU_KEYBOARD)
                        continue

                    if user_id in user_states and user_states[user_id] == 'confirm_delete_all':
                        if text.lower() in ['да', 'yes']:
                            count = database.delete_all_habits(user_id)
                            del user_states[user_id]
                            send_message(peer_id, f"🗑️ Удалено: {count}. Всё чисто!", keyboard=MAIN_MENU_KEYBOARD)
                        elif text.lower() in ['нет', 'no', 'отмена']:
                            del user_states[user_id]
                            send_message(peer_id, "👍 Отмена", keyboard=MAIN_MENU_KEYBOARD)
                        else:
                            send_message(peer_id, "❓ Напиши 'да' или 'нет'", keyboard=MAIN_MENU_KEYBOARD)
                        continue

                    if text.lower() == "/start": show_main_menu(peer_id)
                    elif text.lower() == "/my": 
                        habits = database.get_habits(user_id)
                        if habits:
                            msg = " Твои привычки:\n\n"
                            kb = {"one_time": False, "buttons": []}
                            for h in habits:
                                n, t, d, s = h
                                msg += f"{'✅' if d else '⭕'} {n} — {t} | серия: {s}\n"
                                if not d: kb["buttons"].append([{"action": {"type": "text", "payload": json.dumps({"cmd": "done", "habit": n}), "label": f"✓ {n}"}, "color": "positive"}])
                            kb["buttons"].append([{"action": {"type": "text", "payload": json.dumps({"cmd": "menu", "action": "back"}), "label": "🔙 Назад"}, "color": "secondary"}])
                            send_message(peer_id, msg, keyboard=json.dumps(kb))
                        else: send_message(peer_id, "📋 Нет привычек", keyboard=MAIN_MENU_KEYBOARD)
                    elif text.lower().startswith("/add"):
                        p = text.split()
                        if len(p)>=3:
                            if database.add_habit(user_id, p[1], p[2]): send_message(peer_id, f"✅ Добавлено: {p[1]} на {p[2]}", keyboard=MAIN_MENU_KEYBOARD)
                            else: send_message(peer_id, "⚠️ Уже есть!", keyboard=MAIN_MENU_KEYBOARD)
                        else: send_message(peer_id, "❌ /add Вода 09:00", keyboard=MAIN_MENU_KEYBOARD)
                    elif text.lower().startswith("/done"):
                        p = text.split()
                        if len(p)>=2: send_message(peer_id, "✅ Готово!" if database.mark_done(user_id, p[1]) else "🐶 Уже было!", keyboard=MAIN_MENU_KEYBOARD)
                    elif text.lower().startswith("/del"):
                        p = text.split()
                        if len(p)>=2: database.delete_habit(user_id, p[1]); send_message(peer_id, "🗑️ Удалено", keyboard=MAIN_MENU_KEYBOARD)
                    elif text.lower() == "/meme": send_random_meme(peer_id)
                    elif text.lower() == "/progress": 
                        send_full_progress(user_id)
                    elif text.lower() == "/help": 
                        send_message(peer_id, 
                            "🐶 Я Пончик - помогаю следить за твоими привычками!\n\n"
                            "Как начать работу:\n"
                            "1. Нажми ➕ Добавить\n"
                            "2. Напиши: Вода 09:00\n"
                            "3. Нажми 📋 Мои привычки\n"
                            "4. Кликай на кнопки для отметки выполнения и жди следующих уведоилений\n"
                            "5. Нажми 📊 Прогресс, чтобы увидеть свои достижения за день\n"
                            "6. Кликай 🐶🍩 Мем и улыбайся\n\n"
                            "Команды:\n"
                            "/add [название] [время] - добавить привычку\n"
                            "/my - открыть список привычек\n"
                            "/done [название] - выполнить привычку\n"
                            "/del [название] - удалить привычку\n"
                            "/meme - получить мем\n"
                            "/progress - посмотреть прогресс",
                            keyboard=MAIN_MENU_KEYBOARD
                        )
                    else: send_message(peer_id, "🐶 Нажми кнопку или напиши /start", keyboard=MAIN_MENU_KEYBOARD)
                    
        except Exception as e:
            print(f"Ошибка соединения: {e}")
            time.sleep(5)
            continue

run_bot()
