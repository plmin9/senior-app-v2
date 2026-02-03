import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import base64

st.set_page_config(page_title="노인일자리 관리", layout="wide")
st.title("👵 노인일자리 출퇴근 시스템")

try:
    s = st.secrets["connections"]
    
    # [Base64 해독 로직]
    # Secrets에 저장된 알파벳 덩어리를 다시 원래의 키 형식으로 복구합니다.
    encoded_key = s["key_base64"]
    decoded_key = base64.b64decode(encoded_key).decode("utf-8")

    creds_info = {
        "type": "service_account",
        "project_id": s["project_id"],
        "private_key": decoded_key,
        "client_email": s["email"],
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
    st.error("❌ 시스템 연결 중 오류")
    st.code(str(e))
