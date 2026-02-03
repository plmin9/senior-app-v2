import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="스마트경로당지원 근태관리", layout="wide")

# --- 2. 디자인 CSS (탭 바다색 강조 & 지도 아웃라인 강화) ---
st.markdown("""
    <style>
    .stApp { background-color: #F7F9FB; } 
    
    .main-title {
        font-size: 1.8rem; font-weight: 800; color: #2E7D32;
        text-align: center; margin-bottom: 1rem;
    }

    .custom-label {
        font-size: 1.15rem; font-weight: 800;
        color: #333; margin-bottom: 0.5rem; margin-top: 1rem;
    }

    /* 탭 메뉴: 바다색(Sea Blue) 포인트 및 하단 라인 수정 */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: none !important; }
    
    .stTabs [data-baseweb="tab"] {
        flex: 1; height: 55px; font-size: 1.2rem !important; font-weight: 800 !important;
        border-radius: 12px 12px 0 0; transition: 0.3s;
        border: none !important;
    }

    /* 선택되지 않은 탭 */
    .stTabs [id^="tabs-b-tab"] { background-color: #E0F2F1 !important; color: #00796B !important; }

    /* 선택된 탭: 바다색(Sea Blue)으로 강하게 강조 및 붉은 라인 제거 */
    .stTabs [aria-selected="true"] {
        background-color: #00838F !important; /* 진한 바다색 */
        color: white !important;
        box-shadow: 0 4px 10px rgba(0, 131, 143, 0.3);
    }
    
    /* 탭 하단 기본 붉은색 라인 강제 제거 */
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #00838F !important; /* 하단 라인도 바다색으로 통일 */
        height: 4px !important;
    }

    /* 버튼 스타일 (초록색) */
    div.stButton > button { 
        border-radius: 12px; height: 3.2rem; font-weight: 700; 
        background-color: #4CAF50 !important; color: white !important; border: none;
    }

    .time-card {
        background: white; padding: 20px; border-radius: 20px;
        border: 2px solid #00838F; text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .time-val { font-size: 2.2rem; font-weight: 900; color: #2E7D32; }

    /* 📍 지도 아웃라인 (선명하고 뚜렷하게) */
    .map-outline-box {
        border: 4px solid #004D40; /* 아주 진한 바다색 아웃라인 */
        border-radius: 15px;
        padding: 0px;
        overflow: hidden;
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        background-color: white;
    }

    .location-box {
        background: #E0F2F1; padding: 15px; border-radius: 12px;
        border: 2px solid #00838F; height: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 구글 시트 연결 (기존 로직) ---
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

# --- 5. 메인 화면 ---
st.markdown('<div class="main-title">🏢 스마트경로당지원 근태관리</div>', unsafe_allow_html=True)

cho = st.radio("초성 선택", ["전체", "ㄱ","ㄴ","ㄷ","ㄹ","ㅁ","ㅂ","ㅅ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"], horizontal=True)
all_names = df_vacation['성함'].tolist() if not df_vacation.empty else []
selected_user = st.selectbox("본인 성함을 선택하세요", all_names)

st.write("<br>", unsafe_allow_html=True)

# --- 6. 탭 구성 (바다색 테마) ---
tab_attendance, tab_vacation = st.tabs(["🕒 근태관리", "🏖️ 휴가관리"])

with tab_attendance:
    now = datetime.now()
    st.markdown(f'<div class="custom-label" style="text-align:center; color:#555;">📅 {now.strftime("%Y-%m-%d %H:%M")}</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="time-card">
            <div style="display:flex; justify-content:space-around; align-items:center;">
                <div><div style="font-size:0.9rem; color:#888;">출근 시간</div><div class="time-val">{st.session_state.disp_start}</div></div>
                <div style="font-size:2.5rem; color:#00838F; font-weight:200;">|</div>
                <div><div style="font-size:0.9rem; color:#888;">퇴근 시간</div><div class="time-val">{st.session_state.disp_end}</div></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    loc = get_geolocation()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚀 출근하기", use_container_width=True, disabled=st.session_state.arrived or not loc):
            st.session_state.disp_start = datetime.now().strftime("%H:%M:%S")
            st.session_state.arrived = True
            lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
            sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), st.session_state.disp_start, "", "출근", "정상", lat, lon])
            st.rerun()
    with c2:
        if st.button("🏠 퇴근하기", use_container_width=True, disabled=not st.session_state.arrived or st.session_state.disp_end != "-"):
            st.session_state.disp_end = datetime.now().strftime("%H:%M:%S")
            sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), "", st.session_state.disp_end, "퇴근", "정상", "", ""])
            st.balloons()
            st.rerun()

    st.divider()

    # 🗺️ 지도 섹션 (뚜렷한 아웃라인 적용)
    st.markdown('<div class="custom-label">📍 현재 위치 확인</div>', unsafe_allow_html=True)
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        m_col1, m_col2 = st.columns([1.2, 1])
        with m_col1:
            # 지도 아웃라인 박스 시작
            st.markdown('<div class="map-outline-box">', unsafe_allow_html=True)
            st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=15, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with m_col2:
            st.markdown(f"""
                <div class="location-box">
                    <div style="font-size:0.9rem; color:#006064; font-weight:bold;">수신 위도</div>
                    <div style="font-family:monospace; font-size:1.2rem; color:#333; margin-bottom:10px;">{lat:.6f}</div>
                    <div style="font-size:0.9rem; color:#006064; font-weight:bold;">수신 경도</div>
                    <div style="font-family:monospace; font-size:1.2rem; color:#333;">{lon:.6f}</div>
                    <div style="margin-top:15px; text-align:center; font-size:0.9rem; color:#00838F; font-weight:bold;">● GPS 정상 작동 중</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("🛰️ 위치 정보를 수신 중입니다...")

with tab_vacation:
    st.markdown('<div class="custom-label">🏖️ 나의 휴가 현황</div>', unsafe_allow_html=True)
    if not df_vacation.empty and selected_user in df_vacation['성함'].values:
        u = df_vacation[df_vacation['성함'] == selected_user].iloc[0]
        v_rem = u.get('잔여연차', 0)
        st.success(f"🌟 {selected_user}님, 남은 휴가는 **{v_rem}일**입니다.")
    
    if st.button("➕ 휴가 신청하기", use_container_width=True):
        @st.dialog("휴가 신청")
        def apply_form():
            v_date = st.date_input("날짜 선택")
            v_type = st.selectbox("종류", ["연차", "반차", "병가"])
            if st.button("제출", type="primary"):
                sheet_attendance.append_row([selected_user, v_date.strftime("%Y-%m-%d"), "", "", v_type, "신청", "", ""])
                st.success("신청 완료")
                st.rerun()
        apply_form()

st.caption("실버 복지 사업단 v3.8 | 바다색 테마 & 강화된 맵 디자인")
