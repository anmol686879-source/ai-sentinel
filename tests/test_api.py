from fastapi.testclient import TestClient
from app.main import app
c = TestClient(app)

def test_top_alert_is_employee_a():
    a = c.get('/api/alerts').json()
    assert a[0]['e'] == 'A' and a[0]['score'] >= 85

def test_normal_employees_not_flagged():
    assert not {'S', 'P'} & {a['e'] for a in c.get('/api/alerts').json()}

def test_status_update_and_validation():
    aid = c.get('/api/alerts').json()[0]['id']
    assert c.post(f'/api/alerts/{aid}/status', json={'status': 'Escalated'}).json()['st'] == 'Escalated'
    assert c.post(f'/api/alerts/{aid}/status', json={'status': 'Nope'}).status_code == 422

def test_collusion_ring_found():
    assert any({'A', 'X'} <= set(r) for r in c.get('/api/graph').json()['rings'])
