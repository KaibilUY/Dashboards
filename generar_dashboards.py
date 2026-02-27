"""
=============================================================
  GENERADOR AUTOMÁTICO DE DASHBOARDS - KAIBIL / SEGURA
  Hik-Central Professional → GitHub Pages
  Configurado para: Kaibiluy / d_tel
=============================================================
"""

import os, re, sys, subprocess
from datetime import datetime
from collections import defaultdict

# ─────────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────────
CARPETA_EXCEL  = r"C:\Users\d_tel\Documents\Hik-Central"
CARPETA_REPO   = r"C:\Users\d_tel\Documents\dashboards"
GITHUB_USUARIO = "Kaibiluy"

# ─────────────────────────────────────────────
#  CLASIFICACIÓN
# ─────────────────────────────────────────────
KC_EXACT = {
    'Constancio Vigil', 'Guillemette 2', 'Guani y Delgado',
    'Rostand', 'NVR KAIBIL EMPRESA'
}

def classify(area):
    a = area.strip()
    if a.upper() == 'BAJAS': return None
    if a.startswith('KS'): return 'KS'
    if a.startswith('KC') or a.lower().startswith('grupo') or a in KC_EXACT: return 'KC'
    if a.startswith('MK'): return 'MK'
    if a.startswith('SG') or a.startswith('MS'): return 'SG'
    if a.startswith('SP'): return 'SP'
    if a.startswith('SR'): return 'SR'
    return 'Otros'

# ─────────────────────────────────────────────
#  LEER EXCEL
# ─────────────────────────────────────────────

GOOGLE_DRIVE_FOLDER_ID = os.environ.get("GDRIVE_FOLDER_ID", "1fayZgQE5zRmpo9RchY7Ti0nZKU7qeHmS")

