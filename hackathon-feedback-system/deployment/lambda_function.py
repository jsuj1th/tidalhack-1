# lambda_function.py
"""
AWS Lambda function for serverless hackathon feedback processing
This function handles feedback storage and processing in a serverless environment
"""

import json
import boto3
import logging
from datetime import datetime
from typing import Dict, Any
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.client('dynamodb')
s3 = boto3.client('s3')
cloudwatch = boto3.client('cloudwatch')

# Environment variables
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE_NAME', 'hackathon-feedback')
S3_BUCKET = os.environ.get('S3_BUCKET_NAME', 'hackathon-feedback-data')
CLOUDWATCH_NAMESPACE = os.environ.get('CLOUDWATCH_NAMESPACE', 'HackathonFeedback')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for processing hackathon feedback
    
    Expected event structure:
    {
        "action": "store_feedback" | "get_feedback" | "get_analytics",
        "data": {...}
    }
    """
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Parse the event
        if 'body' in event:
            # API Gateway event
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            # Direct invocation
            body = event
        
        action = body.get('action')
        data = body.get('data', {})
        
        # Route to appropriate handler
        if action == 'store_feedback':
            return handle_store_feedback(data)
        elif action == 'get_feedback':
            return handle_get_feedback(data)
        elif action == 'get_analytics':
            return handle_get_analytics(data)
        else:
            return create_response(400, {'error': f'Unknown action: {action}'})
            
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def handle_store_feedback(data: Dict) -> Dict[str, Any]:
    """Handle feedback storage"""
    try:
        feedback_data = data.get('feedback_data')
        if not feedback_data:
            return create_response(400, {'error': 'Missing feedback_data'})
        
        # Validate required fields
        required_fields = ['feedback_id', 'user_hash', 'hackathon_id', 'feedback_text', 'timestamp']
        for field in required_fields:
            if field not in feedback_data:
                return create_response(400, {'error': f'Missing required field: {field}'})
        
        # Store in DynamoDB
        store_in_dynamodb(feedback_data)
        
        # Backup to S3
        backup_to_s3(feedback_data)
        
        # Send CloudWatch metrics
        send_metrics(feedback_data)
        
        logger.info(f"Successfully processed feedback {feedback_data['feedback_id']}")
        
        return create_response(200, {
            'message': 'Feedback stored successfully',
            'feedback_id': feedback_data['feedback_id']
        })
        
    except Exception as e:
        logger.error(f"Error storing feedback: {str(e)}")
        return create_response(500, {'error': 'Failed to store feedback'})

def handle_get_feedback(data: Dict) -> Dict[str, Any]:
    """Handle feedback retrieval"""
    try:
        hackathon_id = data.get('hackathon_id')
        limit = data.get('limit', 100)
        
        if not hackathon_id:
            return create_response(400, {'error': 'Missing hackathon_id'})
        
        # Query DynamoDB
        response = dynamodb.query(
            TableName=DYNAMODB_TABLE,
            IndexName='hackathon-timestamp-index',
            KeyConditionExpression='hackathon_id = :hid',
            ExpressionAttributeValues={
                ':hid': {'S': hackathon_id}
            },
            ScanIndexForward=False,
            Limit=limit
        )
        
        # Convert DynamoDB format to regular dict
        feedback_list = []
        for item in response.get('Items', []):
            feedback = convert_dynamodb_item(item)
            feedback_list.append(feedback)
        
        return create_response(200, {
            'feedback': feedback_list,
            'count': len(feedback_list)
        })
        
    except Exception as e:
        logger.error(f"Error retrieving feedback: {str(e)}")
        return create_response(500, {'error': 'Failed to retrieve feedback'})

def handle_get_analytics(data: Dict) -> Dict[str, Any]:
    """Handle analytics generation"""
    try:
        hackathon_id = data.get('hackathon_id')
        
        if not hackathon_id:
            return create_response(400, {'error': 'Missing hackathon_id'})
        
        # Get feedback data
        feedback_response = handle_get_feedback({'hackathon_id': hackathon_id, 'limit': 1000})
        
        if feedback_response['statusCode'] != 200:
            return feedback_response
        
        feedback_list = json.loads(feedback_response['body'])['feedback']
        
        # Generate analytics
        analytics = generate_analytics(feedback_list)
        
        return create_response(200, analytics)
        
    except Exception as e:
        logger.error(f"Error generating analytics: {str(e)}")
        return create_response(500, {'error': 'Failed to generate analytics'})

def store_in_dynamodb(feedback_data: Dict) -> None:
    """Store feedback in DynamoDB"""
    try:
        # Convert to DynamoDB format
        item = {
            'feedback_id': {'S': feedback_data['feedback_id']},
            'user_hash': {'S': feedback_data['user_hash']},
            'hackathon_id': {'S': feedback_data['hackathon_id']},
            'feedback_text': {'S': feedback_data['feedback_text']},
            'timestamp': {'S': feedback_data['timestamp']},
            'analysis': {'S': json.dumps(feedback_data.get('analysis', {}))},
            'metadata': {'S': json.dumps(feedback_data.get('metadata', {}))}
        }
        
        if feedback_data.get('user_email'):
            item['user_email'] = {'S': feedback_data['user_email']}
        
        # Store in DynamoDB
        dynamodb.put_item(
            TableName=DYNAMODB_TABLE,
            Item=item
        )
        
        logger.info(f"Stored feedback {feedback_data['feedback_id']} in DynamoDB")
        
    except Exception as e:
        logger.error(f"DynamoDB storage failed: {str(e)}")
        raise

def backup_to_s3(feedback_data: Dict) -> None:
    """Backup feedback to S3"""
    try:
        timestamp = datetime.now()
        s3_key = f"feedback-backups/{timestamp.strftime('%Y/%m/%d')}/{feedback_data['feedback_id']}.json"
        
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=json.dumps(feedback_data, indent=2, default=str),
            ContentType='application/json'
        )
        
        logger.info(f"Backed up feedback {feedback_data['feedback_id']} to S3")
        
    except Exception as e:
        logger.error(f"S3 backup failed: {str(e)}")
        # Don't raise - backup failure shouldn't fail the main operation

def send_metrics(feedback_data: Dict) -> None:
    """Send metrics to CloudWatch"""
    try:
        analysis = feedback_data.get('analysis', {})
        
        # Basic submission metric
        cloudwatch.put_metric_data(
            Namespace=CLOUDWATCH_NAMESPACE,
            MetricData=[
                {
                    'MetricName': 'FeedbackSubmitted',
                    'Value': 1,
                    'Unit': 'Count',
                    'Timestamp': datetime.now(),
                    'Dimensions': [
                        {'Name': 'HackathonId', 'Value': feedback_data['hackathon_id']}
                    ]
                }
            ]
        )
        
        # Sentiment metric
        if 'sentiment' in analysis:
            cloudwatch.put_metric_data(
                Namespace=CLOUDWATCH_NAMESPACE,
                MetricData=[
                    {
                        'MetricName': 'FeedbackBySentiment',
                        'Value': 1,
                        'Unit': 'Count',
                        'Timestamp': datetime.now(),
                        'Dimensions': [
                            {'Name': 'HackathonId', 'Value': feedback_data['hackathon_id']},
                            {'Name': 'Sentiment', 'Value': analysis['sentiment']}
                        ]
                    }
                ]
            )
        
        # Category metric
        if 'category' in analysis:
            cloudwatch.put_metric_data(
                Namespace=CLOUDWATCH_NAMESPACE,
                MetricData=[
                    {
                        'MetricName': 'FeedbackByCategory',
                        'Value': 1,
                        'Unit': 'Count',
                        'Timestamp': datetime.now(),
                        'Dimensions': [
                            {'Name': 'HackathonId', 'Value': feedback_data['hackathon_id']},
                            {'Name': 'Category', 'Value': analysis['category']}
                        ]
                    }
                ]
            )
        
        logger.info("Sent CloudWatch metrics")
        
    except Exception as e:
        logger.error(f"CloudWatch metrics failed: {str(e)}")
        # Don't raise - metrics failure shouldn't fail the main operation

def convert_dynamodb_item(item: Dict) -> Dict:
    """Convert DynamoDB item format to regular dict"""
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
    
    return feedback

def generate_analytics(feedback_list: list) -> Dict:
    """Generate analytics from feedback data"""
    if not feedback_list:
        return {
            'total_feedback': 0,
            'sentiment_distribution': {},
            'category_distribution': {},
            'analytics_generated': datetime.now().isoformat()
        }
    
    # Sentiment distribution
    sentiments = [f.get('analysis', {}).get('sentiment', 'neutral') for f in feedback_list]
    sentiment_dist = {
        'positive': sentiments.count('positive'),
        'negative': sentiments.count('negative'),
        'neutral': sentiments.count('neutral')
    }
    
    # Category distribution
    categories = [f.get('analysis', {}).get('category', 'GENERAL') for f in feedback_list]
    category_dist = {}
    for category in categories:
        category_dist[category] = category_dist.get(category, 0) + 1
    
    # Time-based analysis
    from collections import defaultdict
    hourly_submissions = defaultdict(int)
    
    for feedback in feedback_list:
        try:
            timestamp = datetime.fromisoformat(feedback['timestamp'].replace('Z', '+00:00'))
            hour = timestamp.hour
            hourly_submissions[hour] += 1
        except:
            continue
    
    # Average feedback length
    lengths = [len(f['feedback_text']) for f in feedback_list]
    avg_length = sum(lengths) / len(lengths) if lengths else 0
    
    return {
        'total_feedback': len(feedback_list),
        'sentiment_distribution': sentiment_dist,
        'category_distribution': category_dist,
        'hourly_distribution': dict(hourly_submissions),
        'average_feedback_length': round(avg_length, 2),
        'analytics_generated': datetime.now().isoformat()
    }

def create_response(status_code: int, body: Dict) -> Dict[str, Any]:
    """Create standardized API response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(body, default=str)
    }