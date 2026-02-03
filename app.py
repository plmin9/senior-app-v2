import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
from streamlit_js_eval import get_geolocation

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="내 근태현황", layout="wide")

# --- 2. 다우오피스 앱 스타일 CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #F4F6F8; }
    .header-title { font-size: 26px; font-weight: bold; color: #333; margin-bottom: 10px; }
    .time-card {
        background-color: #FFFFFF; padding: 30px; border-radius: 20px;
        text-align: center; border: 1px solid #EEE;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .time-display { font-size: 42px; font-weight: bold; color: #222; }
    .time-arrow { font-size: 30px; color: #CCC; margin: 0 25px; }
    .stat-container {
        background-color: #FFFFFF; border-radius: 15px; padding: 15px;
        margin-bottom: 15px; display: flex; justify-content: space-around; border: 1px solid #EEE;
    }
    .stat-item { text-align: center; }
    .stat-label { font-size: 14px; color: #888; margin-bottom: 5px; }
    .stat-value { font-size: 16px; font-weight: bold; color: #333; }
    .calendar-row {
        background-color: #FFFFFF; padding: 15px; border-radius: 15px;
        display: flex; justify-content: space-between; margin-bottom: 20px; border: 1px solid #EEE;
    }
    .day-box { text-align: center; padding: 10px; width: 45px; border-radius: 12px; font-size: 14px; }
    .day-today { background-color: #E8F0FE; color: #1A73E8; font-weight: bold; }
    .big-info { font-size: 24px; font-weight: bold; color: #1E3A8A; margin: 20px 0 10px 0; }
    
    /* 성함 선택박스 대형화 */
    div[data-baseweb="select"] > div { font-size: 24px !important; height: 70px !important; border-radius: 15px !important; }
    
    .nav-bar {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background-color: #FFFFFF; padding: 12px 0;
        display: flex; justify-content: space-around;
        border-top: 1px solid #EEE; z-index: 1000;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 구글 시트 연결 및 데이터 정제 ---
@st.cache_resource
def get_gspread_client():
    try:
        s = st.secrets["connections"]["gsheets"]
        creds_info = {
            "type": "service_account", "project_id": s["project_id"],
            "private_key": s["private_key"].replace("\\n", "\n"),
            "client_email": s["service_account_email"],
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        creds = Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except: return None

client = get_gspread_client()
if client:
    s = st.secrets["connections"]["gsheets"]
    sheet_id = s["spreadsheet"].split("/d/")[1].split("/")[0]
    doc = client.open_by_key(sheet_id)
    sheet_attendance = doc.worksheet("근태기록")
    sheet_vacation = doc.worksheet("연차관리")
    df_vacation = pd.DataFrame(sheet_vacation.get_all_records())
else: st.stop()

def get_chosung(text):
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    if not text: return ""
    first_char = str(text)[0]
    if '가' <= first_char <= '힣':
        return CHOSUNG_LIST[(ord(first_char) - 0xAC00) // 588]
    return first_char.upper()

# --- 4. 상단 레이아웃 ---
st.markdown('<div class="header-title">내 근태현황</div>', unsafe_allow_html=True)
now = datetime.now()
st.write(f"📅 {now.strftime('%Y년 %m월 %d일 (%a)')}")

# --- 5. 본인 확인 (초성 버튼 및 이름 선택) ---
st.markdown('<div class="big-info">👤 본인 확인</div>', unsafe_allow_html=True)
cho_list = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
if 'selected_cho' not in st.session_state: st.session_state.selected_cho = "전체"

cols = st.columns(5)
for i, cho in enumerate(cho_list):
    if cols[i % 5].button(cho, use_container_width=True, key=f"cho_{cho}"):
        st.session_state.selected_cho = cho
        st.rerun()

all_names = df_vacation['성함'].tolist() if not df_vacation.empty else []
filtered_names = all_names if st.session_state.selected_cho == "전체" else [n for n in all_names if get_chosung(n) == st.session_state.selected_cho]
selected_user = st.selectbox("성함을 선택하세요", filtered_names if filtered_names else ["해당 없음"], label_visibility="collapsed")

st.divider()

# --- 6. 출퇴근 시간 카드 ---
if 'arrived' not in st.session_state: st.session_state.arrived = False
if 'start_time' not in st.session_state: st.session_state.start_time = "-"

st.markdown(f"""
    <div class="time-card">
        <div style="display: flex; justify-content: center; align-items: center;">
            <div>
                <div style="color: #888; font-size: 14px;">출근 시간</div>
                <div class="time-display">{st.session_state.start_time}</div>
            </div>
            <div class="time-arrow">➔</div>
            <div>
                <div style="color: #888; font-size: 14px;">퇴근 시간</div>
                <div class="time-display">-</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

loc = get_geolocation()
c1, c2 = st.columns(2)
with c1:
    if st.button("🚀 출근하기", use_container_width=True, disabled=st.session_state.arrived or not loc):
        st.session_state.arrived = True
        st.session_state.start_time = datetime.now().strftime("%H:%M:%S")
        sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), st.session_state.start_time, "", "출근", "", loc['coords']['latitude'], loc['coords']['longitude']])
        st.rerun()
with c2:
    if st.button("🏠 퇴근하기", use_container_width=True, disabled=not st.session_state.arrived):
        st.session_state.arrived = False
        st.session_state.start_time = "-"
        st.success("오늘도 고생하셨습니다!")

st.button("근무상태 변경 ∨", use_container_width=True)

st.divider()

# --- 7. 주간 통계 및 캘린더 ---
st.subheader("이번 주 근태 요약")
st.markdown("""
    <div class="stat-container">
        <div class="stat-item"><div class="stat-label">총 근로</div><div class="stat-value" style="color:#00C853;">0h 00m</div></div>
        <div class="stat-item"><div class="stat-label">소정 근로</div><div class="stat-value">0h 00m</div></div>
        <div class="stat-item"><div class="stat-label">초과 근로</div><div class="stat-value">0h 00m</div></div>
        <div class="stat-item"><div class="stat-label">휴가</div><div class="stat-value">0h 00m</div></div>
    </div>
""", unsafe_allow_html=True)

# 캘린더 (오늘 날짜 강조)
days = ["월", "화", "수", "목", "금", "토", "일"]
today_idx = now.weekday()
calendar_html = '<div class="calendar-row">'
for i, day in enumerate(days):
    cls = "day-box day-today" if i == today_idx else "day-box"
    calendar_html += f'<div class="{cls}">{day}</div>'
calendar_html += '</div>'
st.markdown(calendar_html, unsafe_allow_html=True)

# --- 8. 연차 정보 (에러 방지 로직 강화) ---
if not df_vacation.empty and selected_user in df_vacation['성함'].values:
    u = df_vacation[df_vacation['성함'] == selected_user].iloc[0]
    
    # [핵심] 글자를 숫자로 변환하는 안전장치
    def to_num(val):
        try: return float(val)
        except: return 0.0

    v_total = to_num(u.get('총연차', 0))
    v_used = to_num(u.get('사용연차', 0))
    v_rem = to_num(u.get('잔여연차', 0))

    st.markdown(f"🏝️ **잔여 연차: {int(v_rem)}일** / 사용: {int(v_used)}일")
    prog = min(v_used / v_total, 1.0) if v_total > 0 else 0.0
    st.progress(prog)

st.write("<br><br><br>", unsafe_allow_html=True)

# 하단 내비게이션 바
st.markdown("""
    <div class="nav-bar">
        <div style="text-align:center; font-size:12px;">🏠<br>메뉴</div>
        <div style="text-align:center; font-size:12px; color:#1A73E8; font-weight:bold;">📋<br>근태</div>
        <div style="text-align:center; font-size:12px;">🏖️<br>휴가</div>
        <div style="text-align:center; font-size:12px;">🔔<br>알림</div>
    </div>
""", unsafe_allow_html=True)
