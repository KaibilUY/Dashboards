"""
regenerar_token_drive.py
Regenera token_drive.pkl con scopes completos de lectura y escritura.
Ejecutar en la PC local (C:\Users\d_tel\Documents\dashboards\)
"""

import pickle
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Scopes necesarios: lectura + escritura en Drive
SCOPES = [
    "https://www.googleapis.com/auth/drive",  # lectura y escritura completa
]

TOKEN_PATH      = "token_drive.pkl"
CREDS_PATH      = "credentials_drive.json"

def main():
    creds = None

    # Intentar cargar token existente
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)
        print(f"Token existente cargado.")
        if creds and creds.valid:
            print("Token vigente — verificando scopes...")
            if hasattr(creds, 'scopes') and creds.scopes:
                print(f"Scopes actuales: {creds.scopes}")
                if "https://www.googleapis.com/auth/drive" in creds.scopes:
                    print("✅ Ya tiene scope de escritura. No es necesario regenerar.")
                    return
            print("⚠️  Scopes insuficientes o no verificables. Regenerando...")

    # Forzar nuevo flujo OAuth
    print("\nAbriendo navegador para autorizar acceso a Google Drive...")
    flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    # Guardar nuevo token
    with open(TOKEN_PATH, "wb") as f:
        pickle.dump(creds, f)

    print(f"\n✅ Token regenerado y guardado en {TOKEN_PATH}")
    print(f"Scopes otorgados: {creds.scopes}")
    print("\nAhora copiá el nuevo token al VPS:")
    print("  scp token_drive.pkl root@204.168.220.105:/opt/kaibil/bot/")
    print("  pm2 restart realptt-export")

if __name__ == "__main__":
    main()
