import pickle
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

TOKEN_PATH = "token_drive.pkl"

with open(TOKEN_PATH, "rb") as f:
    creds = pickle.load(f)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    with open(TOKEN_PATH, "wb") as f:
        pickle.dump(creds, f)

drive = build("drive", "v3", credentials=creds)

for nombre in ["semaforo_estado.csv", "moviles_estado.csv"]:
    r = drive.files().list(
        q=f"name='{nombre}' and trashed=false",
        fields="files(id, name, modifiedTime)"
    ).execute()
    archivos = r.get("files", [])
    if archivos:
        for f in archivos:
            print(f"Nombre: {f['name']}")
            print(f"ID:     {f['id']}")
            print(f"Modificado: {f['modifiedTime']}")
            print()
    else:
        print(f"No encontrado: {nombre}")
