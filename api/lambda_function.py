import json
import os
import boto3
import csv
import io
from datetime import datetime

def lambda_handler(event, context):
    """Comprehensive Lambda handler for all SpamShield API endpoints"""
    
    try:
        # Parse the event
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        
        # Debug logging
        print(f"DEBUG: Event received: {json.dumps(event, indent=2)}")
        print(f"DEBUG: httpMethod: {http_method}")
        print(f"DEBUG: path: {path}")
        print(f"DEBUG: rawPath: {event.get('rawPath', 'N/A')}")
        print(f"DEBUG: requestContext path: {event.get('requestContext', {}).get('path', 'N/A')}")
        
        # Handle OPTIONS requests for CORS
        if http_method == 'OPTIONS':
            return cors_response(200, {'message': 'CORS preflight successful'})
        
        # Route to appropriate handler based on path
        if path in ['/fast/status-summary', '/status-summary'] or 'status-summary' in path:
            return handle_status_summary()
        elif path in ['/uptime-history'] or 'uptime-history' in path:
            return handle_uptime_history(event, http_method)
        elif path in ['/bot-status'] or 'bot-status' in path:
            return handle_bot_status()
        elif path in ['/stats'] or 'stats' in path:
            return handle_stats()
        elif path in ['/ec2-status'] or 'ec2-status' in path:
            return handle_ec2_status()
        elif path in ['/health'] or 'health' in path:
            return cors_response(200, {
                'status': 'healthy', 
                'message': 'SpamShield API is running',
                'service': 'comprehensive-api'
            })
        else:
            return cors_response(200, {
                'message': 'SpamShield API',
                'status': 'working',
                'path': path,
                'service': 'comprehensive-api',
                'available_endpoints': [
                    '/status-summary',
                    '/fast/status-summary', 
                    '/uptime-history',
                    '/bot-status',
                    '/stats',
                    '/ec2-status',
                    '/health'
                ]
            })
            
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return cors_response(500, {
            'error': 'Internal server error', 
            'details': str(e)
        })

def handle_status_summary():
    """Get latest status for all services from S3 logs"""
    try:
        s3_bucket = os.environ.get('UPTIME_S3_BUCKET', 'spamshield-uptime-545009842663-us-east-1')
        s3_client = boto3.client('s3', region_name='us-east-1')
        
        try:
            # Read uptime history from S3
            response = s3_client.get_object(Bucket=s3_bucket, Key='uptime_history.csv')
            csv_content = response['Body'].read().decode('utf-8')
            
            # Parse CSV and get latest status for each service
            services = {}
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            for row in csv_reader:
                service = row['service']
                timestamp = row['timestamp']
                
                # Keep the most recent record for each service
                if service not in services or timestamp > services[service]['timestamp']:
                    try:
                        details = json.loads(row['details']) if row['details'] else {}
                    except:
                        details = {}
                    
                    services[service] = {
                        'timestamp': timestamp,
                        'status': row['status'],
                        'details': details
                    }
            
            # Format response
            status_summary = {
                'api': {
                    'status': services.get('api', {}).get('status', 'unknown'),
                    'lastCheck': services.get('api', {}).get('timestamp'),
                    'response_time': services.get('api', {}).get('details', {}).get('response_time'),
                    'status_code': services.get('api', {}).get('details', {}).get('status_code')
                },
                'lambda': {
                    'status': services.get('lambda', {}).get('status', 'unknown'),
                    'lastCheck': services.get('lambda', {}).get('timestamp'),
                    'response_time': services.get('lambda', {}).get('details', {}).get('response_time'),
                    'status_code': services.get('lambda', {}).get('details', {}).get('status_code')
                },
                'ec2': {
                    'status': services.get('ec2', {}).get('status', 'unknown'),
                    'lastCheck': services.get('ec2', {}).get('timestamp'),
                    'state': services.get('ec2', {}).get('details', {}).get('state'),
                    'instance_id': services.get('ec2', {}).get('details', {}).get('instance_id'),
                    'public_ip': services.get('ec2', {}).get('details', {}).get('public_ip')
                },
                'bot': {
                    'status': services.get('bot', {}).get('status', 'unknown'),
                    'lastCheck': services.get('bot', {}).get('timestamp'),
                    'platform_status': services.get('bot', {}).get('details', {}).get('platform_status'),
                    'total_groups': services.get('bot', {}).get('details', {}).get('total_groups'),
                    'active_groups': services.get('bot', {}).get('details', {}).get('active_groups'),
                    'workers': services.get('bot', {}).get('details', {}).get('workers')
                },
                'last_updated': datetime.now().isoformat(),
                'data_source': 'uptime_logs'
            }
            
            return cors_response(200, status_summary)
            
        except s3_client.exceptions.NoSuchKey:
            # No data yet, return default status
            return cors_response(200, {
                'api': {'status': 'no_data', 'lastCheck': None},
                'lambda': {'status': 'no_data', 'lastCheck': None},
                'ec2': {'status': 'no_data', 'lastCheck': None},
                'bot': {'status': 'no_data', 'lastCheck': None},
                'last_updated': datetime.now().isoformat(),
                'data_source': 'uptime_logs'
            })
            
    except Exception as e:
        print(f"Error in status summary: {e}")
        return cors_response(500, {'error': f'Status summary error: {str(e)}'})

