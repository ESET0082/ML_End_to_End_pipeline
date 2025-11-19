import sys
sys.path.insert(0, 'src')

try:
    from data.create_datasets import load_data, create_features
    print('IMPORT_OK', callable(load_data), callable(create_features))
except Exception as e:
    print('IMPORT_ERROR', type(e).__name__, str(e))
