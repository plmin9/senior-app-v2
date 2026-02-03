import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="노인일자리 관리", layout="wide")
st.title("👵 노인일자리 출퇴근 관리 시스템")

try:
    # 1. Secrets에서 정보 가져오기
    # [connections.gsheets] 섹션을 사용합니다.
    s = st.secrets["connections"]["gsheets"]
    
    # 2. 인증 설정 (줄바꿈 \n을 실제 줄바꿈으로 변환)
    creds_info = {
        "type": "service_account",
        "project_id": s["project_id"],
        "private_key": s["private_key"].replace("\\n", "\n"),
        "client_email": s["service_account_email"],
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    
    # 3. [핵심] URL 전체가 아니라 시트 'ID'만 추출해서 접속합니다. (404 방지)
    # URL에서 d/ 와 /edit 사이의 문자열만 가져옵니다.
    sheet_url = s["spreadsheet"]
    sheet_id = sheet_url.split("/d/")[1].split("/")[0]
    
    doc = client.open_by_key(sheet_id)
    sheet = doc.get_worksheet(0) # 첫 번째 탭 선택
    
    data = sheet.get_all_records()
    
    if data:
        st.success(f"✅ [{doc.title}] 데이터를 불러왔습니다!")
        st.dataframe(data, use_container_width=True)
    else:
        st.info("시트에 데이터가 없습니다.")

except Exception as e:
    st.error("❌ 연결 오류가 발생했습니다.")
    st.code(str(e))
