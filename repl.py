import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
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
    for pl in playlists:
        title = pl["snippet"]["title"]
        access = pl["status"]["privacyStatus"]
        print(f"{title} ({access})")
    if not playlists:
        print("No playlists found.")

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
