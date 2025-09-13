import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from langchain_core.tools import tool
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
def gmail_send_message(user_email, message_content, subject, receiver_email):
  """Send an email message via Gmail API.
    input args:
      user_email: The email address of the user sending the email
      message_content: The content of the email message
      subject: The subject of the email
      receiver_email: The email address of the recipient
    output args:
      message: The sent email message
  """
  creds = get_access_token(user_email)

  try:
    service = build("gmail", "v1", credentials=creds)
    message = EmailMessage()

    message.set_content(message_content)

    message["To"] = receiver_email
    message["From"] = user_email
    message["Subject"] = subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"raw": encoded_message}
    send_message = (
        service.users()
        .messages()
        .send(userId="me", body=create_message)
        .execute()
    )
    print(f'Message Id: {send_message["id"]}')
  except HttpError as error:
    print(f"An error occurred: {error}")
    send_message = None
  return send_message
@tool
def gmail_create_draft(user_mail, message_content, receiver_email = "srohan24@iitk.ac.in", subject = "Automated draft"):
  """Create and insert a draft email.
   Print the returned draft's message and id.
   Returns: Draft object, including draft id and message meta data.

   input args:
     user_mail: The email address of the user creating the draft
     message_content: The content of the email message
     receiver_email: The email address of the recipient
     subject: The subject of the email
  """
  creds = get_access_token(user_mail)

  try:
    service = build("gmail", "v1", credentials=creds)

    message = EmailMessage()

    message.set_content(message_content)

    message["To"] = receiver_email
    message["From"] = user_mail
    message["Subject"] = subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"message": {"raw": encoded_message}}
    draft = (
        service.users()
        .drafts()
        .create(userId="me", body=create_message)
        .execute()
    )

    print(f'Draft id: {draft["id"]}\nDraft message: {draft["message"]}')

  except HttpError as error:
    print(f"An error occurred: {error}")
    draft = None

  return draft
@tool
def gmail_list_drafts(user_email):
  """List all draft emails for a user.
   input args:
     user_email: The email address of the user
   output args:
     drafts: A list of draft emails
  """
  creds = get_access_token(user_email)

  try:
    service = build("gmail", "v1", credentials=creds)

    drafts = (
        service.users()
        .drafts()
        .list(userId="me")
        .execute()
    )

    print(f'List of drafts: {drafts}')

  except HttpError as error:
    print(f"An error occurred: {error}")
    drafts = None

  return drafts

@tool
def gmail_search_mail(user_email, query):
    """Search for emails matching a query.
    input args:
      user_email: The email address of the user
      query: The search query
    output args:
      messages: A list of matching email messages
    """
    creds = get_access_token(user_email)

    try:
        service = build("gmail", "v1", credentials=creds)

        results = (
            service.users()
            .messages()
            .list(userId="me", q=query)
            .execute()
        )

        messages = results.get("messages", [])
        print(f'Found messages: {messages}')

    except HttpError as error:
        print(f"An error occurred: {error}")
        messages = None

    return messages
@tool
def gmail_delete_draft(user_email, draft_id, confirm: bool = False):
  """Delete a draft email.
  input args:
    user_email: The email address of the user
    draft_id: The ID of the draft to delete
    confirm: Must be True to actually delete; if False, the tool will ask for confirmation
  output args:
    success: Boolean indicating if the deletion was successful
  """
  if not confirm:
    return (
      f"Confirmation required to delete draft '{draft_id}'. "
      f"Reply 'yes' and call gmail_delete_draft with confirm=true to proceed."
    )

  creds = get_access_token(user_email)

  try:
    service = build("gmail", "v1", credentials=creds)

    service.users().drafts().delete(userId="me", id=draft_id).execute()
    print(f'Successfully deleted draft: {draft_id}')
    success = True

  except HttpError as error:
    print(f"An error occurred: {error}")
    success = False

  return success
@tool
def gmail_read_mail(user_mail, message_id):
    """Read a specific email message.
    input args:
      user_mail: The email address of the user
      message_id: The ID of the message to read
    output args:
      message: The email message content
    """
    creds = get_access_token(user_mail)

    try:
        service = build("gmail", "v1", credentials=creds)

        message = (
            service.users()
            .messages()
            .get(userId="me", id=message_id)
            .execute()
        )

        print(f'Read message: {message}')

    except HttpError as error:
        print(f"An error occurred: {error}")
        message = None

    return message

if __name__ == "__main__":
   user_email = "rohan2007singhal@gmail.com"
   message_content = "This is a test email."
   subject = "Test Email"
   receiver_email = "srohan24@iitk.ac.in"


