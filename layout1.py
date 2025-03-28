import streamlit as st
import sys
import os

# 상대 경로를 사용하여 모듈 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__)) #현재 파일이 있는 디렉토리 가져오기
module_paths = [
    os.path.join(current_dir, "sqlagent"),
    os.path.join(current_dir, "chart"),
]
for path in module_paths:
    sys.path.append(path)

import sqlagent1
import sqlquery1
import barchart1
import fileupload1
import fileupload2
import pdfsplit1
import pdfmerge1
import extracturl1

def main():
    st.sidebar.header("메뉴 선택")
    option = st.sidebar.selectbox("옵션을 선택하세요.", ["제안관리", "파일관리", "옵션 3"])

    if option == "제안관리":
        tab1, tab2, tab3 = st.tabs(["LLM조회", "SQL조회", "통계"])
        with tab1:
            try:
                sqlagent1.main()
            except Exception as e:
                st.error(f"sqlagent1 모듈 실행 중 오류 발생: {e}")
        with tab2:
            try:
                sqlquery1.main()
            except Exception as e:
                st.error(f"sqlquery1 모듈 실행 중 오류 발생: {e}")
        with tab3:
            try:
                barchart1.main()
            except Exception as e:
                st.error(f"barchart1 모듈 실행 중 오류 발생: {e}")

    elif option == "파일관리":
        tab11, tab12, tab13, tab14, tab15 = st.tabs(["Read Files", "Upload Files", "PDF분할", "PDF병합", "URL추출"])
        with tab11:
            try:
                fileupload1.main()
            except Exception as e:
                st.error(f"fileupload1 모듈 실행 중 오류 발생: {e}")
        with tab12:
            try:
                fileupload2.main()
            except Exception as e:
                st.error(f"fileupload2 모듈 실행 중 오류 발생: {e}")
        with tab13:
            try:
                pdfsplit1.main()
            except Exception as e:
                st.error(f"fileupload2 모듈 실행 중 오류 발생: {e}")
        with tab14:
            try:
                pdfmerge1.main()
            except Exception as e:
                st.error(f"fileupload2 모듈 실행 중 오류 발생: {e}")
        with tab15:
            try:
                extracturl1.main()
            except Exception as e:
                st.error(f"fileupload2 모듈 실행 중 오류 발생: {e}")      

    elif option == "옵션 3":
        tab5, tab6 = st.tabs(["탭 5", "탭 6"])
        with tab5:
            st.header("탭 5 내용")
            st.write("옵션 3의 탭 5 내용입니다.")
        with tab6:
            st.header("탭 6 내용")
            st.write("옵션 3의 탭 6 내용입니다.")

if __name__ == '__main__':
    main()