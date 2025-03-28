import streamlit as st
import os
import fitz  # PyMuPDF
from io import BytesIO

def merge_pdfs(pdf_files):
    """
    Merge multiple PDF files into a single PDF and return it as a BytesIO object.

    Parameters:
    - pdf_files (list): List of uploaded PDF files.
    """
    pdf_writer = fitz.open()

    try:
        for uploaded_file in pdf_files:
            pdf_reader = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            pdf_writer.insert_pdf(pdf_reader)
            pdf_reader.close()

        # Save the merged PDF to a BytesIO object
        merged_pdf_buffer = BytesIO()
        pdf_writer.save(merged_pdf_buffer)
        merged_pdf_buffer.seek(0)  # Reset buffer position to the beginning
        return merged_pdf_buffer

    except Exception as e:
        st.error(f"Error occurred: {e}")
        return None
    finally:
        pdf_writer.close()

def main():
    st.title("PDF 병합 프로그램")

    uploaded_files = st.file_uploader("병합할 PDF 파일을 선택하세요", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        if st.button("병합"):
            if len(uploaded_files) < 2:
                st.warning("2개 이상의 PDF 파일을 선택해주세요.")
            else:
                with st.spinner("PDF 파일 병합 중..."):
                    merged_pdf_buffer = merge_pdfs(uploaded_files)

                if merged_pdf_buffer:
                    st.success("PDF 파일 병합 완료!")
                    st.download_button(
                        label="병합된 PDF 다운로드",
                        data=merged_pdf_buffer,
                        file_name="merged_output.pdf",
                        mime="application/pdf",
                    )

if __name__ == "__main__":
    main()