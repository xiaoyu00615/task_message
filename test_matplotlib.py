import sys
print(f"Python path: {sys.executable}")
try:
    import matplotlib
    print(f"Successfully imported matplotlib version: {matplotlib.__version__}")
except ImportError as e:
    print(f"Failed to import matplotlib: {e}")
    print(f"sys.path: {sys.path}")