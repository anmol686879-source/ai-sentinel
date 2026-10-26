from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .data import EMP
from .engine import Sentinel

app = FastAPI(title='AI Sentinel', version='1.0', description='Insider-fraud early warning API')
S = Sentinel()


class Status(BaseModel):
    status: str


def _get(aid):
    a = next((x for x in S.alerts if x['id'] == aid), None)
    if not a: raise HTTPException(404, 'Alert not found')
    return a


@app.get('/api/health')
def health(): return {'ok': True, 'alerts': len(S.alerts), 'model': 'IsolationForest + rule-based risk scoring'}


@app.get('/api/bootstrap')
def bootstrap(): return {'emp': {k: list(v) for k, v in EMP.items()}, 'alerts': S.alerts}


@app.get('/api/alerts')
def alerts(min_score: int = 0, status: str | None = None):
    return [a for a in S.alerts if a['score'] >= min_score and (not status or a['st'] == status)]


@app.get('/api/alerts/{aid}')
def alert(aid: str):
    a = _get(aid)
    return {**a, 'baseline': S.baseline(a['e'])}


@app.post('/api/alerts/{aid}/status')
def set_status(aid: str, body: Status):
    if body.status not in ('New', 'Escalated', 'Reviewed'): raise HTTPException(422, 'Invalid status')
    a = _get(aid); a['st'] = body.status
    return a


@app.get('/api/graph')
def graph(): return S.graph()


app.mount('/', StaticFiles(directory=Path(__file__).resolve().parent.parent / 'frontend', html=True), name='ui')
