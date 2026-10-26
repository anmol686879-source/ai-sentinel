# 🛡️ AI Sentinel — AI-Driven Early Warning System for Insider Fraud in Banks
Prahar × ASAI Buildathon · Team Tech Warriors

AI Sentinel learns each bank employee's normal behaviour, scores every day's activity against it, explains *why* something is suspicious, and exposes collusion rings — **before** the fraud completes.

## Run it (2 minutes)
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open **http://localhost:8000** (dashboard) · **http://localhost:8000/docs** (interactive API docs).
Docker: `docker build -t ai-sentinel . && docker run -p 8000:8000 ai-sentinel`
Tests: `pip install -r requirements-dev.txt && pytest`

## How it maps to the idea
| Idea component | Where it lives |
|---|---|
| Behaviour Learning Engine | `engine.py` → per-employee baseline (mean/std over 30 days) + **Isolation Forest** |
| Real-Time Monitoring | `data.py` generates activity; dashboard's Live toggle simulates new alerts |
| Risk Scoring Engine | `engine.rules()` — unusual login +20, large transaction +30, unknown device +15, VIP access +20, … |
| Graph-Based Fraud Detection | `engine.graph()` — **NetworkX** finds employees linked through shared payees (collusion rings) |
| Explainable AI | every alert carries its reasons with point contributions (`r` field) |

Pipeline: `logs → baseline z-scores → Isolation Forest + rules → risk score 0-100 → explainable alert → case`.

## API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | status |
| GET | `/api/bootstrap` | employees + alerts (used by the UI) |
| GET | `/api/alerts?min_score=60&status=New` | filtered alerts |
| GET | `/api/alerts/{id}` | alert + behaviour baseline |
| POST | `/api/alerts/{id}/status` | `{"status":"Escalated"}` / `Reviewed` |
| GET | `/api/graph` | nodes, links, detected rings |

## Structure
```
app/        data.py (synthetic logs) · engine.py (ML + scoring + graph) · main.py (FastAPI)
frontend/   index.html (dashboard, served by FastAPI)
tests/      test_api.py
```

## Demo script (for judges)
1. Dashboard → Employee A: 85+ risk, 2:30 AM login, ₹50 Lakh transfer, unknown device, VIP access.
2. Click the alert → explainable reasons → **Escalate** → opens a case in Investigations.
3. Graph Network → red links show A, X, B tied together through shared customers.
4. Settings → move the threshold, enable Auto-escalate, toggle Privacy mode.

## Production roadmap
Synthetic data → real logs via **Kafka**; **Spark** for scale; **Neo4j** instead of NetworkX; **PyTorch autoencoders**; PostgreSQL for cases; SSO + audit trail; investigator feedback loop to cut false positives.
