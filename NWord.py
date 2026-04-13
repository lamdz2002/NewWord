import pandas as pd
import requests
import os
import json
from datetime import datetime, timezone, timedelta

# Cấu hình biến môi trường từ Github Secrets
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# File lưu "trí nhớ" của bot
STATE_FILE = "state.json"

def get_vietnam_time():
    # Lấy giờ Việt Nam (UTC+7)
    tz = timezone(timedelta(hours=7))
    return datetime.now(tz)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"current_index": 0, "last_pushed_date": ""}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    # Dùng định dạng HTML để làm nổi bật tin nhắn
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"Lỗi gửi Telegram: {response.text}")

def run_bot():
    # Đọc kho từ vựng
    df = pd.read_csv("vocabulary.csv")
    total_words = len(df)
    
    state = load_state()
    today_str = get_vietnam_time().strftime("%Y-%m-%d")
    
    # CHUẨN LOGIC: Nếu sang ngày mới, nhảy cóc thêm 10 từ
    if state["last_pushed_date"] != "" and state["last_pushed_date"] != today_str:
        state["current_index"] += 10
        # Nếu vượt số lượng từ trong file -> Quay lại từ dòng đầu tiên
        if state["current_index"] >= total_words:
            state["current_index"] = 0
            
    # Cập nhật ngày hôm nay và lưu "trí nhớ"
    state["last_pushed_date"] = today_str
    save_state(state) 
    
    # Cắt lấy đúng 10 từ của ngày hôm nay (nếu cuối file còn <10 từ, nó sẽ tự lấy phần còn lại)
    current_idx = state["current_index"]
    words_today = df.iloc[current_idx : current_idx + 10]
    
    # Build tin nhắn gửi Telegram
    msg = f"📚 <b>BÀI HỌC HÔM NAY ({today_str})</b>\n"
    msg += f"👉 <i>Từ số {current_idx + 1} đến {current_idx + len(words_today)} / Tổng {total_words}</i>\n\n"
    
    for i, row in words_today.iterrows():
        word = str(row['Word']).strip()
        meaning = str(row['Meaning']).strip()
        
        # Bắt Pinyin (nếu là Tiếng Trung) hoặc Note (loại từ n,v,adj)
        pinyin = str(row['Pinyin']).strip() if pd.notna(row.get('Pinyin')) and str(row.get('Pinyin')) not in ['nan', ''] else ""
        note = str(row['Note']).strip() if pd.notna(row.get('Note')) and str(row.get('Note')) not in ['nan', ''] else ""
        
        # Phân biệt cờ Anh/Trung cho ngầu
        type_flag = "🇬🇧" if str(row.get('Type', '')).upper() == 'EN' else "🇨🇳"
        
        msg += f"{type_flag} <b>{word}</b>"
        if pinyin: msg += f" ({pinyin})"
        if note: msg += f" <i>({note})</i>"
        msg += f"\n   => {meaning}\n\n"
        
    msg += "🔥 <i>Hãy nhẩm lại những từ này nhé! Hẹn gặp lại vào ca tiếp theo.</i>"
    
    send_telegram(msg)

if __name__ == "__main__":
    run_bot()