import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("👵 노인일자리 출퇴근 시스템")

try:
    s = st.secrets["connections"]
    
    # [자동 청소 로직] 
    # 1. 앞뒤 공백 제거 
    # 2. 줄바꿈(\n) 문자가 텍스트로 섞여있다면 실제 줄바꿈으로 변환
    raw_key = s["private_key"].strip()
    clean_key = raw_key.replace("\\n", "\n")

    creds_info = {
        "type": "service_account",
        "project_id": "senior-work-486210",
        "private_key": clean_key,
        "client_email": s["email"],
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    
    creds = Credentials.from_service_account_info(creds_info, scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ])
    client = gspread.authorize(creds)
    
    doc = client.open_by_url(s["spreadsheet"])
    st.success(f"🎉 [{doc.title}] 연결 성공!")
    
    sheet = doc.get_worksheet(0)
    st.dataframe(sheet.get_all_records())

except Exception as e:
    st.error(f"❌ 접속 오류: {e}")