def handle_uptime_history(event, http_method):
    """Handle uptime history requests"""
    try:
        s3_bucket = os.environ.get('UPTIME_S3_BUCKET', 'spamshield-uptime-545009842663-us-east-1')
        s3_client = boto3.client('s3', region_name='us-east-1')
        
        if http_method == 'GET':
            # Read uptime history
            query_params = event.get('queryStringParameters', {}) or {}
            service = query_params.get('service', 'all')
            minutes = int(query_params.get('minutes', 2880))  # Default 48 hours
            limit = int(query_params.get('limit', 180))  # Default 180 records
            
            try:
                response = s3_client.get_object(Bucket=s3_bucket, Key='uptime_history.csv')
                csv_content = response['Body'].read().decode('utf-8')
                
                # Parse and filter records
                records = []
                csv_reader = csv.DictReader(io.StringIO(csv_content))
                for row in csv_reader:
                    if service == 'all' or row['service'] == service:
                        records.append(row)
                
                # Filter by time
                from datetime import timedelta
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
                
                return cors_response(200, {
                    'minutes': minutes,
                    'limit': limit,
                    'service': service,
                    'records': filtered_records
                })
                
            except s3_client.exceptions.NoSuchKey:
                return cors_response(200, {
                    'minutes': minutes,
                    'limit': limit,
                    'service': service,
                    'records': []
                })
        
        elif http_method == 'POST':
            # Add new uptime record (for the uptime monitor Lambda)
            body = event.get('body', '{}')
            if not body:
                return cors_response(400, {'error': 'No data provided'})
            
            try:
                record_data = json.loads(body) if isinstance(body, str) else body
                
                # Validate required fields
                required_fields = ['service', 'status']
                for field in required_fields:
                    if field not in record_data:
                        return cors_response(400, {'error': f'Missing required field: {field}'})
                
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
                
                return cors_response(200, {'ok': True, 'message': 'Uptime record added'})
                
            except Exception as e:
                return cors_response(500, {'ok': False, 'error': str(e)})
        
        else:
            return cors_response(405, {'error': 'Method not allowed', 'allowed_methods': ['GET', 'POST']})
            
    except Exception as e:
        print(f"Error in uptime history: {e}")
        return cors_response(500, {'error': f'Uptime history error: {str(e)}'})

