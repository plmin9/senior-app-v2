import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("👵 노인일자리 시스템")

def get_client():
    try:
        s = st.secrets["connections"]["gsheets"]
        # 가공 없이 Secrets 값을 직접 전달
        creds = Credentials.from_service_account_info(
            st.secrets["connections"]["gsheets"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ 연결 설정 오류: {e}")
        return None

client = get_client()

if client:
    try:
        # 시트 주소로 파일 열기
        doc = client.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
        st.success(f"✅ [{doc.title}] 연결 성공!")
        
        # 첫 번째 시트 명단 가져오기
        sheet = doc.get_worksheet(0)
        data = sheet.get_all_records()
        st.write("📋 시트 데이터를 성공적으로 불러왔습니다.")
        
    except Exception as e:
        st.error(f"❌ 시트 접근 오류: {e}")
