import streamlit as st
import requests
import xlwings as xw

# 인증 및 토큰 발급 함수
def get_access_token(client_id, client_secret, tenant_id):
    auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "https://graph.microsoft.com/.default"
    }
    response = requests.post(auth_url, data=data)
    token = response.json().get("access_token")
    if token:
        st.success("✅ Access Token 발급 성공!")
        return token
    else:
        st.error(f"❌ Access Token 발급 실패: {response.json()}")
        return None

# 파일 목록 가져오기 함수
def get_sharepoint_files(access_token, site_name, tenant_name, folder_path):
    site_url = f"https://graph.microsoft.com/v1.0/sites/{tenant_name}.sharepoint.com:/sites/{site_name}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(site_url, headers=headers)
    site_id = response.json().get("id")
    if not site_id:
        st.error(f"❌ 사이트 ID를 찾을 수 없습니다: {response.json()}")
        return None

    drive_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    response = requests.get(drive_url, headers=headers)
    drives = response.json().get("value", [])
    drive_id = next((drive["id"] for drive in drives if drive["name"] == "Documents"), None)
    if not drive_id:
        st.error("❌ '문서' 라이브러리를 찾을 수 없습니다.")
        return None

    files_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:{folder_path}:/children"
    response = requests.get(files_url, headers=headers)
    files = response.json().get("value", [])

    return files

def main():
    # Streamlit 앱 설정
    st.title("SharePoint 파일 추출")

    # 입력 필드
    client_id = st.text_input("클라이언트 ID (Client ID)", "")
    client_secret = st.text_input("클라이언트 시크릿 (Client Secret)", "", type="password")
    tenant_id = st.text_input("테넌트 ID (Tenant ID)", "")
    site_name = st.text_input("사이트 이름 (Site Name)", "")
    tenant_name = st.text_input("테넌트 이름 (Tenant Name)", "")
    folder_path = st.text_input("폴더 경로 (Folder Path)", "")

    # 실행 버튼
    if st.button("파일 목록 가져오기 및 엑셀 출력"):
        if not client_id or not client_secret or not tenant_id or not site_name or not tenant_name:
            st.error("모든 필드를 입력해주세요.")
        else:
            access_token = get_access_token(client_id, client_secret, tenant_id)
            if access_token:
                files = get_sharepoint_files(access_token, site_name, tenant_name, folder_path)
                if files:
                    st.write("📄 파일 목록 및 URL:")
                    file_data = []
                    for file in files:
                        file_data.append({"파일명": file["name"], "URL": file["webUrl"]})
                        st.write(f"- {file['name']}: {file['webUrl']}")
                    st.dataframe(file_data)

                    # 엑셀 처리 부분
                    try:
                        app = xw.apps.active
                        wb = app.books.active
                        ws = wb.sheets.active
                        ws.range("A50").value = "파일명"
                        ws.range("B50").value = "URL"
                        row = 51

                        for file in files:
                            ws.range(f"A{row}").value = file['name']
                            ws.range(f"B{row}").value = file['webUrl']
                            row += 1
                        st.success("엑셀 출력 성공!")

                    except xw.XlwingsError as e:
                        st.error(f"❌ 엑셀 오류: {e}. 엑셀이 열려 있는지 확인하세요.")
                    except Exception as e:
                        st.error(f"❌ 엑셀 출력 실패: {e}")
                else:
                    st.warning("해당 폴더에 파일이 없습니다.")

if __name__ == "__main__":
    main()