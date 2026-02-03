import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
from streamlit_js_eval import get_geolocation

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="근태/휴가 관리", layout="wide")

# --- 2. 상세 디자인 CSS (이미지 스타일 재현) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    
    /* 상단 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; background-color: #F8F9FA; }
    .stTabs [data-baseweb="tab"] { font-size: 20px; font-weight: bold; color: #888; }
    .stTabs [aria-selected="true"] { color: #333 !important; border-bottom-color: #333 !important; }

    /* 휴가 박스 스타일 */
    .vacation-container { display: flex; gap: 10px; margin-bottom: 20px; }
    .vacation-box {
        flex: 1; background: white; padding: 20px; border-radius: 15px;
        text-align: center; border: 1px solid #F0F0F0; box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .vacation-box.active { background-color: #EBF5FF; border: 1px solid #C2E0FF; }
    .v-label { font-size: 15px; color: #666; margin-bottom: 8px; }
    .v-value { font-size: 22px; font-weight: bold; color: #333; }
    .v-value.blue { color: #1A73E8; }

    /* 캐릭터 프로그레스 바 영역 */
    .char-progress-container {
        background: white; padding: 20px; border-radius: 15px; 
        margin-bottom: 30px; border: 1px solid #F0F0F0;
    }
    .char-msg-box {
        background: #EBF5FF; padding: 10px 15px; border-radius: 10px;
        font-size: 14px; color: #1A73E8; display: inline-block; margin-left: 10px;
    }

    /* 근태 카드 스타일 */
    .time-card {
        background: white; padding: 30px; border-radius: 20px;
        text-align: center; border: 1px solid #EEE; margin-bottom: 20px;
    }
    .time-val { font-size: 38px; font-weight: bold; color: #222; }

    /* 플로팅 버튼 스타일 대체 (Streamlit 버튼 커스텀) */
    .stButton>button[kind="secondary"] {
        background-color: #00BDD3 !important; color: white !important;
        border-radius: 50% !important; width: 60px !important; height: 60px !important;
        font-size: 30px !important; position: fixed; bottom: 80px; right: 30px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2); z-index: 1000;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 구글 시트 연결 ---
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

# --- 4. 사용자 선택 로직 (초성 필터) ---
def get_chosung(text):
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    char_code = ord(str(text)[0]) - 0xAC00
    return CHOSUNG_LIST[char_code // 588] if 0 <= char_code <= 11171 else str(text)[0].upper()

st.title("내 근태현황")
cho = st.radio("성씨 초성", ["전체", "ㄱ","ㄴ","ㄷ","ㄹ","ㅁ","ㅂ","ㅅ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"], horizontal=True)
names = df_vacation['성함'].tolist()
filtered = names if cho == "전체" else [n for n in names if get_chosung(n) == cho]
selected_user = st.selectbox("본인 성함을 선택하세요", filtered if filtered else ["없음"])

st.divider()

# --- 5. 탭 구성 (근태 / 휴가) ---
tab_attendance, tab_vacation = st.tabs(["근태", "휴가"])

# --- [근태 탭] ---
with tab_attendance:
    now = datetime.now()
    st.write(f"📅 {now.strftime('%Y-%m-%d (%a) %H:%M:%S')} 📍")
    
    # 출퇴근 카드
    st.markdown(f"""
        <div class="time-card">
            <div style="display:flex; justify-content:center; align-items:center; gap:30px;">
                <div><div style="color:#888;">출근 시간</div><div class="time-val">21:03:39</div></div>
                <div style="font-size:30px; color:#EEE;">➔</div>
                <div><div style="color:#888;">퇴근 시간</div><div class="time-val">-</div></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1: st.button("출근하기", use_container_width=True)
    with col2: st.button("퇴근하기", use_container_width=True)
    st.button("근무상태 변경 ∨", use_container_width=True)
    
    st.divider()
    st.subheader("2026-02-02 ~ 2026-02-08")
    st.image("https://img.icons8.com/color/96/calendar.png", width=50) # 예시 아이콘
    st.write("전자결재 요청 내역 0")

# --- [휴가 탭] ---
with tab_vacation:
    st.header("휴가")
    st.write(f"{now.strftime('%Y년 %m월 %d일 (%a)')}")
    
    if selected_user in df_vacation['성함'].values:
        u = df_vacation[df_vacation['성함'] == selected_user].iloc[0]
        v_rem = u.get('잔여연차', 0)
        v_used = u.get('사용연차', 0)
        v_total = u.get('총연차', 0)
        
        # 1. 상단 3단 박스
        st.markdown(f"""
            <div class="vacation-container">
                <div class="vacation-box active">
                    <div style="font-size:30px;">🏖️</div>
                    <div class="v-label">잔여 연차</div>
                    <div class="v-value blue">{v_rem}d</div>
                </div>
                <div class="vacation-box">
                    <div style="font-size:30px;">📅</div>
                    <div class="v-label">사용 연차</div>
                    <div class="v-value">{v_used}d</div>
                </div>
                <div class="vacation-box">
                    <div style="font-size:30px;">✈️</div>
                    <div class="v-label">총 연차</div>
                    <div class="v-value">{v_total}d</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 2. 캐릭터 프로그레스 바
        prog = min(v_used / v_total, 1.0) if v_total > 0 else 0.0
        msg = "사용 가능한 연차가 충분합니다!" if v_rem > 0 else "사용 가능한 연차가 없습니다."
        
        st.markdown(f"""
            <div class="char-progress-container">
                <div style="display:flex; align-items:center; margin-bottom:10px;">
                    <span style="font-size:40px;">🐰</span>
                    <div class="char-msg-box">{msg}</div>
                </div>
        """, unsafe_allow_html=True)
        st.progress(prog)
        st.markdown(f"<div style='text-align:right; color:#888;'>{int(prog*100)}% ({v_used} / {v_total})</div></div>", unsafe_allow_html=True)

    st.subheader("휴가 신청")
    st.info("신청 내역 결과가 없습니다.")

    # 3. 우측 하단 플로팅 신청 버튼 (+)
    if st.button("+", key="apply_v"):
        @st.dialog("휴가 신청")
        def apply_form():
            st.date_input("휴가 날짜")
            st.selectbox("휴가 종류", ["연차", "반차", "경조사", "병가"])
            st.text_area("사유")
            if st.button("신청서 제출"):
                st.success("신청되었습니다.")
                st.rerun()
        apply_form()

# --- 하단 공통 네비게이션 바 ---
st.markdown("""
    <div style="position:fixed; bottom:0; left:0; width:100%; background:white; display:flex; justify-content:space-around; padding:15px; border-top:1px solid #EEE; z-index:999;">
        <div style="text-align:center; color:#888;">⠿<br><span style="font-size:10px;">메뉴</span></div>
        <div style="text-align:center; color:#333; font-weight:bold;">📋<br><span style="font-size:10px;">근태</span></div>
        <div style="text-align:center; color:#888;">🏖️<br><span style="font-size:10px;">휴가</span></div>
        <div style="text-align:center; color:#888;">🔔<br><span style="font-size:10px;">알림</span></div>
    </div>
    <div style="height:80px;"></div>
""", unsafe_allow_html=True)
