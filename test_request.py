#!/usr/bin/env python
import urllib.request
import urllib.error

try:
    response = urllib.request.urlopen('http://localhost:8000/dashboard')
    print("Status: 200 OK")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} {e.reason}")
    print(e.read().decode('utf-8')[:500])
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
