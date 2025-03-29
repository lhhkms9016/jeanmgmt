import streamlit as st
import pandas as pd
# db_scbank 모듈 import 시 주의사항 명시
from db_scbank import * # 주의: 이 모듈의 함수들은 수정 필요 (테이블/컬럼 이름 일치, 보안, DB 경로 처리 등)
import streamlit.components.v1 as stc
import datetime # 날짜 처리를 위해 추가

# Data Viz Pkgs
import plotly.express as px

# --- Gemini SQL Agent 관련 라이브러리 추가 ---
import google.generativeai as genai
import re
import sqlite3 # 명시적으로 import

# --- 데이터베이스 경로 및 테이블 이름 정의 ---
# 하드코딩된 DB 경로 제거됨. 경로는 사이드바 입력을 통해 st.session_state.db_path 에 저장됨
TABLE_NAME = "chk1_table" # 작업 대상 테이블

# --- Gemini SQL Agent 및 차트 생성 함수들 ---
MODEL_NAME = 'gemini-1.5-flash' # 사용할 모델 이름

def generate_sql_query(natural_language_query, table_name=None):
    """자연어 쿼리를 SQL 쿼리로 변환 (Gemini API 사용)"""
    if 'api_configured' not in st.session_state or not st.session_state.api_configured:
         st.error("Gemini API 키가 설정되지 않았거나 유효하지 않습니다. 사이드바에서 확인해주세요.")
         return None
    prompt = f"Generate **only** the SQL query (without any explanation, comments, or markdown like ```sql ... ```) for the table named '{table_name}' based on the following request: {natural_language_query}"
    model = genai.GenerativeModel(MODEL_NAME)
    try:
        response = model.generate_content(prompt)
        if response.parts:
            generated_text = response.text.strip()
            if generated_text.upper().startswith(("SELECT", "UPDATE", "DELETE", "INSERT")):
                 return generated_text
            else:
                st.warning(f"Gemini가 유효한 SQL 쿼리를 생성하지 못했습니다. 응답: \"{generated_text}\"")
                return None
        else:
            feedback = response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'N/A'
            st.error(f"Gemini API로부터 비어있는 응답을 받았습니다. (차단 사유 등: {feedback})")
            return None
    except Exception as e:
        st.error(f"Gemini API 호출 중 오류 발생: {e}")
        return None

