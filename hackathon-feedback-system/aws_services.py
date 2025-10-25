# aws_services.py
"""
AWS service integrations for hackathon feedback system
Handles DynamoDB, S3, CloudWatch, and other AWS services
"""




import boto3
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from botocore.exceptions import ClientError, NoCredentialsError
import logging

from config import (
    AWS_REGION,
    DYNAMODB_TABLE_NAME,
    DYNAMODB_ENDPOINT,
    S3_BUCKET_NAME,
    S3_BACKUP_PREFIX,
    CLOUDWATCH_LOG_GROUP,
    CLOUDWATCH_METRICS_NAMESPACE,
    get_aws_config
)

logger = logging.getLogger(__name__)

# Initialize AWS clients
def get_dynamodb_client():
    """Get DynamoDB client with proper configuration"""
    try:
        config = get_aws_config()
        if DYNAMODB_ENDPOINT:  # For local development
            config['endpoint_url'] = DYNAMODB_ENDPOINT
        return boto3.client('dynamodb', **config)
    except Exception as e:
        logger.error(f"Failed to create DynamoDB client: {e}")
        return None

def get_s3_client():
    """Get S3 client with proper configuration"""
    try:
        config = get_aws_config()
        return boto3.client('s3', **config)
    except Exception as e:
        logger.error(f"Failed to create S3 client: {e}")
        return None

def get_cloudwatch_client():
    """Get CloudWatch client with proper configuration"""
    try:
        config = get_aws_config()
        return boto3.client('cloudwatch', **config)
    except Exception as e:
        logger.error(f"Failed to create CloudWatch client: {e}")
        return None

async def create_dynamodb_table():
    """Create DynamoDB table if it doesn't exist"""
    try:
        dynamodb = get_dynamodb_client()
        if not dynamodb:
            return False
        
        # Check if table exists
        try:
            response = dynamodb.describe_table(TableName=DYNAMODB_TABLE_NAME)
            logger.info(f"Table {DYNAMODB_TABLE_NAME} already exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise e
        
        # Create table
        table_definition = {
            'TableName': DYNAMODB_TABLE_NAME,
            'KeySchema': [
                {
                    'AttributeName': 'feedback_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'feedback_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'hackathon_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'timestamp',
                    'AttributeType': 'S'
                }
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'hackathon-timestamp-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'hackathon_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'timestamp',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST'
        }
        
        response = dynamodb.create_table(**table_definition)
        logger.info(f"Created table {DYNAMODB_TABLE_NAME}")
        
        # Wait for table to be active
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=DYNAMODB_TABLE_NAME)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create DynamoDB table: {e}")
        return False

async def store_feedback_dynamodb(feedback_data: Dict) -> bool:
    """Store feedback data in DynamoDB"""
    try:
        dynamodb = get_dynamodb_client()
        if not dynamodb:
            raise Exception("DynamoDB client not available")
        
        # Ensure table exists
        await create_dynamodb_table()
        
        # Convert data to DynamoDB format
        item = {
            'feedback_id': {'S': feedback_data['feedback_id']},
            'user_hash': {'S': feedback_data['user_hash']},
            'hackathon_id': {'S': feedback_data['hackathon_id']},
            'feedback_text': {'S': feedback_data['feedback_text']},
            'timestamp': {'S': feedback_data['timestamp']},
            'analysis': {'S': json.dumps(feedback_data.get('analysis', {}))},
            'metadata': {'S': json.dumps(feedback_data.get('metadata', {}))}
        }
        
        # Add email if provided
        if feedback_data.get('user_email'):
            item['user_email'] = {'S': feedback_data['user_email']}
        
        # Store in DynamoDB
        response = dynamodb.put_item(
            TableName=DYNAMODB_TABLE_NAME,
            Item=item
        )
        
        logger.info(f"Stored feedback {feedback_data['feedback_id']} in DynamoDB")
        return True
        
    except Exception as e:
        logger.error(f"Failed to store feedback in DynamoDB: {e}")
        raise

async def get_feedback_from_dynamodb(hackathon_id: str, limit: int = 100) -> List[Dict]:
    """Retrieve feedback from DynamoDB for a specific hackathon"""
    try:
        dynamodb = get_dynamodb_client()
        if not dynamodb:
            return []
        
        # Query using GSI
        response = dynamodb.query(
            TableName=DYNAMODB_TABLE_NAME,
            IndexName='hackathon-timestamp-index',
            KeyConditionExpression='hackathon_id = :hid',
            ExpressionAttributeValues={
                ':hid': {'S': hackathon_id}
            },
            ScanIndexForward=False,  # Sort by timestamp descending
            Limit=limit
        )
        
        # Convert DynamoDB format back to regular dict
        feedback_list = []
        for item in response.get('Items', []):
            feedback = {
                'feedback_id': item['feedback_id']['S'],
                'user_hash': item['user_hash']['S'],
                'hackathon_id': item['hackathon_id']['S'],
                'feedback_text': item['feedback_text']['S'],
                'timestamp': item['timestamp']['S'],
                'analysis': json.loads(item.get('analysis', {}).get('S', '{}')),
                'metadata': json.loads(item.get('metadata', {}).get('S', '{}'))
            }
            
            if 'user_email' in item:
                feedback['user_email'] = item['user_email']['S']
            
            feedback_list.append(feedback)
        
        return feedback_list
        
    except Exception as e:
        logger.error(f"Failed to retrieve feedback from DynamoDB: {e}")
        return []

async def backup_to_s3(feedback_data: Dict) -> bool:
    """Backup feedback data to S3"""
    try:
        s3 = get_s3_client()
        if not s3:
            logger.warning("S3 client not available, skipping backup")
            return False
        
        # Create S3 bucket if it doesn't exist
        try:
            s3.head_bucket(Bucket=S3_BUCKET_NAME)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Bucket doesn't exist, create it
                if AWS_REGION == 'us-east-1':
                    s3.create_bucket(Bucket=S3_BUCKET_NAME)
                else:
                    s3.create_bucket(
                        Bucket=S3_BUCKET_NAME,
                        CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
                    )
                logger.info(f"Created S3 bucket {S3_BUCKET_NAME}")
        
        # Generate S3 key
        timestamp = datetime.now()
        s3_key = f"{S3_BACKUP_PREFIX}{timestamp.strftime('%Y/%m/%d')}/{feedback_data['feedback_id']}.json"
        
        # Upload to S3
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(feedback_data, indent=2, default=str),
            ContentType='application/json'
        )
        
        logger.info(f"Backed up feedback {feedback_data['feedback_id']} to S3")
        return True
        
    except Exception as e:
        logger.error(f"Failed to backup to S3: {e}")
        return False

