import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px  # Plotly Express 라이브러리 추가

# SQLite 연결 설정 함수
def connect_to_sqlite(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        st.error(f"SQLite 연결 실패: {e}")
        return None

# SQL 쿼리를 실행하고 결과를 st.write로 표시하는 함수
def execute_sql_and_display(conn, sql_query):
    try:
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
    st.title("SQL 쿼리 조회 및 Bar Chart 생성")

    # 세션 상태 초기화
    if 'df' not in st.session_state:
        st.session_state['df'] = pd.DataFrame()
    if 'selected_row' not in st.session_state:
        st.session_state['selected_row'] = None
    if 'selected_row_index' not in st.session_state:
        st.session_state['selected_row_index'] = 1  # 초기값 1로 설정

    # SQLite 파일 선택 (파일 업로드)
    uploaded_file = st.file_uploader("SQLite 파일 업로드", type=["db", "sqlite", "sqlite3"], key="sqlite_uploader3")

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
            selected_table = st.selectbox("테이블 선택:", st.session_state['table_names'], key="table_selector1")
            default_query = f"SELECT * FROM {selected_table} LIMIT 10;"  # 선택한 테이블에 대한 기본 쿼리 생성
            sql_query = st.text_area("SQL 쿼리 입력:", value=default_query, key="barchart1_sqlquery1")  # 기본 쿼리를 text_area에 표시

            if st.button("실행", key="barchart1_execute_button1"):
                conn = connect_to_sqlite(db_file)
                if conn:
                    execute_sql_and_display(conn, sql_query)
                    conn.close()

            # Bar Chart 생성 및 표시
            if not st.session_state['df'].empty:
                try:
                    if len(st.session_state['df'].columns) >= 2:  # count 또는 sum을 위한 최소 열 수
                        x_axis = st.selectbox("X축 선택:", st.session_state['df'].columns, key="x_axis_selector1")
                        y_axis_type = st.selectbox("Y축 계산 방식 선택:", ["count", "sum"], key="y_axis_type_selector1")

                        if y_axis_type == "count":
                            counts = st.session_state['df'][x_axis].value_counts()
                            total_count = counts.sum()  # 총 합계 계산
                            fig = px.bar(x=counts.index, y=counts.values, labels={'x': x_axis, 'y': 'count'}, text=counts.values)
                            fig.update_layout(title=f"총 합계: {total_count}")  # 타이틀에 총 합계 추가
                            st.plotly_chart(fig)
                        elif y_axis_type == "sum":
                            numeric_columns = st.session_state['df'].select_dtypes(include=['number']).columns.tolist()
                            if numeric_columns:
                                y_axis_sum = st.selectbox("합계를 구할 열 선택:", numeric_columns, key="y_axis_sum_selector2")
                                sums = st.session_state['df'].groupby(x_axis)[y_axis_sum].sum()
                                total_sum = sums.sum()  # 총 합계 계산
                                fig = px.bar(x=sums.index, y=sums.values, labels={'x': x_axis, 'y': 'sum'}, text=sums.values)
                                fig.update_layout(title=f"총 합계: {total_sum}")  # 타이틀에 총 합계 추가
                                st.plotly_chart(fig)
                            else:
                                st.error("숫자형 열이 없어 합계를 계산할 수 없습니다.")

                    else:
                        st.write("차트 생성에 필요한 최소 2개 이상의 열이 없습니다.")
                except Exception as e:
                    st.error(f"차트 생성 오류: {e}")

        else:
            selected_table = None
            sql_query = st.text_area("SQL 쿼리 입력:", "SELECT * FROM table_name LIMIT 10;", key="barchart1_sqlquery2")

    else:
        st.write('SQLite 파일을 먼저 업로드해주세요.')

if __name__ == "__main__":
    main()