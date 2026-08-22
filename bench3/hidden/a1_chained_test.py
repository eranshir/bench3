import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TASK_DIR = Path(__file__).parent


def run_scenario(src, timeout=60):
    """Run a scenario in a child process with SVC_DB isolated."""
    header = """import os, sys, tempfile
sys.path.insert(0, {task_dir!r})
os.environ['SVC_DB'] = os.path.join(tempfile.mkdtemp(prefix='a1t_'), 'dev.db')
""".format(task_dir=str(TASK_DIR))
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write(header + src)
        tmp = f.name
    try:
        r = subprocess.run([sys.executable, tmp], capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -9, "", "TIMEOUT"
    finally:
        os.unlink(tmp)


SCENARIO_FRESH = '''
from svc.db import connect
from svc.reports import report_totals
conn = connect()
conn.execute('DELETE FROM transactions')
rows = [('a', 1000, '2026-08-01 10:00:00', 'USD'),
        ('b', 2000, '2026-08-01 11:00:00', 'USD'),
        ('c', 4000, '2026-08-01 12:00:00', 'EUR'),
        ('d', 8000, '2026-08-01 13:00:00', 'USD')]
conn.executemany('INSERT INTO transactions (account, amount_cents, at, currency) VALUES (?,?,?,?)', rows)
conn.commit(); conn.close()
r = report_totals('2026-08-01 00:00:00', '2026-08-01 12:00:00')
print('TOTAL', r['total_cents'])
p1 = report_totals('2026-08-01 00:00:00', '2026-08-02 00:00:00', page=1, per_page=2)
p2 = report_totals('2026-08-01 00:00:00', '2026-08-02 00:00:00', page=2, per_page=2)
print('P1', [x[0] for x in p1['rows']])
print('P2', [x[0] for x in p2['rows']])
print('CUR', p1['rows'][0][3])
'''

SCENARIO_STALE = '''
import sqlite3, os
from svc.config import DB_PATH
conn = sqlite3.connect(DB_PATH)
conn.execute('CREATE TABLE transactions (id INTEGER PRIMARY KEY, account TEXT, amount_cents INTEGER, at TIMESTAMP)')
conn.commit(); conn.close()
from svc.db import connect
c = connect()
c.execute('INSERT INTO transactions (account, amount_cents, at, currency) VALUES (?,?,?,?)',
          ('q', 9, '2026-08-01 10:00:00', 'USD'))
c.commit(); c.close()
print('STALE_OK')
'''


class T(unittest.TestCase):
    def test_end_to_end_fresh(self):
        rc, out, err = run_scenario(SCENARIO_FRESH)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("TOTAL 7000", out, "end date must be inclusive: " + out + err)
        self.assertIn("P1 ['a', 'b']", out, "page 1 skips rows: " + out + err)
        self.assertIn("P2 ['c', 'd']", out, "page 2 wrong: " + out + err)
        self.assertIn("CUR USD", out, "currency missing: " + out + err)

    def test_survives_stale_db(self):
        rc, out, err = run_scenario(SCENARIO_STALE)
        self.assertEqual(rc, 0, "stale db not repaired: " + out + err)
        self.assertIn("STALE_OK", out, out + err)


if __name__ == "__main__":
    unittest.main()
