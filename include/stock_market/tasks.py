from airflow.hooks.base import BaseHook
import  json
from io import BytesIO
from minio import Minio

# These are the tasks executed by the DAG - stock_market.py

# Gets Stock Prices and outputs the data as JSON
def _get_stock_prices(url, symbol):
    import requests
    import json

    url = f"{url}{symbol}?metrics=high?&interval=1d&range=1y"
    api = BaseHook.get_connection('stock_api')
    response = requests.get(url, headers=api.extra_dejson['headers'])
    return json.dumps(response.json()['chart']['result'][0])

# Store Prices Function returns the path to the stored object in the format required in the MinIO Storage
def _store_prices(stock):
    minio = BaseHook.get_connection('minio')
    client = Minio(
        endpoint=minio.extra_dejson['endpoint_url'].split('//')[1],
        access_key=minio.login,
        secret_key=minio.password, 
        secure=False
    )
    bucket_name = 'stock-market'
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
    stock = json.loads(stock)
    symbol = stock['meta']['symbol']
    data = json.dumps(stock, ensure_ascii=False).encode('utf8')
    obgw = client.put_object(
        bucket_name = bucket_name, 
        object_name = f'{symbol}/prices.json',
        data = BytesIO(data),
        length = len(data)
        )
    return f'{obgw.bucket_name}/{symbol}'