def extract_sql_query(text):
    """Gemini 응답에서 순수 SQL 쿼리 추출"""
    if not text: return None
    text = re.sub(r'^```sql\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()

# --- 차트 생성 헬퍼 함수 ---
def generate_and_display_charts(df):
    """Analyzes the DataFrame and displays relevant charts inside an expander."""
    if df.empty: return # 데이터 없으면 종료

    with st.expander("Query Results Analysis (Charts)", expanded=False): # Expander 사용
        if df.empty: # Expander 내부에서 다시 체크
            st.info("차트를 생성할 데이터가 없습니다.")
            return

        chart_cols = st.columns(2) ; col_idx = 0

        # Status 분포
        if 'status' in df.columns:
            valid_status_data = df['status'].dropna()
            if not valid_status_data.empty:
                with chart_cols[col_idx % 2]:
                    st.markdown("##### Status Distribution")
                    status_counts = valid_status_data.value_counts().reset_index()
                    status_counts.columns = ['Status', 'Count']
                    try:
                        fig_bar = px.bar(status_counts, x='Status', y='Count', title="Count by Status", color='Status', text_auto=True)
                        fig_bar.update_layout(showlegend=False) ; st.plotly_chart(fig_bar, use_container_width=True)
                        if 1 < len(status_counts) < 8:
                             fig_pie = px.pie(status_counts, names='Status', values='Count', title="Proportion by Status")
                             st.plotly_chart(fig_pie, use_container_width=True)
                        col_idx += 1
                    except Exception as e: st.warning(f"Status 차트 생성 오류: {e}")

        # Result 분포
        if 'result' in df.columns:
            valid_result_data = df['result'].dropna()
            if not valid_result_data.empty:
                with chart_cols[col_idx % 2]:
                    st.markdown("##### Result Distribution")
                    result_counts = valid_result_data.value_counts().reset_index()
                    result_counts.columns = ['Result', 'Count']
                    try:
                        fig_bar = px.bar(result_counts, x='Result', y='Count', title="Count by Result", color='Result', text_auto=True)
                        fig_bar.update_layout(showlegend=False) ; st.plotly_chart(fig_bar, use_container_width=True)
                        col_idx += 1
                    except Exception as e: st.warning(f"Result 차트 생성 오류: {e}")

        # Owner 분포
        if 'owner' in df.columns:
            valid_owner_data = df['owner'].dropna()
            if not valid_owner_data.empty:
                owner_counts = valid_owner_data.value_counts()
                if 1 < len(owner_counts) < 30:
                    with chart_cols[col_idx % 2]:
                        st.markdown("##### Count by Owner")
                        owner_counts_df = owner_counts.reset_index()
                        owner_counts_df.columns = ['Owner', 'Count']
                        try:
                            fig_bar = px.bar(owner_counts_df, x='Owner', y='Count', title="Count by Owner", text_auto=True)
                            st.plotly_chart(fig_bar, use_container_width=True)
                            col_idx += 1
                        except Exception as e: st.warning(f"Owner 차트 생성 오류: {e}")

        # 수치형 데이터 히스토그램
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        if 'id' in numeric_cols and len(numeric_cols) > 1:
            try: numeric_cols.remove('id')
            except ValueError: pass
        for num_col in numeric_cols:
            valid_num_data = df[num_col].dropna()
            if valid_num_data.nunique() > 1:
                with chart_cols[col_idx % 2]:
                    st.markdown(f"##### Distribution of {num_col}")
                    try:
                        fig_hist = px.histogram(df, x=num_col, title=f"Histogram of {num_col}", nbins=15)
                        st.plotly_chart(fig_hist, use_container_width=True)
                        col_idx += 1
                    except Exception as e: st.warning(f"{num_col} 히스토그램 생성 오류: {e}")

        if col_idx == 0: # 생성된 차트가 없을 경우
             st.info("현재 쿼리 결과에 대해 자동으로 생성할 수 있는 표준 차트가 없습니다.")


# --- SQL 실행 및 결과/차트 표시 함수 ---
def execute_sql_and_display(conn, sql_query):
    """SQL 쿼리 실행 및 결과 표시 (SELECT 전용 + 결과 저장 + 차트 생성)"""
    st.session_state.query_result_df = pd.DataFrame() # 새 쿼리 전 이전 결과 초기화
    if not sql_query:
        st.warning("실행할 SQL 쿼리가 없습니다."); return
    st.write("---") ; st.write(f"실행될 SQL 쿼리:")
    st.code(sql_query, language="sql") ; st.write("---")
    try:
        if not sql_query.strip().upper().startswith("SELECT"):
             st.error("보안상의 이유로 이 에이전트에서는 **SELECT** 쿼리만 실행할 수 있습니다."); return
        df = pd.read_sql_query(sql_query, conn)
        st.session_state.query_result_df = df # 결과를 Session State에 저장
        with st.expander("쿼리 결과 보기", expanded=True):
            st.dataframe(df)
            st.success(f"쿼리 성공! 총 {len(df)}개의 행이 반환되었습니다.")
        # 차트 생성 및 표시 함수 호출
        if not df.empty:
             generate_and_display_charts(df) # 헬퍼 함수 호출
    except sqlite3.Error as db_err:
        st.error(f"데이터베이스 오류 발생: {db_err}"); st.error(f"실행 시도된 쿼리: {sql_query}")
        st.session_state.query_result_df = pd.DataFrame() # 오류 시 초기화
    except Exception as e:
        st.error(f"쿼리 실행 중 예외 발생: {e}"); st.error(f"실행 시도된 쿼리: {sql_query}")
        st.session_state.query_result_df = pd.DataFrame() # 오류 시 초기화


# --- HTML 배너 ---
HTML_BANNER = """
    <div style="background-color:#464e5f;padding:10px;border-radius:10px">
    <h1 style="color:white;text-align:center;">SC제일은행 RFP분석</h1>
    <p style="color:white;text-align:center;">Checklist1</p>
    </div>
    """

# --- 메인 애플리케이션 로직 ---
def main():
    stc.html(HTML_BANNER)
    # --- 세션 상태 초기화 ---
    if 'api_configured' not in st.session_state: st.session_state.api_configured = False
    if 'query_result_df' not in st.session_state: st.session_state.query_result_df = pd.DataFrame()
    if 'db_path' not in st.session_state: st.session_state.db_path = None

    # --- Gemini API 키 입력 (사이드바) ---
    st.sidebar.subheader("Gemini API 설정")
    api_key = st.sidebar.text_input("Gemini API 키", type="password", key="gemini_api_key_input", help="Gemini API 사용을 위해 키를 입력하세요.")
    if api_key:
        try:
            genai.configure(api_key=api_key)
            if not st.session_state.api_configured: st.sidebar.success("API 키가 입력/변경되었습니다.")
            st.session_state.api_configured = True
        except Exception as config_err:
             if st.session_state.api_configured: st.sidebar.error(f"API 키 설정 중 오류 발생 가능성: {config_err}")
             st.session_state.api_configured = False
    else:
        if st.session_state.api_configured: st.sidebar.warning("API 키가 제거되었습니다.")
        st.session_state.api_configured = False

    # --- Database Path Input (Sidebar) ---
    st.sidebar.divider()
    st.sidebar.subheader("데이터베이스 설정")
    db_path_input = st.sidebar.text_input(
        "데이터베이스 파일 경로", value=st.session_state.get('db_path', ''),
        placeholder="예: D:\\path\\to\\your\\data.db", key="db_path_input",
        help="분석할 SQLite 데이터베이스 파일의 전체 경로를 입력하세요."
    )
    current_db_path = st.session_state.get('db_path')
    if db_path_input != current_db_path:
        st.session_state.db_path = db_path_input if db_path_input else None
        st.session_state.query_result_df = pd.DataFrame() # 경로 변경 시 결과 초기화
        st.rerun() # 경로 변경 즉시 반영
    if st.session_state.get('db_path'): st.sidebar.caption(f"현재 DB 경로: {st.session_state.db_path}")
    else: st.sidebar.warning("데이터베이스 경로를 입력해주세요.")

    # --- 메뉴 선택 ---
    menu = ["About", "Read", "Create", "Update(예정)", "Delete(예정)"]
    choice = st.sidebar.selectbox("Menu", menu, key="main_menu_selector")

    # --- DB 테이블 생성 확인 ---
    # !!! 중요: db_scbank.py 수정 필요 !!!
    if st.session_state.get('db_path'):
        try: create_table() # 이상적으로는 create_table(st.session_state.db_path)
        except NameError: st.error("`db_scbank.py`에서 `create_table` 함수를 찾을 수 없거나 import되지 않았습니다.")
        except Exception as tbl_err: st.error(f"테이블 생성/확인 중 오류 발생: {tbl_err}. DB 경로 및 `db_scbank.py` 확인 필요.")
    # else: # 경로 미설정 시 메시지 표시 (선택적)
    #    if choice != "About": # About 메뉴 외에는 경로 필요
    #        st.error("데이터베이스 경로가 설정되지 않았습니다. 사이드바에서 경로를 먼저 입력해주세요.")

    # --- 메뉴별 화면 처리 ---
    if choice == "Create":
        st.warning("Create 기능은 `db_scbank.py`가 사용자가 입력한 DB 경로를 사용하도록 수정되어야 정상 작동합니다.")
        if not st.session_state.get('db_path'):
            st.error("항목을 추가하려면 먼저 사이드바에서 데이터베이스 경로를 설정해주세요.")
        else:
            st.subheader("Add Item")
            col1, col2 = st.columns(2)
            with col1:
                cat1_input = st.text_input("Category 1 (cat1)", key="create_cat1")
                cat2_input = st.text_input("Category 2 (cat2)", key="create_cat2")
                cat3_input = st.text_input("Category 3 (cat3)", key="create_cat3")
                cat4_input = st.text_input("Category 4 (cat4)", key="create_cat4")
                cat5_input = st.text_input("Category 5 (cat5)", key="create_cat5")
                desc_input = st.text_area("Description (desc)", key="create_desc")
            with col2:
                owner_input = st.text_input("Owner", key="create_owner")
                action_input = st.text_area("Action Required", key="create_action")
                status_input = st.selectbox("Status", ["Green", "Yellow", "Red"], key="status_create")
                result_input = st.selectbox("Result", ["Yes", "No", "NA"], key="create_result")
                memo_input = st.text_area("Memo", key="create_memo")

            if st.button("Add Item", key="create_add_button"):
                 if desc_input:
                     try: # 이상적으로는 add_data(st.session_state.db_path, ...)
                         add_data(cat1=cat1_input, cat2=cat2_input, cat3=cat3_input, cat4=cat4_input, cat5=cat5_input, desc=desc_input, owner=owner_input, action=action_input, status=status_input, result=result_input, memo=memo_input)
                         st.success(f"항목 '{desc_input[:30]}...' 추가 완료.")
                     except NameError: st.error("`db_scbank.py`에 `add_data` 함수가 없거나 import되지 않았습니다.")
                     except Exception as add_err: st.error(f"데이터 추가 중 오류 발생: {add_err}. `db_scbank.py` 확인 필요.")
                 else: st.warning("Description (desc) 필드는 비워둘 수 없습니다.")
            st.divider()
            # --- CSV 파일 업로드 섹션 ---
            st.subheader("Bulk Upload from CSV")
            with st.expander("Upload CSV File"):
                 if not st.session_state.get('db_path'):
                     st.warning("CSV 파일을 업로드하려면 먼저 사이드바에서 데이터베이스 경로를 설정해야 합니다.")
                 else:
                     uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'], key="create_csv_uploader")
                     if uploaded_file is not None:
                         upload_option = st.radio("Select Upload Mode:", ('Append', 'Replace'), index=0, horizontal=True, key='upload_mode')
                         if upload_option == 'Replace': st.warning("**경고:** 'Replace' 모드는 테이블의 **모든 기존 데이터를 삭제**하고 CSV 데이터로 대체합니다.")
                         st.info(f"파일 '{uploaded_file.name}' 선택됨. 모드: '{upload_option}'. 버튼을 눌러 진행하세요.")
                         if st.button("Upload Data from CSV", key="create_csv_upload_button"):
                             st.info("CSV 업로드 시 `db_scbank.py`에 정의된 `delete_all_data` 및 `bulk_insert_data` 함수를 사용합니다.")
                             try:
                                 df = pd.read_csv(uploaded_file) ; st.dataframe(df.head())
                                 required_db_cols = ['cat1', 'cat2', 'cat3', 'cat4', 'cat5', 'desc', 'owner', 'action', 'status', 'result', 'memo']
                                 df.columns = df.columns.str.lower() ; csv_cols = df.columns.tolist()
                                 missing_cols = [col for col in required_db_cols if col not in csv_cols]
                                 if missing_cols: st.error(f"CSV 파일에 필요한 컬럼이 없습니다: {', '.join(missing_cols)}")
                                 else:
                                     st.success("CSV 컬럼 검증 완료.") ; data_to_insert = []
                                     for index, row in df.fillna('').iterrows():
                                         try: data_to_insert.append(tuple(row[col] for col in required_db_cols))
                                         except KeyError as e: st.error(f"행 {index+2} 처리 오류: 컬럼 '{e}' 없음."); data_to_insert = [] ; break
                                         except Exception as e: st.error(f"행 {index+2} 처리 오류: {e}"); data_to_insert = [] ; break
                                     if data_to_insert:
                                         st.info(f"{len(data_to_insert)}개 행 삽입 준비 완료.")
                                         try: # --- db_scbank 함수 호출 ---
                                             delete_success = True
                                             if upload_option == 'Replace':
                                                 st.write(f"모드: Replace. '{TABLE_NAME}' 테이블 데이터 삭제 중...")
                                                 delete_success = delete_all_data(TABLE_NAME) # 이상적: delete_all_data(st.session_state.db_path, TABLE_NAME)
                                                 if delete_success: st.write("기존 데이터 삭제 완료.")
                                                 else: st.error("기존 데이터 삭제 중 오류 발생.")
                                             insert_success = False
                                             if delete_success:
                                                 st.write(f"{len(data_to_insert)}개 새 레코드 삽입 중...")
                                                 insert_success = bulk_insert_data(data_to_insert, TABLE_NAME) # 이상적: bulk_insert_data(st.session_state.db_path, ...)
                                                 if insert_success: st.write("새 데이터 삽입 완료.")
                                                 else: st.error("새 데이터 삽입 중 오류 발생.")
                                             if delete_success and insert_success:
                                                 op_str = "교체" if upload_option == 'Replace' else "추가"
                                                 st.success(f"'{uploaded_file.name}' 파일로부터 {len(data_to_insert)}개 레코드를 성공적으로 **{op_str}**했습니다!")
                                             else: st.error("CSV 업로드 작업 중 오류가 발생하여 완료되지 않았습니다.")
                                         except NameError as ne: st.error(f"`db_scbank.py`에 필요한 함수(delete_all_data 또는 bulk_insert_data)가 정의되지 않았거나 import되지 않았습니다: {ne}")
                                         except Exception as db_op_err: st.error(f"데이터베이스 작업 호출 중 오류 발생: {db_op_err}. `db_scbank.py` 확인 필요.")
                             except pd.errors.EmptyDataError: st.error("업로드된 CSV 파일이 비어있습니다.")
                             except Exception as e: st.error(f"파일 처리 중 오류 발생: {e}")


    elif choice == "Read":
        if not st.session_state.get('db_path'):
            st.error("데이터를 조회하려면 먼저 사이드바에서 데이터베이스 경로를 설정해주세요.")
        else:
            st.subheader("View Items")
            # --- 전체 데이터 조회 및 대시보드 ---
            # !!! 중요: db_scbank.py 수정 필요 !!!
            result_data = []
            try: result_data = view_all_data() # 이상적: view_all_data(st.session_state.db_path)
            except NameError: st.error("`db_scbank.py`에 `view_all_data` 함수가 없거나 import되지 않았습니다.")
            except Exception as view_err: st.error(f"데이터 조회 중 오류 발생: {view_err}. `db_scbank.py` 확인 필요.")
            if result_data:
                db_columns = ['id', 'cat1', 'cat2', 'cat3', 'cat4', 'cat5', 'desc', 'owner', 'action', 'status', 'result', 'memo']
                try:
                    clean_df = pd.DataFrame(result_data, columns=db_columns)
                    with st.expander("View All Items (전체 데이터)", expanded=False): st.dataframe(clean_df)
                    with st.expander("Overall Status Dashboard (전체 데이터 기준)"):
                        if 'status' in clean_df.columns:
                            task_df = clean_df['status'].value_counts().to_frame().reset_index(); task_df.columns = ['Status Type', 'Count']
                            st.dataframe(task_df)
                            p1 = px.pie(task_df, names='Status Type', values='Count', title="Overall Status Distribution"); st.plotly_chart(p1, use_container_width=True)
                        else: st.warning("'status' 컬럼을 찾을 수 없습니다.")
                except Exception as df_err: st.error(f"전체 데이터 표시 중 오류: {df_err}")
            else: st.info("표시할 전체 데이터가 없거나 조회에 실패했습니다.")
            st.divider()

            # --- 쿼리 섹션 (선택 방식 + 결과/차트 표시) ---
            # 이 섹션은 사용자가 입력한 DB 경로를 사용
            st.subheader("Query Database")
            query_method = st.radio("Select Query Method:", ("Natural Language (Gemini)", "Direct SQL Input"), key="query_method_radio", horizontal=True)
            conn = None
            db_path_to_use = st.session_state.get('db_path') # 사용할 경로 변수

            if query_method == "Natural Language (Gemini)":
                st.markdown("Ask questions about the data in natural language.")
                if not st.session_state.api_configured: st.warning("Gemini SQL Agent를 사용하려면 사이드바에서 유효한 Gemini API 키를 입력해야 합니다.")
                else:
                    natural_language_query = st.text_input("데이터 관련 질문 입력:", placeholder="예: status가 Done인 항목 개수 세어줘", key="nl_query_input")
                    if st.button("질문 실행하기 (Gemini)", key="run_nl_query_button"):
                        if natural_language_query:
                            if db_path_to_use: # 경로 확인
                                try:
                                    conn = sqlite3.connect(db_path_to_use, check_same_thread=False)
                                    st.info(f"'{TABLE_NAME}' 테이블 질문 처리 중...")
                                    sql_query_raw = generate_sql_query(natural_language_query, TABLE_NAME)
                                    sql_query_extracted = extract_sql_query(sql_query_raw)
                                    if sql_query_extracted: execute_sql_and_display(conn, sql_query_extracted) # 차트 생성 포함
                                except sqlite3.Error as db_con_err: st.error(f"DB 연결 실패: {db_con_err}")
                                except Exception as agent_err: st.error(f"NL 쿼리 처리 중 오류: {agent_err}")
                                finally:
                                    if conn: conn.close()
                            else: st.error("데이터베이스 경로가 설정되지 않았습니다.")
                        else: st.warning("질문 내용을 입력해주세요.")

            elif query_method == "Direct SQL Input":
                st.markdown("Enter your SQL query directly. **(Only `SELECT` statements are allowed for security)**")
                default_sql = f"SELECT id, desc, owner, status FROM {TABLE_NAME} WHERE status = 'ToDo' LIMIT 10;"
                sql_query_direct = st.text_area("Enter SQL Query:", value=default_sql, height=150, key="direct_sql_input")
                if st.button("SQL 실행하기", key="run_direct_sql_button"):
                    if sql_query_direct:
                        if db_path_to_use: # 경로 확인
                            try:
                                conn = sqlite3.connect(db_path_to_use, check_same_thread=False)
                                st.info("직접 입력된 SQL 실행 중...")
                                execute_sql_and_display(conn, sql_query_direct) # 차트 생성 포함
                            except sqlite3.Error as db_con_err: st.error(f"DB 연결 실패: {db_con_err}")
                            except Exception as direct_sql_err: st.error(f"직접 SQL 실행 중 오류: {direct_sql_err}")
                            finally:
                                if conn: conn.close()
                        else: st.error("데이터베이스 경로가 설정되지 않았습니다.")
                    else: st.warning("실행할 SQL 쿼리를 입력해주세요.")

            # --- View Details from Query Results by ID (쿼리 결과 기반 상세 보기) ---
            st.divider()
            st.subheader("View Details from Query Results by ID")
            if 'query_result_df' in st.session_state and not st.session_state.query_result_df.empty:
                result_df = st.session_state.query_result_df
                if 'id' in result_df.columns and pd.api.types.is_numeric_dtype(result_df['id']):
                    min_id_val = int(result_df['id'].min()) if pd.notna(result_df['id'].min()) else 1
                    max_id_val = int(result_df['id'].max()) if pd.notna(result_df['id'].max()) else None
                    search_id_from_results = st.number_input("Enter ID from the results above:", min_value=min_id_val, max_value=max_id_val, step=1, key="view_id_from_results_input")
                    if st.button("Search in Results by ID", key="view_id_from_results_button"):
                        if search_id_from_results is not None:
                            filtered_rows = result_df[result_df['id'] == search_id_from_results]
                            if not filtered_rows.empty:
                                item_series = filtered_rows.iloc[0]
                                st.success(f"Displaying details for ID {search_id_from_results} from the current results:")
                                col1, col2 = st.columns(2)
                                with col1: # .get(col, default) 사용
                                    st.text_input("Category 1 (cat1)", value=item_series.get('cat1', ''), disabled=True, key="view_res_cat1")
                                    st.text_input("Category 2 (cat2)", value=item_series.get('cat2', ''), disabled=True, key="view_res_cat2")
                                    st.text_input("Category 3 (cat3)", value=item_series.get('cat3', ''), disabled=True, key="view_res_cat3")
                                    st.text_input("Category 4 (cat4)", value=item_series.get('cat4', ''), disabled=True, key="view_res_cat4")
                                    st.text_input("Category 5 (cat5)", value=item_series.get('cat5', ''), disabled=True, key="view_res_cat5")
                                    st.text_area("Description (desc)", value=item_series.get('desc', ''), disabled=True, key="view_res_desc", height=100)
                                with col2:
                                    st.text_input("Owner", value=item_series.get('owner', ''), disabled=True, key="view_res_owner")
                                    st.text_area("Action Required", value=item_series.get('action', ''), disabled=True, key="view_res_action", height=100)
                                    st.text_input("Status", value=item_series.get('status', ''), disabled=True, key="view_res_status")
                                    st.text_input("Result", value=item_series.get('result', ''), disabled=True, key="view_res_result")
                                    st.text_area("Memo", value=item_series.get('memo', ''), disabled=True, key="view_res_memo", height=100)
                            else: st.warning(f"ID {search_id_from_results} not found in the current query results.")
                        else: st.warning("조회할 ID를 입력하세요.")
                else: st.warning("현재 쿼리 결과에 'id' 컬럼이 없거나 숫자 형식이 아니어서 ID로 상세 보기를 할 수 없습니다.")
            else: st.info("먼저 위에서 데이터베이스 쿼리를 실행하여 결과를 확인하세요. 결과 내에서 ID로 상세 정보를 조회할 수 있습니다.")


    elif choice == "Update(예정)":
        st.subheader("Update Item")
        st.warning("Update 기능은 아직 구현되지 않았습니다.")
        # !!! 중요: Update UI 및 db_scbank.py 수정/연동 필요 !!!

    elif choice == "Delete(예정)":
        st.subheader("Delete Item")
        st.warning("Delete 기능은 아직 구현되지 않았습니다.")
        # !!! 중요: Delete UI 및 db_scbank.py 수정/연동 필요 !!!

    else: # About (첫 번째 메뉴로 변경됨)
        st.subheader("RFP분석 어플리케이션")
        st.info("이 어플리케이션 RFP 분석에 대한 결과 대시보드 테스트 목적입니다.")
        st.info("Features include CRUD operations, CSV bulk upload, and database querying via Item ID (from query results), Natural Language (Gemini), or Direct SQL with automated chart generation.")
        st.markdown("Developed by: [강민수 / 컨설팅2팀]")

# --- 앱 실행 ---
if __name__ == '__main__':
    main()