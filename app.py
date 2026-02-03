import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. 화면 시작 확인
st.set_page_config(page_title="출퇴근 시스템 테스트")
st.title("👵 시스템 접속 시도 중...")

# 2. 인증 시도
try:
    st.info("🔄 1단계: Secrets 정보를 읽어오는 중입니다.")
    s = st.secrets["connections"]["gsheets"]
    
    # 비밀키 정제
    p_key = s["private_key"].replace("\\n", "\n")
    
    creds_info = {
        "type": s["type"],
        "project_id": s["project_id"],
        "private_key_id": s["private_key_id"],
        "private_key": p_key,
        "client_email": s["client_email"],
        "client_id": s["client_id"],
        "auth_uri": s["auth_uri"],
        "token_uri": s["token_uri"],
        "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
        "client_x509_cert_url": s["client_x509_cert_url"]
    }
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    st.success("✅ 2단계: 구글 서버 인증에 성공했습니다!")

    # 3. 시트 열기 시도
    st.info("🔄 3단계: 구글 시트 파일을 여는 중입니다.")
    sheet_url = s["spreadsheet"]
    doc = client.open_by_url(sheet_url)
    st.success(f"✅ 4단계: [{doc.title}] 파일 연결 성공!")

    # 4. 데이터 표시
    sheet = doc.get_worksheet(0)
    data = sheet.get_all_records()
    
    if data:
        st.write("📋 아래는 시트에서 불러온 명단입니다:")
        st.table(pd.DataFrame(data).head())
    else:
        st.warning("⚠️ 시트 연결은 됐으나 데이터가 비어있습니다.")

except Exception as e:
    st.error(f"❌ 오류 발생 지점: {e}")
    st.info("💡 위 오류 메시지를 확인하여 알려주세요.")
