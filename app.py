import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# [필수] set_page_config는 반드시 코드의 최상단에 와야 합니다.
st.set_page_config(page_title="노인일자리 출퇴근 시스템", layout="centered")

st.title("👵 노인일자리 시스템 접속")

# 진단 메시지 출력용 함수
def log_step(msg, success=True):
    if success:
        st.write(f"✅ {msg}")
    else:
        st.error(f"❌ {msg}")

try:
    log_step("시스템 시작")
    
    # 1. Secrets 읽기
    if "connections" not in st.secrets:
        st.error("Secrets 설정에 'connections' 섹션이 없습니다.")
        st.stop()
        
    s = st.secrets["connections"]["gsheets"]
    log_step("Secrets 로드 완료")

    # 2. 키 교정 및 인증
    p_key = s["private_key"].replace("\\n", "\n").strip()
    if not p_key.endswith("\n"):
        p_key += "\n"

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
    log_step("구글 서버 인증 성공")

    # 3. 시트 열기
    sheet_url = s["spreadsheet"]
    doc = client.open_by_url(sheet_url)
    log_step(f"시트 연결 성공: {doc.title}")

    # 4. 데이터 로드 및 표시
    sheet = doc.get_worksheet(0)
    records = sheet.get_all_records()
    
    if records:
        df = pd.DataFrame(records)
        st.success("🎉 데이터를 성공적으로 불러왔습니다!")
        st.dataframe(df) # 데이터를 표 형태로 즉시 표시
    else:
        st.warning("⚠️ 시트에 데이터가 비어 있습니다.")

except Exception as e:
    st.error(f"⚠️ 실행 중 오류 발생: {e}")
    # 상세 에러 로그 출력
    import traceback
    st.code(traceback.format_exc())