def handle_bot_status():
    """Check SpamShield Platform status on EC2"""
    try:
        ssm_client = boto3.client('ssm', region_name='us-east-1')
        
        # Check platform status
        command = "cd /home/ubuntu/GroupMe_Anti-Spam_Bot && ./manage_platform.sh status"
        response = ssm_client.send_command(
            InstanceIds=['i-0a0001f601291b280'],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': [command]},
            TimeoutSeconds=30
        )
        
        command_id = response['Command']['CommandId']
        
        # Wait for command completion
        import time
        for _ in range(10):
            time.sleep(1)
            output = ssm_client.get_command_invocation(
                CommandId=command_id,
                InstanceId='i-0a0001f601291b280'
            )
            if output['Status'] in ['Success', 'Failed', 'Cancelled', 'TimedOut']:
                break
        
        # Parse platform status
        status_output = output.get('StandardOutputContent', '').strip()
        is_active = 'is running' in status_output and 'Health check: ✅ PASSED' in status_output
        
        # Extract PID
        pid = 'unknown'
        if 'PID:' in status_output:
            try:
                pid = status_output.split('PID: ')[1].split(')')[0]
            except:
                pass
        
        # Get additional platform info
        health_command = "curl -s http://localhost:8000/health"
        health_response = ssm_client.send_command(
            InstanceIds=['i-0a0001f601291b280'],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': [health_command]},
            TimeoutSeconds=30
        )
        
        health_command_id = health_response['Command']['CommandId']
        time.sleep(2)
        
        health_output = ssm_client.get_command_invocation(
            CommandId=health_command_id,
            InstanceId='i-0a0001f601291b280'
        )
        
        # Parse health data
        health_data = {}
        try:
            health_json = health_output.get('StandardOutputContent', '{}')
            health_data = json.loads(health_json)
        except:
            pass
        
        # Get groups count
        groups_command = "curl -s http://localhost:8000/api/v1/groups/"
        groups_response = ssm_client.send_command(
            InstanceIds=['i-0a0001f601291b280'],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': [groups_command]},
            TimeoutSeconds=30
        )
        
        groups_command_id = groups_response['Command']['CommandId']
        time.sleep(2)
        
        groups_output = ssm_client.get_command_invocation(
            CommandId=groups_command_id,
            InstanceId='i-0a0001f601291b280'
        )
        
        groups_data = {}
        try:
            groups_json = groups_output.get('StandardOutputContent', '{}')
            groups_data = json.loads(groups_json)
        except:
            pass
        
        bot_data = {
            "active": is_active,
            "status": "operational" if is_active else "outage",
            "platform_status": "running" if is_active else "stopped",
            "main_pid": pid,
            "health_status": health_data.get('status', 'unknown'),
            "orchestrator_running": health_data.get('orchestrator', {}).get('running', False),
            "total_groups": groups_data.get('total_count', 0),
            "active_groups": groups_data.get('active_count', 0),
            "workers": len(health_data.get('orchestrator', {}).get('workers', {})),
            "database_status": health_data.get('components', {}).get('database', 'unknown'),
            "metrics_status": health_data.get('components', {}).get('metrics_collector', 'unknown'),
            "last_checked": datetime.now().isoformat(),
            "note": "Real-time SpamShield Platform status from EC2",
            "service_type": "spamshield_platform"
        }
        
        return cors_response(200, bot_data)
        
    except Exception as e:
        print(f"Error checking bot status: {e}")
        return cors_response(200, {
            "active": False,
            "status": "outage",
            "error": f"Platform check failed: {str(e)}",
            "last_checked": datetime.now().isoformat(),
            "note": "Fallback status due to platform check error",
            "service_type": "spamshield_platform"
        })

def handle_stats():
    """Return stats data for the frontend"""
            stats_data = {
                "total_messages": 1250,
                "spam_detected": 45,
                "accuracy": 97.5,
                "total_predictions": 1250,
                "groups_monitored": 8,
                "last_updated": datetime.now().isoformat(),
        "status": "active"
    }
    
    return cors_response(200, stats_data)

def handle_ec2_status():
    """Return comprehensive EC2 instance status"""
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
                "region": instance['Placement']['AvailabilityZone'][:-1],
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
                
        return cors_response(200, ec2_data)
        
            except Exception as e:
                print(f"Error getting EC2 status: {e}")
                # Fallback to basic info if AWS call fails
                ec2_data = {
                    "instanceId": "i-0a0001f601291b280",
                    "state": "checking",
            "publicIp": "3.91.154.73",
                    "instanceType": "t2.micro",
                    "region": "us-east-1",
                    "launchTime": "2025-08-31T19:55:44+00:00",
                    "lastChecked": datetime.now().isoformat(),
                    "statusCheck": "error",
                    "systemStatus": "error",
                    "instanceStatus": "error",
                    "error": str(e)
                }
            
        return cors_response(200, ec2_data)

def cors_response(status_code, body):
    """Helper function to create CORS-enabled responses"""
                        return {
        'statusCode': status_code,
                            'headers': {
                                'Content-Type': 'application/json',
                                'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                            },
        'body': json.dumps(body)
        }
