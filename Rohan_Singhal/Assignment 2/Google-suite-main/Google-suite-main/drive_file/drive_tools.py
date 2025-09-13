import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from langchain_core.tools import tool
from googleapiclient.http import MediaFileUpload
import io
from googleapiclient.http import MediaIoBaseDownload

ALL_SCOPES = [
    # Gmail scopes
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    
    # Calendar scopes
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
    
    # Drive scopes
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.readonly"
]



def get_access_token(user_email):

    print(f"🔐 Authenticating user: {user_email}")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    users_file = os.path.join(script_dir, 'users.json')
    
    with open(users_file, 'r') as f:
        users = json.load(f)
    
    user_index = None
    for i, user in enumerate(users):
        if user['email'] == user_email:
            user_index = i
            break
    
    creds = None
    if user_index is not None and 'access_token' in users[user_index] and users[user_index]['access_token'] != "your_access_token":
        token_info = {
            'token': users[user_index]['access_token'],
            'refresh_token': users[user_index].get('refresh_token'),
            'token_uri': "https://oauth2.googleapis.com/token",
            'client_id': users[user_index].get('client_id'),
            'client_secret': users[user_index].get('client_secret'),
            'scopes': ALL_SCOPES
        }
        
        creds = Credentials.from_authorized_user_info(token_info)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                token_info = {
                    'access_token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'client_id': creds.client_id,
                    'client_secret': creds.client_secret
                }

                if user_index is not None:
                    users[user_index].update(token_info)
                    print(f"✅ Updated credentials for existing user: {user_email}")
                with open(users_file, 'w') as f:
                    json.dump(users, f, indent=4)
            except Exception as e:
                print(f"❌ Error refreshing token: {e}")
                print("🔄 User needs to re-authenticate. Please run the authentication flow again.")
                return None
        else: 
           print("user is not registered")
           return None
    
    print(f"🎯 Access token obtained successfully for: {user_email}")
    return creds

@tool
def drive_upload(user_email: str, file_path: str) -> str:
  """Uploads a file to the user's Google Drive.
  
  Args:
      user_email: Email address of the Google account
      file_path: Path to the file to upload
      
  Returns:
      File ID of the uploaded file, or error message if failed
  """
  try:
    creds = get_access_token(user_email)
    service = build("drive", "v3", credentials=creds)

    file_name = os.path.basename(file_path)
    file_extension = os.path.splitext(file_name)[1].lower()
    
    mime_type_map = {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
        '.pdf': 'application/pdf', '.txt': 'text/plain', 
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    mime_type = mime_type_map.get(file_extension, 'application/octet-stream')

    file_metadata = {"name": file_name}
    media = MediaFileUpload(file_path, mimetype=mime_type)
    
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )
    
    file_id = file.get("id")
    print(f' File uploaded successfully. File ID: {file_id}')
    return file_id

  except HttpError as error:
    error_msg = f" An error occurred during upload: {error}"
    print(error_msg)
    return error_msg
  except Exception as error:
    error_msg = f" Unexpected error: {error}"
    print(error_msg)
    return error_msg


@tool
def drive_download_file(user_email: str, file_id: str, local_file_path: str = None) -> str:
  """Downloads a file from Google Drive and saves it locally.
  
  Args:
      user_email: Email address of the Google account
      file_id: ID of the file to download from Google Drive
      local_file_path: Local path where to save the file (optional, will auto-generate if not provided)
      
  Returns:
      Local file path where the file was saved, or error message if failed
  """
  try:
    creds = get_access_token(user_email)
    service = build("drive", "v3", credentials=creds)
    
    
    if local_file_path is None:
        file_metadata = service.files().get(fileId=file_id).execute()
        filename = file_metadata.get('name', f'downloaded_file_{file_id}')
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        local_file_path = os.path.join(script_dir, f"downloaded_{filename}")

    request = service.files().get_media(fileId=file_id)
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request)
    done = False
    while done is False:
      status, done = downloader.next_chunk()
      print(f"Download {int(status.progress() * 100)}%")

   
    with open(local_file_path, 'wb') as f:
        f.write(file.getvalue())
    
    print(f"✅ File downloaded successfully to: {local_file_path}")
    return local_file_path

  except HttpError as error:
    error_msg = f"❌ An error occurred during download: {error}"
    print(error_msg)
    return error_msg
  except Exception as error:
    error_msg = f"❌ Unexpected error: {error}"
    print(error_msg)
    return error_msg


@tool
def drive_search_file(user_email: str, query: str = None, file_name: str = None, mime_type: str = None, max_results: int = 10) -> str:
  """Search files in Google Drive based on various criteria.
  
  Args:
      user_email: Email address of the Google account
      query: Custom query string for Google Drive search (optional)
      file_name: Specific file name to search for - partial match (optional)
      mime_type: File type to filter (e.g., 'image/jpeg', 'application/pdf', 'text/plain') (optional)
      max_results: Maximum number of results to return (default: 10)
  
  Returns:
      String containing formatted list of files found, or error message if failed
  """
  try:
    creds = get_access_token(user_email)
    service = build("drive", "v3", credentials=creds)
    files = []
    page_token = None
    
    search_query = []
    
    if query:
        search_query.append(query)
    else:
        if file_name:
            search_query.append(f"name contains '{file_name}'")
        if mime_type:
            search_query.append(f"mimeType='{mime_type}'")
    
   
    final_query = " and ".join(search_query) if search_query else None
    
    print(f"🔍 Searching Google Drive with query: {final_query or 'All files'}")
    
    while True:
      response = (
          service.files()
          .list(
              q=final_query,
              spaces="drive",
              fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)",
              pageToken=page_token,
              pageSize=min(max_results, 100)
          )
          .execute()
      )
      for file in response.get("files", []):
        file_info = {
            'id': file.get("id"),
            'name': file.get("name"),
            'mimeType': file.get("mimeType"),
            'size': file.get("size", "Unknown"),
            'modifiedTime': file.get("modifiedTime")
        }
        files.append(file_info)
        
        if len(files) >= max_results:
            break
      
      page_token = response.get("nextPageToken", None)
      if page_token is None or len(files) >= max_results:
        break

    # Format results as string
    if files:
        result = f"Found {len(files)} file(s):\n"
        for i, file in enumerate(files, 1):
            size_info = f" ({file['size']} bytes)" if file['size'] != "Unknown" else ""
            result += f"{i}. {file['name']} (ID: {file['id']}) - Type: {file['mimeType']}{size_info}\n"
        print(result)
        return result
    else:
        error_msg = " No files found matching the search criteria."
        print(error_msg)
        return error_msg

  except HttpError as error:
    error_msg = f"An error occurred during search: {error}"
    print(error_msg)
    return error_msg
  except Exception as error:
    error_msg = f"Unexpected error: {error}"
    print(error_msg)
    return error_msg



