"""Single-user, append-only daily check-ins. Network access is controlled by Tailscale."""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.environ.get('PP_DATABASE', ROOT / 'data' / 'pp-daily.sqlite3'))
SHANGHAI = ZoneInfo('Asia/Shanghai')


def today():
    return datetime.now(SHANGHAI).date().isoformat()


@contextmanager
def database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    try:
        with conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS projects(
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, color TEXT NOT NULL,
                    position INTEGER NOT NULL, created TEXT NOT NULL, archived TEXT);
                CREATE TABLE IF NOT EXISTS completions(
                    project_id TEXT NOT NULL REFERENCES projects(id), day TEXT NOT NULL,
                    completed_at TEXT NOT NULL, PRIMARY KEY(project_id, day));
            ''')
            conn.execute("INSERT OR IGNORE INTO meta VALUES('generation', ?)", (str(uuid4()),))
        yield conn
    finally:
        conn.close()


def snapshot(conn):
    return {'version': 1, 'generation': conn.execute("SELECT value FROM meta WHERE key='generation'").fetchone()[0],
            'projects': [dict(r) for r in conn.execute('SELECT * FROM projects ORDER BY position, id')],
            'completions': [dict(r) for r in conn.execute('SELECT * FROM completions ORDER BY day, project_id')]}


class Model(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ProjectInput(Model):
    name: str = Field(min_length=1, max_length=40)
    color: str = Field(pattern=r'^#[0-9a-fA-F]{6}$')

    @field_validator('name')
    @classmethod
    def clean_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('名称不能为空')
        return value


class EditProject(ProjectInput):
    generation: UUID


class CreateProject(EditProject):
    pass


class GenerationInput(Model):
    generation: UUID


class Reorder(GenerationInput):
    ids: list[UUID] = Field(max_length=1000)


class Completion(Model):
    project_id: UUID
    day: date
    completed_at: datetime

    @field_validator('completed_at')
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None:
            raise ValueError('必须携带时区')
        return value


class Sync(GenerationInput):
    completions: list[Completion] = Field(max_length=10000)


class BackupProject(ProjectInput):
    id: UUID
    position: int = Field(ge=0)
    created: date
    archived: date | None = None


class Backup(Model):
    version: int
    generation: UUID
    projects: list[BackupProject] = Field(max_length=1000)
    completions: list[Completion] = Field(max_length=100000)


class Restore(GenerationInput):
    backup: Backup


def check_generation(conn, generation):
    if str(generation) != conn.execute("SELECT value FROM meta WHERE key='generation'").fetchone()[0]:
        raise HTTPException(409, '服务器数据已恢复，请先导出本地备份，再重新载入服务器数据')


def get_project(conn, project_id):
    row = conn.execute('SELECT * FROM projects WHERE id=?', (str(project_id),)).fetchone()
    if not row:
        raise HTTPException(404, '项目不存在')
    return dict(row)


def validate_completion(record, project):
    stamp = record.completed_at.astimezone(SHANGHAI)
    if stamp.date() != record.day:
        raise HTTPException(422, '日期必须对应实际操作时间')
    if record.completed_at > datetime.now(timezone.utc) + timedelta(minutes=2) or record.day.isoformat() > today():
        raise HTTPException(422, '不能完成未来日期，请检查设备时间')
    if record.day.isoformat() < project['created'] or (project['archived'] and record.day.isoformat() > project['archived']):
        raise HTTPException(422, '该日期不在项目有效范围内')


app = FastAPI(title='pp Daily', docs_url=None, redoc_url=None)


@app.get('/api/state')
def state():
    with database() as conn:
        conn.execute('BEGIN')
        return snapshot(conn)


@app.post('/api/projects')
def create_project(body: CreateProject):
    with database() as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        check_generation(conn, body.generation)
        position = conn.execute('SELECT COALESCE(MAX(position), -1)+1 FROM projects').fetchone()[0]
        conn.execute('INSERT INTO projects VALUES(?,?,?,?,?,NULL)', (str(uuid4()), body.name, body.color, position, today()))
        return snapshot(conn)


@app.put('/api/projects/order')
def reorder(body: Reorder):
    with database() as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        check_generation(conn, body.generation)
        ids = [str(i) for i in body.ids]
        existing = {p['id'] for p in snapshot(conn)['projects']}
        if len(ids) != len(set(ids)) or set(ids) != existing:
            raise HTTPException(422, '排序必须包含全部项目且不能重复')
        conn.executemany('UPDATE projects SET position=? WHERE id=?', enumerate(ids))
        return snapshot(conn)


@app.put('/api/projects/{project_id}')
def edit(project_id: UUID, body: EditProject):
    with database() as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        check_generation(conn, body.generation)
        if get_project(conn, project_id)['archived']:
            raise HTTPException(422, '归档项目不能再修改')
        conn.execute('UPDATE projects SET name=?,color=? WHERE id=?', (body.name, body.color, str(project_id)))
        return snapshot(conn)


@app.post('/api/projects/{project_id}/archive')
def archive(project_id: UUID, body: GenerationInput):
    with database() as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        check_generation(conn, body.generation)
        get_project(conn, project_id)
        conn.execute('UPDATE projects SET archived=COALESCE(archived,?) WHERE id=?', (today(), str(project_id)))
        return snapshot(conn)


@app.post('/api/sync')
def sync(body: Sync):
    with database() as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        check_generation(conn, body.generation)
        for record in body.completions:
            project = get_project(conn, record.project_id)
            validate_completion(record, project)
            conn.execute('INSERT OR IGNORE INTO completions VALUES(?,?,?)',
                         (str(record.project_id), record.day.isoformat(), record.completed_at.isoformat()))
        return snapshot(conn)


@app.get('/api/backup')
def export_backup():
    with database() as conn:
        conn.execute('BEGIN')
        return snapshot(conn)


@app.post('/api/restore')
def restore(body: Restore):
    backup = body.backup
    if backup.version != 1:
        raise HTTPException(422, '不支持的备份版本')
    projects = {str(p.id): p.model_dump(mode='json') for p in backup.projects}
    if len(projects) != len(backup.projects):
        raise HTTPException(422, '项目标识重复')
    for p in projects.values():
        if p['created'] > today() or (p['archived'] and (p['archived'] < p['created'] or p['archived'] > today())):
            raise HTTPException(422, '项目日期无效')
    keys = set()
    for record in backup.completions:
        project = projects.get(str(record.project_id))
        if not project:
            raise HTTPException(422, '完成记录关联的项目不存在')
        validate_completion(record, project)
        key = (str(record.project_id), record.day.isoformat())
        if key in keys:
            raise HTTPException(422, '完成记录重复')
        keys.add(key)
    with database() as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        check_generation(conn, body.generation)
        folder = DB_PATH.parent / 'backups'
        folder.mkdir(exist_ok=True)
        safety = folder / f"before-restore-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{uuid4().hex[:8]}.json"
        safety.write_text(json.dumps(snapshot(conn), ensure_ascii=False), encoding='utf-8')
        conn.execute('DELETE FROM completions')
        conn.execute('DELETE FROM projects')
        conn.executemany('INSERT INTO projects VALUES(?,?,?,?,?,?)',
                         [(p['id'], p['name'], p['color'], p['position'], p['created'], p['archived']) for p in projects.values()])
        conn.executemany('INSERT INTO completions VALUES(?,?,?)',
                         [(str(c.project_id), c.day.isoformat(), c.completed_at.isoformat()) for c in backup.completions])
        conn.execute("UPDATE meta SET value=? WHERE key='generation'", (str(uuid4()),))
        return snapshot(conn)


DIST = ROOT / 'frontend' / 'dist'
if DIST.exists():
    app.mount('/', StaticFiles(directory=DIST, html=True), name='frontend')
