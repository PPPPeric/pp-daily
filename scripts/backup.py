"""SQLite online backup. Safe with a live server and WAL; retain latest 30 daily backups."""
import argparse
import sqlite3
from datetime import datetime
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--database', type=Path, required=True)
parser.add_argument('--destination', type=Path, required=True)
args = parser.parse_args()
if not args.database.exists():
    raise SystemExit('Database does not exist; no backup created')
args.destination.mkdir(parents=True, exist_ok=True)
target = args.destination / f"pp-daily-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.sqlite3"
with sqlite3.connect(f'{args.database.resolve().as_uri()}?mode=ro',uri=True) as source, sqlite3.connect(target) as destination:
    source.backup(destination)
    if destination.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        raise SystemExit('Backup integrity check failed')
for stale in sorted(args.destination.glob('pp-daily-*.sqlite3'), reverse=True)[30:]:
    stale.unlink()
print(target)
