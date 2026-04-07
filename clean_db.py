import boto3

# Connect to your specific table
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('f1-live-telemetry')

print(" Scanning table for old data...")

# FIX: Use an alias (#ts) to bypass the reserved word 'Timestamp'
response = table.scan(
    ProjectionExpression="Driver, #ts",
    ExpressionAttributeNames={"#ts": "Timestamp"}
)
items = response.get('Items', [])

if not items:
    print("Table is already empty. Nothing to clean!")
else:
    print(f" Found {len(items)} records. Deleting now...")
    
    # Use batch_writer for high-speed deletion
    with table.batch_writer() as batch:
        for item in items:
            batch.delete_item(
                Key={
                    'Driver': item['Driver'],
                    'Timestamp': item['Timestamp']
                }
            )
    print("Database is clean! You are ready for a fresh test.")