import os
os.environ['DATABASE_URL']='sqlite:///./test_pocketsmart.db'
os.environ['SECRET_KEY']='test-secret-key'
os.environ['AI_ENABLED']='false'
from fastapi.testclient import TestClient
from app.main import app

def test_health():
    with TestClient(app) as client:
        r=client.get('/health'); assert r.status_code==200; assert r.json()['status']=='ok'

def test_register_and_home():
    try: os.remove('test_pocketsmart.db')
    except FileNotFoundError: pass
    with TestClient(app) as client:
        r=client.post('/register',json={'name':'Test User','email':'test@example.com','password':'password123'}); assert r.status_code==200
        payload={'budget':20000,'room':'Living Room','style':'modern','items':[{'category':'lighting','quantity':2}]}
        r=client.post('/generate-home',json=payload); assert r.status_code==200; assert r.json()['planner']=='home'
