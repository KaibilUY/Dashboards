"""
buscar_abonado_historico.py
Busca un abonado en todos los Excel historicos de Hik-Central guardados en Google Drive.
Correr desde la carpeta dashboards donde esta token_drive.pkl

Uso: python buscar_abonado_historico.py
"""

import io
import pickle
import os

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import openpyxl
except ImportError:
    print("Instalando dependencias...")
    os.system("pip install google-api-python-client openpyxl")
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import openpyxl

# ─── CONFIGURACION ───────────────────────────────────────────────
FOLDER_ID = '1fayZgQE5zRmpo9RchY7Ti0nZKU7qeHmS'
ABONADO   = 'KS-5037'          # cambiar si se quiere buscar otro
TOKEN_PKL = 'token_drive.pkl'  # debe estar en la misma carpeta
# ─────────────────────────────────────────────────────────────────

def cargar_credenciales():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    token_path = os.path.join(script_dir, TOKEN_PKL)
    if not os.path.exists(token_path):
        print(f"ERROR: No se encontro {TOKEN_PKL} en {script_dir}")
        exit(1)
    with open(token_path, 'rb') as f:
        return pickle.load(f)

def listar_archivos(service):
    results = service.files().list(
        q=f"'{FOLDER_ID}' in parents and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'",
        orderBy='name asc',
        fields='files(id, name)',
        pageSize=200
    ).execute()
    return results.get('files', [])

def descargar_excel(service, file_id):
    req = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    buf.seek(0)
    return buf

def extraer_fecha(nombre):
    # Nombre formato: Resource Online and Offline Log_YYYYMMDDHHMMSS.xlsx
    try:
        parte = nombre.split('_')[-1].replace('.xlsx', '')
        anio, mes, dia = parte[0:4], parte[4:6], parte[6:8]
        return f"{dia}/{mes}/{anio}"
    except:
        return nombre

def buscar_en_excel(buf, abonado):
    """Retorna lista de (area, estado) donde aparece el abonado"""
    wb = openpyxl.load_workbook(buf, read_only=True, data_only=True)
    ws = wb.active
    
    resultados = []
    headers = None
    
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            headers = [str(c).strip() if c else '' for c in row]
            continue
        if not any(row):
            continue
        
        # Buscar abonado en cualquier columna
        fila_str = [str(c) if c else '' for c in row]
        if abonado in ' '.join(fila_str):
            # Intentar extraer area y estado
            area = fila_str[0] if fila_str else ''
            estado = ''
            for cell in fila_str:
                if cell.lower() in ('online', 'offline'):
                    estado = cell
                    break
            resultados.append((area, estado))
    
    wb.close()
    return resultados

def main():
    print(f"\nBuscando historial de: {ABONADO}")
    print("=" * 60)
    
    creds = cargar_credenciales()
    service = build('drive', 'v3', credentials=creds)
    
    archivos = listar_archivos(service)
    print(f"Total de archivos encontrados: {len(archivos)}\n")
    
    primer_offline = None
    ultimo_online  = None
    
    for f in archivos:
        fecha = extraer_fecha(f['name'])
        print(f"Procesando {fecha}...", end=' ', flush=True)
        
        try:
            buf = descargar_excel(service, f['id'])
            resultados = buscar_en_excel(buf, ABONADO)
            
            if resultados:
                for area, estado in resultados:
                    print(f"{estado or '?'} | {area}")
                    if estado.lower() == 'offline':
                        if primer_offline is None:
                            primer_offline = fecha
                    elif estado.lower() == 'online':
                        ultimo_online = fecha
                        primer_offline = None  # reset si vuelve a online
            else:
                print("NO ENCONTRADO en este reporte")
        except Exception as e:
            print(f"ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("RESUMEN:")
    if primer_offline:
        print(f"  Primer reporte offline consecutivo: {primer_offline}")
    if ultimo_online:
        print(f"  Ultimo reporte online:              {ultimo_online}")
    if not primer_offline and not ultimo_online:
        print(f"  {ABONADO} no fue encontrado en ningun archivo.")
    print("=" * 60)

if __name__ == '__main__':
    main()
