import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="스마트경로당지원 근태관리", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F7F9FB; } 
    .main-title { font-size: 1.8rem; font-weight: 800; color: #2E7D32; text-align: center; margin-bottom: 1rem; }
    .custom-label { font-size: 1.15rem; font-weight: 800; color: #333; margin-bottom: 0.5rem; margin-top: 1rem; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: none !important; }
    .stTabs [data-baseweb="tab"] { flex: 1; height: 55px; font-size: 1.2rem !important; font-weight: 800 !important; border-radius: 12px 12px 0 0; border: none !important; }
    .stTabs [id^="tabs-b-tab"] { background-color: #E0F2F1 !important; color: #00796B !important; }
    .stTabs [aria-selected="true"] { background-color: #00838F !important; color: white !important; }
    .stTabs [data-baseweb="tab-highlight"] { background-color: #00838F !important; height: 4px !important; }

    div.stButton > button { 
        border-radius: 15px; height: 5rem !important; font-size: 1.5rem !important; 
        font-weight: 800 !important; background-color: #4CAF50 !important; color: white !important;
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
    }
    div.stButton > button:disabled { background-color: #E0E0E0 !important; color: #9E9E9E !important; box-shadow: none !important; }
    .map-outline-box { border: 4px solid #004D40; border-radius: 15px; overflow: hidden; box-shadow: 0 8px 20px rgba(0,0,0,0.15); }
    </style>
""", unsafe_allow_html=True)

# --- 2. 구글 시트 연결 ---
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

# --- 3. 유틸리티 함수 ---
def get_chosung(text):
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    if not text: return ""
    char_code = ord(str(text)[0]) - 0xAC00
    return CHOSUNG_LIST[char_code // 588] if 0 <= char_code <= 11171 else str(text)[0].upper()

# --- 4. 세션 상태 ---
if 'disp_start' not in st.session_state: st.session_state.disp_start = "-"
if 'disp_end' not in st.session_state: st.session_state.disp_end = "-"
if 'arrived' not in st.session_state: st.session_state.arrived = False

# --- 5. 메인 화면 ---
st.markdown('<div class="main-title">🏢 스마트경로당지원 근태관리</div>', unsafe_allow_html=True)

# 초성 및 성함 선택
cho = st.radio("초성 선택", ["전체", "ㄱ","ㄴ","ㄷ","ㄹ","ㅁ","ㅂ","ㅅ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"], horizontal=True)
all_names = df_vacation['성함'].tolist() if not df_vacation.empty else []
filtered_names = all_names if cho == "전체" else [n for n in all_names if get_chosung(n) == cho]
selected_user = st.selectbox("본인 성함을 선택하세요", filtered_names if filtered_names else ["데이터 없음"])

# 업무 선택 및 입력 (이제 출근 시 필수가 아님)
st.markdown('<div class="custom-label">📝 수행 업무 선택 및 상세내용 입력 (퇴근 전까지 입력 가능)</div>', unsafe_allow_html=True)
work_options = ["경로당 청소", "배식 및 주방지원", "시설물 안전점검", "사무 업무 보조", "행사 지원", "기타 활동"]
selected_works = st.multiselect("업무 선택", work_options, placeholder="업무를 골라주세요")
work_detail = st.text_input("상세 업무 입력", placeholder="상세 내용을 적어주세요")
combined_work = f"[{', '.join(selected_works)}] {work_detail}".strip()

st.write("<br>", unsafe_allow_html=True)

# --- 6. 탭 구성 ---
tab_attendance, tab_vacation = st.tabs(["🕒 근태관리", "🏖️ 휴가관리"])

with tab_attendance:
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    
    st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 20px; border: 2px solid #00838F; text-align: center; margin-bottom: 20px;">
            <div style="display:flex; justify-content:space-around; align-items:center;">
                <div><div style="font-size:0.9rem; color:#888;">출근 시간</div><div style="font-size:2.5rem; font-weight:900; color:#2E7D32;">{st.session_state.disp_start}</div></div>
                <div style="font-size:2.5rem; color:#00838F; font-weight:200;">|</div>
                <div><div style="font-size:0.9rem; color:#888;">퇴근 시간</div><div style="font-size:2.5rem; font-weight:900; color:#2E7D32;">{st.session_state.disp_end}</div></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    loc = get_geolocation()
    col1, col2 = st.columns(2)
    
    with col1:
        # 출근 시: 업무 내용이 비어있어도 즉시 등록
        if st.button("🚀 출근하기", use_container_width=True, disabled=st.session_state.arrived or not loc):
            st.session_state.disp_start = datetime.now().strftime("%H:%M:%S")
            st.session_state.arrived = True
            lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
            
            # 초기 등록 시 combined_work가 비어있어도 그대로 등록 (나중에 퇴근 시 업데이트)
            sheet_attendance.append_row([selected_user, today_date, st.session_state.disp_start, "", "출근", combined_work, lat, lon])
            st.rerun()
            
    with col2:
        # 퇴근 시: 퇴근 시간 기록 + 현재 입력된 업무 내용으로 업데이트
        if st.button("🏠 퇴근하기", use_container_width=True, disabled=not st.session_state.arrived or st.session_state.disp_end != "-"):
            st.session_state.disp_end = datetime.now().strftime("%H:%M:%S")
            try:
                all_records = sheet_attendance.get_all_values()
                target_row = -1
                for idx, row in enumerate(all_records):
                    if row[0] == selected_user and row[1] == today_date and row[4] == "출근":
                        target_row = idx + 1
                
                if target_row != -1:
                    # 퇴근 시간(4열), 상태(5열), 그리고 업무내용(6열)을 현재 입력값으로 최종 업데이트
                    sheet_attendance.update_cell(target_row, 4, st.session_state.disp_end)
                    sheet_attendance.update_cell(target_row, 5, "퇴근")
                    sheet_attendance.update_cell(target_row, 6, combined_work) # 최종 업무내용 반영
                    st.success("퇴근 시간과 업무 내용이 모두 저장되었습니다!")
                else:
                    sheet_attendance.append_row([selected_user, today_date, "", st.session_state.disp_end, "퇴근", combined_work, "", ""])
            except Exception as e:
                st.error(f"오류: {e}")
            st.balloons()
            st.rerun()

    st.divider()
    # 지도 영역 생략 (기존 디자인 유지)
