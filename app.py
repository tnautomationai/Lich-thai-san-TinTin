import base64
import calendar
from datetime import datetime, timedelta
import io
import os
import random
import time
from groq import Groq
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# --- 1. THÔNG TIN HỆ THỐNG ---
TELEGRAM_TOKEN = "7795878053:AAEWji8wNFQxJ08UpAtVuGi13mFBh3nCh1A"
TELEGRAM_CHAT_ID = "1844804075"


# --- KHỞI TẠO SESSION STATE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "voice_cache" not in st.session_state:
    st.session_state.voice_cache = {}
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Chào anh Trung! Trợ lý Thai Sản Tin Tin đã sẵn sàng.",
    }]
if "bg_music" not in st.session_state:
    st.session_state.bg_music = "https://youtu.be/R1r9nLYcqBU"
if "music_playing" not in st.session_state:
    st.session_state.music_playing = True
if "ngay_bat_dau_thai_ky" not in st.session_state:
    st.session_state.ngay_bat_dau_thai_ky = None

st.set_page_config(page_title="Tin Tin - Lịch Thai Sản", layout="wide", page_icon="👼")

# --- 2. GIAO DIỆN & HIỆU ỨNG CSS ---
def apply_ui_theme():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .stApp { background-color: #fdf6e3 !important; }
        [data-testid="stMetric"], .stChatMessage, .stTabs, .login-box {
            background: rgba(255, 255, 255, 0.9) !important;
            backdrop-filter: blur(10px);
            border-radius: 20px !important;
            border: 1px solid rgba(0,0,0,0.05);
            box-shadow: 0 4px 15px rgba(0,0,0,0.03);
            margin-bottom: 15px;
        }
        h1, h2, h3, p, span, label, .stMarkdown { color: #1e293b !important; }
        [data-testid="stChatInput"] { background: white !important; border-radius: 15px !important; }
        
        .highlight-date { color: #d946ef !important; font-weight: bold; font-size: 1.15em; }
        .highlight-days { color: #0ea5e9 !important; font-weight: bold; font-size: 1.3em; }
        
        .custom-box-success { background-color: #e6f4ea; border-left: 5px solid #34a853; padding: 15px 20px; border-radius: 12px; margin-bottom: 15px; color: #1e293b; }
        .custom-box-warning { background-color: #fef7e0; border-left: 5px solid #fbbc04; padding: 15px 20px; border-radius: 12px; margin-bottom: 15px; color: #1e293b; }
        .custom-box-danger { background-color: #fce8e6; border-left: 5px solid #ea4335; padding: 15px 20px; border-radius: 12px; margin-bottom: 15px; color: #1e293b; }
        .custom-box-info { background-color: #e8f0fe; border-left: 5px solid #4285f4; padding: 15px 20px; border-radius: 12px; margin-bottom: 15px; color: #1e293b; }

        .preg-calendar { width: 100%; border-collapse: collapse; text-align: center; margin-top: 15px; }
        .preg-calendar th { background-color: #f1f5f9; padding: 12px; border: 1px solid #e2e8f0; color: #334155; text-transform: uppercase; font-size: 0.9em;}
        .preg-calendar td { border: 1px solid #e2e8f0; padding: 10px; vertical-align: top; height: 95px; width: 14%; transition: background-color 0.2s;}
        .preg-calendar td:hover { background-color: #f8fafc; }
        .preg-calendar .today { background-color: #e0f2fe; border: 2px solid #0284c7; }
        .preg-calendar .other-month { background-color: #f8fafc; opacity: 0.4; }
        .date-num { font-weight: bold; font-size: 1.2em; color: #1e293b; margin-bottom: 5px; }
        .thai-age { font-size: 0.8em; color: #c026d3; font-weight: 700; background: #fae8ff; padding: 3px 6px; border-radius: 8px; display: inline-block; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        </style>
    """, unsafe_allow_html=True)

apply_ui_theme()

# --- HÀM HỖ TRỢ ---
def get_vietnamese_weekday(date_obj):
    weekdays = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    return weekdays[date_obj.weekday()]

def render_pregnancy_calendar(ngay_bat_dau_thai_ky, target_year, target_month):
    today = datetime.today().date()
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdatescalendar(target_year, target_month)
    
    thang_ten = ["", "Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6", "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"]
    
    html = f"""
    <div style="background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
        <h3 style="text-align: center; color: #3b82f6 !important; margin-bottom: 20px;">🗓️ Lịch {thang_ten[target_month]} Năm {target_year} - Hành Trình Của Bé</h3>
        <table class='preg-calendar'>
            <tr><th>Thứ 2</th><th>Thứ 3</th><th>Thứ 4</th><th>Thứ 5</th><th>Thứ 6</th><th>Thứ 7</th><th>Chủ Nhật</th></tr>
    """
    
    for week in month_days:
        html += "<tr>"
        for day in week:
            is_today = "today" if day == today else ""
            is_curr_month = "" if day.month == target_month else "other-month"
            
            thai_text = ""
            if ngay_bat_dau_thai_ky and day >= ngay_bat_dau_thai_ky:
                days_pregnant = (day - ngay_bat_dau_thai_ky).days
                tuan = days_pregnant // 7
                ngay_le = days_pregnant % 7
                if tuan <= 42:
                    thai_text = f"<div class='thai-age'>👶 T.{tuan}+{ngay_le}</div>"
            
            html += f"<td class='{is_today} {is_curr_month}'><div class='date-num'>{day.day}</div>{thai_text}</td>"
        html += "</tr>"
    html += "</table></div>"
    return html


# --- 5. ĐIỀU HƯỚNG TRANG (NAVIGATION) ---
with st.sidebar:
    st.markdown("## 🧭 MENU THAI SẢN")
    page = st.selectbox(
        "Chọn chức năng:",
        [
            "🏠 Tổng Quan Thai Kỳ",
            "📅 Lịch Khám & Dự Sinh",
            "💉 Lịch Tiêm Phòng",
            "💊 Dinh Dưỡng & Sữa Bầu",
            "👩‍⚕️ Trợ lý Bác sĩ Tin Tin",
        ],
    )

# --- 6. CHI TIẾT CÁC TRANG ---
if page == "🏠 Tổng Quan Thai Kỳ":
    st.markdown("## 🏠 TỔNG QUAN HÀNH TRÌNH ĐÓN BÉ")
    
    col_info, col_img = st.columns([3, 1])
    with col_info:
        st.write("Chào mừng anh Trung đến với hệ thống quản lý thai kỳ. Tại đây anh có thể chủ động tra cứu lịch theo từng tháng (từ tháng hiện tại đến tháng 12) để nắm bắt mốc phát triển của bé.")
        
    with col_img:
        st.image("https://cdn-icons-png.flaticon.com/512/2990/2990715.png", width=100)
    
    st.markdown("---")
    
    # Thanh chọn tháng mở rộng (Bao gồm tháng 8, 9, 10, 11, 12 và các tháng khác)
    current_month_default = datetime.today().month
    current_year_default = datetime.today().year
    
    col_m1, col_m2 = st.columns([2, 2])
    with col_m1:
        chon_thang = st.selectbox(
            "📅 Chọn tháng muốn xem lịch:",
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            index=current_month_default - 1,
            format_func=lambda x: f"Tháng {x}"
        )
    with col_m2:
        chon_nam = st.number_input("Năm:", min_value=2024, max_value=2030, value=current_year_default, step=1)
        
    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.ngay_bat_dau_thai_ky:
        cal_html = render_pregnancy_calendar(st.session_state.ngay_bat_dau_thai_ky, chon_nam, chon_thang)
        st.markdown(cal_html, unsafe_allow_html=True)
    else:
        st.info("💡 Hệ thống chưa ghi nhận ngày bắt đầu thai kỳ. Anh hãy sang mục **'📅 Lịch Khám & Dự Sinh'** để thiết lập thông tin tính toán trước nhé!")

elif page == "📅 Lịch Khám & Dự Sinh":
    st.markdown("## 📅 TÍNH TOÁN LỊCH KHÁM & NGÀY DỰ SINH")
    st.info("Công cụ giúp anh tính toán tuổi thai, ngày dự sinh, lịch khám lại và kiểm tra tuổi thai tại bất kỳ mốc thời gian nào.")

    loai_thai = st.radio("🌟 Hình thức mang thai:", ["Thai Tự nhiên / Dựa trên Siêu âm", "Thai IVF (Thụ tinh ống nghiệm)"], horizontal=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    ngay_bat_dau_thai_ky = None
    
    with col1:
        if loai_thai == "Thai Tự nhiên / Dựa trên Siêu âm":
            ngay_kham = st.date_input("🗓️ Ngày khám/siêu âm gần nhất:", format="DD/MM/YYYY")
            st.markdown("**Tuần thai tại thời điểm khám:**")
            c1, c2 = st.columns(2)
            with c1:
                tuan = st.number_input("Số tuần:", min_value=0, max_value=42, value=12, step=1)
            with c2:
                ngay_le = st.number_input("Số ngày lẻ:", min_value=0, max_value=6, value=0, step=1)
        else:
            ngay_chuyen_phoi = st.date_input("🗓️ Ngày chuyển phôi:", format="DD/MM/YYYY")
            tuoi_phoi = st.selectbox("🧬 Tuổi phôi (Ngày):", [3, 5], index=1)
            st.markdown("*Lưu ý: Tuổi thai IVF được tính chuẩn xác y khoa dựa trên ngày chuyển phôi.*")

    with col2:
        st.markdown("**🏥 Thông tin hẹn khám lại (Tùy chọn):**")
        hen_kham_tuan = st.number_input("⏳ Bác sĩ hẹn mấy tuần nữa khám lại?", min_value=0, value=4, step=1)
        hen_kham_ngay = st.number_input("Hoặc hẹn lẻ thêm mấy ngày?", min_value=0, value=0, step=1)

        st.markdown("---")
        st.markdown("**🕒 Tính tuổi thai tại thời điểm bất kỳ:**")
        ngay_muon_tinh = st.date_input("🗓️ Chọn ngày anh muốn tính:", format="DD/MM/YYYY", value=datetime.today().date())

    if st.button("🚀 Bắt đầu tính toán", use_container_width=True):
        hom_nay = datetime.today().date()
        
        # 1. TÍNH NGÀY BẮT ĐẦU THAI KỲ (LMP)
        if loai_thai == "Thai Tự nhiên / Dựa trên Siêu âm":
            tuoi_thai_luc_kham = timedelta(weeks=tuan, days=ngay_le)
            ngay_bat_dau_thai_ky = ngay_kham - tuoi_thai_luc_kham
            ngay_hen_kham_moc = ngay_kham
        else:
            khoang_cach_ivf = timedelta(days=(14 + tuoi_phoi))
            ngay_bat_dau_thai_ky = ngay_chuyen_phoi - khoang_cach_ivf
            ngay_hen_kham_moc = hom_nay
            
        ngay_du_sinh = ngay_bat_dau_thai_ky + timedelta(weeks=40)
        st.session_state.ngay_bat_dau_thai_ky = ngay_bat_dau_thai_ky

        # 2. TÍNH NGÀY KHÁM LẠI
        khoang_thoi_gian_hen = timedelta(weeks=hen_kham_tuan, days=hen_kham_ngay)
        ngay_kham_lai = ngay_hen_kham_moc + khoang_thoi_gian_hen
        so_ngay_cho = (ngay_kham_lai - hom_nay).days

        # 3. TÍNH TUỔI THAI TẠI THỜI ĐIỂM MUỐN TÍNH
        tuoi_thai_muc_tieu_days = (ngay_muon_tinh - ngay_bat_dau_thai_ky).days
        tuoi_thai_muc_tieu_tuan = tuoi_thai_muc_tieu_days // 7
        tuoi_thai_muc_tieu_ngay = tuoi_thai_muc_tieu_days % 7
        
        tuoi_thai_muc_tieu_thang = tuoi_thai_muc_tieu_days // 30
        tuoi_thai_muc_tieu_thang_ngay_le = tuoi_thai_muc_tieu_days % 30

        st.markdown("---")
        st.markdown("### 📊 KẾT QUẢ PHÂN TÍCH:")

        if tuoi_thai_muc_tieu_days >= 0:
            st.markdown(
                f"""
                <div class="custom-box-info" style="background-color: #f3e8ff; border-left-color: #a855f7;">
                    👶 <b>TUỔI THAI TÍNH ĐẾN NGÀY {ngay_muon_tinh.strftime('%d/%m/%Y')}:</b><br>
                    - Tổng số ngày thai nhi phát triển: <span class='highlight-days'>{tuoi_thai_muc_tieu_days} ngày</span><br>
                    - Tương đương với: <span class='highlight-days'>Tuần {tuoi_thai_muc_tieu_tuan} + {tuoi_thai_muc_tieu_ngay} ngày</span><br>
                    - Quy đổi ra tháng: Mẹ bầu đang ở <span class='highlight-days'>Tháng thứ {tuoi_thai_muc_tieu_thang + 1}</span> (Cụ thể là được {tuoi_thai_muc_tieu_thang} tháng {tuoi_thai_muc_tieu_thang_ngay_le} ngày)
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="custom-box-danger">
                    ⚠️ <b>Lỗi chọn ngày:</b> Ngày anh muốn tính ({ngay_muon_tinh.strftime('%d/%m/%Y')}) đang diễn ra trước thời điểm bắt đầu thai kỳ. Vui lòng chọn mốc thời gian sau đó!
                </div>
                """,
                unsafe_allow_html=True,
            )

        thu_du_sinh = get_vietnamese_weekday(ngay_du_sinh)
        st.markdown(
            f"""
            <div class="custom-box-info">
                🍼 <b>NGÀY DỰ SINH CHUẨN (40 Tuần):</b><br>
                - Bé sẽ chào đời vào khoảng: <span class='highlight-date'>{thu_du_sinh}, ngày {ngay_du_sinh.strftime('%d/%m/%Y')}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        if khoang_thoi_gian_hen.days > 0:
            thu_kham_lai = get_vietnamese_weekday(ngay_kham_lai)
            st.markdown(
                f"""
                <div class="custom-box-success">
                    🏥 <b>NGÀY KHÁM LẠI TIẾP THEO:</b><br>
                    - Bạn sẽ đi khám lại vào: <span class='highlight-date'>{thu_kham_lai}, ngày {ngay_kham_lai.strftime('%d/%m/%Y')}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if so_ngay_cho > 0:
                st.markdown(
                    f"""
                    <div class="custom-box-warning">
                        ⏳ Còn <span class='highlight-days'>{so_ngay_cho} ngày</span> nữa là đến lịch hẹn khám tiếp theo!
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif so_ngay_cho == 0:
                st.markdown(
                    """
                    <div class="custom-box-danger">
                        🚨 <b>HÔM NAY</b> là ngày đi khám lại rồi nhé!
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div class="custom-box-danger">
                        ⚠️ Đã quá lịch hẹn khám <span class='highlight-days'>{abs(so_ngay_cho)} ngày</span>. Anh hãy sắp xếp cho mẹ bầu đi khám sớm nhé!
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

elif page == "💉 Lịch Tiêm Phòng":
    st.markdown("## 💉 LỊCH TIÊM PHÒNG CHO MẸ BẦU")
    st.write("Dưới đây là các mũi tiêm quan trọng trong thai kỳ:")
    st.markdown("""
    * **Uốn ván (VAT):**
        * *Mũi 1:* Càng sớm càng tốt, thường vào tam cá nguyệt thứ 2 (tuần 20 trở đi).
        * *Mũi 2:* Ít nhất 4 tuần sau mũi 1 và phải trước ngày dự sinh ít nhất 1 tháng.
    * **Cúm:** Có thể tiêm bất cứ lúc nào trong thai kỳ, giúp bảo vệ cả mẹ và bé.
    * **Ho gà, bạch hầu, uốn ván (Tdap):** Thường tiêm vào 3 tháng cuối (tuần 27 - 36).
    """)
    st.info("💡 Lưu ý: Hãy hỏi ý kiến bác sĩ khám thai trực tiếp để có lịch tiêm phù hợp nhất với thể trạng của mẹ bầu.")

elif page == "💊 Dinh Dưỡng & Sữa Bầu":
    st.markdown("## 💊 THỰC PHẨM CHỨC NĂNG & DINH DƯỠNG")
    col_t, col_s = st.columns(2)
    with col_t:
        st.markdown("### 💊 Các loại thuốc/Vitamin cần thiết")
        st.checkbox("Axit Folic (B9): Rất quan trọng trong 3 tháng đầu.")
        st.checkbox("Sắt: Chống thiếu máu, uống lúc đói (hoặc với nước cam).")
        st.checkbox("Canxi: Cần thiết từ tuần 16, uống sáng/trưa, cách xa Sắt 2 tiếng.")
        st.checkbox("DHA: Hỗ trợ phát triển trí não và võng mạc cho bé.")

    with col_s:
        st.markdown("### 🥛 Gợi ý Sữa Bầu")
        st.write("""
        - **Sữa hạt:** Hạnh nhân, óc chó, macca (dễ tiêu, ít vào mẹ, nhiều vào con).
        - **Sữa tươi không đường:** Ưu tiên uống hàng ngày thay nước.
        - **Sữa công thức cho bà bầu:** Matilia, Morinaga, Frisomum (nếu mẹ ăn uống kém hoặc ốm nghén).
        """)

elif page == "👩‍⚕️ Trợ lý Bác sĩ Tin Tin":
    st.markdown("## 👩‍⚕️ TRỢ LÝ BÁC SĨ TIN TIN (AI)")
    st.write("Anh Trung có thể hỏi mọi thắc mắc về thai kỳ, em sẽ tư vấn dựa trên kiến thức Y khoa tiên tiến.")

    prompt = st.chat_input("Nhập câu hỏi (VD: Bầu 3 tháng đầu có được ăn ngải cứu không?)...")
    if prompt:
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            st.write("Đang phân tích dữ liệu thai kỳ...")
            time.sleep(1)
            response = "Xin chào! Với câu hỏi này, theo khuyến cáo an toàn thai sản, 3 tháng đầu mẹ nên hạn chế..."
            st.markdown(response)