def descargar_desde_drive(carpeta_destino):
    """Descarga el Excel más reciente desde Google Drive"""
    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        import pickle as pkl

        SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        token_path = os.path.join(os.path.dirname(__file__), 'token_drive.pkl')
        creds_path = os.path.join(os.path.dirname(__file__), 'credentials_drive.json')

        creds = None

        # Modo GitHub Actions: usar variables de entorno
        refresh_token  = os.environ.get('GDRIVE_REFRESH_TOKEN')
        client_id      = os.environ.get('GDRIVE_CLIENT_ID')
        client_secret  = os.environ.get('GDRIVE_CLIENT_SECRET')

        if refresh_token and client_id and client_secret:
            from google.oauth2.credentials import Credentials as OAuthCreds
            creds = OAuthCreds(
                token=None,
                refresh_token=refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=client_id,
                client_secret=client_secret,
                scopes=SCOPES
            )
            creds.refresh(Request())

        # Modo local: usar token guardado o autenticación interactiva
        elif os.path.exists(token_path):
            with open(token_path, 'rb') as tk:
                creds = pkl.load(tk)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(creds_path):
                        print("  ⚠ No se encontró credentials_drive.json")
                        print("  Usando carpeta local como fallback.")
                        return None
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                with open(token_path, 'wb') as tk:
                    pkl.dump(creds, tk)
        else:
            if not os.path.exists(creds_path):
                print("  ⚠ No se encontró credentials_drive.json")
                print("  Usando carpeta local como fallback.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_path, 'wb') as tk:
                pkl.dump(creds, tk)

        service = build('drive', 'v3', credentials=creds)

        # Buscar archivos Excel en la carpeta
        results = service.files().list(
            q=f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and name contains 'Resource' and name contains '.xlsx' and trashed=false",
            orderBy='name desc',
            pageSize=1,
            fields='files(id, name)'
        ).execute()

        files = results.get('files', [])
        if not files:
            print("  ⚠ No se encontraron archivos en Google Drive. Usando carpeta local.")
            return None

        archivo = files[0]
        print(f"  Archivo en Drive: {archivo['name']}")

        if not os.path.exists(carpeta_destino):
            os.makedirs(carpeta_destino)

        ruta_local = os.path.join(carpeta_destino, archivo['name'])

        # Descargar solo si no existe ya localmente
        if not os.path.exists(ruta_local):
            from googleapiclient.http import MediaIoBaseDownload
            import io
            request = service.files().get_media(fileId=archivo['id'])
            fh = io.FileIO(ruta_local, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            print(f"  ✓ Descargado desde Drive")
        else:
            print(f"  ✓ Ya existe localmente")

        return ruta_local

    except ImportError:
        print("  Instalando librerías de Google Drive...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install',
                               'google-api-python-client', 'google-auth-httplib2',
                               'google-auth-oauthlib'])
        print("  ✓ Librerías instaladas. Volvé a ejecutar el script.")
        sys.exit(0)
    except Exception as e:
        print(f"  ⚠ Error al conectar con Drive: {e}")
        print("  Usando carpeta local como fallback.")
        return None


def encontrar_excel(carpeta):
    # Intentar descargar desde Google Drive primero
    ruta = descargar_desde_drive(carpeta)
    if ruta:
        return ruta

    # Fallback: buscar en carpeta local
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
        print(f"  Carpeta creada: {carpeta}")
    archivos = [
        f for f in os.listdir(carpeta)
        if f.lower().replace(' ', '_').startswith('resource_online_and_offline_log')
        and f.endswith('.xlsx')
        and '__1_' not in f
    ]
    if not archivos:
        print(f"\n  ERROR: No se encontró ningún archivo Excel en:\n  {carpeta}")
        print("  Copiá el archivo de Hik-Central a esa carpeta y volvé a ejecutar.")
        sys.exit(1)
    archivos.sort(reverse=True)
    ruta = os.path.join(carpeta, archivos[0])
    print(f"  Archivo local: {archivos[0]}")
    return ruta

def leer_excel(ruta):
    try:
        import openpyxl
    except ImportError:
        print("  Instalando openpyxl...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'openpyxl'])
        import openpyxl

    m = re.search(r'(\d{8})', os.path.basename(ruta))
    fecha = datetime.strptime(m.group(1), '%Y%m%d').strftime('%d/%m/%Y') if m else datetime.today().strftime('%d/%m/%Y')

    area_stats = defaultdict(lambda: {'total': 0, 'offline': 0, 'client': ''})
    wb = openpyxl.load_workbook(ruta)
    ws = wb.active
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i <= 8: continue
        area   = str(row[2]).strip() if row[2] else ''
        status = str(row[3]).strip() if row[3] else ''
        client = classify(area)
        if client is None: continue  # ignorar área BAJAS
        area_stats[area]['total']  += 1
        area_stats[area]['client']  = client
        if status == 'Offline':
            area_stats[area]['offline'] += 1

    areas = []
    for area, v in area_stats.items():
        pct = round(v['offline'] / v['total'] * 100, 1) if v['total'] else 0
        areas.append({
            'client': v['client'], 'area': area,
            'offline': v['offline'], 'total': v['total'], 'pct': pct
        })
    return areas, fecha

# ─────────────────────────────────────────────
#  HTML
# ─────────────────────────────────────────────
def sem(pct):
    if pct > 30: return ('sem-red',   'pct-red',    '#ef4444')
    if pct > 10: return ('sem-yellow','pct-yellow', '#f59e0b')
    return             ('sem-green',  'pct-green',  '#22c55e')

def area_row(a):
    sc, pc, bc = sem(a['pct'])
    pct_str = f"{a['pct']}%" if a['pct'] > 0 else "0%"
    return f"""      <div class="area-row">
        <div class="semaforo {sc}"></div>
        <div class="area-name" title="{a['area']}">{a['area']}</div>
        <div class="area-counts">{a['offline']}/{a['total']} off</div>
        <div class="mini-bar"><div class="mfill" style="width:{min(a['pct'],100)}%;background:{bc}"></div></div>
        <div class="area-pct {pc}">{pct_str}</div>
      </div>"""

CSS = """
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:'Segoe UI',Arial,sans-serif;background:#0f1117;color:#e0e0e0;min-height:100vh}
  .top-bar{background:linear-gradient(135deg,#1a1f2e,#232a3e);padding:18px 32px;
    display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid #2d3550}
  .logo{font-size:2rem;font-weight:900;letter-spacing:3px}
  .sublabel{font-size:0.88rem;letter-spacing:1px;font-weight:600;margin-top:2px}
  .fecha{font-size:0.82rem;color:#8899bb;margin-top:3px}
  .top-bar h1{font-size:1.2rem;font-weight:700;color:#fff}
  .summary-bar{display:flex;gap:16px;padding:20px 32px;background:#13172a;
    border-bottom:1px solid #2d3550;flex-wrap:wrap}
  .s-card{flex:1;min-width:130px;background:#1a1f2e;border-radius:10px;
    padding:14px 18px;border-left:4px solid}
  .s-card .lbl{font-size:0.72rem;color:#8899bb;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px}
  .s-card .val{font-size:1.7rem;font-weight:800}
  .s-card .sub{font-size:0.78rem;color:#aab;margin-top:2px}
  .sem-summary{display:flex;gap:12px;padding:14px 32px 4px;flex-wrap:wrap}
  .sem-badge{display:flex;align-items:center;gap:8px;background:#1a1f2e;
    border-radius:8px;padding:9px 16px;font-size:0.83rem;font-weight:600}
  .dot{width:13px;height:13px;border-radius:50%;flex-shrink:0}
  .dot-red{background:#ef4444;box-shadow:0 0 8px #ef444499}
  .dot-yellow{background:#f59e0b;box-shadow:0 0 8px #f59e0b99}
  .dot-green{background:#22c55e;box-shadow:0 0 8px #22c55e99}
  .clients-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(460px,1fr));
    gap:22px;padding:22px 32px 32px}
  .client-panel{background:#1a1f2e;border-radius:14px;overflow:hidden;border:1px solid #2d3550}
  .client-header{padding:16px 22px;display:flex;align-items:center;justify-content:space-between}
  .client-header h2{font-size:1.05rem;font-weight:700;color:#fff}
  .client-stats{display:flex;gap:10px}
  .stat-b{display:flex;flex-direction:column;align-items:center;
    background:rgba(0,0,0,0.3);border-radius:8px;padding:6px 14px}
  .stat-b .n{font-size:1.25rem;font-weight:800}
  .stat-b .l{font-size:0.65rem;color:#99aacc;text-transform:uppercase}
  .pct-bar-wrap{margin:0 22px 14px;background:#0f1117;border-radius:6px;overflow:hidden;height:8px}
  .pct-bar-fill{height:100%;border-radius:6px;background:linear-gradient(90deg,#ef4444,#f59e0b)}
  .legend{display:flex;gap:16px;padding:4px 22px 12px;font-size:0.72rem;color:#8899bb}
  .legend-item{display:flex;align-items:center;gap:5px}
  .areas-list{padding:0 16px 16px;display:flex;flex-direction:column;gap:6px;
    max-height:540px;overflow-y:auto}
  .areas-list::-webkit-scrollbar{width:5px}
  .areas-list::-webkit-scrollbar-track{background:#0f1117}
  .areas-list::-webkit-scrollbar-thumb{background:#334;border-radius:3px}
  .area-row{display:flex;align-items:center;gap:10px;background:#131826;
    border-radius:8px;padding:8px 12px;border:1px solid #222b40}
  .semaforo{width:13px;height:13px;border-radius:50%;flex-shrink:0}
  .sem-green{background:#22c55e;box-shadow:0 0 7px #22c55e88}
  .sem-yellow{background:#f59e0b;box-shadow:0 0 7px #f59e0b88}
  .sem-red{background:#ef4444;box-shadow:0 0 7px #ef444488}
  .area-name{flex:1;font-size:0.8rem;color:#ccd;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .area-counts{font-size:0.75rem;color:#8899bb;white-space:nowrap}
  .area-pct{font-size:0.8rem;font-weight:700;width:44px;text-align:right}
  .pct-red{color:#ef4444}.pct-yellow{color:#f59e0b}.pct-green{color:#22c55e}
  .mini-bar{width:65px;background:#0f1117;border-radius:3px;height:5px;flex-shrink:0}
  .mini-bar .mfill{height:100%;border-radius:3px}
  .footer{text-align:center;padding:14px;color:#445;font-size:0.75rem}
"""

def build_panel(label, hdr_color, subset):
    total   = sum(a['total']   for a in subset)
    offline = sum(a['offline'] for a in subset)
    online  = total - offline
    pct     = round(offline / total * 100, 1) if total else 0
    rows    = '\n'.join(area_row(a) for a in sorted(subset, key=lambda x: -x['pct']))
    return f"""  <div class="client-panel">
    <div class="client-header" style="background:linear-gradient(135deg,{hdr_color},#1a1f2e)">
      <div>
        <h2>{label}</h2>
        <div style="font-size:0.78rem;color:#8899bb;margin-top:3px">{len(subset)} áreas · {total} cámaras</div>
      </div>
      <div class="client-stats">
        <div class="stat-b"><span class="n" style="color:#22c55e">{online}</span><span class="l">Online</span></div>
        <div class="stat-b"><span class="n" style="color:#ef4444">{offline}</span><span class="l">Offline</span></div>
        <div class="stat-b"><span class="n" style="color:#f59e0b">{pct}%</span><span class="l">Caída</span></div>
      </div>
    </div>
    <div class="pct-bar-wrap"><div class="pct-bar-fill" style="width:{min(pct,100)}%"></div></div>
    <div class="legend">
      <div class="legend-item"><div class="semaforo sem-green"></div> &lt;10%</div>
      <div class="legend-item"><div class="semaforo sem-yellow"></div> 10–30%</div>
      <div class="legend-item"><div class="semaforo sem-red"></div> &gt;30%</div>
    </div>
    <div class="areas-list">{rows}</div>
  </div>"""

def build_dashboard(titulo, logo_txt, logo_color, sub_label, panels_config, areas, fecha, filename):
    all_subset = [a for a in areas if a['client'] in [c for cfg in panels_config for c in cfg[0]]]
    g_total   = sum(a['total']   for a in all_subset)
    g_offline = sum(a['offline'] for a in all_subset)
    g_online  = g_total - g_offline
    g_pct     = round(g_offline / g_total * 100, 1) if g_total else 0
    n_red    = sum(1 for a in all_subset if a['pct'] > 30)
    n_yellow = sum(1 for a in all_subset if 10 < a['pct'] <= 30)
    n_green  = sum(1 for a in all_subset if a['pct'] <= 10)

    extra_cards = ''
    for client_keys, label, color in panels_config:
        sub = [a for a in areas if a['client'] in client_keys]
        if not sub: continue
        t = sum(a['total'] for a in sub)
        o = sum(a['offline'] for a in sub)
        p = round(o/t*100,1) if t else 0
        short = label.split('—')[-1].strip() if '—' in label else label
        extra_cards += f'  <div class="s-card" style="border-color:{color};margin-left:6px"><div class="lbl">{short}</div><div class="val" style="color:{color}">{t}</div><div class="sub">{o} offline ({p}%)</div></div>\n'

    panels_html = '\n'.join(
        build_panel(lbl, color, [a for a in areas if a['client'] in cl_keys])
        for cl_keys, lbl, color in panels_config
        if any(a['client'] in cl_keys for a in areas)
    )

    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{titulo} — Dashboard Cámaras</title><style>{CSS}</style></head><body>
<div class="top-bar">
  <div><div class="logo" style="color:{logo_color}">{logo_txt}</div>
  <div class="sublabel" style="color:{logo_color}88">{sub_label}</div>
  <div class="fecha">Dashboard de Estado de Cámaras — {fecha}</div></div>
  <h1>Monitor de Disponibilidad</h1>
</div>
<div class="summary-bar">
  <div class="s-card" style="border-color:{logo_color}"><div class="lbl">Total Cámaras</div><div class="val" style="color:{logo_color}">{g_total}</div><div class="sub">{len(all_subset)} áreas</div></div>
  <div class="s-card" style="border-color:#22c55e"><div class="lbl">Online</div><div class="val" style="color:#22c55e">{g_online}</div><div class="sub">{round(g_online/g_total*100,1) if g_total else 0}% disponibles</div></div>
  <div class="s-card" style="border-color:#ef4444"><div class="lbl">Offline</div><div class="val" style="color:#ef4444">{g_offline}</div><div class="sub">{g_pct}% fuera de línea</div></div>
  {extra_cards}
</div>
<div class="sem-summary">
  <div class="sem-badge"><div class="dot dot-red"></div><span style="color:#ef4444">{n_red}</span>&nbsp;áreas críticas (&gt;30%)</div>
  <div class="sem-badge"><div class="dot dot-yellow"></div><span style="color:#f59e0b">{n_yellow}</span>&nbsp;áreas en alerta (10–30%)</div>
  <div class="sem-badge"><div class="dot dot-green"></div><span style="color:#22c55e">{n_green}</span>&nbsp;áreas normales (&lt;10%)</div>
</div>
<div class="clients-grid">{panels_html}</div>
<div class="footer">Datos al {fecha} · Reporte automático Hik-Central Professional</div>
</body></html>"""

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  ✓ {os.path.basename(filename)}")

# ─────────────────────────────────────────────
#  SUBIR A GITHUB
# ─────────────────────────────────────────────
def subir_github(repo_dir, fecha):
    try:
        os.chdir(repo_dir)
        subprocess.run(['git', 'add', '.'], check=True)
        result = subprocess.run(['git', 'commit', '-m', f'Dashboard {fecha}'],
                                capture_output=True, text=True)
        if 'nothing to commit' in result.stdout or 'nothing to commit' in result.stderr:
            print("  ✓ GitHub ya estaba actualizado (sin cambios nuevos)")
            return
        subprocess.run(['git', 'push'], check=True)
        print("  ✓ Subido a GitHub Pages correctamente")
    except subprocess.CalledProcessError as e:
        print(f"  ERROR al subir a GitHub: {e}")

# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  GENERADOR DE DASHBOARDS — KAIBIL / SEGURA")
    print("=" * 55)

    print("\n[1/4] Buscando Excel más reciente...")
    ruta_excel = encontrar_excel(CARPETA_EXCEL)

    print("\n[2/4] Procesando datos...")
    areas, fecha = leer_excel(ruta_excel)
    print(f"  Fecha del reporte: {fecha}")
    print(f"  Áreas procesadas:  {len(areas)}")

    print("\n[3/4] Generando dashboards...")
    out = os.path.dirname(os.path.abspath(__file__))

    build_dashboard('Kaibil', 'KAIBIL', '#4a9eff', 'Seguridad Privada',
        [(['KS'], '🔵 KS — Kaibil Abonados', '#1a3a6e'),
         (['KC'], '🟢 KC — Kaibil Barriales', '#1a4a2e')],
        areas, fecha, os.path.join(out, 'index.html'))

    build_dashboard('Segura', 'SEGURA', '#a855f7', 'Monitoreo y Vigilancia',
        [(['SG'], '🟣 SG — Segura', '#3b1a6e'),
         (['SR'], '🩷 SR — Segura + Recorridas Kaibil', '#6e1a3a')],
        areas, fecha, os.path.join(out, 'segura.html'))

    build_dashboard('Segura Punta del Este', 'SEGURA', '#4a9eff', 'Punta del Este',
        [(['SP'], '🔵 SP — Segura Punta del Este', '#1a3a7e')],
        areas, fecha, os.path.join(out, 'punta-del-este.html'))

    print("\n[4/4] Subiendo a GitHub...")
    subir_github(CARPETA_REPO, fecha)

    print("\n" + "=" * 55)
    print("  ✓ PROCESO COMPLETADO")
    print(f"\n  🔵 Kaibil:        https://{GITHUB_USUARIO}.github.io/dashboards/")
    print(f"  🟣 Segura:        https://{GITHUB_USUARIO}.github.io/dashboards/segura.html")
    print(f"  🔵 Punta del Este:https://{GITHUB_USUARIO}.github.io/dashboards/punta-del-este.html")
    print("=" * 55)

if __name__ == '__main__':
    main()
