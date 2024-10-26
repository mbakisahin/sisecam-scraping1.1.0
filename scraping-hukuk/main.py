from src.saved import ScriptRunner

from src.utils.uploadFiles import upload_all
from src.utils.zipFiles import compress, zip_files_with_same_names, copy_raw_data
from src.utils.mail_trigger import put_blob_object, delete_blob_from_path, select_file_to_upload, get_blob_service_client

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

from dotenv import load_dotenv

import os

def check_for_zip_files(main_folder):
    is_there_file_to_upload = False
    for root, dirs, files in os.walk(main_folder):
        for file in files:
            if file.endswith('.zip'):
                is_there_file_to_upload = True
    return is_there_file_to_upload

load_dotenv()

#root directory for data
ROOT_DIR = os.path.join(os.path.join(os.getcwd(), 'data'), 'processed')

source_directory = os.path.join(os.path.join(os.getcwd(), 'data'), 'raw')
destination_directory = os.path.join(os.path.join(os.getcwd(), 'data'), 'processed')

# Azure Storage Account Name
ACCOUNT_NAME = os.getenv("account_name")
# Azure Storage Account URL
ACCOUNT_URL = os.getenv("account_url")
# Account Key
ACCOUNT_KEY = os.getenv("account_key")

if __name__ == '__main__':
    scripts_file_path = 'scripts.txt'

    runner = ScriptRunner()
    scripts = runner.read_scripts_from_file(scripts_file_path)
    runner.run_scripts(scripts)

    copy_raw_data(source_directory, destination_directory)

    files_, destination = zip_files_with_same_names(source_directory, destination_directory)

    index = 0
    for item, values in files_.items():
        compress(values, destination[index], item + '.zip')
        index += 1

    os.chdir(ROOT_DIR)
    for root_dir in os.listdir():
        upload_all(ACCOUNT_KEY, ACCOUNT_NAME, ACCOUNT_URL, root_dir, 'ds-sisecam-hukuk')

    if not check_for_zip_files(ROOT_DIR):
        blob_service_client = get_blob_service_client(ACCOUNT_NAME, ACCOUNT_KEY, ACCOUNT_URL)

        # Select, move, and delete a blob
        selected_blob = select_file_to_upload(blob_service_client, "hukuk")
        put_blob_object(blob_service_client, selected_blob)
        delete_blob_from_path(blob_service_client, selected_blob)