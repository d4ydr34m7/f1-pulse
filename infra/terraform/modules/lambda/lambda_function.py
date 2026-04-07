import json
import boto3
import base64
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('f1-live-telemetry')

def lambda_handler(event, context):
    for record in event['Records']:
        # 1. Decode Kinesis data
        data_str = base64.b64decode(record['kinesis']['data']).decode('utf-8')
        
        # Force DynamoDB to accept decimals
        payload = json.loads(data_str, parse_float=Decimal)
        
        # 2. Build the item - explicitly including X and Y!
        item = {
            'Driver': payload['Driver'],
            'Timestamp': payload['Timestamp'],
            'Speed': payload['Speed'],
            'RPM': payload['RPM'],
            'Throttle': payload['Throttle'],
            'TractionLoss': payload.get('TractionLoss', 0),
            'Position_X': payload.get('Position_X', 0),
            'Position_Y': payload.get('Position_Y', 0)
        }
        
        table.put_item(Item=item)
        
    return {'statusCode': 200}