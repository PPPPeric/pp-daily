import copy
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from backend import app as module


def test_icon_create_edit_backup_and_legacy_restore(client):
    state = create(client)
    project = state['projects'][0]
    response = client.put('/api/projects/' + project['id'], json={
        'generation':state['generation'], 'name':project['name'], 'color':project['color'], 'icon':' 读 '})
    assert response.status_code == 200
    assert response.json()['projects'][0]['icon'] == '读'
    saved = client.get('/api/backup').json()
    restored = client.post('/api/restore',json={'generation':saved['generation'],'backup':saved})
    assert restored.status_code == 200
    assert restored.json()['projects'][0]['icon'] == '读'
    legacy = copy.deepcopy(restored.json())
    del legacy['projects'][0]['icon']
    restored = client.post('/api/restore',json={'generation':legacy['generation'],'backup':legacy})
    assert restored.status_code == 200
    assert restored.json()['projects'][0]['icon'] == ''
    body = {'generation':restored.json()['generation'], 'name':'散步', 'color':'#285C47', 'icon':'走'}
    assert client.post('/api/projects',json=body).json()['projects'][-1]['icon'] == '走'
    body['icon'] = '散步'
    assert client.post('/api/projects',json=body).status_code == 422


def test_migrates_existing_project_without_losing_records(client):
    with sqlite3.connect(module.DB_PATH) as conn:
        conn.execute('CREATE TABLE projects(id TEXT PRIMARY KEY, name TEXT NOT NULL, color TEXT NOT NULL, position INTEGER NOT NULL, created TEXT NOT NULL, archived TEXT)')
        conn.execute('INSERT INTO projects VALUES(?,?,?,?,?,?)',('old','阅读','#285C47',0,'2026-01-01',None))
    state = client.get('/api/state').json()
    assert state['projects'][0]['id'] == 'old'
    assert state['projects'][0]['name'] == '阅读'
    assert state['projects'][0]['icon'] == ''
    assert client.get('/api/state').json()['projects'] == state['projects']


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'DB_PATH', tmp_path / 'test.sqlite3')
    return TestClient(module.app)


def create(client, name='阅读'):
    generation = client.get('/api/state').json()['generation']
    response = client.post('/api/projects', json={'generation':generation,'name':name,'color':'#285C47'})
    assert response.status_code == 200
    return response.json()


def payload(state):
    now = datetime.now(module.SHANGHAI)
    return {'generation':state['generation'], 'completions':[{
        'project_id':state['projects'][0]['id'], 'day':now.date().isoformat(), 'completed_at':now.isoformat()}]}


def test_duplicate_and_no_cancel(client):
    state = create(client)
    body = payload(state)
    for _ in range(3):
        response = client.post('/api/sync',json=body)
        assert response.status_code == 200
        assert len(response.json()['completions']) == 1
    assert client.delete('/api/completions').status_code in (404,405)


def test_date_must_match_timestamp(client):
    body = payload(create(client))
    body['completions'][0]['day'] = (datetime.now(module.SHANGHAI).date()-timedelta(days=1)).isoformat()
    assert client.post('/api/sync',json=body).status_code == 422
    assert client.get('/api/state').json()['completions'] == []


def test_delayed_offline_record_and_future(client):
    state = create(client)
    p = state['projects'][0]
    yesterday = datetime.now(module.SHANGHAI)-timedelta(days=1)
    with module.database() as conn, conn:
        conn.execute('UPDATE projects SET created=? WHERE id=?',(yesterday.date().isoformat(),p['id']))
    body = payload(state)
    body['completions'][0].update(day=yesterday.date().isoformat(),completed_at=yesterday.isoformat())
    assert client.post('/api/sync',json=body).status_code == 200
    future = datetime.now(module.SHANGHAI)+timedelta(days=1)
    body['completions'][0].update(day=future.date().isoformat(),completed_at=future.isoformat())
    assert client.post('/api/sync',json=body).status_code == 422


def test_restore_roundtrip_and_old_generation(client):
    state = create(client)
    saved = client.post('/api/sync',json=payload(state)).json()
    create(client,'散步')
    response = client.post('/api/restore',json={'generation':saved['generation'],'backup':saved})
    assert response.status_code == 200
    restored = response.json()
    assert restored['projects'] == saved['projects']
    assert restored['completions'] == saved['completions']
    assert restored['generation'] != saved['generation']
    assert client.post('/api/sync',json=payload(saved)).status_code == 409
    assert list((module.DB_PATH.parent/'backups').glob('before-restore-*.json'))


def test_invalid_restore_preserves_database(client):
    state = create(client)
    backup = copy.deepcopy(state)
    backup['projects'].append(backup['projects'][0])
    assert client.post('/api/restore',json={'generation':state['generation'],'backup':backup}).status_code == 422
    assert client.get('/api/state').json() == state


def test_archive_and_no_restore(client):
    state = create(client)
    p = state['projects'][0]
    archived = client.post(f"/api/projects/{p['id']}/archive",json={'generation':state['generation']})
    assert archived.status_code == 200
    assert archived.json()['projects'][0]['archived'] == module.today()
    assert client.put(f"/api/projects/{p['id']}",json={'generation':state['generation'],'name':'新名字','color':'#285C47'}).status_code == 422


def test_batch_atomicity(client):
    state = create(client)
    body = payload(state)
    invalid = copy.deepcopy(body['completions'][0])
    invalid['day'] = '2000-01-01'
    body['completions'].append(invalid)
    assert client.post('/api/sync',json=body).status_code == 422
    assert client.get('/api/state').json()['completions'] == []


def test_concurrent_duplicate_upload(client):
    body = payload(create(client))
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(lambda _: client.post('/api/sync',json=body), range(10)))
    assert all(r.status_code == 200 for r in results)
    assert len(client.get('/api/state').json()['completions']) == 1


def test_order_requires_full_unique_list(client):
    state = create(client)
    state = create(client,'散步')
    ids = [p['id'] for p in state['projects']]
    assert client.put('/api/projects/order',json={'generation':state['generation'],'ids':[ids[0],ids[0]]}).status_code == 422
    reordered = client.put('/api/projects/order',json={'generation':state['generation'],'ids':ids[::-1]})
    assert [p['id'] for p in reordered.json()['projects']] == ids[::-1]
