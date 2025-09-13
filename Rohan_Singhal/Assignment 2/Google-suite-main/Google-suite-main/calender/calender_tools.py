import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from langchain_core.tools import tool
import requests
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
def calender_create_event(user_email ,  event_name , start_datetime,end_datetime,calendar_id = "primary"):
    '''
    Create a calendar event for a specific user and calendar.
    input args:
        user_email: The email of the user creating the event.
        calendar_id: The ID of the calendar to create the event in.
        event_name: The name of the event.
        start_datetime: The start date and time of the event.
        end_datetime: The end date and time of the event.
    output:
        A confirmation message indicating the event has been created.
    '''
    import json

    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    users_file = os.path.join(script_dir, 'users.json')

    access_token = get_access_token(user_email).token
    timezone = "Asia/Kolkata"
    event_data = {
            "summary": event_name + " (created by agent)",
            "start": {
                "dateTime": start_datetime,
                "timeZone": timezone, 
            },
            "end": {
                "dateTime": end_datetime,
                "timeZone": timezone,
            },
        }
    endpoint = (
            f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
        )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    response = requests.post(endpoint, headers=headers, json=event_data)
    if response.status_code == 201:
        event_info = response.json()
        event_id = event_info.get('id')
        event_link = event_info.get('htmlLink')
        return f"✅ Event created successfully!\n📅 Event ID: {event_id}\n🔗 View event: {event_link}"
    else:
        return f"❌ Error creating event (Status {response.status_code}): {response.text}"
    

@tool
def calender_list_events(user_email, calendar_id="primary", max_results=10):
    '''
    List upcoming calendar events for a specific user and calendar.
    input args:
        user_email: The email of the user.
        calendar_id: The ID of the calendar to list events from.
        max_results: Maximum number of events to return (default: 10).
    output:
        A list of upcoming calendar events.
    '''
    import datetime
    
    access_token = get_access_token(user_email)
    if not access_token:
        return "❌ Failed to get access token for user"
    
    # Get current time in ISO format for timeMin parameter
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    
    endpoint = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
    
    headers = {
        "Authorization": f"Bearer {access_token.token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    params = {
        "timeMin": now,
        "maxResults": max_results,
        "singleEvents": True,
        "orderBy": "startTime"
    }
    
    response = requests.get(endpoint, headers=headers, params=params)
    
    if response.status_code == 200:
        events_data = response.json()
        events = events_data.get('items', [])
        
        if not events:
            return " No upcoming events found."
        
        events_list = []
        for event in events:
            summary = event.get('summary', 'No Title')
            start = event.get('start', {})
            end = event.get('end', {})
            
           
            start_time = start.get('dateTime', start.get('date', 'Unknown'))
            end_time = end.get('dateTime', end.get('date', 'Unknown'))
            
            event_link = event.get('htmlLink', '')
            event_id = event.get('id', '')
            
            events_list.append(f"📌 {summary}\n   🕐 Start: {start_time}\n   🕑 End: {end_time}\n   🔗 Link: {event_link}\n")
        
        return f"📅 Upcoming Events ({len(events_list)}):\n\n" + "\n".join(events_list)
    else:
        return f"❌ Error fetching events (Status {response.status_code}): {response.text}"
    
@tool
def calender_search_event(user_email , query, calendar_id="primary", max_results=10):
    '''
    Search for calendar events based on a query.
    input args:
        user_email: The email of the user.
        query: The search query to filter events.
        calendar_id: The ID of the calendar to search in.
        max_results: Maximum number of events to return (default: 10).
    output:
        A list of matching calendar events.
    '''
    access_token = get_access_token(user_email)
    if not access_token:
        return "❌ Failed to get access token for user"
    
    endpoint = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
    
    headers = {
        "Authorization": f"Bearer {access_token.token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    params = {
        "q": query,
        "maxResults": max_results,
        "singleEvents": True,
        "orderBy": "startTime"
    }
    
    response = requests.get(endpoint, headers=headers, params=params)
    
    if response.status_code == 200:
        events_data = response.json()
        events = events_data.get('items', [])
        
        if not events:
            return "📅 No matching events found."
        
        events_list = []
        for event in events:
            summary = event.get('summary', 'No Title')
            start = event.get('start', {})
            end = event.get('end', {})
            
            # Handle both dateTime and date formats
            start_time = start.get('dateTime', start.get('date', 'Unknown'))
            end_time = end.get('dateTime', end.get('date', 'Unknown'))
            
            event_link = event.get('htmlLink', '')
            event_id = event.get('id', '')
            
            events_list.append(f"📌 {summary}\n   🕐 Start: {start_time}\n   🕑 End: {end_time}\n   🔗 Link: {event_link}\n   event_id: {event_id}")
        
        return f"📅 Matching Events ({len(events_list)}):\n\n" + "\n".join(events_list)
    else:
        return f"❌ Error searching events (Status {response.status_code}): {response.text}"
    
@tool
def calender_delete_event(user_email, event_id):
    '''
    Delete a calendar event.
    input args:
        user_email: The email of the user.
        event_id: The ID of the event to delete.
    output:
        A message indicating the result of the deletion.
    '''
    access_token = get_access_token(user_email)
    if not access_token:
        return "❌ Failed to get access token for user"

    endpoint = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}"

    headers = {
        "Authorization": f"Bearer {access_token.token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    response = requests.delete(endpoint, headers=headers)

    if response.status_code == 204:
        return "✅ Event deleted successfully."
    else:
        return f"❌ Error deleting event (Status {response.status_code}): {response.text}"

    

if __name__ == "__main__":
    user_email = "rohan2007singhal@gmail.com"
    event_name = "calvin"
    start_datetime = "2025-09-01T10:00:00"
    end_datetime = "2025-09-01T11:00:00"
    result = calender_delete_event(user_email, "ke4i8s44ja87g4k092k1lad4d4")
    print(result) 