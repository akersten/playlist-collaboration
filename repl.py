import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import time

SCOPES = ["https://www.googleapis.com/auth/youtube"]
TOKEN_FILE = "token.json"
CLIENT_SECRETS_FILE = "client_secrets.json"  # You need to download this from Google Cloud Console

# Color codes for alerts
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def is_authenticated():
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            return creds and creds.valid
        except Exception:
            return False
    return False

def authenticate():
    if is_authenticated():
        print(f"{YELLOW}Already authenticated. Run 'auth' again to re-authenticate.{RESET}")
        confirm = input("Proceed with authentication? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Authentication cancelled.")
            return None
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(TOKEN_FILE, "w") as token:
        token.write(creds.to_json())
    print(f"{GREEN}Authenticated and token saved.{RESET}")
    return creds

def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        creds = authenticate()
    return build("youtube", "v3", credentials=creds)

def list_playlists():
    youtube = get_authenticated_service()
    request = youtube.playlists().list(
        part="snippet,status",
        mine=True,
        maxResults=50
    )
    response = request.execute()
    playlists = response.get("items", [])
    if not playlists:
        print("No playlists found.")
        return
    for idx, pl in enumerate(playlists, 1):
        title = pl["snippet"]["title"]
        access = pl["status"]["privacyStatus"]
        print(f"{idx}. {title} ({access})")
    while True:
        sel = input("Select a playlist number to view videos, or press Enter to return: ").strip()
        if sel == '':
            break
        if not sel.isdigit() or not (1 <= int(sel) <= len(playlists)):
            print("Invalid selection. Try again.")
            continue
        playlist_id = playlists[int(sel)-1]["id"]
        show_playlist_videos(youtube, playlist_id)
        break

def show_playlist_videos(youtube, playlist_id):
    all_items = []
    next_page_token = None
    while True:
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        items = response.get("items", [])
        all_items.extend(items)
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
    if not all_items:
        print("No videos found in this playlist.")
        return
    print("Videos:")
    for idx, item in enumerate(all_items, 1):
        title = item["snippet"]["title"]
        added_by = item["snippet"].get("videoOwnerChannelTitle", "Unknown")
        print(f"  {idx}. {title} (added by: {added_by})")
    while True:
        swap_input = input("Enter two comma separated numbers to swap videos, or press Enter to return: ").strip()
        if swap_input == '':
            break
        try:
            first, second = map(int, swap_input.split(','))
            if not (1 <= first <= len(all_items)) or not (1 <= second <= len(all_items)):
                print("Invalid numbers. Try again.")
                continue
            if first == second:
                print("Numbers must be different.")
                continue
            # Get video IDs and playlistItem IDs
            first_item = all_items[first-1]
            second_item = all_items[second-1]
            first_id = first_item["id"]
            second_id = second_item["id"]
            first_pos = first_item["snippet"]["position"]
            second_pos = second_item["snippet"]["position"]
            # Swap positions using YouTube API
            youtube.playlistItems().update(
                part="snippet",
                body={
                    "id": first_id,
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": first_item["snippet"]["resourceId"],
                        "position": second_pos
                    }
                }
            ).execute()
            youtube.playlistItems().update(
                part="snippet",
                body={
                    "id": second_id,
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": second_item["snippet"]["resourceId"],
                        "position": first_pos
                    }
                }
            ).execute()
            print(f"Swapped video {first} and {second}.")
            time.sleep(1)
            # Refresh list
            all_items = []
            next_page_token = None
            while True:
                request = youtube.playlistItems().list(
                    part="snippet",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                items = response.get("items", [])
                all_items.extend(items)
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
            for idx, item in enumerate(all_items, 1):
                title = item["snippet"]["title"]
                added_by = item["snippet"].get("videoOwnerChannelTitle", "Unknown")
                print(f"  {idx}. {title} (added by: {added_by})")
        except Exception as e:
            print(f"Error: {e}. Try again.")

# Print authentication status on startup
if is_authenticated():
    print(f"{GREEN}You are already authenticated with YouTube!{RESET}")
else:
    print(f"{RED}Not authenticated. Run 'auth' to authenticate with YouTube.{RESET}")

print("Quick & Dirty Python REPL. Type 'exit' to quit.")
print("Commands: auth, list, exit")
while True:
    try:
        cmd = input('>>> ')
        if cmd.strip().lower() == 'exit':
            break
        elif cmd.strip().lower() == 'auth':
            authenticate()
        elif cmd.strip().lower() == 'list':
            list_playlists()
        else:
            result = eval(cmd, globals())
            if result is not None:
                print(result)
    except Exception as e:
        print(f"Error: {e}")
