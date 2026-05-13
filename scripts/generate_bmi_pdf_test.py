"""Developer helper: generate a sample BMI PDF using TestClient.

This script previously executed at import time and was picked up by pytest
(because its filename ends with `_test.py`). Import-time execution set
`AUTH_DISABLED` and made live HTTP requests which interfered with the
test-run environment. Wrap execution in a __main__ guard so pytest will
import the module harmlessly and not execute the script.

Run directly from the repo root when needed:

    python scripts/generate_bmi_pdf_test.py

"""

from fastapi.testclient import TestClient
import importlib.util, pathlib, sys, os


def main():
    # Disable auth when running this helper locally
    os.environ['AUTH_DISABLED'] = '1'

    spec = importlib.util.spec_from_file_location('backend_main', str(pathlib.Path('backend') / 'main.py'))
    mod = importlib.util.module_from_spec(spec)
    backend_dir = str(pathlib.Path('backend').resolve())
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    spec.loader.exec_module(mod)
    app = mod.app
    client = TestClient(app)

    # find any BMI record to use month/year
    resp_list = client.get('/api/bmi')
    print('list status', resp_list.status_code)
    recs = resp_list.json()
    print('count', len(recs))
    from datetime import datetime
    if not recs:
        print('No BMI records found to test PDF endpoint')
    else:
        r = recs[0]
        dt = r.get('date_taken')
        if dt:
            try:
                parsed = datetime.fromisoformat(dt)
                m = parsed.month
                y = parsed.year
            except Exception:
                now = datetime.utcnow()
                m = now.month
                y = now.year
        else:
            now = datetime.utcnow()
            m = now.month
            y = now.year
        print('Requesting PDF for month,year', m, y)
        resp = client.post('/api/bmi/report', data={'month': str(m), 'year': str(y), 'report_type': 'pdf', 'file_name': 'test_bmi_pdf', 'unit': 'All Units'})
        print('status', resp.status_code)
        print('headers', resp.headers.get('content-disposition'))
        if resp.status_code == 200:
            open('scripts/test_bmi_sample.pdf', 'wb').write(resp.content)
            print('Saved scripts/test_bmi_sample.pdf')


if __name__ == '__main__':
    main()
