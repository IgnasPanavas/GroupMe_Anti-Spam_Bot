import json
import os

def lambda_handler(event, context):
    """Simple test Lambda handler"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': 'Hello from Lambda!',
            'files': os.listdir('/var/task'),
            'event': event
        })
    }
