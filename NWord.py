import pandas as pd
import requests
import os
import json
from datetime import datetime, timezone, timedelta

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
STATE_FILE = "state.json"

def get_vietnam_time():
    return datetime.now(timezone(timedelta(hours=7)))

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {"current_index": 0, "last_pushed_date": ""}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def run_bot():
    df = pd.read_csv("vocabulary.csv")
    total_words = len(df)
    state = load_state()
    today_str = get_vietnam_time().strftime("%Y-%m-%d")

    # Nếu sang ngày mới, tịnh tiến index lên 10
    if state["last_pushed_date"] != "" and state["last_pushed_date"] != today_str:
        state["current_index"] += 10
        if state["current_index"] >= total_words:
            state["current_index"] = 0
            
    state["last_pushed_date"] = today_str
    save_state(state) 
    
    current_idx = state["current_index"]
    words_today = df.iloc[current_idx : current_idx + 10]
    
    msg = f"📚 <b>BÀI HỌC HÔM NAY ({today_str})</b>\n"
    msg += f"👉 <i>Từ {current_idx + 1} đến {current_idx + len(words_today)} / {total_words}</i>\n\n"
    
    for i, row in words_today.iterrows():
        word = str(row['Word']).strip()
        meaning = str(row['Meaning']).strip()
        pinyin = str(row['Pinyin']).strip() if pd.notna(row.get('Pinyin')) and str(row.get('Pinyin')) not in ['nan', ''] else ""
        note = str(row['Note']).strip() if pd.notna(row.get('Note')) and str(row.get('Note')) not in ['nan', ''] else ""
        type_flag = "🇬🇧" if str(row.get('Type', '')).upper() == 'EN' else "🇨🇳"
        
        msg += f"{type_flag} <b>{word}</b>"
        if pinyin: msg += f" ({pinyin})"
        if note: msg += f" <i>({note})</i>"
        msg += f"\n   => {meaning}\n\n"
    
    msg += "🔥 <i>Hãy ôn lại nhé! Hẹn gặp lại vào ca tiếp theo.</i>"
    send_telegram(msg)

if __name__ == "__main__":
    run_bot()