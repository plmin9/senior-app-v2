import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("👵 노인일자리 출퇴근 관리")

try:
    # 1. Secrets에서 'key_raw'라는 이름으로 데이터를 가져옵니다.
    s = st.secrets["connections"]
    body = s["key_raw"].strip()
    
    # 2. [PEM 규격 강제 생성] 라이브러리가 거부하지 못하도록 64자마다 줄바꿈을 넣습니다.
    formatted_key = "-----BEGIN PRIVATE KEY-----\n"
    for i in range(0, len(body), 64):
        formatted_key += body[i:i+64] + "\n"
    formatted_key += "-----END PRIVATE KEY-----"

    # 3. 인증 정보 구성
    creds_info = {
        "type": "service_account",
        "project_id": s["project_id"],
        "private_key": formatted_key,
        "client_email": s["email"],
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    
    # 4. 권한 설정 및 연결
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    
    # 5. 시트 열기
    doc = client.open_by_url(s["spreadsheet"])
    st.success(f"🎉 [{doc.title}] 연결 성공!")
    
    sheet = doc.get_worksheet(0)
    st.dataframe(sheet.get_all_records())

except Exception as e:
    st.error("❌ 연결 중 문제가 발생했습니다.")
    st.code(str(e))
