import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re

# SQLite 연결 설정 함수
def connect_to_sqlite(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        st.error(f"SQLite 연결 실패: {e}")
        return None

# 자연어 쿼리를 SQL 쿼리로 변환하는 함수
def generate_sql_query(natural_language_query, table_name=None):
    if table_name:
        prompt = f"Generate only SQL query for table '{table_name}': {natural_language_query}"
    else:
        prompt = f"Generate only SQL query: {natural_language_query}"

    model = genai.GenerativeModel(MODEL_NAME)
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Gemini API 오류: {e}")
        return None

# SQL 쿼리를 실행하고 결과를 st.write로 표시하는 함수
def execute_sql_and_display(conn, sql_query):
    try:
        sql_query = extract_sql_query(sql_query)
        sql_query = sql_query.strip()
        df = pd.read_sql_query(sql_query, conn)
        with st.expander("결과 보기"):
            st.write(f"총 행 수: {len(df)}")
            st.write(df)
        st.session_state['df'] = df  # 데이터프레임 저장
    except sqlite3.Error as db_err:
        st.error(f"데이터베이스 오류: {db_err}")
        raise db_err
    except Exception as e:
        st.error(f"알 수 없는 오류: {e}")
        raise e

# SQL 쿼리 추출 함수
def extract_sql_query(text):
    match = re.search(r'(SELECT|INSERT|UPDATE|DELETE).*;', text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(0)
    match = re.search(r'`sql(.*?)`', text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return text

# SQLite 테이블 목록을 가져오는 함수
def get_table_names(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    except sqlite3.Error as e:
        st.error(f"테이블 목록을 가져오는 중 오류 발생: {e}")
        return []

# 메인 Streamlit 앱
def main():
    st.title("SQL Agent with Gemini")

    # 세션 상태 초기화
    if 'df' not in st.session_state:
        st.session_state['df'] = pd.DataFrame()
    if 'selected_row' not in st.session_state:
        st.session_state['selected_row'] = None
    if 'selected_row_index' not in st.session_state:
        st.session_state['selected_row_index'] = 1  # 초기값 1로 설정

    # Gemini API 키 입력
    api_key = st.text_input("Gemini API 키를 입력하세요:", type="password")
    if api_key:
        genai.configure(api_key=api_key)
        global MODEL_NAME
        MODEL_NAME = 'gemini-1.5-flash'

        # SQLite 파일 선택 (파일 업로드)
        uploaded_file = st.file_uploader("SQLite 파일 업로드", type=["db", "sqlite", "sqlite3"], key="sqlite_uploader1")

        if uploaded_file is not None:
            db_file = "temp.db"  # 임시 파일 이름
            with open(db_file, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state['db_file'] = db_file
            st.session_state['table_names'] = []

        if 'db_file' in st.session_state:
            db_file = st.session_state['db_file']
            st.write(f"선택된 파일: {uploaded_file.name if uploaded_file else '임시파일'}")

            conn = connect_to_sqlite(db_file)
            if conn:
                table_names = get_table_names(conn)
                if table_names:
                    st.session_state['table_names'] = table_names
                else:
                    st.write('테이블이 없습니다.')
                conn.close()

            if st.session_state['table_names']:
                selected_table = st.selectbox("테이블 선택:", st.session_state['table_names'], key="sqlagent1_table_selector1")
            else:
                selected_table = None

            natural_language_query = st.text_input("자연어 쿼리:", "Show all data from table")

            if st.button("실행", key="sqlagent1_button1"):
                conn = connect_to_sqlite(db_file)
                if conn:
                    sql_query = generate_sql_query(natural_language_query, selected_table)
                    if sql_query:
                        st.write(f"생성된 SQL 쿼리:\n{sql_query}")
                        execute_sql_and_display(conn, sql_query)
                    conn.close()

            else:
                st.session_state['selected_row'] = None

        else:
            st.write('SQLite 파일을 먼저 업로드해주세요.')
    else:
        st.write('Gemini API 키를 입력해주세요.')

if __name__ == "__main__":
    main()