import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="스마트경로당지원 근태관리", layout="wide")

# --- 2. 반응형 디자인 & 컬러 테마 CSS ---
st.markdown("""
    <style>
    /* 전체 배경 및 폰트 */
    .stApp { background-color: #F0F9F4; } /* 연한 연두빛 배경 */
    
    /* 제목 스타일 */
    .main-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: #2D5A27;
        text-align: center;
        margin-bottom: 1rem;
    }

    /* 반응형 레이블 스타일 */
    .custom-label {
        font-size: clamp(1rem, 4vw, 1.15rem);
        font-weight: 800;
        color: #333;
        margin-bottom: 0.5rem;
        margin-top: 1rem;
    }

    /* 탭 메뉴 디자인 (연파랑 & 연두 활용) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        flex: 1; /* 가로 가득 채우기 (반응형) */
        height: 55px;
        background-color: #E3F2FD !important; /* 연파랑 배경 */
        border-radius: 12px 12px 0 0;
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        color: #1976D2 !important;
        border: none;
        transition: 0.3s;
    }

    .stTabs [aria-selected="true"] {
        background-color: #8BC34A !important; /* 연두색 강조 */
        color: white !important;
        box-shadow: 0 4px 10px rgba(139, 195, 74, 0.3);
    }

    /* 출퇴근 시간 카드 (연파랑 포인트) */
    .time-card {
        background: white;
        padding: 20px;
        border-radius: 20px;
        border: 2px solid #E3F2FD;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .time-val { font-size: clamp(1.8rem, 8vw, 2.2rem); font-weight: 900; color: #1976D2; }
    .time-label { font-size: 0.8rem; color: #888; margin-bottom: 5px; }

    /* 위치 정보 박스 */
    .location-box {
        background: #F1F8E9; /* 아주 연한 연두색 */
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #C5E1A5;
    }
    
    /* 버튼 모서리 둥글게 */
    div.stButton > button {
        border-radius: 12px;
        height: 3rem;
        font-weight: 700;
    }

    /* 모바일 최적화: 여백 조정 */
    @media (max-width: 640px) {
        .stApp { padding: 10px; }
        .time-card { padding: 15px; }
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

# --- 4. 세션 상태 ---
if 'disp_start' not in st.session_state: st.session_state.disp_start = "-"
if 'disp_end' not in st.session_state: st.session_state.disp_end = "-"
if 'arrived' not in st.session_state: st.session_state.arrived = False

def to_num(val):
    try: return float(str(val).replace(',', ''))
    except: return 0.0

def get_chosung(text):
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    if not text: return ""
    char_code = ord(str(text)[0]) - 0xAC00
    return CHOSUNG_LIST[char_code // 588] if 0 <= char_code <= 11171 else str(text)[0].upper()

# --- 5. 메인 화면 ---
st.markdown('<div class="main-title">🏢 스마트경로당지원 근태관리</div>', unsafe_allow_html=True)

# 초성 선택
st.markdown('<div class="custom-label">초성 선택</div>', unsafe_allow_html=True)
cho = st.radio("초성", ["전체", "ㄱ","ㄴ","ㄷ","ㄹ","ㅁ","ㅂ","ㅅ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"], horizontal=True, label_visibility="collapsed")

# 성함 선택
st.markdown('<div class="custom-label">본인 성함을 선택하세요</div>', unsafe_allow_html=True)
names = df_vacation['성함'].tolist() if not df_vacation.empty else []
filtered = names if cho == "전체" else [n for n in names if get_chosung(n) == cho]
selected_user = st.selectbox("성함", filtered if filtered else ["데이터 없음"], label_visibility="collapsed")

st.write("<br>", unsafe_allow_html=True)

# --- 6. 탭 구성 (반응형 & 컬러 적용) ---
tab_attendance, tab_vacation = st.tabs(["🕒 근태관리", "🏖️ 휴가관리"])

with tab_attendance:
    now = datetime.now()
    st.markdown(f'<div class="custom-label" style="text-align:center; color:#555;">📅 {now.strftime("%Y-%m-%d %H:%M")}</div>', unsafe_allow_html=True)
    
    # 시간 표시 카드
    st.markdown(f"""
        <div class="time-card">
            <div style="display:flex; justify-content:space-around; align-items:center;">
                <div><div class="time-label">출근 시간</div><div class="time-val">{st.session_state.disp_start}</div></div>
                <div style="font-size:2rem; color:#E3F2FD;">|</div>
                <div><div class="time-label">퇴근 시간</div><div class="time-val">{st.session_state.disp_end}</div></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    loc = get_geolocation()
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("🚀 출근하기", use_container_width=True, type="primary", disabled=st.session_state.arrived or not loc):
            st.session_state.disp_start = datetime.now().strftime("%H:%M:%S")
            st.session_state.arrived = True
            lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
            sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), st.session_state.disp_start, "", "출근", "정상출근", lat, lon])
            st.rerun()

    with col_btn2:
        if st.button("🏠 퇴근하기", use_container_width=True, disabled=not st.session_state.arrived or st.session_state.disp_end != "-"):
            st.session_state.disp_end = datetime.now().strftime("%H:%M:%S")
            sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), "", st.session_state.disp_end, "퇴근", "정상퇴근", "", ""])
            st.balloons()
            st.rerun()

    st.divider()

    # 위치 정보 및 맵 (반응형 컬럼)
    st.markdown('<div class="custom-label">📍 현재 위치 확인</div>', unsafe_allow_html=True)
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        # 화면 너비에 따라 맵과 정보를 배치 (태블릿 이상은 가로, 폰트는 세로 자동 전환)
        m_col1, m_col2 = st.columns([1.5, 1])
        with m_col1:
            st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=14, use_container_width=True)
        with m_col2:
            st.markdown(f"""
                <div class="location-box">
                    <div style="font-size:0.8rem; color:#689F38; font-weight:bold;">위도</div>
                    <div style="font-family:monospace; font-size:1.1rem; color:#333; margin-bottom:10px;">{lat:.6f}</div>
                    <div style="font-size:0.8rem; color:#689F38; font-weight:bold;">경도</div>
                    <div style="font-family:monospace; font-size:1.1rem; color:#333;">{lon:.6f}</div>
                    <div style="margin-top:15px; text-align:center; font-size:0.85rem; color:#4CAF50;">✅ GPS 수신중</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("🛰️ 위치 정보를 가져오고 있습니다...")

with tab_vacation:
    st.markdown('<div class="custom-label">🏖️ 나의 휴가 현황</div>', unsafe_allow_html=True)
    if not df_vacation.empty and selected_user in df_vacation['성함'].values:
        u = df_vacation[df_vacation['성함'] == selected_user].iloc[0]
        v_total, v_used, v_rem = to_num(u.get('총연차', 0)), to_num(u.get('사용연차', 0)), to_num(u.get('잔여연차', 0))
        st.success(f"🌟 {selected_user}님, 사용할 수 있는 연차가 **{int(v_rem)}일** 남았습니다.")
        st.progress(min(v_used / v_total, 1.0) if v_total > 0 else 0.0)
    
    if st.button("➕ 휴가 신청하기", use_container_width=True):
        @st.dialog("휴가 신청")
        def apply_form():
            v_date = st.date_input("날짜 선택")
            v_type = st.selectbox("종류", ["연차", "반차", "병가"])
            if st.button("제출", type="primary"):
                sheet_attendance.append_row([selected_user, v_date.strftime("%Y-%m-%d"), "", "", v_type, "휴가신청", "", ""])
                st.success("신청되었습니다.")
                st.rerun()
        apply_form()

st.write("<br><br>", unsafe_allow_html=True)
st.caption("실버 복지 사업단 v3.5 | 테마: 포레스트 블루")
