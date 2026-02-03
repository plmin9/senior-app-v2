import streamlit as st
import json
import gspread
from google.oauth2.service_account import Credentials

try:
    # Secrets에서 텍스트를 읽어와 진짜 JSON으로 변환
    raw_json = st.secrets["connections"]["gsheets"]["service_account_json"]
    info = json.loads(raw_json) # 여기서 에러가 나면 Secrets 형식이 틀린 것임
    
    creds = Credentials.from_service_account_info(info, scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ])
    client = gspread.authorize(creds)
    
    doc = client.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
    st.success(f"🎉 성공! [{doc.title}] 연결 완료")
except Exception as e:
    st.error(f"❌ 연결 실패: {e}")
