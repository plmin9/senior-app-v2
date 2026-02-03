import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("👵 노인일자리 출퇴근 관리")

try:
    s = st.secrets["connections"]
    
    # [강력 세척 로직]
    # 1. 모든 종류의 공백, 줄바꿈, 탭을 완전히 제거합니다.
    clean_body = "".join(s["key_body"].split())
    
    # 2. 구글이 인식할 수 있는 표준 PEM 형식으로 재조립합니다.
    # 이 과정에서 오타가 날 확률을 0%로 만듭니다.
    private_key = f"-----BEGIN PRIVATE KEY-----\n{clean_body}\n-----END PRIVATE KEY-----"

    creds_info = {
        "type": "service_account",
        "project_id": s["project_id"],
        "private_key": private_key,
        "client_email": s["email"],
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    
    # 3. 구글 인증 시도
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    
    # 4. 시트 열기
    doc = client.open_by_url(s["spreadsheet"])
    st.success(f"✅ [{doc.title}] 시트에 무사히 연결되었습니다!")
    
    sheet = doc.get_worksheet(0)
    st.dataframe(sheet.get_all_records())

except Exception as e:
    st.error("❌ 연결 중 오류가 발생했습니다.")
    st.info("파이썬이 키를 재조립하는 과정에서 문제가 생겼을 수 있습니다.")
    st.code(str(e))
