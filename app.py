import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="스마트경로당지원 근태관리", layout="wide")

# --- 2. 디자인 CSS (탭 메뉴 디자인 대폭 강화) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    
    /* 주요 안내 레이블 스타일 */
    .custom-label {
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        color: #1E1E1E;
        margin-bottom: 0.8rem;
        margin-top: 1.2rem;
    }
    
    /* 탭 메뉴 전체 컨테이너 높이 및 배경 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }

    /* 탭 버튼 개별 디자인 (버튼처럼 보이게) */
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #FFFFFF;
        border-radius: 10px 10px 0px 0px;
        border: 1px solid #E0E0E0;
        padding: 10px 30px !important;
        font-size: 1.2rem !important; /* 크기 키움 */
        font-weight: 800 !important;   /* 굵게 */
        color: #888888 !important;
        transition: all 0.3s ease;
    }

    /* 활성화된 탭 디자인 (강조) */
    .stTabs [aria-selected="true"] {
        background-color: #1A73E8 !important;
        color: #FFFFFF !important;
        border: 1px solid #1A73E8 !important;
        box-shadow: 0 4px 6px rgba(26, 115, 232, 0.2);
    }

    .time-card {
        background: white; padding: 25px; border-radius: 20px;
        text-align: center; border: 1px solid #EEE; margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .time-val { font-size: 34px; font-weight: bold; color: #111; }
    
    .location-box {
        background: white; padding: 15px; border-radius: 15px;
        border: 1px solid #E0E0E0;
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

# --- 4. 세션 상태 및 헬퍼 함수 ---
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
st.markdown("# 🏢 스마트경로당지원 근태관리")

# 초성 선택
st.markdown('<div class="custom-label">초성 선택</div>', unsafe_allow_html=True)
cho = st.radio("초성", ["전체", "ㄱ","ㄴ","ㄷ","ㄹ","ㅁ","ㅂ","ㅅ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"], horizontal=True, label_visibility="collapsed")

# 성함 선택
st.markdown('<div class="custom-label">본인 성함을 선택하세요</div>', unsafe_allow_html=True)
names = df_vacation['성함'].tolist() if not df_vacation.empty else []
filtered = names if cho == "전체" else [n for n in names if get_chosung(n) == cho]
selected_user = st.selectbox("성함", filtered if filtered else ["데이터 없음"], label_visibility="collapsed")

st.write("<br>", unsafe_allow_html=True)

# --- 6. 탭 구성 (버튼 스타일 적용) ---
tab_attendance, tab_vacation = st.tabs(["🕒 근태관리", "🏖️ 휴가관리"])

with tab_attendance:
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    
    st.markdown(f'<div class="custom-label">📅 {now.strftime("%Y년 %m월 %d일 %H:%M")}</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="time-card">
            <div style="display:flex; justify-content:center; align-items:center; gap:25px;">
                <div><div style="color:#888; font-size:13px; margin-bottom:5px;">출근 시간</div><div class="time-val">{st.session_state.disp_start}</div></div>
                <div style="font-size:30px; color:#DDD; padding-top:10px;">➔</div>
                <div><div style="color:#888; font-size:13px; margin-bottom:5px;">퇴근 시간</div><div class="time-val">{st.session_state.disp_end}</div></div>
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
            sheet_attendance.append_row([selected_user, today_date, st.session_state.disp_start, "", "출근", "정상출근", lat, lon])
            st.rerun()

    with col_btn2:
        if st.button("🏠 퇴근하기", use_container_width=True, disabled=not st.session_state.arrived or st.session_state.disp_end != "-"):
            st.session_state.disp_end = datetime.now().strftime("%H:%M:%S")
            sheet_attendance.append_row([selected_user, today_date, "", st.session_state.disp_end, "퇴근", "정상퇴근", "", ""])
            st.success("퇴근 기록 완료!")
            st.rerun()

    st.divider()

    st.markdown('<div class="custom-label">📍 현재 위치 확인</div>', unsafe_allow_html=True)
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        col_map, col_gps = st.columns([1.6, 1])
        with col_map:
            st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=14, use_container_width=True)
        with col_gps:
            st.markdown(f"""
                <div class="location-box">
                    <div style="font-size:13px; color:#666; font-weight:bold;">🛰️ 위도 (Latitude)</div><div style="color:#1A73E8; font-family:monospace; font-size:15px;">{lat:.6f}</div>
                    <div style="margin-top:15px; font-size:13px; color:#666; font-weight:bold;">🛰️ 경도 (Longitude)</div><div style="color:#1A73E8; font-family:monospace; font-size:15px;">{lon:.6f}</div>
                    <hr style="margin:15px 0; border:0; border-top:1px solid #EEE;">
                    <div style="font-size:12px; color:#28a745; text-align:center; font-weight:bold;">✔️ 위치 수신 상태 양호</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("위치 정보를 수신 중입니다...")

with tab_vacation:
    st.markdown('<div class="custom-label">🏖️ 나의 휴가 현황</div>', unsafe_allow_html=True)
    if not df_vacation.empty and selected_user in df_vacation['성함'].values:
        u = df_vacation[df_vacation['성함'] == selected_user].iloc[0]
        v_total, v_used, v_rem = to_num(u.get('총연차', 0)), to_num(u.get('사용연차', 0)), to_num(u.get('잔여연차', 0))
        st.info(f"💡 {selected_user}님의 잔여 연차는 {int(v_rem)}일입니다.")
        st.progress(min(v_used / v_total, 1.0) if v_total > 0 else 0.0)
    
    if st.button("➕ 휴가 신청하기", use_container_width=True):
        @st.dialog("휴가 신청")
        def apply_form():
            v_date = st.date_input("날짜 선택")
            v_type = st.selectbox("종류", ["연차", "반차", "병가"])
            if st.button("제출"):
                sheet_attendance.append_row([selected_user, v_date.strftime("%Y-%m-%d"), "", "", v_type, "휴가신청", "", ""])
                st.success("신청 완료")
                st.rerun()
        apply_form()

st.caption("실버 복지 사업단 v3.4 - 프리미엄 UI 업데이트")
