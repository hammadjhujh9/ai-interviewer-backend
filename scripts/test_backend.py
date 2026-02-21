#!/usr/bin/env python3
"""
Test backend health and API endpoints.
Usage: python scripts/test_backend.py [--base-url URL]
       Default: http://localhost:8000
       Example for remote: python scripts/test_backend.py --base-url http://your-server:8000
"""
import argparse
import sys
import time

try:
    import httpx
except ImportError:
    print("FAIL: httpx not installed. Run: pip install httpx")
    sys.exit(1)


def test_root(base_url: str) -> bool:
    """Test backend root endpoint."""
    try:
        r = httpx.get(f"{base_url}/", timeout=10)
        if r.status_code == 200 and "Recruiter.AI" in r.text:
            print("PASS: Backend root (/) responding")
            return True
        print(f"FAIL: Root returned {r.status_code}: {r.text[:200]}")
        return False
    except httpx.ConnectError:
        print(f"FAIL: Cannot connect to {base_url} - is the backend running?")
        return False
    except Exception as e:
        print(f"FAIL: Root check failed - {e}")
        return False


def test_docs(base_url: str) -> bool:
    """Test API docs are accessible."""
    try:
        r = httpx.get(f"{base_url}/docs", timeout=10)
        if r.status_code == 200:
            print("PASS: API docs (/docs) accessible")
            return True
        print(f"FAIL: Docs returned {r.status_code}")
        return False
    except Exception as e:
        print(f"FAIL: Docs check failed - {e}")
        return False


def test_auth_signup(base_url: str) -> tuple[bool, str | None]:
    """Test candidate signup. Returns (success, email) for login test."""
    email = f"health_check_{int(time.time())}@test.example.com"
    payload = {
        "email": email,
        "full_name": "Health Check User",
        "password": "TestPass123!",
        "role": "candidate",
    }
    try:
        r = httpx.post(f"{base_url}/auth/candidate/signup", json=payload, timeout=10)
        if r.status_code == 201:
            print("PASS: Auth signup (/auth/candidate/signup)")
            return True, email
        print(f"FAIL: Signup returned {r.status_code}: {r.text[:200]}")
        return False, None
    except Exception as e:
        print(f"FAIL: Signup failed - {e}")
        return False, None


def test_auth_login(base_url: str, email: str, password: str = "TestPass123!") -> tuple[bool, str | None]:
    """Test login. Returns (success, token)."""
    payload = {"email": email, "password": password}
    try:
        r = httpx.post(f"{base_url}/auth/login", json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json()
            token = data.get("access_token")
            if token:
                print("PASS: Auth login (/auth/login)")
                return True, token
        print(f"FAIL: Login returned {r.status_code}: {r.text[:200]}")
        return False, None
    except Exception as e:
        print(f"FAIL: Login failed - {e}")
        return False, None


def test_protected_endpoint(base_url: str, token: str) -> bool:
    """Test protected endpoint (candidate profile) with token."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = httpx.get(f"{base_url}/auth/candidate/profile", headers=headers, timeout=10)
        if r.status_code == 200:
            print("PASS: Protected API (/auth/candidate/profile) with token")
            return True
        print(f"FAIL: Profile returned {r.status_code}: {r.text[:200]}")
        return False
    except Exception as e:
        print(f"FAIL: Profile check failed - {e}")
        return False


def run_all(base_url: str) -> bool:
    """Run all backend/API tests."""
    print(f"\n--- Testing backend at {base_url} ---\n")
    all_ok = True

    if not test_root(base_url):
        all_ok = False
    if not test_docs(base_url):
        all_ok = False

    ok, email = test_auth_signup(base_url)
    if not ok:
        all_ok = False
    else:
        ok2, token = test_auth_login(base_url, email)
        if not ok2:
            all_ok = False
        elif not test_protected_endpoint(base_url, token):
            all_ok = False

    print(f"\n--- Result: {'ALL TESTS PASSED' if all_ok else 'SOME TESTS FAILED'} ---\n")
    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test backend and APIs")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the backend (default: http://localhost:8000)",
    )
    args = parser.parse_args()
    success = run_all(args.base_url.strip("/"))
    sys.exit(0 if success else 1)
