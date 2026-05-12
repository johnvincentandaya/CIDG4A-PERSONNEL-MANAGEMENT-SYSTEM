"""Manual CORS check script.

Note: This file is named like a pytest test module, but it performs live HTTP
requests. To avoid failures during `pytest` collection (when the API server is
not running), the script only executes when run directly.
"""

import requests


def main() -> None:
    endpoints = [
        'http://127.0.0.1:8001/',
        'http://127.0.0.1:8001/api/bmi',
        'http://127.0.0.1:8001/api/personnel',
    ]

    print("Testing CORS configuration...\n")

    for url in endpoints:
        try:
            resp = requests.get(url, headers={'Origin': 'http://localhost:3000'}, timeout=2)
            cors_header = resp.headers.get('access-control-allow-origin', 'MISSING')
            creds_header = resp.headers.get('access-control-allow-credentials', 'not-set')
            print(f"GET {url}")
            print(f"  Status: {resp.status_code}")
            print(f"  access-control-allow-origin: {cors_header}")
            print(f"  access-control-allow-credentials: {creds_header}")
            print()
        except Exception as e:
            print(f"GET {url}: ERROR - {str(e)}\n")

    ok = all(
        'localhost:3000' in requests.get(url, headers={'Origin': 'http://localhost:3000'}, timeout=2).headers.get('access-control-allow-origin', '')
        for url in endpoints
    )
    print("CORS is properly configured!" if ok else "CORS configuration needs review")


if __name__ == "__main__":
    main()
