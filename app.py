import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="스마트경로당지원 근태관리", layout="wide")

# --- 2. 디자인 CSS (색상 테마 및 지도 프레임 최적화) ---
st.markdown("""
    <style>
    .stApp { background-color: #F7F9FB; } 
    
    .main-title {
        font-size: 1.8rem; font-weight: 800; color: #2E7D32;
        text-align: center; margin-bottom: 1rem;
    }

    .custom-label {
        font-size: clamp(1rem, 4vw, 1.15rem); font-weight: 800;
        color: #333; margin-bottom: 0.5rem; margin-top: 1rem;
    }

    /* 탭 메뉴: 라임색(근태) & 바다색(휴가) */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    
    .stTabs [data-baseweb="tab"] {
        flex: 1; height: 50px; font-size: 1.1rem !important; font-weight: 800 !important;
        border-radius: 12px 12px 0 0; transition: 0.3s;
    }

    /* 근태관리 탭 (라임색 포인트) */
    .stTabs [id="tabs-b-tab-0"] { background-color: #F9FBE7 !important; color: #827717 !important; }
    .stTabs [id="tabs-b-tab-0"][aria-selected="true"] { background-color: #CDDC39 !important; color: white !important; }

    /* 휴가관리 탭 (바다색 포인트) */
    .stTabs [id="tabs-b-tab-1"] { background-color: #E0F2F1 !important; color: #00796B !important; }
    .stTabs [id="tabs-b-tab-1"][aria-selected="true"] { background-color: #009688 !important; color: white !important; }

    /* 출퇴근 버튼 (초록색) */
    div.stButton > button { 
        border-radius: 12px; height: 3.2rem; font-weight: 700; 
        background-color: #4CAF50 !important; color: white !important; border: none;
    }
    div.stButton > button:disabled { background-color: #E0E0E0 !important; color: #9E9E9E !important; }

    /* 출퇴근 시간 카드 */
    .time-card {
        background: white; padding: 20px; border-radius: 20px;
        border: 2px solid #CDDC39; text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .time-val { font-size: clamp(1.8rem, 8vw, 2.2rem); font-weight: 900; color: #2E7D32; }

    /* 📍 지도 영역 전체 테두리 프레임 */
    .map-frame {
        border: 2px solid #BDBDBD; /* 전체 외곽 테두리 */
        padding: 15px;
        border-radius: 20px;
        background-color: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .map-container {
        border: 2px solid #CDDC39; /* 지도 직속 테두리(라임) */
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 10px;
    }

    .location-box {
        background: #F9FBE7; padding: 12px; border-radius: 12px;
        border: 1px solid #DCE775;
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

def get_chosung(text):
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    if not text: return ""
    char_code = ord(str(text)[0]) - 0xAC00
    return CHOSUNG_LIST[char_code // 588] if 0 <= char_code <= 11171 else str(text)[0].upper()

# --- 5. 메인 화면 ---
st.markdown('<div class="main-title">🏢 스마트경로당지원 근태관리</div>', unsafe_allow_html=True)

cho = st.radio("초성 선택", ["전체", "ㄱ","ㄴ","ㄷ","ㄹ","ㅁ","ㅂ","ㅅ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"], horizontal=True)
all_names = df_vacation['성함'].tolist() if not df_vacation.empty else []
filtered = all_names if cho == "전체" else [n for n in all_names if get_chosung(n) == cho]
selected_user = st.selectbox("본인 성함을 선택하세요", filtered if filtered else ["데이터 없음"])

st.write("<br>", unsafe_allow_html=True)

# --- 6. 탭 구성 (컬러 적용) ---
tab_attendance, tab_vacation = st.tabs(["🕒 근태관리", "🏖️ 휴가관리"])

with tab_attendance:
    now = datetime.now()
    st.markdown(f'<div class="custom-label" style="text-align:center; color:#666;">📅 {now.strftime("%Y-%m-%d %H:%M")}</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="time-card">
            <div style="display:flex; justify-content:space-around; align-items:center;">
                <div><div style="font-size:0.85rem; color:#888;">출근 시간</div><div class="time-val">{st.session_state.disp_start}</div></div>
                <div style="font-size:2rem; color:#CDDC39;">|</div>
                <div><div style="font-size:0.85rem; color:#888;">퇴근 시간</div><div class="time-val">{st.session_state.disp_end}</div></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    loc = get_geolocation()
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("🚀 출근하기", use_container_width=True, disabled=st.session_state.arrived or not loc):
            st.session_state.disp_start = datetime.now().strftime("%H:%M:%S")
            st.session_state.arrived = True
            lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
            sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), st.session_state.disp_start, "", "출근", "정상", lat, lon])
            st.rerun()

    with col_btn2:
        if st.button("🏠 퇴근하기", use_container_width=True, disabled=not st.session_state.arrived or st.session_state.disp_end != "-"):
            st.session_state.disp_end = datetime.now().strftime("%H:%M:%S")
            sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), "", st.session_state.disp_end, "퇴근", "정상", "", ""])
            st.success("고생하셨습니다!")
            st.rerun()

    st.divider()

    # 🗺️ 지도 섹션 (프레임 및 크기 축소 적용)
    st.markdown('<div class="custom-label">📍 현재 위치 확인</div>', unsafe_allow_html=True)
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        
        # 지도 프레임 시작
        st.markdown('<div class="map-frame">', unsafe_allow_html=True)
        m_col1, m_col2 = st.columns([1.2, 1]) # 맵 비중을 더 줄임
        with m_col1:
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            # 맵 높이를 250px 정도로 고정하여 콤팩트하게 만듦
            st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=15, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with m_col2:
            st.markdown(f"""
                <div class="location-box">
                    <div style="font-size:0.85rem; color:#827717; font-weight:bold;">수신 위도</div>
                    <div style="font-family:monospace; font-size:1.1rem; color:#333; margin-bottom:8px;">{lat:.6f}</div>
                    <div style="font-size:0.85rem; color:#827717; font-weight:bold;">수신 경도</div>
                    <div style="font-family:monospace; font-size:1.1rem; color:#333;">{lon:.6f}</div>
                    <div style="margin-top:10px; text-align:center; font-size:0.8rem; color:#4CAF50; font-weight:bold;">● GPS 수신 중</div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True) # 프레임 끝
    else:
        st.info("🛰️ 위치 정보를 수신 중입니다...")

with tab_vacation:
    st.markdown('<div class="custom-label">🏖️ 나의 휴가 현황</div>', unsafe_allow_html=True)
    if not df_vacation.empty and selected_user in df_vacation['성함'].values:
        u = df_vacation[df_vacation['성함'] == selected_user].iloc[0]
        v_rem = u.get('잔여연차', 0)
        st.success(f"🌟 {selected_user}님, 남은 휴가는 {v_rem}일입니다.")
    
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

st.caption("실버 복지 사업단 v3.7 | 라임 & 씨 테마")
