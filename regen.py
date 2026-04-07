import pickle 
from google_auth_oauthlib.flow import InstalledAppFlow 
SCOPES = ['https://www.googleapis.com/auth/drive'] 
flow = InstalledAppFlow.from_client_secrets_file('credentials_drive.json', SCOPES) 
creds = flow.run_local_server(port=0) 
open('token_drive.pkl', 'wb').write(__import__('pickle').dumps(creds)) 
print('Token OK:', creds.scopes) 
