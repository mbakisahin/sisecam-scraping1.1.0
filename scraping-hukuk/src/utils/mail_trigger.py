from azure.storage.blob import BlobServiceClient, ContainerClient
import random

def get_blob_service_client(account_name: str, account_key: str, account_url: str):
    # Create a BlobServiceClient using the account name, key, and URL
    blob_service_client = BlobServiceClient(
        account_url=account_url,
        credential={
            'account_name': account_name,
            'account_key': account_key
        }
    )
    return blob_service_client


def select_file_to_upload(blob_service_client: BlobServiceClient, category: str):
    # Container and base path details
    container_name = "ds-sisecam-mail-sender"
    base_path = f"raw/{category}"
    
    # Get the container client
    container_client = blob_service_client.get_container_client(container_name)
    
    # List all blobs under the category path
    blobs = container_client.list_blobs(name_starts_with=base_path)
    
    # Filter out blobs to select the ones in subdirectories
    blob_list = [blob for blob in blobs if '/' in blob.name]
    
    if not blob_list:
        raise Exception(f"No blobs found in the path: {base_path}")
    
    # Select a random blob
    selected_blob = random.choice(blob_list)
    
    print(f"Selected Blob: {selected_blob.name}")
    return selected_blob.name


def delete_blob_from_path(blob_service_client: BlobServiceClient, blob_path: str):
    container_name = "ds-sisecam-mail-sender"
    
    # Get the blob client
    blob_client = blob_service_client.get_blob_client(container_name, blob_path)
    
    # Delete the blob
    blob_client.delete_blob()
    print(f"Deleted Blob: {blob_path}")


def put_blob_object(blob_service_client: BlobServiceClient, blob_path: str):
    container_name = "ds-sisecam-mail-sender"
    
    # Define new path by replacing 'raw' with 'processed'
    new_blob_path = blob_path.replace("raw/", "processed/")
    
    # Get blob clients for source (raw) and destination (processed)
    source_blob_client = blob_service_client.get_blob_client(container_name, blob_path)
    destination_blob_client = blob_service_client.get_blob_client(container_name, new_blob_path)
    
    # Download the blob's content from the original path
    blob_data = source_blob_client.download_blob().readall()
    
    # Upload the blob to the new location
    destination_blob_client.upload_blob(blob_data)
    
    print(f"Moved Blob from {blob_path} to {new_blob_path}")

