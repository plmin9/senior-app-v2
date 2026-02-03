import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json

st.set_page_config(page_title="노인일자리 관리", layout="wide")
st.title("👵 노인일자리 출퇴근 시스템")

try:
    # 1. Secrets에서 JSON 덩어리를 가져옵니다.
    s = st.secrets["connections"]
    
    # 2. JSON 텍스트를 파이썬 사전 형식으로 변환합니다.
    # 이 방식은 PEM 파일을 직접 다루지 않아 형식이 깨질 위험이 없습니다.
    info = json.loads(s["gcp_service_account"])
    
    # 3. 인증 및 연결
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    client = gspread.authorize(creds)
    
    # 4. 시트 열기
    doc = client.open_by_url(s["spreadsheet"])
    st.success(f"✅ [{doc.title}] 연결 성공!")
    
    sheet = doc.get_worksheet(0)
    st.dataframe(sheet.get_all_records(), use_container_width=True)

except Exception as e:
    st.error("❌ 시스템 연결 중 오류가 발생했습니다.")
    st.code(str(e))
