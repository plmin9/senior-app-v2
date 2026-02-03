import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation

# --- 1. 페이지 기본 설정 ---
st.set_page_config(page_title="스마트 근태관리 시스템", layout="wide")

# --- 2. CSS 스타일링 (다우오피스 스타일) ---
st.markdown("""
    <style>
    .main-title { font-size: 32px; font-weight: bold; color: #1E3A8A; margin-bottom: 5px; }
    .business-unit { font-size: 20px; color: #64748B; margin-bottom: 25px; }
    .status-box { background-color: #F8FAFC; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #E2E8F0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .time-text { font-size: 30px; font-weight: bold; color: #2563EB; }
    .stat-label { font-size: 16px; color: #64748B; font-weight: 600; }
    .vacation-section { background-color: #FFFFFF; padding: 20px; border-radius: 15px; border: 1px solid #E5E7EB; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 구글 시트 연결 함수 ---
@st.cache_resource
def get_gspread_client():
    try:
        s = st.secrets["connections"]["gsheets"]
        creds_info = {
            "type": "service_account",
            "project_id": s["project_id"],
            "private_key": s["private_key"].replace("\\n", "\n"),
            "client_email": s["service_account_email"],
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        creds = Credentials.from_service_account_info(creds_info, scopes=[
            "https://www.googleapis.com/auth/spreadsheets", 
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(creds)
    except Exception as e:
        st.error("구글 시트 인증 정보가 올바르지 않습니다.")
        return None

# 데이터 로드
client = get_gspread_client()
if client:
    try:
        s = st.secrets["connections"]["gsheets"]
        sheet_id = s["spreadsheet"].split("/d/")[1].split("/")[0]
        doc = client.open_by_key(sheet_id)
        
        # 각 시트 탭 연결
        sheet_attendance = doc.worksheet("근태기록")
        sheet_vacation = doc.worksheet("연차관리")
        sheet_notice = doc.worksheet("공지사항")
        
        # 데이터프레임 변환
        df_vacation = pd.DataFrame(sheet_vacation.get_all_records())
        df_notice = pd.DataFrame(sheet_notice.get_all_records())
    except Exception as e:
        st.error(f"시트 로드 오류: {e}")
        st.stop()
else:
    st.stop()

# --- 4. 한글 초성 추출 로직 ---
def get_chosung(text):
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    if not text: return ""
    first_char = text[0]
    if '가' <= first_char <= '힣':
        char_code = ord(first_char) - 0xAC00
        return CHOSUNG_LIST[char_code // 588]
    return first_char.upper()

# --- 5. 상단 헤더 ---
st.markdown('<div class="main-title">📊 근태현황</div>', unsafe_allow_html=True)
st.markdown('<div class="business-unit">🏢 실버 복지 사업단</div>', unsafe_allow_html=True)

now = datetime.now()
st.info(f"📅 **현재 정보:** {now.strftime('%Y년 %m월 %d일 %H:%M:%S')}")

# --- 6. 사용자 선택 (초성 필터링) ---
st.subheader("👤 본인 확인")
cho_list = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
selected_cho = st.radio("성씨 초성 선택", cho_list, horizontal=True)

all_names = df_vacation['성함'].tolist() if not df_vacation.empty else []
if selected_cho == "전체":
    filtered_names = all_names
else:
    filtered_names = [name for name in all_names if get_chosung(str(name)) == selected_cho]

selected_user = st.selectbox("성함을 선택하세요", filtered_names if filtered_names else ["검색 결과 없음"])

st.divider()

# --- 7. GPS 및 지도 섹션 ---
st.subheader("📍 위치 인증 및 출퇴근")
loc = get_geolocation()
col_map, col_btns = st.columns([2, 1])

with col_map:
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
    else:
        st.warning("위치 권한을 허용하면 지도가 나타나며 출근이 가능해집니다.")

# 출퇴근 세션 상태 관리
if 'arrived' not in st.session_state: st.session_state.arrived = False
if 'start_time' not in st.session_state: st.session_state.start_time = "--:--"

with col_btns:
    st.markdown(f'<div class="status-box"><span class="stat-label">출근 시간</span><br><span class="time-text">{st.session_state.start_time}</span></div>', unsafe_allow_html=True)
    st.write("")
    
    work_mode = st.selectbox("📝 업무 내용 선택", ["행정지원", "현장관리", "상담업무", "생활지원", "기타"])
    
    # 출근 버튼 (GPS 필수)
    gps_ready = True if loc else False
    if st.button("🚀 출근하기", use_container_width=True, disabled=st.session_state.arrived or not gps_ready):
        st.session_state.arrived = True
        st.session_state.start_time = datetime.now().strftime("%H:%M")
        sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), st.session_state.start_time, "", "출근", work_mode, lat, lon])
        st.success("출근 기록 완료!")
        st.rerun()

    # 퇴근 버튼
    if st.button("🏠 퇴근하기", use_container_width=True, disabled=not st.session_state.arrived):
        end_time = datetime.now().strftime("%H:%M")
        sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), "", end_time, "퇴근", work_mode, "", ""])
        st.session_state.arrived = False
        st.session_state.start_time = "--:--"
        st.success("퇴근 처리되었습니다. 수고하셨습니다!")
        st.rerun()

st.divider()

# --- 8. 연차 및 근로 정보 섹션 ---
st.subheader("🏖️ 연차 및 근로 정보")
if not df_vacation.empty and selected_user in df_vacation['성함'].values:
    user_data = df_vacation[df_vacation['성함'] == selected_user].iloc[0]
    
    try:
        v_total = float(user_data['총연차'])
        v_used = float(user_data['사용연차'])
        v_remain = float(user_data['잔여연차'])
        work_hour = user_data.get('소정근로시간', 0)
    except:
        v_total, v_used, v_remain, work_hour = 0, 0, 0, 0
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="status-box"><span class="stat-label">총 연차</span><br><b>{int(v_total)}일</b></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="status-box"><span class="stat-label">사용 연차</span><br><b>{int(v_used)}일</b></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="status-box"><span class="stat-label">잔여 연차</span><br><b>{int(v_remain)}일</b></div>', unsafe_allow_html=True)
    
    st.write("📊 **연차 사용 현황**")
    progress_val = min(v_used / v_total, 1.0) if v_total > 0 else 0.0
    st.progress(progress_val)
    st.caption(f"🌴 전체 연차의 {int(progress_val * 100)}%를 사용하셨습니다. (총 근로시간: {work_hour}시간)")

# 연차 신청 팝업
if st.button("➕ 연차 신청하기"):
    @st.dialog("연차/휴가 신청서")
    def vacation_form():
        d = st.date_input("휴가 날짜 선택", now)
        t = st.selectbox("신청 항목", ["연차", "오전반차", "오후반차", "경조사", "병가"])
        reason = st.text_input("상세 사유")
        if st.button("제출하기"):
            sheet_attendance.append_row([selected_user, d.strftime("%Y-%m-%d"), "", "", t, reason, "", ""])
            st.success("신청서가 제출되었습니다.")
            st.rerun()
    vacation_form()

st.divider()

# --- 9. 기록 검색 및 알림 섹션 ---
col_search, col_notice = st.columns([2, 1])

with col_search:
    st.subheader("🔍 기록 조회")
    tab_week, tab_month, tab_cal = st.tabs(["주간 현황", "월간 현황", "📅 캘린더"])
    with tab_week:
        st.write("최근 기록은 구글 시트에서 실시간 업데이트 됩니다.")
        # 간단한 최근 기록 노출 (성함 필터링)
        try:
            all_att = pd.DataFrame(sheet_attendance.get_all_records())
            user_att = all_att[all_att['성함'] == selected_user].tail(5)
            st.table(user_att[['날짜', '출근시간', '퇴근시간', '상태']])
        except:
            st.write("기록이 없습니다.")

with col_notice:
    st.subheader("🔔 중요 알림")
    if not df_notice.empty:
        for idx, row in df_notice.iterrows():
            with st.expander(f"{row['날짜']} | {row['제목']}"):
                st.write(row['세부내용'])
    else:
        st.write("현재 공지사항이 없습니다.")

# --- 하단 정보 ---
st.caption("Copyright © 2024 실버 복지 사업단 근태관리 시스템 v2.0")
