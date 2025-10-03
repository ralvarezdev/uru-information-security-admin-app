import io
import zipfile

import streamlit as st
import grpc
import pandas as pd

from google.protobuf.empty_pb2 import Empty
from microservice.grpc import (
	DECRYPTER_GRPC_HOST,
	DECRYPTER_GRPC_PORT
)
from microservice.grpc.decrypter import create_grpc_client
from ralvarezdev import decrypter_pb2

# UI
st.set_page_config(layout="wide")
st.title("Admin Client: Manage Received Files")

# gRPC Client Setup
try:
    stub = create_grpc_client(DECRYPTER_GRPC_HOST, DECRYPTER_GRPC_PORT)
except Exception as e:
    st.error(f"Could not connect to gRPC server: {e}")
    st.stop()

@st.cache_data(ttl=60)
def get_active_files():
    try:
        response = stub.ListActiveFiles(Empty())
        file_list = []
        for company in response.company_files:
            for filename in company.filenames:
                file_list.append({"Company (CN)": company.common_name, "File Name": filename})
        return file_list
    except grpc.RpcError as e:
        st.error(f"Error listing files: {e.details()}")
        return []

tab1, tab2 = st.tabs(["View & Download Files", "Manage Files"])

with tab1:
    st.header("Received Files")
    if st.button("Refresh List"):
        st.cache_data.clear()

    active_files = get_active_files()

    if not active_files:
        st.info("No active Files in the system.")
    else:
        df = pd.DataFrame(active_files)
        st.dataframe(df, use_container_width=True)

        st.subheader("Download  File")
        filenames = [f['File Name'] for f in active_files]
        selected_file = st.selectbox("Select a File to decrypt and decompress", options=filenames)

        if st.button("Decrypt & Prepare Download"):
            if selected_file:
                request = decrypter_pb2.DecryptFileRequest(filename=selected_file)
                try:
                    with st.spinner(f"Decrypting '{selected_file}'..."):
                        response_iterator = stub.DecryptFile(request)
                        decrypted_content = b"".join([r.file_content for r in response_iterator])

                    st.success("File successfully decrypted. Now decompressing...")

                    try:
                        # Create a memory buffer with .zip content
                        zip_buffer = io.BytesIO(decrypted_content)
                        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
                            if not zip_ref.namelist():
                                st.error("Error: Received .zip is empty and cannot be decompressed.")
                                st.stop()

                            original_filename = zip_ref.namelist()[0]
                            uncompressed_content = zip_ref.read(original_filename)

                        st.info(f"'{original_filename}' decompressed successfully.")

                        st.download_button(
                            label=f"Download '{original_filename}' (Original)",
                            data=uncompressed_content,
                            file_name=original_filename
                        )

                    except zipfile.BadZipFile:
                        st.error("Error: The received file is not a valid .zip. Cannot decompress.")
                        st.download_button(
                            label=f"Download corrupted file '{selected_file}' for analysis",
                            data=decrypted_content,
                            file_name=f"corrupted_{selected_file}"
                        )

                except grpc.RpcError as e:
                    st.error(f"Error while decrypting file: {e.details()}")

with tab2:
    st.header("Delete Files")
    st.warning("Actions in this section are irreversible.")

    col1, col2 = st.columns(2)

    # Delete specific file
    with col1:
        st.subheader("Delete a specific file")
        with st.form("remove_one_form"):
            cn_to_remove = st.text_input("Company Common Name (CN)")
            fn_to_remove = st.text_input("File Name to delete")
            submitted_one = st.form_submit_button("Delete File")
            if submitted_one:
                if cn_to_remove and fn_to_remove:
                    request = decrypter_pb2.RemoveEncryptedFileRequest(common_name=cn_to_remove, filename=fn_to_remove)
                    try:
                        stub.RemoveEncryptedFile(request)
                        st.success(f"File '{fn_to_remove}' from company '{cn_to_remove}' deleted.")
                        st.cache_data.clear()
                    except grpc.RpcError as e:
                        st.error(f"Error deleting file: {e.details()}")
                else:
                    st.warning("Both fields are required.")

    # Delete ALL files
    with col2:
        st.subheader("Delete ALL files")
        confirm = st.checkbox("I understand this will delete all encrypted files from all companies.")
        if st.button("Delete All", disabled=not confirm, type="primary"):
            try:
                with st.spinner("Deleting all files..."):
                    stub.RemoveEncryptedFiles(Empty())
                st.success("All files have been deleted.")
                st.cache_data.clear()
            except grpc.RpcError as e:
                st.error(f"Error during bulk deletion: {e.details()}")
