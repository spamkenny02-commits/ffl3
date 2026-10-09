@echo off
cd /d "%~dp0"
python "%~dp0ffl3_editor.py" gui "%~1" "%~dp0project_fr.json"
if errorlevel 1 pause
