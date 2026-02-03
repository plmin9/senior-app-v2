import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation

# --- 1. 페이지 설정 및 반응형 디자인 설정 ---
st.set_page_config(page_title="스마트경로당지원 근태관리", layout="wide")

# 반응형 CSS: 화면 크기에 따라 글자 크기와 간격이 자동으로 조절됩니다.
st.markdown("""
    <style>
    /* 공통 배경 */
    .stApp { background-color: #F0F4F8; } 
    
    /* 제목 스타일 (반응형) */
    .main-title { 
        font-size: clamp(1.5rem, 5vw, 2.5rem); 
        font-weight: 900; color: #1B5E20; text-align: center; margin-bottom: 2rem; 
    }
    
    /* 안내 헤더 (반응형) */
    .step-header {
        background-color: #FFFFFF; padding: 12px 18px; border-left: 8px solid #00838F;
        border-radius: 12px; font-size: clamp(1rem, 3vw, 1.5rem); font-weight: 800;
        color: #004D40; margin-top: 20px; margin-bottom: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    /* 탭 디자인 (모바일 고려 크기 조정) */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; padding: 8px; background-color: #CFD8DC; border-radius: 15px; }
    .stTabs [data-baseweb="tab"] { 
        flex: 1; height: clamp(50px, 8vw, 80px); 
        font-size: clamp(1rem, 3vw, 1.6rem) !important; font-weight: 900 !important; 
        border-radius: 12px !important; background-color: #ECEFF1; color: #455A64; 
    }
    .stTabs [aria-selected="true"] { background-color: #00838F !important; color: white !important; }

    /* 대형 버튼 (반응형 높이) */
    div.stButton > button { 
        border-radius: 20px; height: clamp(4rem, 10vw, 6.5rem) !important; 
        font-size: clamp(1.2rem, 4vw, 1.8rem) !important; font-weight: 900 !important; 
    }
    
    /* 현황판 컨테이너 (모바일에서 세로 정렬 대응) */
    .dashboard-container {
        background: white; padding: 25px; border-radius: 25px; border: 4px solid #00838F;
        display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap; gap: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    .stat-item { text-align: center; min-width: 100px; flex: 1; }

    /* 지도 및 위치 정보 */
    .map-container { border: 5px solid #004D40; border-radius: 20px; overflow: hidden; }
    .loc-info { 
        background-color: #E0F2F1; padding: 15px; border-radius: 15px; 
        border: 2px solid #00838F; font-size: 0.9rem;
    }
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
    except Exception: return None

client = get_gspread_client()
if client:
    s = st.secrets["connections"]["gsheets"]
    sheet_id = s["spreadsheet"].split("/d/")[1].split("/")[0]
    doc = client.open_by_key(sheet_id)
    sheet_attendance = doc.worksheet("근태기록")
    sheet_vacation = doc.worksheet("연차관리")
    df_vacation = pd.DataFrame(sheet_vacation.get_all_records())
else:
    st.error("구글 시트 연결에 실패했습니다. 설정을 확인해 주세요.")
    st.stop()

# --- 3. 유틸리티 함수 ---
def get_chosung(text):
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    if not text: return ""
    char_code = ord(str(text)[0]) - 0xAC00
    return CHOSUNG_LIST[char_code // 588] if 0 <= char_code <= 11171 else str(text)[0].upper()

if 'disp_start' not in st.session_state: st.session_state.disp_start = "-"
if 'disp_end' not in st.session_state: st.session_state.disp_end = "-"
if 'arrived' not in st.session_state: st.session_state.arrived = False

# --- 4. 위치 수집 ---
loc = get_geolocation()

# --- 5. 메인 화면 구성 ---
st.markdown('<div class="main-title">🏢 어르신 일자리 근태관리</div>', unsafe_allow_html=True)

# 단계 1: 초성 및 이름 선택
st.markdown('<div class="step-header">👤 본인 성함 선택 (필수)</div>', unsafe_allow_html=True)
cho = st.radio("초성", ["전체", "ㄱ","ㄴ","ㄷ","ㄹ","ㅁ","ㅂ","ㅅ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"], horizontal=True, label_visibility="collapsed")
all_names = df_vacation['성함'].tolist() if not df_vacation.empty else []
filtered_names = all_names if cho == "전체" else [n for n in all_names if get_chosung(n) == cho]

selected_user = st.selectbox("성함 선택", ["성함을 선택해 주세요"] + filtered_names if filtered_names else ["데이터 없음"], label_visibility="collapsed")

# 단계 2: 업무 선택
st.markdown('<div class="step-header">📝 오늘 수행 업무</div>', unsafe_allow_html=True)
work_options = ["경로당 청소", "배식 및 주방지원", "시설물 안전점검", "사무 업무 보조", "행사 지원", "기타 활동"]
selected_works = st.multiselect("업무 선택", work_options, placeholder="업무를 골라주세요")
work_detail = st.text_input("상세 내용", placeholder="기타 상세 내용을 적어주세요")
combined_work = f"[{', '.join(selected_works)}] {work_detail}".strip()

# 이름 선택 여부 체크
is_user_selected = (selected_user != "성함을 선택해 주세요" and selected_user != "데이터 없음")

st.write("<br>", unsafe_allow_html=True)

# --- 6. 탭 브라우징 ---
tab_attendance, tab_vacation = st.tabs(["🕒 출퇴근 체크", "🏖️ 휴가 확인"])

with tab_attendance:
    if not is_user_selected:
        st.warning("⚠️ 위에서 **성함을 먼저 선택**하셔야 출근/퇴근 버튼이 활성화됩니다.")

    # 실시간 출퇴근 현황판
    st.markdown(f"""
        <div class="dashboard-container">
            <div class="stat-item">
                <div style="font-size:1.1rem; color:#666;">☀️ 출근 시각</div>
                <div style="font-size:clamp(2rem, 6vw, 3.5rem); font-weight:900; color:#2E7D32;">{st.session_state.disp_start}</div>
            </div>
            <div style="font-size:2rem; color:#EEE; @media(max-width:600px){display:none;}">|</div>
            <div class="stat-item">
                <div style="font-size:1.1rem; color:#666;">🌙 퇴근 시각</div>
                <div style="font-size:clamp(2rem, 6vw, 3.5rem); font-weight:900; color:#C62828;">{st.session_state.disp_end}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("<br>", unsafe_allow_html=True)
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("🚀 출근하기", use_container_width=True, 
                     disabled=not is_user_selected or st.session_state.arrived or not loc):
            st.session_state.disp_start = datetime.now().strftime("%H:%M:%S")
            st.session_state.arrived = True
            lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
            sheet_attendance.append_row([selected_user, datetime.now().strftime("%Y-%m-%d"), st.session_state.disp_start, "", "출근", combined_work, lat, lon])
            st.rerun()
            
    with btn_col2:
        if st.button("🏠 퇴근하기", use_container_width=True, 
                     disabled=not is_user_selected or not st.session_state.arrived or st.session_state.disp_end != "-"):
            st.session_state.disp_end = datetime.now().strftime("%H:%M:%S")
            try:
                all_records = sheet_attendance.get_all_values()
                today_str = datetime.now().strftime("%Y-%m-%d")
                target_row = next((i+1 for i, r in enumerate(all_records) if r[0]==selected_user and r[1]==today_str and r[4]=="출근"), -1)
                if target_row != -1:
                    sheet_attendance.update_cell(target_row, 4, st.session_state.disp_end)
                    sheet_attendance.update_cell(target_row, 5, "퇴근")
                    sheet_attendance.update_cell(target_row, 6, combined_work)
                    st.success("퇴근 확인되었습니다!")
            except Exception as e: st.error(f"오류: {e}")
            st.balloons()
            st.rerun()

    # 위치 정보 및 지도
    st.markdown('<div class="step-header">📍 위치 인증 및 지도</div>', unsafe_allow_html=True)
    if loc:
        m_col1, m_col2 = st.columns([2.5, 1])
        with m_col1:
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            df_map = pd.DataFrame([{'latitude': loc['coords']['latitude'], 'longitude': loc['coords']['longitude']}])
            st.map(df_map, zoom=16, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with m_col2:
            st.markdown(f"""
                <div class="loc-info">
                    <b style="color:#004D40;">[위치 수신 상태: 정상]</b><br><br>
                    위도: <b>{loc['coords']['latitude']:.6f}</b><br>
                    경도: <b>{loc['coords']['longitude']:.6f}</b><br><br>
                    <small>※ 지도에 표시된 위치가 본인의 현재 위치입니다.</small>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📍 위치 신호를 확인하고 있습니다. 잠시만 기다려 주세요...")

with tab_vacation:
    if is_user_selected:
        u = df_vacation[df_vacation['성함'] == selected_user].iloc[0]
        try:
            total = int(pd.to_numeric(u.get('총연차', 0), errors='coerce'))
            used = int(pd.to_numeric(u.get('사용연차', 0), errors='coerce'))
            # 잔여연차가 비어있으면 앱에서 직접 계산
            remain_val = pd.to_numeric(u.get('잔여연차', 0), errors='coerce')
            remain = int(remain_val) if pd.notnull(remain_val) else (total - used)
        except: total, used, remain = 0, 0, 0
        
        percent = (remain / total) if total > 0 else 0

        st.markdown(f"""
            <div style="background: white; padding: 30px; border-radius: 25px; border: 3px solid #E0E0E0; text-align: center;">
                <div style="font-size: 1.8rem; font-weight: 800; color: #1B5E20; margin-bottom: 25px;">🏖️ {selected_user} 어르신 휴가 현황</div>
                <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 10px;">
                    <div class="stat-item"><div style="color: #666;">전체 휴가</div><div style="font-size: 2rem; font-weight: 800;">{total}일</div></div>
                    <div class="stat-item"><div style="color: #666;">사용한 휴가</div><div style="font-size: 2rem; font-weight: 800; color: #C62828;">{used}일</div></div>
                    <div class="stat-item"><div style="color: #666;">남은 휴가</div><div style="font-size: 2rem; font-weight: 800; color: #2E7D32;">{remain}일</div></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.write("<br>", unsafe_allow_html=True)
        st.markdown(f"**📉 휴가 잔여량 ({int(percent*100)}%)**")
        st.progress(percent)
    else:
        st.warning("⚠️ 성함을 먼저 선택해 주세요.")

st.caption("실버 복지 사업단 v5.6 | 반응형 통합 레이아웃")
