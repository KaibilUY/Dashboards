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

IDS = {
    "semaforo_estado.csv": "1_72lWUbaxgYSCAgsVsBK6zF7_aINCN08",
    "moviles_estado.csv":  "1R_TBA992emV_mzR2XJEoBIeLYl5kEe0g",
}

for nombre, file_id in IDS.items():
    drive.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"},
    ).execute()
    print(f"✅ {nombre} — acceso público habilitado")
    print(f"   URL directa: https://drive.google.com/uc?export=download&id={file_id}")
    print()
