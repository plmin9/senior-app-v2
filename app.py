import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="노인일자리 출퇴근 관리", layout="wide")
st.title("👵 노인일자리 출퇴근 관리 시스템")

try:
    # 1. Secrets 데이터 가져오기
    s = st.secrets["connections"]
    
    # 2. [강력 정제 로직] 모든 공백을 제거하고 PEM 형식을 강제로 만듭니다.
    # 이렇게 하면 Secrets 설정창에서 줄이 어떻게 바뀌든 상관없이 작동합니다.
    body = "".join(s["key_raw"].split()) 
    formatted_key = "-----BEGIN PRIVATE KEY-----\n"
    for i in range(0, len(body), 64):
        formatted_key += body[i:i+64] + "\n"
    formatted_key += "-----END PRIVATE KEY-----"

    # 3. 구글 인증 정보 설정
    creds_info = {
        "type": "service_account",
        "project_id": s["project_id"],
        "private_key": formatted_key,
        "client_email": s["email"],
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    
    # 4. Google Sheets 연결
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    
    # 5. 시트 열기 및 데이터 표시
    doc = client.open_by_url(s["spreadsheet"])
    st.success(f"✅ [{doc.title}] 연결 성공!")
    
    sheet = doc.get_worksheet(0)
    data = sheet.get_all_records()
    
    if data:
        st.dataframe(data, use_container_width=True)
    else:
        st.info("데이터가 없습니다.")

except Exception as e:
    st.error("❌ 연결 오류가 발생했습니다.")
    st.code(str(e))
