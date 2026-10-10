#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
PROJECT_ROOT="$(pwd)"
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
(cd frontend && npm ci && npm run build)
mkdir -p data/backups data/logs "$HOME/Library/LaunchAgents"
export PP_INSTALL_ROOT="$PROJECT_ROOT"
.venv/bin/python - <<'PY'
import os, pathlib, plistlib
root = pathlib.Path(os.environ['PP_INSTALL_ROOT'])
agents = pathlib.Path.home() / 'Library/LaunchAgents'
base = {'WorkingDirectory':str(root),'RunAtLoad':True,
        'EnvironmentVariables':{'PP_DATABASE':str(root/'data/pp-daily.sqlite3')}}
server = {**base,'Label':'local.pp-daily.server',
          'ProgramArguments':[str(root/'.venv/bin/python'),'-m','uvicorn','backend.app:app','--host','127.0.0.1','--port','8000'],
          'KeepAlive':True,'StandardOutPath':str(root/'data/logs/server.log'),'StandardErrorPath':str(root/'data/logs/server-error.log')}
backup = {**base,'Label':'local.pp-daily.backup',
          'ProgramArguments':[str(root/'.venv/bin/python'),str(root/'scripts/backup.py'),'--database',str(root/'data/pp-daily.sqlite3'),'--destination',str(root/'data/backups')],
          'StartCalendarInterval':{'Hour':3,'Minute':0},
          'StandardOutPath':str(root/'data/logs/backup.log'),'StandardErrorPath':str(root/'data/logs/backup-error.log')}
for item in (server,backup):
    with (agents/(item['Label']+'.plist')).open('wb') as f: plistlib.dump(item,f)
PY
for job in server backup; do
  launchctl bootout "gui/$(id -u)/local.pp-daily.$job" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/local.pp-daily.$job.plist"
done
echo 'Installed. Configure private HTTPS: tailscale serve --bg http://127.0.0.1:8000'
