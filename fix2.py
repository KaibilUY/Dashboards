content = open('generar_dashboards.py', 'r', encoding='utf-8').read() 
content = content.replace('os.chdir(repo_dir)', 'os.chdir(os.path.dirname(os.path.abspath(__file__)))') 
open('generar_dashboards.py', 'w', encoding='utf-8').write(content) 
