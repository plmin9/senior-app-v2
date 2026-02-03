import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="스마트경로당지원 근태관리", layout="wide")

# --- 2. 디자인 CSS (대형 버튼 및 바다색 테마) ---
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

    /* 탭 메뉴 스타일 */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: none !important; }
    .stTabs [data-baseweb="tab"] {
        flex: 1; height: 55px; font-size: 1.2rem !important; font-weight: 800 !important;
        border-radius: 12px 12px 0 0; border: none !important;
    }
    .stTabs [id^="tabs-b-tab"] { background-color: #E0F2F1 !important; color: #00796B !important; }
    .stTabs [aria-selected="true"] { background-color: #00838F !important; color: white !important; }
    .stTabs [data-baseweb="tab-highlight"] { background-color: #00838F !important; height: 4px !important; }

    /* 🚀 대형 버튼 스타일 (초록색, 크기 대폭 확대) */
    div.stButton > button { 
        border-radius: 15px; 
        height: 5rem !important; /* 높이를 5rem으로 크게 확대 */
        font-size: 1.5rem !important; /* 글자 크기 확대 */
        font-weight: 800 !important; 
        background-color: #4CAF50 !important; 
        color: white !important; 
        border: none;
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
        transition: all 0.2s;
    }
    
    /* 버튼 클릭/호버 효과 */
    div.stButton > button:hover { transform: scale(1.02); }
    
    /* 비활성화된 버튼 스타일 (회색) */
    div.stButton > button:disabled { 
        background-color: #E0E0E0 !important; 
        color: #9E9E9E !important; 
        box-shadow: none !important;
        transform: none !important;
    }

    .time-card {
        background: white; padding: 20px; border-radius: 20px;
        border: 2px solid #00838F; text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .time-val { font-size: 2.5rem; font-weight: 900; color: #2E7D32; }

    .map-outline-box {
        border: 4px solid #004D40; border-radius: 15px;
        overflow: hidden; box-shadow: 0 8px 20px rgba(0,0,0,0.15);
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

# --- 4. 세션 상태 (로직 제어 핵심) ---
if 'disp_start' not in st.session_state: st.session_state.disp_start = "-"
if 'disp_end' not in st.session_state: st.session_state.disp_end = "-"
if 'arrived' not in st.session_state: st.session_state.arrived = False # 출근 여부 체크

# --- 5. 메인 화면 ---
st.markdown('<div class="main-title">🏢 스마트경로당지원 근태관리</div>', unsafe_allow_html=True)

# 성함 선택
all_names = df_vacation['성함'].tolist() if not df_vacation.empty else []
selected_user = st.selectbox("본인 성함을 선택하세요", all_names)

st.write("<br>", unsafe_allow_html=True)

# --- 6. 탭 구성 ---
tab_attendance, tab_vacation = st.tabs(["🕒 근태관리", "🏖️ 휴가관리"])

with tab_attendance:
    now = datetime.now()
    st.markdown(f'<div class="custom-label" style="text-align:center; color:#555;">📅 {now.strftime("%Y-%m-%d %H:%M")}</div>', unsafe_allow_html=True)
    
    # 시간 표시 카드
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
    
    # --- 🚀 버튼 배치 및 로직 제어 ---
    col1, col2 = st.columns(2)
    
    with col1:
        # 조건: 아직 출근 버튼을 안 눌렀고(not arrived), 위치 정보가 있을 때만 활성화
        btn_start = st.button("🚀 출근하기", use_container_width=True, 
                              disabled=st.session_state.arrived or not loc)
        if btn_start:
            st.session_state.disp_start = datetime.now().strftime("%H:%M:%S")
            st.session_state.arrived = True # 출근 처리 완료
            lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
            sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), st.session_state.disp_start, "", "출근", "정상", lat, lon])
            st.rerun()
            
    with col2:
        # 조건: 반드시 출근을 먼저 했어야 하고(arrived), 아직 퇴근을 안 했을 때만 활성화
        btn_end = st.button("🏠 퇴근하기", use_container_width=True, 
                            disabled=not st.session_state.arrived or st.session_state.disp_end != "-")
        if btn_end:
            st.session_state.disp_end = datetime.now().strftime("%H:%M:%S")
            sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), "", st.session_state.disp_end, "퇴근", "정상", "", ""])
            st.balloons()
            st.rerun()

    st.divider()

    # 위치 정보 (지도 아웃라인 유지)
    st.markdown('<div class="custom-label">📍 현재 위치 확인</div>', unsafe_allow_html=True)
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        m_col1, m_col2 = st.columns([1.2, 1])
        with m_col1:
            st.markdown('<div class="map-outline-box">', unsafe_allow_html=True)
            st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=15, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with m_col2:
            st.markdown(f"""
                <div style="background:#E0F2F1; padding:15px; border-radius:12px; border:2px solid #00838F;">
                    <div style="font-size:0.9rem; color:#006064; font-weight:bold;">수신 위치</div>
                    <div style="font-family:monospace; font-size:1.1rem; color:#333;">{lat:.4f} / {lon:.4f}</div>
                    <div style="margin-top:10px; text-align:center; font-size:0.9rem; color:#00838F; font-weight:bold;">● GPS 정상</div>
                </div>
            """, unsafe_allow_html=True)

with tab_vacation:
    st.markdown('<div class="custom-label">🏖️ 나의 휴가 현황</div>', unsafe_allow_html=True)
    if not df_vacation.empty and selected_user in df_vacation['성함'].values:
        u = df_vacation[df_vacation['성함'] == selected_user].iloc[0]
        st.success(f"🌟 {selected_user}님, 남은 휴가는 **{u.get('잔여연차', 0)}일**입니다.")
    
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

st.caption("실버 복지 사업단 v3.9 | 대형 버튼 & 스마트 로직")
