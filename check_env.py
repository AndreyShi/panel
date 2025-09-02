#!/usr/bin/env python3
import sys
import subprocess
import os

print("=== ENVIRONMENT DEBUG ===")
print(f"Executable: {sys.executable}")
print(f"Version: {sys.version}")
print(f"Path: {sys.path}")

# Проверяем pyserial
try:
    import serial
    print(f"✓ Serial imported: {serial.__version__}")
except ImportError:
    print("✗ Serial NOT imported")
    
    # Пробуем установить
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "pyserial"
        ], capture_output=True, text=True, timeout=60)
        
        print(f"Install result: {result.returncode}")
        if result.stdout:
            print(f"STDOUT: {result.stdout}")
        if result.stderr:
            print(f"STDERR: {result.stderr}")
            
    except Exception as e:
        print(f"Install failed: {e}")

print("=== END DEBUG ===")