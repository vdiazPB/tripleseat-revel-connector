#!/usr/bin/env python
import subprocess
import time
import sys

print("Starting server...")
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd=r"c:\Users\vdiaz\OneDrive - The Siegel Group Nevada, Inc\Revel API Scripts\tripleseat-revel-connector"
)

print("Server started. Press Ctrl+C to stop.")
try:
    proc.wait()
except KeyboardInterrupt:
    print("\nStopping server...")
    proc.terminate()
    proc.wait()
