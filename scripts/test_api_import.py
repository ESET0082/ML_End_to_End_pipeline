import sys
sys.path.insert(0, 'src')

try:
    from api.server import MeterFeatures
    print('IMPORT_OK: MeterFeatures available')
except Exception as e:
    print('IMPORT_ERROR:', type(e).__name__, str(e))
