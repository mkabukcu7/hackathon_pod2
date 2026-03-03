import pandas as pd

files = [
    'bronze_customers_raw',
    'bronze_policies_raw',
    'bronze_claims_raw',
    'bronze_customer_features_raw',
    'bronze_external_signals_raw',
    'bronze_producers_raw',
    'bronze_producer_activity_raw',
]

for f in files:
    df = pd.read_parquet(f'data/{f}.parquet')
    print(f'\n=== {f} === rows={len(df)}, cols={len(df.columns)}')
    print('Columns:', list(df.columns))
    first = df.iloc[0].to_dict()
    # Show just the ID-like columns
    id_cols = [c for c in df.columns if 'id' in c.lower() or 'ID' in c]
    print('ID columns:', id_cols)
