import streamlit as st 
from groq import Groq
import requests
import pandas as pd
from datetime import datetime
import os
import plotly.express as px
from gtts import gTTS 
import base64
import time
import io
import random

# --- 1. THÔNG TIN HỆ THỐNG (GIỮ NGUYÊN) ---
TELEGRAM_TOKEN = "7795878053:AAEWji8wNFQxJ08UpAtVuGi13mFBh3nCh1A"
TELEGRAM_CHAT_ID = "1844804075"

# Khởi tạo Session State
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "voice_cache" not in st.session_state: st.session_state.voice_cache = {}
if "messages" not in st.session_state: st.session_state.messages = [{"role": "assistant", "content": "Chào anh Trung! Hệ thống Tin Tin OS đã sẵn sàng."}]
if "bg_music" not in st.session_state: st.session_state.bg_music = "https://youtu.be/R1r9nLYcqBU"
if "music_playing" not in st.session_state: st.session_state.music_playing = True 
if "todo" not in st.session_state: st.session_state.todo = []

st.set_page_config(page_title="NeuroDesk OS - Anh Trung", layout="wide")

# --- 2. GIAO DIỆN & HIỆU ỨNG (MÀU KEM & RANDOM ANIMATIONS) ---
def apply_ui_theme(is_playing):
    play_state = "running" if is_playing else "paused"
    icons = [
        "https://cdn-icons-png.flaticon.com/512/1358/1358934.png", # Mèo
        "https://cdn-icons-png.flaticon.com/512/3069/3069172.png", # Sao
        "https://cdn-icons-png.flaticon.com/512/4710/4710821.png", # Thỏ
        "https://cdn-icons-png.flaticon.com/512/2353/2353678.png"  # Ma
    ]
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        * {{ font-family: 'Inter', sans-serif; }}
        .stApp {{ background-color: #fdf6e3 !important; }}
        .sparkle {{ position: fixed; background: rgba(234, 179, 8, 0.2); border-radius: 50%; z-index: 0; animation: blink var(--d) infinite; }}
        @keyframes blink {{ 0%, 100% {{ opacity: 0; }} 50% {{ opacity: 1; }} }}
        .float-item {{ position: fixed; width: 40px; height: 40px; background-size: contain; background-repeat: no-repeat; z-index: 0; opacity: 0.3; animation: moveRandom var(--t) linear infinite; }}
        @keyframes moveRandom {{ 0% {{ transform: translate(-100px, 0vh) rotate(0deg); }} 100% {{ transform: translate(110vw, 100vh) rotate(360deg); }} }}
        [data-testid="stMetric"], .stChatMessage, .stTabs, .login-box {{ background: rgba(255, 255, 255, 0.8) !important; backdrop-filter: blur(10px); border-radius: 20px !important; border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 4px 15px rgba(0,0,0,0.03); margin-bottom: 15px; }}
        h1, h2, h3, p, span, label, .stMarkdown {{ color: #1e293b !important; }}
        [data-testid="stChatInput"] {{ background: white !important; border-radius: 15px !important; }}
        .disc {{ width: 100px; height: 100px; border-radius: 50%; background: url('https://cdn-icons-png.flaticon.com/512/2612/2612480.png'); background-size: cover; margin: 0 auto; border: 3px solid #8b5cf6; animation: rotateDisk 5s linear infinite; animation-play-state: {play_state}; }}
        @keyframes rotateDisk {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
        .hidden-audio {{ display: none; }}
        </style>
    """, unsafe_allow_html=True)
    for _ in range(8):
        st.markdown(f'<div class="sparkle" style="top:{random.randint(0,100)}%; left:{random.randint(0,100)}%; width:{random.randint(3,8)}px; height:{random.randint(3,8)}px; --d:{random.randint(2,5)}s;"></div>', unsafe_allow_html=True)
    for i in range(2):
        st.markdown(f'<div class="float-item" style="background-image: url(\'{random.choice(icons)}\'); --t:{random.randint(20,40)}s; top:{random.randint(-20,80)}vh; animation-delay: {i*5}s;"></div>', unsafe_allow_html=True)

apply_ui_theme(st.session_state.music_playing)

# --- 3. LOGIC HỆ THỐNG (GIỮ NGUYÊN) ---
@st.cache_data(ttl=60)
def load_kpi_fast():
    if os.path.isfile("nhat_ky_kpi.csv"): return pd.read_csv("nhat_ky_kpi.csv")
    return None

def get_voice_data(text):
    try:
        tts = gTTS(text=text[:500], lang='vi')
        fp = io.BytesIO()
        tts.write_to_fp(fp); fp.seek(0)
        return base64.b64encode(fp.read()).decode()
    except: return None

def send_telegram(text):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=5)
        return True
    except: return False

# --- 4. BẢO MẬT ---
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; margin-top: 10%;'>⚡ TIN TIN Website</h1>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1,1.5,1])
    with col_login:
        pwd = st.text_input("Mật khẩu truy cập:", type="password")
        if st.button("Mở khóa hệ thống"):
            if pwd == PASSWORD_APP: st.session_state.authenticated = True; st.rerun()
    st.stop()

# --- 5. ĐIỀU HƯỚNG TRANG (NAVIGATION) ---
with st.sidebar:
    st.markdown("## 🧭 MENU HỆ THỐNG")
    # Menu chính để chuyển trang
    page = st.selectbox("Chọn không gian làm việc:", 
        ["🏠 Trang Chủ (Giao diện chính)", "💻 Lập trình chuyên sâu", "🏥 Sức khỏe & Đời sống", "📚 Tổng hợp kiến thức", "🖼️ Siêu lưu trữ Ảnh/Video", "🛒 Sàn bán hàng"])
    
    st.divider()
    st.markdown("### 🎵 NHẠC NỀN")
    st.markdown('<div class="disc"></div>', unsafe_allow_html=True)
    if st.button("▶️ Play"): st.session_state.music_playing = True; st.rerun()
    if st.button("⏸️ Pause"): st.session_state.music_playing = False; st.rerun()
    if st.session_state.music_playing:
        v_id = st.session_state.bg_music.split("v=")[1].split("&")[0] if "v=" in st.session_state.bg_music else st.session_state.bg_music.split("/")[-1]
        st.markdown(f'<iframe class="hidden-audio" src="https://www.youtube.com/embed/{v_id}?autoplay=1&loop=1&playlist={v_id}" allow="autoplay"></iframe>', unsafe_allow_html=True)
    
    st.divider()
    if st.button("🗑️ Reset Chat"): st.session_state.messages = []; st.rerun()
    if st.button("🚪 Thoát"): st.session_state.authenticated = False; st.rerun()

# --- 6. CHI TIẾT CÁC TRANG ---

# --- TRANG 1: TRANG CHỦ (GIỮ NGUYÊN TOÀN BỘ TÍNH NĂNG GỐC CỦA ANH) ---
if page == "🏠 Trang Chủ (Giao diện chính)":
    df_kpi = load_kpi_fast()
    curr_kpi = df_kpi.iloc[-1]['KPI (%)'] if df_kpi is not None else 0

    st.markdown("<h1 style='text-align: center;'>Tin Tin DESK ANALYTICS</h1>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tốc độ mạng", f"{curr_kpi}%")
    m2.metric("Điểm AI", "98.2%")
    m3.metric("Dữ liệu", "1,204")
    m4.metric("Thời gian", "99.9%")
    st.divider()

    col_chat, col_tool = st.columns([0.6, 0.4])
    with col_chat:
        st.markdown("### 🤖 Đối thoại AI")
        for i, msg in enumerate(st.session_state.messages):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant" and msg["content"] in st.session_state.voice_cache:
                    if st.button(f"🔊 Nghe", key=f"v_{i}"):
                        b64 = st.session_state.voice_cache[msg["content"]]
                        st.markdown(f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)

        if prompt := st.chat_input("Gửi mệnh lệnh..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                res_p = st.empty(); full_res = ""
                for chunk in client.chat.completions.create(
                    messages=[{"role": "system", "content": "Bạn là trợ lý ảo Tin Tin OS của anh Trung."}] + 
                             [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    model="llama-3.3-70b-versatile", stream=True):
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_p.markdown(full_res + " ●")
                b64_v = get_voice_data(full_res)
                if b64_v: st.session_state.voice_cache[full_res] = b64_v
                st.session_state.messages.append({"role": "assistant", "content": full_res})
                st.rerun()

    with col_tool:
        tab1, tab2, tab3 = st.tabs(["📉 Báo cáo", "📝 Lên lịch", "📺 Xem Youtube"])
        with tab1:
            k_val = st.slider("KPI", 0, 100, int(curr_kpi))
            if st.button("💾 Lưu báo cáo"):
                now = datetime.now().strftime("%d/%m %H:%M")
                pd.DataFrame({"Thời gian": [now], "KPI (%)": [k_val]}).to_csv("nhat_ky_kpi.csv", mode='a', header=not os.path.exists("nhat_ky_kpi.csv"), index=False)
                st.cache_data.clear()
                send_telegram(f"🚀 Neuro OS: KPI cập nhật {k_val}%")
                st.success("Đã báo cáo!")
                st.rerun()
            if df_kpi is not None:
                st.plotly_chart(px.line(df_kpi, x="Thời gian", y="KPI (%)", markers=True), use_container_width=True)
        with tab2:
            task = st.text_input("Nhiệm vụ:")
            if st.button("Thêm"):
                if task: st.session_state.todo.append(task); st.rerun()
            for i, t in enumerate(st.session_state.todo): st.checkbox(t, key=f"tk_{i}")
            if st.button("🔔 Báo lịch"):
                send_telegram("📝 LỊCH:\n- " + "\n- ".join(st.session_state.todo))
        with tab3:
            y_url = st.text_input("Youtube URL:", "https://youtu.be/4ahl6J3zhWA")
            st.video(y_url)

# --- TRANG 2: LẬP TRÌNH (TIỀN ĐỀ XÂY DỰNG TIẾP) ---
elif page == "💻 Lập trình chuyên sâu":
    st.markdown("## 💻 KHÔNG GIAN LẬP TRÌNH")
    st.info("Đây là nơi anh Trung sẽ xây dựng các công cụ Code, Debug và lưu trữ Snippets.")
    code_input = st.text_area("Viết Code tại đây:", height=200, placeholder="print('Hello Anh Trung!')")
    if st.button("Gửi AI phân tích Code"):
        st.write("Đang kết nối với Llama 3.3 để Review Code...")

# --- TRANG 3: SỨC KHỎE ---
elif page == "🏥 Sức khỏe & Đời sống":
    st.markdown("## 🏥 TƯ VẤN SỨC KHỎE")
    st.text_input("Nhập triệu chứng hoặc thắc mắc:")
    st.markdown("- Chế độ dinh dưỡng\n- Lịch tập luyện\n- Theo dõi chỉ số cơ thể")

# --- TRANG 4: KIẾN THỨC ---
elif page == "📚 Tổng hợp kiến thức":
    st.markdown("## 📚 THƯ VIỆN TRI THỨC")
    st.searchbox("Tìm kiếm kiến thức...")
    st.write("Nơi tổng hợp các Wiki cá nhân của anh.")

# --- TRANG 5: LƯU TRỮ ---
elif page == "🖼️ Siêu lưu trữ Ảnh/Video":
    st.markdown("## 🖼️ MEDIA STORAGE")
    uploaded_files = st.file_uploader("Tải ảnh hoặc video lên bộ nhớ siêu lưu trữ:", accept_multiple_files=True)
    if uploaded_files: st.success(f"Đã nhận {len(uploaded_files)} tệp của anh!")

# --- TRANG 6: BÁN HÀNG ---
elif page == "🛒 Sàn bán hàng":
    st.markdown("## 🛒 TIN TIN SHOP")
    st.write("Quản lý sản phẩm, đơn hàng và doanh thu.")
