"""Synthetic bank activity logs: 30 days of normal behaviour + today's injected insider-fraud scenarios.
Feature vector per employee-day: [login_hour, txn_count, log(max_amount), new_device, vip_access, customers, edits]"""
import numpy as np

EMP = {'A': ('Employee A', 'Branch Ops'), 'X': ('Employee X', 'Loans'), 'M': ('Employee M', 'Treasury'),
       'R': ('Employee R', 'Cash Desk'), 'K': ('Employee K', 'Support'), 'B': ('Employee B', 'Forex'),
       'T': ('Employee T', 'Cards'), 'S': ('Employee S', 'Audit'), 'P': ('Employee P', 'HR Ops')}
FEATURES = ['login_hour', 'txn_count', 'log_max_amount', 'new_device', 'vip_access', 'customers', 'edits']
L = np.log1p


def _normal(rng):
    return [rng.normal(10, 1.2), rng.poisson(30), rng.normal(L(25000), 0.35), 0, rng.poisson(0.5),
            rng.integers(15, 30), rng.poisson(2)]


def generate(seed=7, days=30):
    rng = np.random.default_rng(seed)
    hist = [(e, _normal(rng)) for e in EMP for _ in range(days)]
    today = {e: _normal(rng) for e in EMP}
    today.update({  # injected insider scenarios
        'A': [2.5, 38, L(5_000_000), 1, 6, 22, 3],       # 2:30 AM, Rs 50L transfer, unknown device, VIP access
        'X': [1.17, 40, L(300_000), 0, 1, 42, 19],       # many unusual customers + repeated account edits
        'B': [0.75, 55, L(900_000), 0, 0, 28, 4],        # split transactions, late session
        'M': [23.3, 30, L(26000), 1, 0, 34, 2],          # unknown device, late login
        'R': [22.1, 31, L(280_000), 0, 0, 20, 9],        # after-hours, repeated edits
        'T': [21.7, 33, L(150_000), 1, 0, 24, 3],        # card limit overrides on new device
        'K': [20.25, 30, L(27000), 0, 0, 40, 2]})        # new customer segment
    touch = {e: [f'C{i}'] for i, e in enumerate(EMP)}     # customers each employee handled today
    touch.update({'A': ['Y'], 'X': ['Y', 'Z'], 'B': ['Z']})  # Y and Z are shared between flagged staff
    return hist, today, touch
