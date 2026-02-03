import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation

# --- 1. 페이지 기본 설정 ---
st.set_page_config(page_title="스마트 근태관리 시스템", layout="wide")

# --- 2. CSS 스타일링 (대형 폰트 및 다우오피스 스타일) ---
st.markdown("""
    <style>
    /* 전체 배경 및 폰트 */
    .main { background-color: #F9FAFB; }
    .main-title { font-size: 38px !important; font-weight: bold; color: #1E3A8A; margin-bottom: 5px; }
    .business-unit { font-size: 24px; color: #64748B; margin-bottom: 25px; }
    
    /* 박스형 디자인 */
    .status-box { background-color: #FFFFFF; padding: 25px; border-radius: 15px; text-align: center; border: 1px solid #E2E8F0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .time-text { font-size: 36px; font-weight: bold; color: #2563EB; }
    .stat-label { font-size: 20px; color: #64748B; font-weight: 600; }
    
    /* 안내 문구 대형화 */
    .big-info-text { font-size: 26px !important; font-weight: bold; color: #1E40AF; margin-top: 15px; margin-bottom: 10px; }
    .filter-info { font-size: 22px !important; color: #059669; font-weight: bold; padding: 10px 0; }
    
    /* 성함 선택박스 글자 크기 극대화 */
    div[data-baseweb="select"] > div {
        font-size: 28px !important;
        height: 75px !important;
        display: flex;
        align-items: center;
    }
    
    /* 버튼 폰트 크기 */
    .stButton>button {
        font-size: 22px !important;
        font-weight: bold !important;
        padding: 12px 0px !important;
    }
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
        st.error(f"구글 시트 인증 정보 오류: {e}")
        return None

client = get_gspread_client()
if client:
    try:
        s = st.secrets["connections"]["gsheets"]
        sheet_id = s["spreadsheet"].split("/d/")[1].split("/")[0]
        doc = client.open_by_key(sheet_id)
        sheet_attendance = doc.worksheet("근태기록")
        sheet_vacation = doc.worksheet("연차관리")
        sheet_notice = doc.worksheet("공지사항")
        df_vacation = pd.DataFrame(sheet_vacation.get_all_records())
        df_notice = pd.DataFrame(sheet_notice.get_all_records())
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        st.stop()
else:
    st.stop()

# --- 4. 한글 초성 추출 로직 ---
def get_chosung(text):
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    if not text: return ""
    first_char = str(text)[0]
    if '가' <= first_char <= '힣':
        char_code = ord(first_char) - 0xAC00
        return CHOSUNG_LIST[char_code // 588]
    return first_char.upper()

# --- 5. 상단 헤더 ---
st.markdown('<div class="main-title">📊 근태현황</div>', unsafe_allow_html=True)
st.markdown('<div class="business-unit">🏢 실버 복지 사업단</div>', unsafe_allow_html=True)

now = datetime.now()
st.info(f"📅 **현재 정보:** {now.strftime('%Y년 %m월 %d일 %H:%M:%S')}")

st.divider()

# --- 6. 본인 확인 (대형 박스형 초성 버튼) ---
st.markdown('<div class="big-info-text">👤 본인 확인 (성씨 초성을 선택하세요)</div>', unsafe_allow_html=True)
cho_list = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]

if 'selected_cho' not in st.session_state:
    st.session_state.selected_cho = "전체"

rows = [cho_list[i:i + 5] for i in range(0, len(cho_list), 5)]
for row in rows:
    cols = st.columns(5)
    for idx, cho in enumerate(row):
        if cols[idx].button(cho, use_container_width=True, key=f"btn_{cho}"):
            st.session_state.selected_cho = cho
            st.rerun()

# 필터 적용 안내 문구 대형화
st.markdown(f'<div class="filter-info">✅ 현재 \'{st.session_state.selected_cho}\' 필터가 적용 중입니다.</div>', unsafe_allow_html=True)

# 이름 필터링 및 대형 선택창
all_names = df_vacation['성함'].tolist() if not df_vacation.empty else []
if st.session_state.selected_cho == "전체":
    filtered_names = all_names
else:
    filtered_names = [name for name in all_names if get_chosung(name) == st.session_state.selected_cho]

# 성함 선택 안내 문구 대형화
st.markdown('<div class="big-info-text">👇 아래에서 본인의 성함을 선택하세요</div>', unsafe_allow_html=True)
selected_user = st.selectbox("", filtered_names if filtered_names else ["해당 없음"], label_visibility="collapsed")

st.divider()

# --- 7. GPS 및 출퇴근 ---
st.subheader("📍 위치 인증 및 출퇴근")
loc = get_geolocation()
col_map, col_btns = st.columns([2, 1])

if 'arrived' not in st.session_state: st.session_state.arrived = False
if 'start_time' not in st.session_state: st.session_state.start_time = "--:--"

with col_map:
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
    else:
        st.warning("위치 권한을 허용해 주세요. 지도가 나타나야 출근 버튼이 작동합니다.")

with col_btns:
    st.markdown(f'<div class="status-box"><span class="stat-label">출근 시간</span><br><span class="time-text">{st.session_state.start_time}</span></div>', unsafe_allow_html=True)
    st.write("")
    work_mode = st.selectbox("📝 업무 내용", ["행정지원", "현장관리", "상담업무", "생활지원", "기타"], key="work_mode")
    
    gps_ready = True if loc else False
    if st.button("🚀 출근하기", use_container_width=True, disabled=st.session_state.arrived or not gps_ready):
        st.session_state.arrived = True
        st.session_state.start_time = datetime.now().strftime("%H:%M")
        sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), st.session_state.start_time, "", "출근", work_mode, lat, lon])
        st.success("✅ 출근 완료!")
        st.rerun()

    if st.button("🏠 퇴근하기", use_container_width=True, disabled=not st.session_state.arrived):
        end_time = datetime.now().strftime("%H:%M")
        sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), "", end_time, "퇴근", work_mode, "", ""])
        st.session_state.arrived = False
        st.session_state.start_time = "--:--"
        st.success("✅ 퇴근 완료! 고생하셨습니다.")
        st.rerun()

st.divider()

# --- 8. 연차 정보 ---
st.subheader("🏖️ 연차 사용 및 근로 정보")
if not df_vacation.empty and selected_user in df_vacation['성함'].values:
    u_data = df_vacation[df_vacation['성함'] == selected_user].iloc[0]
    try:
        total_v = float(u_data['총연차'])
        used_v = float(u_data['사용연차'])
        rem_v = float(u_data['잔여연차'])
    except:
        total_v, used_v, rem_v = 0, 0, 0
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="status-box"><span class="stat-label">총 연차</span><br><b>{int(total_v)}일</b></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="status-box"><span class="stat-label">사용 연차</span><br><b>{int(used_v)}일</b></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="status-box"><span class="stat-label">잔여 연차</span><br><b>{int(rem_v)}일</b></div>', unsafe_allow_html=True)
    
    prog = min(used_v / total_v, 1.0) if total_v > 0 else 0.0
    st.write("📈 **연차 사용 현황**")
    st.progress(prog)

if st.button("➕ 연차/휴가 신청하기"):
    @st.dialog("휴가 신청 팝업")
    def show_v_form():
        v_date = st.date_input("날짜 선택")
        v_type = st.selectbox("유형", ["연차", "반차", "병가", "경조사"])
        v_reason = st.text_input("사유")
        if st.button("제출"):
            sheet_attendance.append_row([selected_user, v_date.strftime("%Y-%m-%d"), "", "", v_type, v_reason])
            st.success("신청 완료!")
            st.rerun()
    show_v_form()

st.divider()

# --- 9. 알림 및 기록 검색 ---
col_rec, col_noti = st.columns([2, 1])
with col_rec:
    st.subheader("🔍 최근 나의 기록")
    try:
        all_att = pd.DataFrame(sheet_attendance.get_all_records())
        my_att = all_att[all_att['성함'] == selected_user].tail(5)
        st.table(my_att[['날짜', '출근시간', '퇴근시간', '상태']])
    except:
        st.write("표시할 기록이 없습니다.")

with col_noti:
    st.subheader("🔔 중요 공지")
    if not df_notice.empty:
        for _, n_row in df_notice.iterrows():
            with st.expander(f"{n_row['날짜']} | {n_row['제목']}") (expanded=True):
                st.write(n_row['세부내용'])

st.caption("실버 복지 사업단 근태관리 시스템 v2.6")
