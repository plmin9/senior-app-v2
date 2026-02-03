import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

def get_gspread_client():
    try:
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            s = st.secrets["connections"]["gsheets"]
            
            # [핵심 수리 로직] 
            # 비밀키에서 '글자로 된 \n'을 '실제 줄바꿈'으로 바꾸고 앞뒤 공백을 완전히 제거
            p_key = s["private_key"].replace("\\n", "\n").strip()
            
            # PEM 파일 형식(-----BEGIN...-----)이 깨졌는지 최종 확인 후 복구
            if not p_key.startswith("-----BEGIN PRIVATE KEY-----"):
                p_key = "-----BEGIN PRIVATE KEY-----\n" + p_key
            if not p_key.endswith("-----END PRIVATE KEY-----"):
                p_key = p_key + "\n-----END PRIVATE KEY-----"

            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            
            creds = Credentials.from_service_account_info({
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
            }, scopes=scopes)
            
            return gspread.authorize(creds)
        return None
    except Exception as e:
        st.error(f"⚠️ 인증 처리 중 상세 오류: {e}")
        return None

# 사용 예시
client = get_gspread_client()
if client:
    # '근태로그'는 실제 구글 시트 파일 이름입니다.
    doc = client.open("근태로그") 
    st.success("데이터베이스 연결 성공!")