async def send_cloudwatch_metrics(metric_name: str, value: float, dimensions: Dict = None) -> bool:
    """Send custom metrics to CloudWatch"""
    try:
        cloudwatch = get_cloudwatch_client()
        if not cloudwatch:
            logger.warning("CloudWatch client not available, skipping metrics")
            return False
        
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': 'Count',
            'Timestamp': datetime.now()
        }
        
        if dimensions:
            metric_data['Dimensions'] = [
                {'Name': key, 'Value': value} for key, value in dimensions.items()
            ]
        
        cloudwatch.put_metric_data(
            Namespace=CLOUDWATCH_METRICS_NAMESPACE,
            MetricData=[metric_data]
        )
        
        logger.info(f"Sent CloudWatch metric: {metric_name} = {value}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send CloudWatch metrics: {e}")
        return False

async def create_cloudwatch_dashboard(hackathon_id: str) -> bool:
    """Create CloudWatch dashboard for hackathon feedback monitoring"""
    try:
        cloudwatch = get_cloudwatch_client()
        if not cloudwatch:
            return False
        
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "x": 0,
                    "y": 0,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            [CLOUDWATCH_METRICS_NAMESPACE, "FeedbackSubmitted"]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": AWS_REGION,
                        "title": "Feedback Submissions Over Time"
                    }
                },
                {
                    "type": "metric",
                    "x": 12,
                    "y": 0,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            [CLOUDWATCH_METRICS_NAMESPACE, "FeedbackSubmitted", "Sentiment", "positive"],
                            [".", ".", ".", "negative"],
                            [".", ".", ".", "neutral"]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": AWS_REGION,
                        "title": "Feedback by Sentiment"
                    }
                }
            ]
        }
        
        cloudwatch.put_dashboard(
            DashboardName=f"HackathonFeedback-{hackathon_id}",
            DashboardBody=json.dumps(dashboard_body)
        )
        
        logger.info(f"Created CloudWatch dashboard for {hackathon_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create CloudWatch dashboard: {e}")
        return False

async def setup_aws_resources(hackathon_id: str) -> Dict[str, bool]:
    """Setup all required AWS resources"""
    results = {}
    
    # Create DynamoDB table
    results['dynamodb'] = await create_dynamodb_table()
    
    # Create S3 bucket (will be created on first upload)
    results['s3'] = True
    
    # Create CloudWatch dashboard
    results['cloudwatch_dashboard'] = await create_cloudwatch_dashboard(hackathon_id)
    
    return results

# Lambda function handler (for serverless deployment)
def lambda_handler(event, context):
    """AWS Lambda handler for processing feedback"""
    try:
        # Parse the event
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event
        
        feedback_data = body.get('feedback_data')
        if not feedback_data:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing feedback_data'})
            }
        
        # Store feedback
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success = loop.run_until_complete(store_feedback_dynamodb(feedback_data))
        
        if success:
            # Send metrics
            loop.run_until_complete(send_cloudwatch_metrics(
                "FeedbackSubmitted", 
                1, 
                {"HackathonId": feedback_data.get("hackathon_id", "unknown")}
            ))
            
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Feedback stored successfully'})
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to store feedback'})
            }
            
    except Exception as e:
        logger.error(f"Lambda handler error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

# Testing functions
async def test_aws_services():
    """Test AWS service connections"""
    print("Testing AWS services...")
    
    # Test DynamoDB
    try:
        success = await create_dynamodb_table()
        print(f"DynamoDB: {'✅' if success else '❌'}")
    except Exception as e:
        print(f"DynamoDB: ❌ ({e})")
    
    # Test S3
    try:
        s3 = get_s3_client()
        print(f"S3 Client: {'✅' if s3 else '❌'}")
    except Exception as e:
        print(f"S3 Client: ❌ ({e})")
    
    # Test CloudWatch
    try:
        cw = get_cloudwatch_client()
        print(f"CloudWatch Client: {'✅' if cw else '❌'}")
    except Exception as e:
        print(f"CloudWatch Client: ❌ ({e})")

if __name__ == "__main__":
    # Run tests
    asyncio.run(test_aws_services())