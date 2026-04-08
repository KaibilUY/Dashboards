"""
crear_planilla_puntos_control.py
Crea la planilla de puntos de control en Google Drive dentro de la carpeta GPS-Moviles.
Ejecutar en C:\\Users\\d_tel\\Documents\\dashboards\\
"""

import pickle
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

TOKEN_PATH  = "token_drive.pkl"
FOLDER_ID   = "17wPMql7NJkv54Y6oznzRoQdyKz0a4cmb"

# Puntos de control iniciales - Zorzales
PUNTOS = [
    ["Nariño 2252",        "Zorzales", -34.874825, -56.051462, 80, 30, "pasada", "todos", "si"],
    ["Acosta y Lara 7240", "Zorzales", -34.870389, -56.050135, 80, 30, "pasada", "todos", "si"],
    ["Santander 2254",     "Zorzales", -34.873374, -56.050754, 80, 30, "pasada", "todos", "si"],
]

HEADERS = [
    "nombre", "barrio", "lat", "lng",
    "radio_metros", "ventana_minutos", "tipo",
    "turno", "activo"
]

def get_services():
    with open(TOKEN_PATH, "rb") as f:
        creds = pickle.load(f)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)

    drive   = build("drive",   "v3", credentials=creds)
    sheets  = build("sheets",  "v4", credentials=creds)
    return drive, sheets

def main():
    drive, sheets = get_services()

    # Crear Spreadsheet
    spreadsheet = {
        "properties": {"title": "Puntos de Control GPS"},
        "sheets": [{"properties": {"title": "Puntos"}}]
    }
    result = sheets.spreadsheets().create(body=spreadsheet).execute()
    sheet_id    = result["spreadsheetId"]
    sheet_url   = result["spreadsheetUrl"]
    print(f"Planilla creada: {sheet_url}")

    # Mover a carpeta GPS-Moviles
    file = drive.files().get(fileId=sheet_id, fields="parents").execute()
    previous_parents = ",".join(file.get("parents", []))
    drive.files().update(
        fileId=sheet_id,
        addParents=FOLDER_ID,
        removeParents=previous_parents,
        fields="id, parents"
    ).execute()
    print(f"Movida a carpeta GPS-Moviles")

    # Escribir headers + datos
    values = [HEADERS] + PUNTOS
    sheets.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range="Puntos!A1",
        valueInputOption="RAW",
        body={"values": values}
    ).execute()
    print(f"Datos cargados: {len(PUNTOS)} puntos de control")

    # Formato: encabezado en negrita y color
    requests = [
        {
            "repeatCell": {
                "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1},
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
                    "sheetId": 0,
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": 9
                }
            }
        }
    ]
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": requests}
    ).execute()
    print("Formato aplicado")

    print(f"\n✅ Listo!")
    print(f"ID planilla: {sheet_id}")
    print(f"URL: {sheet_url}")
    print(f"\nGuarda el ID para el script del VPS:")
    print(f"SHEET_ID_PUNTOS = \"{sheet_id}\"")

if __name__ == "__main__":
    main()
