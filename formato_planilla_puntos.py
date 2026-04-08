import pickle
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

TOKEN_PATH = "token_drive.pkl"
SHEET_ID   = "1fPzrrZRfI_FlfEhznQ_QtT2o1JGJFGXEbLLzls2MY9E"

with open(TOKEN_PATH, "rb") as f:
    creds = pickle.load(f)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    with open(TOKEN_PATH, "wb") as f:
        pickle.dump(creds, f)

sheets = build("sheets", "v4", credentials=creds)

meta = sheets.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
grid_id = meta["sheets"][0]["properties"]["sheetId"]
print(f"Grid ID: {grid_id}")

requests = [
    {
        "repeatCell": {
            "range": {"sheetId": grid_id, "startRowIndex": 0, "endRowIndex": 1},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.118, "green": 0.227, "blue": 0.373},
                    "textFormat": {
                        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                        "bold": True
                    }
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }
    },
    {
        "autoResizeDimensions": {
            "dimensions": {
                "sheetId": grid_id,
                "dimension": "COLUMNS",
                "startIndex": 0,
                "endIndex": 9
            }
        }
    }
]

sheets.spreadsheets().batchUpdate(
    spreadsheetId=SHEET_ID,
    body={"requests": requests}
).execute()

print("Formato aplicado OK")
print(f"\nID planilla para el VPS:")
print(f'SHEET_ID_PUNTOS = "{SHEET_ID}"')
