"""Manual CORS check for personnel creation.

This is a live HTTP script and is intentionally guarded so it won't run during
`pytest` collection.
"""

import requests


def main() -> None:
    url = 'http://127.0.0.1:8001/api/personnel/basic'
    data = {
        'rank': 'PGEN',
        'last_name': 'TEST2',
        'first_name': 'USER2',
        'unit': 'RHQ',
        'status': 'ACTIVE',
        'birthdate': '1990-05-01',
        'religion': 'CATHOLIC',
    }

    files = {k: (None, v) for k, v in data.items()}

    # Make request with CORS header
    resp = requests.post(url, files=files, headers={'Origin': 'http://localhost:3000'})

    print(f'Status: {resp.status_code}')
    print(f'\nCORS Headers:')
    cors_found = False
    for k, v in resp.headers.items():
        if 'access-control' in k.lower():
            cors_found = True
            print(f'  ✓ {k}: {v}')

    if not cors_found:
        print("  No CORS headers found")

    if resp.status_code == 200:
        payload = resp.json()
        print(f'\n✓ Personnel record created successfully!')
        print(f'  ID: {payload["id"]}')
        print(f'  Name: {payload["first_name"]} {payload["last_name"]}')
        print(f'  Department: {payload["unit"]}')


if __name__ == "__main__":
    main()
