import pandas as pd
import requests
import os
import json
from datetime import datetime, timezone, timedelta

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
STATE_FILE = "chinese_state.json"

def get_vietnam_time():
    return datetime.now(timezone(timedelta(hours=7)))

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except: pass
    # State giờ cần lưu thêm chỉ số của Chủ đề (topic_idx)
    return {"topic_idx": 0, "word_idx": 0, "last_date": ""}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def run_bot():
    df = pd.read_csv("clean_chinese.csv")
    
    # Lấy danh sách các chủ đề (không bị trùng) theo đúng thứ tự file
    topics = df['Topic'].unique().tolist()
    
    state = load_state()
    today_str = get_vietnam_time().strftime("%Y-%m-%d")
    
    topic_idx = state["topic_idx"]
    word_idx = state["word_idx"]
    
    # Xác định số lượng từ trong chủ đề hiện tại
    current_topic = topics[topic_idx]
    topic_df = df[df['Topic'] == current_topic]
    total_in_topic = len(topic_df)

    # LOGIC NHẢY NGÀY & NHẢY CHỦ ĐỀ
    if state["last_date"] != "" and state["last_date"] != today_str:
        word_idx += 10
        
        # Nếu vượt quá số từ của chủ đề hiện tại (VD: từ 30 nhảy lên 40, nhưng chủ đề chỉ có 36 từ)
        if word_idx >= total_in_topic:
            topic_idx += 1    # Nhảy sang chủ đề tiếp theo
            word_idx = 0      # Reset lại index từ vựng về 0
            
            # Nếu đã học hết sạch các chủ đề thì quay lại học lại từ đầu
            if topic_idx >= len(topics):
                topic_idx = 0
                
        state["topic_idx"] = topic_idx
        state["word_idx"] = word_idx
        
    state["last_date"] = today_str
    save_state(state) 
    
    # Lấy lại data của chủ đề (đề phòng trường hợp vừa bị nhảy chủ đề ở trên)
    current_topic = topics[state["topic_idx"]]
    topic_df = df[df['Topic'] == current_topic]
    total_in_topic = len(topic_df)
    current_word_idx = state["word_idx"]
    
    # Cắt lấy 10 từ (Nếu chủ đề chỉ còn 6 từ, nó sẽ tự cắt đúng 6 từ cuối)
    words_today = topic_df.iloc[current_word_idx : current_word_idx + 10]
    
    # Build tin nhắn
    msg = f"🇨🇳 <b>CA HỌC TIẾNG TRUNG ({today_str})</b>\n"
    msg += f"📑 <b>Chủ đề:</b> <i>{current_topic}</i>\n"
    msg += f"👉 <i>Từ {current_word_idx + 1} đến {current_word_idx + len(words_today)} / Tổng {total_in_topic} từ</i>\n\n"
    
    for _, row in words_today.iterrows():
        word = str(row['Word']).strip()
        pinyin = str(row['Pinyin']).strip()
        pronun = str(row['Pronunciation']).strip()
        meaning = str(row['Meaning']).strip()
        
        msg += f"🔹 <b>{word}</b> ({pinyin})\n   🗣 <i>Đọc: {pronun}</i>\n   => {meaning}\n\n"
        
    msg += "🔥 <i>Ôn kỹ nhé, 1 tiếng sau TOEIC là có Tiếng Trung!</i>"
    
    # Gửi Telegram
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    requests.post(url, json=payload)

if __name__ == "__main__":
    run_bot()
