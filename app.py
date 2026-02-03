import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="노인일자리 관리", layout="wide")
st.title("👵 노인일자리 출퇴근 시스템")

try:
    s = st.secrets["connections"]
    
    # [가장 안전한 직접 주입 방식]
    # 줄바꿈(\n) 문제를 해결하기 위해 코드가 직접 줄바꿈을 붙여줍니다.
    raw_key = s["private_key"].replace(" ", "").strip()
    formatted_key = "-----BEGIN PRIVATE KEY-----\n"
    for i in range(0, len(raw_key), 64):
        formatted_key += raw_key[i:i+64] + "\n"
    formatted_key += "-----END PRIVATE KEY-----\n"

    creds_info = {
        "type": "service_account",
        "project_id": s["project_id"],
        "private_key": formatted_key,
        "client_email": s["client_email"],
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    
    doc = client.open_by_url(s["spreadsheet"])
    st.success(f"✅ [{doc.title}] 연결 성공!")
    
    sheet = doc.get_worksheet(0)
    st.dataframe(sheet.get_all_records(), use_container_width=True)

except Exception as e:
    st.error("❌ 연결 오류 발생")
    st.code(str(e))
