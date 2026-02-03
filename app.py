import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="노인일자리 관리", layout="wide")
st.title("👵 노인일자리 출퇴근 시스템")

try:
    # 설정을 가져옵니다.
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 404 에러 방지를 위해 명시적으로 spreadsheet 주소를 전달합니다.
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    df = conn.read(spreadsheet=url)
    
    st.success("✅ 구글 시트 데이터를 성공적으로 가져왔습니다!")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error("❌ 데이터를 가져오는 중 오류가 발생했습니다.")
    st.code(str(e))
    st.info("1. 시트가 '링크가 있는 모든 사용자'에게 공유되었는지 확인하세요.\n2. Secrets의 spreadsheet 주소가 정확한지 확인하세요.")
