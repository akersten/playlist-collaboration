import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
TOKEN_FILE = "token.json"
CLIENT_SECRETS_FILE = "client_secrets.json"  # You need to download this from Google Cloud Console

def authenticate():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(TOKEN_FILE, "w") as token:
        token.write(creds.to_json())
    print("Authenticated and token saved.")
    return creds

def get_authenticated_service():
    from google.oauth2.credentials import Credentials
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
