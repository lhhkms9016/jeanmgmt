import streamlit as st
import os
import pandas as pd
from PIL import Image

@st.cache_data
def load_image(image_file):
    if image_file is not None:
        try:
            img = Image.open(image_file)
            return img
        except Exception as e:
            st.error(f"Error loading image: {e}")
            return None
    else:
        return None

def save_uploaded_file(uploadedfile, save_dir):
    if uploadedfile is None:
        return st.error("No file uploaded.")

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    save_path = os.path.join(save_dir, uploadedfile.name)

    with open(save_path, "wb") as f:
        f.write(uploadedfile.getbuffer())

    return st.success(f"Saved file : {uploadedfile.name} in {save_path}")

def main():
    st.title("특정 폴더로 파일 업로드")

    menu = ["Image", "CSV"]
    choice = st.selectbox("파일 타입 선택", menu, key="fileupload2_menu") #selectbox를 title 밑으로 이동

    save_directory = st.text_input("파일 저장 경로를 입력하세요.", value="D:\\lhhkms", key="fileupload2_save_directory") #저장경로 text_input 입력받기.

    if choice == "Image":
        st.subheader("Upload Images")
        image_file = st.file_uploader("Upload An Image", type=['png', 'jpeg', 'jpg'], key="fileupload2_image_file")

        if image_file is not None:
            file_details = {"FileName": image_file.name, "FileType": image_file.type}
            st.write(file_details)
            img = load_image(image_file)

            if img is not None:
                st.image(img, width=250)

            save_uploaded_file(image_file, save_directory)

    elif choice == "CSV":
        st.subheader("CSV")
        datafile = st.file_uploader("Upload CSV", type=['csv'], key="fileupload2_data_file")

        if datafile is not None:
            file_details = {"FileName": datafile.name, "FileType": datafile.type}
            df = pd.read_csv(datafile)
            st.dataframe(df)
            save_uploaded_file(datafile, save_directory)

if __name__ == '__main__':
    main()