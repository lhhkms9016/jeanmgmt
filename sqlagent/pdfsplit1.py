import streamlit as st
import os
import zipfile
import fitz  # PyMuPDF
from io import BytesIO

def split_pdf(uploaded_file, output_folder):
    """PDF 파일을 페이지별로 분할하고 압축합니다."""

    pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    file_list = []

    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        new_pdf = fitz.open()
        new_pdf.insert_pdf(pdf_document, from_page=page_number, to_page=page_number)
        
        output_filename = f"page_{page_number + 1}.pdf"
        output_path = os.path.join(output_folder, output_filename)
        new_pdf.save(output_path)
        file_list.append(output_path)
        new_pdf.close()
    
    pdf_document.close()
    return file_list

def create_zip(file_list):
    """주어진 파일 목록을 zip 파일로 압축합니다."""
    
    zip_buffer = BytesIO()  # 메모리 버퍼에 zip 파일 생성
    
    with zipfile.ZipFile(zip_buffer, 'w') as zipf:
        for file_path in file_list:
            zipf.write(file_path, os.path.basename(file_path))
    
    zip_buffer.seek(0) # 버퍼의 시작 위치로 이동
    return zip_buffer
    

def main():
    st.title("PDF 분할 프로그램")

    uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])

    if uploaded_file is not None:
        if st.button("실행"):
            temp_dir = "temp_pdf_split" #임시 폴더 생성
            os.makedirs(temp_dir, exist_ok=True)
            
            with st.spinner("PDF 분할 및 압축 중..."):
                file_list = split_pdf(uploaded_file, temp_dir)
                zip_buffer = create_zip(file_list)
                st.success("PDF 분할 및 압축 완료!")
            
            st.download_button(
                label="분할된 PDF 다운로드 (ZIP)",
                data=zip_buffer,
                file_name="split_pdf.zip",
                mime="application/zip",
            )
            
            # 임시 폴더 및 파일 삭제
            for file_path in file_list:
              os.remove(file_path)
            os.rmdir(temp_dir)

if __name__ == "__main__":
    main()