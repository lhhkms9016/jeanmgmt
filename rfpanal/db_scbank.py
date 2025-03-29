import sqlite3

# 데이터베이스 연결 및 커서 생성
# check_same_thread=False는 Streamlit과 함께 사용할 때 필요합니다.
conn = sqlite3.connect(r"D:\lhhkms\streamlit_test\todo_app\data.db", check_same_thread=False)
c = conn.cursor()

# --- 테이블 관리 ---
def create_table():
    """taskstable 테이블이 없으면 생성합니다."""
    c.execute('''CREATE TABLE IF NOT EXISTS chk1_table(
                    id INTEGER PRIMARY KEY,
                    cat1 TEXT,
                    cat2 TEXT,
                    cat3 TEXT,
                    cat4 TEXT,
                    cat5 TEXT,
                    desc TEXT,
                    owner TEXT,
                    action TEXT,
                    status TEXT,
                    result TEXT,
                    memo TEXT
                )''')

# --- 데이터 추가 (Create) ---
def add_data(cat1, cat2, cat3, cat4, cat5, desc, owner, action, status, result, memo):
    """새로운 항목을 데이터베이스 chk1_table 추가합니다. (SQL 인젝션 안전)"""
    try:
        # 파라미터화된 쿼리 (?) 를 사용하여 SQL 인젝션 방지
        # INSERT 문에 새로운 컬럼들과 해당 값 플레이스홀더 추가 (총 11개)
        c.execute('''INSERT INTO chk1_table(
                        cat1, cat2, cat3, cat4, cat5,
                        desc, owner, action, status, result, memo
                     ) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                  (cat1, cat2, cat3, cat4, cat5, desc, owner, action, status, result, memo))
        conn.commit() # 변경 사항 저장
        print("데이터 추가 완료") # 콘솔 확인용 로그 (선택 사항)
    except Exception as e:
        print(f"데이터 추가 중 오류 발생: {e}") # 오류 발생 시 로그 출력

# --- 데이터 조회 (Read) - 오류 처리 추가 버전 ---
def view_all_data():
    """모든 항목 데이터를 데이터베이스에서 조회합니다."""
    try:
        c.execute('SELECT * FROM chk1_table')
        data = c.fetchall() # 모든 결과 가져오기
        return data
    except Exception as e:
        print(f"데이터 조회 중 오류 발생: {e}")
        return [] # 오류 발생 시 빈 리스트 반환 또는 다른 처리

def view_all_task_names():
    """모든 고유한 할 일 이름(task)을 조회합니다."""
    c.execute('SELECT DISTINCT task FROM chk1_table')
    data = c.fetchall()
    return data

# --- 데이터 조회 (Read) --- 부분 또는 파일의 적절한 위치에 추가하세요 ---

def get_data_by_id(item_id):
    """
    chk1_table에서 고유 ID를 기준으로 특정 행(row) 데이터를 조회합니다.

    Args:
        item_id (int): 조회할 항목의 ID.

    Returns:
        tuple: 해당 ID의 데이터 행을 담은 튜플. 데이터가 없으면 None을 반환합니다.
               오류 발생 시에도 None을 반환합니다.
    """
    try:
        # 파라미터화된 쿼리 (?) 를 사용하여 SQL 인젝션 방지
        c.execute("SELECT * FROM chk1_table WHERE id=?", (item_id,))
        # fetchone()을 사용하여 ID에 해당하는 하나의 행만 가져옵니다.
        data = c.fetchone()
        return data # 데이터가 있으면 튜플, 없으면 None 반환
    except sqlite3.Error as e:
        # 데이터베이스 관련 오류 발생 시 로그 출력 및 None 반환
        print(f"ID {item_id} 조회 중 데이터베이스 오류 발생: {e}")
        return None
    except Exception as e:
        # 기타 예상치 못한 오류 발생 시 로그 출력 및 None 반환
        print(f"ID {item_id} 조회 중 예상치 못한 오류 발생: {e}")
        return None

# --------------------------------------------------------------------
# 아래 함수들을 db_scbank.py 파일에 추가하세요.

def delete_all_data(table_name="chk1_table"):
    """지정된 테이블의 모든 데이터를 삭제합니다."""
    global conn, c # 전역 conn, c를 사용한다고 명시 (필요시)
    try:
        # 테이블 이름 직접 사용 시 주의 (여기서는 고정값이므로 괜찮음)
        # 동적 테이블 이름 사용 시 SQL 인젝션 주의 필요
        c.execute(f"DELETE FROM {table_name}")
        conn.commit()
        print(f"테이블 '{table_name}'의 모든 데이터 삭제 완료.")
        return True # 성공 시 True 반환
    except sqlite3.Error as e:
        print(f"'{table_name}' 데이터 삭제 중 오류 발생: {e}")
        try: conn.rollback() # 오류 발생 시 롤백 시도
        except Exception as rb_err: print(f"롤백 실패: {rb_err}")
        return False # 실패 시 False 반환
    except Exception as e:
        print(f"'{table_name}' 데이터 삭제 중 예상치 못한 오류: {e}")
        return False

def bulk_insert_data(data_to_insert, table_name="chk1_table"):
    """지정된 테이블에 여러 행의 데이터를 한 번에 삽입합니다."""
    global conn, c # 전역 conn, c를 사용한다고 명시 (필요시)
    if not data_to_insert:
        print("삽입할 데이터가 없습니다.")
        return False

    # 컬럼 순서가 INSERT 문과 data_to_insert의 튜플 순서와 일치해야 함
    insert_sql = f'''INSERT INTO {table_name}(
                         cat1, cat2, cat3, cat4, cat5,
                         desc, owner, action, status, result, memo
                     ) VALUES (?,?,?,?,?,?,?,?,?,?,?)''' # 11개 컬럼
    try:
        c.executemany(insert_sql, data_to_insert)
        conn.commit()
        print(f"'{table_name}' 테이블에 {len(data_to_insert)}개 행 삽입 완료.")
        return True # 성공 시 True 반환
    except sqlite3.Error as e:
        print(f"'{table_name}' 대량 삽입 중 데이터베이스 오류 발생: {e}")
        try: conn.rollback() # 오류 발생 시 롤백 시도
        except Exception as rb_err: print(f"롤백 실패: {rb_err}")
        return False # 실패 시 False 반환
    except Exception as e:
        print(f"'{table_name}' 대량 삽입 중 예상치 못한 오류: {e}")
        return False
    
# def get_task(task):
#     """특정 할 일 이름(task)에 해당하는 데이터를 조회합니다. (SQL 인젝션 안전)"""
#     # 파라미터화된 쿼리 (?) 를 사용하여 SQL 인젝션 방지
#     c.execute('SELECT * FROM taskstable WHERE task=?', (task,)) # 튜플 형태로 전달 (task,)
#     data = c.fetchall()
#     return data

# def get_task_by_status(task_status):
#     """특정 상태(task_status)에 해당하는 데이터를 조회합니다. (SQL 인젝션 안전)"""
#     # 파라미터화된 쿼리 (?) 를 사용하여 SQL 인젝션 방지
#     c.execute('SELECT * FROM taskstable WHERE task_status=?', (task_status,))
#     data = c.fetchall()
#     return data # 누락되었던 return 문 추가

# # --- 데이터 수정 (Update) ---
# def edit_task_data(new_task, new_task_status, new_task_date, task, task_status, task_due_date):
#     """기존 할 일 데이터를 새로운 데이터로 업데이트합니다. (SQL 인젝션 안전)"""
#     # 파라미터화된 쿼리 (?) 를 사용하여 SQL 인젝션 방지
#     # WHERE 절에서 기존의 모든 값을 비교하여 정확한 항목만 업데이트
#     c.execute("UPDATE taskstable SET task=?, task_status=?, task_due_date=? WHERE task=? and task_status=? and task_due_date=?",
#               (new_task, new_task_status, new_task_date, task, task_status, task_due_date))
#     conn.commit() # 변경 사항 저장
#     # UPDATE 문은 결과를 반환하지 않으므로 fetchall() 및 return 제거

# # --- 데이터 삭제 (Delete) ---
# def delete_data(task):
#     """특정 할 일 이름(task)에 해당하는 데이터를 삭제합니다. (SQL 인젝션 안전)"""
#     # 파라미터화된 쿼리 (?) 를 사용하여 SQL 인젝션 방지
#     c.execute('DELETE FROM taskstable WHERE task=?', (task,))
#     conn.commit() # 변경 사항 저장

# # 참고: 데이터베이스 연결을 닫는 함수도 추가할 수 있습니다. (애플리케이션 종료 시 호출)
# # def close_db():
# #    conn.close()