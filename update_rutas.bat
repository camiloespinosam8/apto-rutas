@echo off
REM Regenera el centro de control (datos + panel + rutas) y lo publica en GitHub Pages.
REM Corre varias veces al dia (Task Scheduler: APTO_PanelRutas). Solo publica si algo cambio.
setlocal
set PY="C:\Users\Cami\AppData\Local\Programs\Python\Python312\python.exe"
cd /d "C:\Users\Cami\Desktop\CLAUDE\APTO\Operacional\Cerebro_Turismo\panel_rutas"

echo ---- %date% %time% ---- >> update_rutas.log
%PY% build_incidencias.py >> update_rutas.log 2>&1
%PY% build_data.py  >> update_rutas.log 2>&1
%PY% build_panel.py >> update_rutas.log 2>&1
%PY% build_rutas.py >> update_rutas.log 2>&1

git add index.html panel.html datos.json accesos_enviados.json anuncios_sin_registro.json reservas_fantasma.json incidencias.json
git diff --cached --quiet
if %errorlevel%==0 (
  echo sin cambios >> update_rutas.log
  exit /b 0
)
git commit -m "auto: centro de control APTO" >> update_rutas.log 2>&1
git push >> update_rutas.log 2>&1
echo PUBLICADO >> update_rutas.log
exit /b 0
