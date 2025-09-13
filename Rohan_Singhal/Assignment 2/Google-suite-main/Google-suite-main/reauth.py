import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
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

def reauth_user(user_email):
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    client_secret_file = os.path.join(script_dir, 'client_secret.json')
    users_file = os.path.join(script_dir, 'users.json')
    
    if not os.path.exists(client_secret_file):
        print(" client_secret.json not found!")
        return False
    
    with open(users_file, 'r') as f:
        users = json.load(f)
    
    user_index = None
    for i, user in enumerate(users):
        if user['email'] == user_email:
            user_index = i
            break
    
    if user_index is None:
        print(f" User {user_email} not found in users.json")
        return False
    
    print(f" Re-authenticating user: {user_email}")
    print(" Please complete the authentication in your browser...")

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secret_file, SCOPES)
        
        creds = flow.run_local_server(port=8080)
        
        users[user_index].update({
            'access_token': creds.token,
            'refresh_token': creds.refresh_token,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret
        })
        
        with open(users_file, 'w') as f:
            json.dump(users, f, indent=4)
        
        print(f" Successfully re-authenticated {user_email}")
        return True
        
    except Exception as e:
        print(f" Authentication failed: {e}")
        return False

if __name__ == "__main__":
    user_email = "ammafinder@gmail.com"
    reauth_user(user_email)
