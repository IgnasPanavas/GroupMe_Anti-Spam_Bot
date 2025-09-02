import json
import os
import sys
from datetime import datetime
import boto3
import csv
import io

def lambda_handler(event, context):
    """Lambda handler focused on status monitoring endpoints"""
    print(f"Status Lambda invoked with event: {event}")
    print(f"Context: {context}")
    
    try:
        # Parse the event - handle both direct invocation and API Gateway
        if 'httpMethod' in event:
            # Direct invocation
            http_method = event.get('httpMethod', 'GET')
            path = event.get('path', '/')
        else:
            # API Gateway invocation
            http_method = event.get('httpMethod', 'GET')
            path = event.get('path', '/')
            # Handle proxy path
            if 'pathParameters' in event and event['pathParameters'] and 'proxy' in event['pathParameters']:
                path = '/' + event['pathParameters']['proxy']
        
        # Debug logging for path parsing
        print(f"DEBUG: Event keys: {list(event.keys())}")
        print(f"DEBUG: httpMethod: {http_method}")
        print(f"DEBUG: path: {path}")
        print(f"DEBUG: rawPath: {event.get('rawPath', 'N/A')}")
        print(f"DEBUG: requestContext: {event.get('requestContext', {}).get('path', 'N/A')}")
        
        # Try alternative path extraction methods
        if not path or path == '/':
            # Try rawPath (newer API Gateway format)
            if 'rawPath' in event:
                path = event['rawPath']
            # Try requestContext path
            elif 'requestContext' in event and 'path' in event['requestContext']:
                path = event['requestContext']['path']
            # Try resource path
            elif 'resource' in event:
                path = event['resource']
        
        # Handle OPTIONS requests for CORS
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps({'message': 'CORS preflight successful'})
            }
        
        # Handle different endpoints
        if path == '/stats' or path.endswith('/stats'):
            # Return stats data that your frontend expects
            stats_data = {
                "total_messages": 1250,
                "spam_detected": 45,
                "accuracy": 97.5,
                "total_predictions": 1250,
                "groups_monitored": 8,
                "last_updated": datetime.now().isoformat(),
                "status": "active"
            }
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps(stats_data)
            }
        
        elif path == '/ec2-status' or path.endswith('/ec2-status'):
            # Return comprehensive EC2 instance status using AWS SDK
            try:
                ec2_client = boto3.client('ec2', region_name='us-east-1')
                
                # Get real instance status
                response = ec2_client.describe_instances(
                    InstanceIds=['i-0a0001f601291b280']
                )
                
                if response['Reservations']:
                    instance = response['Reservations'][0]['Instances'][0]
                    
                    # Get instance status checks
                    try:
                        status_response = ec2_client.describe_instance_status(
                            InstanceIds=['i-0a0001f601291b280']
                        )
                        status_checks = status_response.get('InstanceStatuses', [])
                        system_status = "passed" if status_checks and status_checks[0].get('SystemStatus', {}).get('Status') == 'ok' else "checking"
                        instance_status = "passed" if status_checks and status_checks[0].get('InstanceStatus', {}).get('Status') == 'ok' else "checking"
                    except Exception as status_error:
                        print(f"Error getting instance status: {status_error}")
                        system_status = "checking"
                        instance_status = "checking"
                    
                    ec2_data = {
                        "instanceId": instance['InstanceId'],
                        "state": instance['State']['Name'],
                        "publicIp": instance.get('PublicIpAddress', 'N/A'),
                        "instanceType": instance['InstanceType'],
                        "region": instance['Placement']['AvailabilityZone'][:-1],  # Remove last character to get region
                        "launchTime": instance['LaunchTime'].isoformat(),
                        "lastChecked": datetime.now().isoformat(),
                        "statusCheck": "passed" if instance.get('StateReason', {}).get('Code') == 'User initiated (2015-01-01 00:00:00 UTC)' else "checking",
                        "systemStatus": system_status,
                        "instanceStatus": instance_status,
                        "availabilityZone": instance['Placement']['AvailabilityZone'],
                        "vpcId": instance.get('VpcId', 'N/A'),
                        "subnetId": instance.get('SubnetId', 'N/A'),
                        "securityGroups": [sg['GroupName'] for sg in instance.get('SecurityGroups', [])],
                        "monitoring": instance.get('Monitoring', {}).get('State', 'disabled'),
                        "platform": instance.get('Platform', 'linux'),
                        "architecture": instance.get('Architecture', 'x86_64'),
                        "rootDeviceType": instance.get('RootDeviceType', 'ebs'),
                        "ebsOptimized": instance.get('EbsOptimized', False),
                        "networkInterfaces": len(instance.get('NetworkInterfaces', [])),
                        "tags": {tag['Key']: tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] in ['Name', 'Environment', 'Project']}
                    }
                else:
                    ec2_data = {
                        "instanceId": "i-0a0001f601291b280",
                        "state": "unknown",
                        "publicIp": "N/A",
                        "instanceType": "t2.micro",
                        "region": "us-east-1",
                        "launchTime": "Unknown",
                        "lastChecked": datetime.now().isoformat(),
                        "statusCheck": "failed",
                        "systemStatus": "failed",
                        "instanceStatus": "failed",
                        "error": "Instance not found"
                    }
                
            except Exception as e:
                print(f"Error getting EC2 status: {e}")
                # Fallback to basic info if AWS call fails
                ec2_data = {
                    "instanceId": "i-0a0001f601291b280",
                    "state": "checking",
                    "publicIp": "3.91.154.73",  # Updated to actual IP
                    "instanceType": "t2.micro",
                    "region": "us-east-1",
                    "launchTime": "2025-08-31T19:55:44+00:00",
                    "lastChecked": datetime.now().isoformat(),
                    "statusCheck": "error",
                    "systemStatus": "error",
                    "instanceStatus": "error",
                    "error": str(e)
                }
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps(ec2_data)
            }
        
        elif path == '/uptime-history' or path.endswith('/uptime-history') or '/uptime-history' in path:
            print(f"DEBUG: Matched uptime-history condition! path='{path}'")
            # Handle uptime history requests
            try:
                from datetime import timedelta
                
                # Get S3 configuration
                s3_bucket = os.environ.get('UPTIME_S3_BUCKET', 'spamshield-uptime-545009842663-us-east-1')
                s3_client = boto3.client('s3', region_name='us-east-1')
                
                if http_method == 'GET':
                    # Read uptime history
                    query_params = event.get('queryStringParameters', {}) or {}
                    service = query_params.get('service', 'all')
                    minutes = int(query_params.get('minutes', 2880))  # Default 48 hours
                    limit = int(query_params.get('limit', 180))  # Default 180 records
                    
                    try:
                        # Try to read existing data
                        response = s3_client.get_object(Bucket=s3_bucket, Key='uptime_history.csv')
                        csv_content = response['Body'].read().decode('utf-8')
                        
                        # Parse CSV
                        records = []
                        csv_reader = csv.DictReader(io.StringIO(csv_content))
                        for row in csv_reader:
                            if service == 'all' or row['service'] == service:
                                records.append(row)
                        
                        # Filter by time
                        cutoff_time = datetime.now() - timedelta(minutes=minutes)
                        filtered_records = []
                        for record in records:
                            try:
                                record_time = datetime.fromisoformat(record['timestamp'])
                                if record_time >= cutoff_time:
                                    filtered_records.append(record)
                            except:
                                continue
                        
                        # Sort by timestamp (newest first) and limit
                        filtered_records.sort(key=lambda x: x['timestamp'], reverse=True)
                        filtered_records = filtered_records[:limit]
                        
                        return {
                            'statusCode': 200,
                            'headers': {
                                'Content-Type': 'application/json',
                                'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                            },
                            'body': json.dumps({
                                'minutes': minutes,
                                'limit': limit,
                                'service': service,
                                'records': filtered_records
                            })
                        }
                        
                    except s3_client.exceptions.NoSuchKey:
                        # No data yet, return empty response
                        return {
                            'statusCode': 200,
                            'headers': {
                                'Content-Type': 'application/json',
                                'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                            },
                            'body': json.dumps({
                                'minutes': minutes,
                                'limit': limit,
                                'service': service,
                                'records': []
                            })
                        }
                
                elif http_method == 'POST':
                    # Add new uptime record
                    body = event.get('body', '{}')
                    if not body:
                        return {
                            'statusCode': 400,
                            'headers': {
                                'Content-Type': 'application/json',
                                'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                            },
                            'body': json.dumps({'error': 'No data provided'})
                        }
                    
                    try:
                        # Parse request body
                        if isinstance(body, str):
                            record_data = json.loads(body)
                        else:
                            record_data = body
                        
                        # Validate required fields (timestamp is optional - will be auto-generated)
                        required_fields = ['service', 'status']
                        for field in required_fields:
                            if field not in record_data:
                                return {
                                    'statusCode': 400,
                                    'headers': {
                                        'Content-Type': 'application/json',
                                        'Access-Control-Allow-Origin': '*',
                                        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                                        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                                    },
                                    'body': json.dumps({'error': f'Missing required field: {field}'})
                                }
                        
                        # Auto-generate timestamp if not provided
                        if 'timestamp' not in record_data:
                            record_data['timestamp'] = datetime.now().isoformat()
                        
                        # Read existing data
                        existing_records = []
                        try:
                            response = s3_client.get_object(Bucket=s3_bucket, Key='uptime_history.csv')
                            csv_content = response['Body'].read().decode('utf-8')
                            csv_reader = csv.DictReader(io.StringIO(csv_content))
                            existing_records = list(csv_reader)
                        except s3_client.exceptions.NoSuchKey:
                            # Create new file with headers
                            existing_records = []
                        
                        # Add new record
                        new_record = {
                            'timestamp': record_data['timestamp'],
                            'service': record_data['service'],
                            'status': record_data['status'],
                            'details': record_data.get('details', '{}')
                        }
                        existing_records.append(new_record)
                        
                        # Write back to S3
                        csv_buffer = io.StringIO()
                        fieldnames = ['timestamp', 'service', 'status', 'details']
                        csv_writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames, extrasaction='ignore')
                        csv_writer.writeheader()
                        csv_writer.writerows(existing_records)
                        
                        s3_client.put_object(
                            Bucket=s3_bucket,
                            Key='uptime_history.csv',
                            Body=csv_buffer.getvalue(),
                            ContentType='text/csv'
                        )
                        
                        return {
                            'statusCode': 200,
                            'headers': {
                                'Content-Type': 'application/json',
                                'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                            },
                            'body': json.dumps({'ok': True, 'message': 'Uptime record added'})
                        }
                        
                    except Exception as e:
                        return {
                            'statusCode': 500,
                            'headers': {
                                'Content-Type': 'application/json',
                                'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                            },
                            'body': json.dumps({'ok': False, 'error': str(e)})
                        }
                
                else:
                    return {
                        'statusCode': 405,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*',
                            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                        },
                        'body': json.dumps({'error': 'Method not allowed', 'allowed_methods': ['GET', 'POST']})
                    }
                    
            except Exception as e:
                print(f"Error in uptime-history endpoint: {e}")
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                    },
                    'body': json.dumps({'error': f'Internal server error: {str(e)}'})
                }
        
        elif path == '/bot-status' or path.endswith('/bot-status'):
            # Check actual GroupMe bot systemd service status on EC2
            try:
                # Use AWS Systems Manager to run command on EC2 instance
                ssm_client = boto3.client('ssm', region_name='us-east-1')
                
                # Command to check systemd service status
                command = "systemctl is-active groupme-bot.service"
                
                response = ssm_client.send_command(
                    InstanceIds=['i-0a0001f601291b280'],
                    DocumentName='AWS-RunShellScript',
                    Parameters={'commands': [command]},
                    TimeoutSeconds=30
                )
                
                command_id = response['Command']['CommandId']
                
                # Wait for command completion and get result
                import time
                for _ in range(10):  # Wait up to 10 seconds
                    time.sleep(1)
                    output = ssm_client.get_command_invocation(
                        CommandId=command_id,
                        InstanceId='i-0a0001f601291b280'
                    )
                    if output['Status'] in ['Success', 'Failed', 'Cancelled', 'TimedOut']:
                        break
                
                service_status = output.get('StandardOutputContent', '').strip()
                is_active = service_status == 'active'
                
                # Get additional service info
                info_command = "systemctl show groupme-bot.service --property=ActiveState,SubState,LoadState,UnitFileState,MainPID,MemoryCurrent"
                info_response = ssm_client.send_command(
                    InstanceIds=['i-0a0001f601291b280'],
                    DocumentName='AWS-RunShellScript',
                    Parameters={'commands': [info_command]},
                    TimeoutSeconds=30
                )
                
                info_command_id = info_response['Command']['CommandId']
                time.sleep(2)  # Brief wait for command completion
                
                info_output = ssm_client.get_command_invocation(
                    CommandId=info_command_id,
                    InstanceId='i-0a0001f601291b280'
                )
                
                service_info = info_output.get('StandardOutputContent', '')
                
                # Parse service info
                info_lines = service_info.strip().split('\n')
                service_details = {}
                for line in info_lines:
                    if '=' in line:
                        key, value = line.split('=', 1)
                        service_details[key] = value
                
                bot_data = {
                    "active": is_active,
                    "status": "operational" if is_active else "outage",
                    "service_status": service_status,
                    "active_state": service_details.get('ActiveState', 'unknown'),
                    "sub_state": service_details.get('SubState', 'unknown'),
                    "load_state": service_details.get('LoadState', 'unknown'),
                    "unit_file_state": service_details.get('UnitFileState', 'unknown'),
                    "main_pid": service_details.get('MainPID', 'unknown'),
                    "memory_usage": service_details.get('MemoryCurrent', 'unknown'),
                    "last_checked": datetime.now().isoformat(),
                    "note": "Real-time systemd service status from EC2"
                }
                
            except Exception as e:
                print(f"Error checking bot status: {e}")
                # Fallback to basic status check
                bot_data = {
                    "active": False,
                    "status": "outage",
                    "error": f"Service check failed: {str(e)}",
                    "last_checked": datetime.now().isoformat(),
                    "note": "Fallback status due to service check error"
                }
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps(bot_data)
            }
        
        elif path == '/health' or path.endswith('/health'):
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps({
                    'status': 'healthy', 
                    'message': 'SpamShield Status API is running',
                    'service': 'status-monitoring'
                })
            }
        
        else:
            print(f"DEBUG: Falling back to generic response for path='{path}'")
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': json.dumps({
                    'message': 'SpamShield Status API',
                    'status': 'working',
                    'path': path,
                    'service': 'status-monitoring'
                })
            }
            
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'error': 'Internal server error', 
                'details': str(e),
                'traceback': traceback_str,
                'event_received': str(event)[:500] if event else 'No event received'
            })
        }
