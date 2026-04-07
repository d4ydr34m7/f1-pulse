import json
import boto3
import base64
import time
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('f1-live-telemetry')

def lambda_handler(event, context):
    with table.batch_writer() as batch:
        for record in event['Records']:
            # 1. Decode Kinesis data
            data_str = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            
            # 2. Parse JSON and handle AWS Decimals automatically
            payload = json.loads(data_str, parse_float=Decimal)
            
            # 3. Build item natively including our GPS coordinates
            item = {
                'Driver': payload['Driver'],
                'Timestamp': payload['Timestamp'],
                'Speed': payload['Speed'],
                'RPM': payload['RPM'],
                'Throttle': payload['Throttle'],
                'TractionLoss': payload.get('TractionLoss', Decimal('0')),
                'Position_X': payload.get('Position_X', Decimal('0')),
                'Position_Y': payload.get('Position_Y', Decimal('0')),
                'ExpirationTime': int(time.time()) + 86400
            }
            
            batch.put_item(Item=item)
            
    return {'statusCode': 200, 'body': 'Success'}