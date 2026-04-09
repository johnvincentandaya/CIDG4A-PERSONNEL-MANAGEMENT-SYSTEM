import requests
import io

url = 'http://127.0.0.1:8001/api/personnel/report'

# Test with various parameters
params_tests = [
    {'file_name': 'test_report', 'scope': 'Overall'},
    {'file_name': 'rhq_only', 'scope': 'RHQ only'},
    {'file_name': 'active_only', 'status': 'ACTIVE'},
]

print("=== Testing /api/personnel/report with CORS ===\n")

for i, params in enumerate(params_tests, 1):
    print(f"Test {i}: {params}")
    
    files = {k: (None, v) for k, v in params.items()}
    
    try:
        resp = requests.post(
            url,
            files=files,
            headers={'Origin': 'http://localhost:3000'},
            timeout=10
        )
        
        # Check status and CORS
        cors_present = 'access-control-allow-origin' in resp.headers
        cors_value = resp.headers.get('access-control-allow-origin', 'MISSING')
        
        print(f"  Status: {resp.status_code}")
        print(f"  CORS: {cors_value if cors_present else 'MISSING'}")
        print(f"  File size: {len(resp.content)} bytes")
        
        # Verify it's a valid ZIP (Excel files are ZIP archives)
        is_excel = resp.content[:2] == b'PK'  # PK = ZIP signature
        print(f"  Valid Excel: {'✓' if is_excel else '✗'}")
        
        if resp.status_code == 200 and cors_present and is_excel:
            print(f"  Result: ✓ SUCCESS\n")
        else:
            print(f"  Result: ✗ FAILED\n")
            
    except Exception as e:
        print(f"  Error: {str(e)}\n")

print("=== All Tests Complete ===")
