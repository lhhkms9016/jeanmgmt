import streamlit as st
from PIL import Image
import pandas as pd
import docx2txt
from PyPDF2 import PdfReader
import pdfplumber

# Load Images
@st.cache_data
def load_image(image_file):
    img = Image.open(image_file)
    return img

def read_pdf(file):
    pdfReader = PdfReader(file)
    count = len(pdfReader.pages)
    all_page_text = ""
    for i in range(count):
        page = pdfReader.pages[i]
        all_page_text += page.extract_text()
    return all_page_text

def main():
    st.title("파일 텍스트 확인")

    menu = ["Image", "CSV", "문서파일"]
    choice = st.selectbox("파일 타입 선택", menu, key="fileupload1_menu") #selectbox를 title 밑으로 이동

    if choice == "Image":
        st.subheader("Image")
        image_file = st.file_uploader("Upload Images", type=["png", "jpg", "jpeg"], key="fileupload1_image_file")
        if image_file is not None:
            file_details = {"filename": image_file.name, "filetype": image_file.type, "filesize": image_file.size}
            st.write(file_details)
            img = load_image(image_file)
            st.image(img, width=250)

    elif choice == "CSV":
        st.subheader("CSV")
        data_file = st.file_uploader("Upload CSV", type=["csv"], key="fileupload1_data_file")
        if data_file is not None:
            file_details = {"filename": data_file.name, "filetype": data_file.type, "filesize": data_file.size}
            st.write(file_details)
            df = pd.read_csv(data_file)
            st.dataframe(df)

    elif choice == "문서파일":
        st.subheader("문서파일")
        docx_file = st.file_uploader("Upload Document", type=["pdf", "docx", "txt"], key="fileupload1_docx_file")
        if st.button("Process"):
            if docx_file is not None:
                file_details = {"filename": docx_file.name, "filetype": docx_file.type, "filesize": docx_file.size}
                st.write(file_details)
                if docx_file.type == "text/plain":
                    raw_text = str(docx_file.read(), "utf-8")
                    st.text(raw_text)
                elif docx_file.type == "application/pdf":
                    raw_text = read_pdf(docx_file)
                    st.write(raw_text)
                else:
                    raw_text = docx2txt.process(docx_file)
                    st.write(raw_text)

if __name__ == '__main__':
    main()