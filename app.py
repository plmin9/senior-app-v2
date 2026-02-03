import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import re

st.set_page_config(page_title="노인일자리 출퇴근 관리", layout="wide")
st.title("👵 노인일자리 출퇴근 관리 시스템")

try:
    s = st.secrets["connections"]
    
    # [초강력 세척 로직]
    # 1. 관리자님이 어떻게 붙여넣든, 영어/숫자/더하기(+)/슬래시(/)/등호(=)만 남기고 싹 지웁니다.
    # 이 과정에서 눈에 안 보이는 줄바꿈, 공백, 특수문자가 100% 제거됩니다.
    raw_content = s["key_pure"]
    clean_body = re.sub(r'[^A-Za-z0-9+/=]', '', raw_content)
    
    # 2. 구글이 원하는 완벽한 PEM 형식으로 재조립 (64자마다 줄바꿈 추가)
    formatted_key = "-----BEGIN PRIVATE KEY-----\n"
    for i in range(0, len(clean_body), 64):
        formatted_key += clean_body[i:i+64] + "\n"
    formatted_key += "-----END PRIVATE KEY-----\n"

    # 3. 인증 정보 설정
    creds_info = {
        "type": "service_account",
        "project_id": s["project_id"],
        "private_key": formatted_key,
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
    st.error("❌ 연결 오류가 발생했습니다.")
    st.info("비밀번호(Secrets) 설정에서 'key_pure' 값이 정확한지 확인해 주세요.")
    st.code(str(e))
