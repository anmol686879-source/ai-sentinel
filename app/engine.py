"""AI Sentinel core: behaviour profiling -> anomaly model -> risk scoring -> explainable alerts -> collusion graph."""
import numpy as np, networkx as nx
from sklearn.ensemble import IsolationForest
from .data import EMP, FEATURES, generate

NAMES = {e: v[0] for e, v in EMP.items()}


def _clock(h):
    h = h % 24
    total = round(h * 60)
    hh, m = divmod(int(total), 60)
    return f"{(hh % 12) or 12}:{m:02d} {'AM' if hh < 12 else 'PM'}"


def _rupees(logv):
    v = np.expm1(logv)
    return f"₹{v / 1e5:.0f} Lakh" if v >= 1e5 else f"₹{v:,.0f}"


def rules(f, z):
    """Risk Scoring Engine: each rule adds points when behaviour deviates from the employee's own baseline."""
    r = []
    if z[0] < -3 or z[0] > 3: r.append(('🕑', f'Unusual login at {_clock(f[0])}', 20))
    if z[2] > 3: r.append(('💸', f'Large {_rupees(f[2])} transfer', 30))
    if f[3] >= 1: r.append(('💻', 'Unknown device', 15))
    if z[4] > 3: r.append(('⭐', f'Accessed {int(f[4])} VIP accounts', 20))
    if z[5] > 3: r.append(('👥', f'Accessed {int(f[5])} unusual customers', 20))
    if z[6] > 3: r.append(('✏️', 'Repeated account modifications', 25))
    return r


class Sentinel:
    def __init__(self, seed=7):
        hist, self.today, self.touch = generate(seed)
        by = {e: np.array([f for ee, f in hist if ee == e]) for e in EMP}
        self.mu = {e: v.mean(0) for e, v in by.items()}
        self.sd = {e: v.std(0) + 1e-6 for e, v in by.items()}
        Z = np.array([(f - self.mu[e]) / self.sd[e] for e, f in hist])
        self.model = IsolationForest(n_estimators=200, contamination=0.02, random_state=seed).fit(Z)
        self.alerts = self._score()

    def z(self, e):
        return (np.array(self.today[e]) - self.mu[e]) / self.sd[e]

    def _score(self):
        res = {}
        for e, f in self.today.items():
            z = self.z(e)
            res[e] = {'rules': rules(f, z), 'ml': float(-self.model.score_samples([z])[0]), 'f': f}
        flagged = {e for e, v in res.items() if v['rules']}
        by_cust = {}
        for e in flagged:
            for c in self.touch[e]: by_cust.setdefault(c, set()).add(e)
        for e in flagged:  # collusion: customers shared with another flagged employee
            for c, who in by_cust.items():
                if e in who and who - {e}:
                    res[e]['rules'].append(('🔗', f'Shared payee with {NAMES[sorted(who - {e})[0]]}', 35)); break
        out = []
        for e, v in res.items():
            if not v['rules']: continue
            bonus = int(np.clip((v['ml'] - 0.5) * 30, 0, 10))
            pts = sum(p for *_, p in v['rules'])
            rs = v['rules'] + ([('🤖', 'Behaviour model anomaly', bonus)] if bonus else [])
            score = min(100, pts + bonus)
            if score < 30: continue
            top = max(v['rules'], key=lambda x: x[2])
            out.append({'e': e, 'trig': top[1], 'score': score, 'st': 'New', 't': _clock(v['f'][0]),
                        'r': ';'.join(f'{i}|{t}|{p}' for i, t, p in rs)})
        out.sort(key=lambda a: -a['score'])
        for i, a in enumerate(out): a['id'] = f'A-{2041 - i * 3}'
        return out

    def graph(self):
        flagged = {a['e'] for a in self.alerts}
        G = nx.Graph()
        for e in flagged:
            G.add_node(e, kind='employee')
            for c in self.touch[e]: G.add_edge(e, c)
        for c in G: G.nodes[c].setdefault('kind', 'customer')
        shared = {c for c in G if G.nodes[c]['kind'] == 'customer' and G.degree(c) >= 2}
        sus = G.subgraph(flagged | shared)
        rings = [sorted(c) for c in nx.connected_components(sus) if len(c) >= 3]
        return {'nodes': [{'id': n, 'kind': d['kind']} for n, d in G.nodes(data=True)],
                'links': [{'source': a, 'target': b, 'suspicious': a in shared or b in shared} for a, b in G.edges],
                'rings': rings}

    def baseline(self, e):
        return {n: {'today': round(float(v), 2), 'normal': round(float(m), 2)}
                for n, v, m in zip(FEATURES, self.today[e], self.mu[e])}
