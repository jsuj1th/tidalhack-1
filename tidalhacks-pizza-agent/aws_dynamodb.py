# aws_dynamodb.py
"""
DynamoDB integration for Pizza Agent
Replaces local JSON storage with cloud-based DynamoDB
"""

import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import json
import hashlib
from aws_config import get_aws_services, DYNAMODB_TABLE_NAME, DYNAMODB_ANALYTICS_TABLE

class DynamoDBManager:
    """Manages DynamoDB operations for Pizza Agent"""
    
    def __init__(self):
        self.aws = get_aws_services()
        self.table_name = DYNAMODB_TABLE_NAME
        self.analytics_table_name = DYNAMODB_ANALYTICS_TABLE
        self.table = None
        self.analytics_table = None
        self._initialize_tables()
    
    def _initialize_tables(self):
        """Initialize DynamoDB tables"""
        try:
            # Main data table
            self.table = self.aws.dynamodb.Table(self.table_name)
            
            # Analytics table
            self.analytics_table = self.aws.dynamodb.Table(self.analytics_table_name)
            
            print(f"✅ Connected to DynamoDB tables: {self.table_name}, {self.analytics_table_name}")
            
        except Exception as e:
            print(f"❌ Error connecting to DynamoDB tables: {e}")
            raise
    
    def create_tables_if_not_exist(self):
        """Create DynamoDB tables if they don't exist"""
        try:
            # Create main data table
            self._create_main_table()
            
            # Create analytics table
            self._create_analytics_table()
            
        except Exception as e:
            print(f"Error creating tables: {e}")
            raise
    
    def _create_main_table(self):
        """Create main data table for user states and coupons"""
        try:
            self.aws.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {
                        'AttributeName': 'user_id',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'user_id',
                        'AttributeType': 'S'
                    }
                ],
                BillingMode='PAY_PER_REQUEST'  # On-demand pricing
            )
            
            # Wait for table to be created
            table = self.aws.dynamodb.Table(self.table_name)
            table.wait_until_exists()
            print(f"✅ Created main table: {self.table_name}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"✅ Table {self.table_name} already exists")
            else:
                raise
    
    def _create_analytics_table(self):
        """Create analytics table for tracking metrics"""
        try:
            self.aws.dynamodb.create_table(
                TableName=self.analytics_table_name,
                KeySchema=[
                    {
                        'AttributeName': 'event_id',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'event_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'timestamp',
                        'AttributeType': 'S'
                    }
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'timestamp-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'timestamp',
                                'KeyType': 'HASH'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            # Wait for table to be created
            table = self.aws.dynamodb.Table(self.analytics_table_name)
            table.wait_until_exists()
            print(f"✅ Created analytics table: {self.analytics_table_name}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"✅ Table {self.analytics_table_name} already exists")
            else:
                raise
    
    def get_user_hash(self, sender: str) -> str:
        """Generate consistent hash for user identification"""
        return hashlib.sha256(sender.encode()).hexdigest()[:16].upper()
    
    def get_user_state(self, sender: str) -> Optional[str]:
        """Get user state from DynamoDB"""
        try:
            user_id = self.get_user_hash(sender)
            response = self.table.get_item(Key={'user_id': user_id})
            
            if 'Item' in response:
                return response['Item'].get('state')
            return None
            
        except Exception as e:
            print(f"Error getting user state: {e}")
            return None
    
    def set_user_state(self, sender: str, state: str):
        """Set user state in DynamoDB"""
        try:
            user_id = self.get_user_hash(sender)
            
            self.table.update_item(
                Key={'user_id': user_id},
                UpdateExpression='SET #state = :state, updated_at = :timestamp',
                ExpressionAttributeNames={'#state': 'state'},
                ExpressionAttributeValues={
                    ':state': state,
                    ':timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            print(f"Error setting user state: {e}")
            raise
    
    def has_user_received_coupon(self, sender: str) -> bool:
        """Check if user has received a coupon"""
        try:
            user_id = self.get_user_hash(sender)
            response = self.table.get_item(Key={'user_id': user_id})
            
            if 'Item' in response:
                return response['Item'].get('coupon_issued', False)
            return False
            
        except Exception as e:
            print(f"Error checking coupon status: {e}")
            return False
    
    def mark_coupon_issued(self, sender: str, coupon_code: str, tier: str, rating: int, story: str = ""):
        """Mark that user has received a coupon"""
        try:
            user_id = self.get_user_hash(sender)
            
            self.table.update_item(
                Key={'user_id': user_id},
                UpdateExpression='''SET coupon_issued = :issued, 
                                   coupon_code = :code, 
                                   coupon_tier = :tier,
                                   story_rating = :rating,
                                   story_text = :story,
                                   coupon_issued_at = :timestamp,
                                   updated_at = :timestamp''',
                ExpressionAttributeValues={
                    ':issued': True,
                    ':code': coupon_code,
                    ':tier': tier,
                    ':rating': rating,
                    ':story': story,
                    ':timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            print(f"Error marking coupon issued: {e}")
            raise
    
    def get_user_coupon(self, sender: str) -> Optional[str]:
        """Get user's existing coupon code"""
        try:
            user_id = self.get_user_hash(sender)
            response = self.table.get_item(Key={'user_id': user_id})
            
            if 'Item' in response:
                return response['Item'].get('coupon_code')
            return None
            
        except Exception as e:
            print(f"Error getting user coupon: {e}")
            return None
    
    def record_analytics_event(self, event_type: str, user_id: str, data: Dict[str, Any]):
        """Record analytics event"""
        try:
            event_id = f"{event_type}_{user_id}_{datetime.now().timestamp()}"
            
            self.analytics_table.put_item(
                Item={
                    'event_id': event_id,
                    'event_type': event_type,
                    'user_id': user_id,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'data': json.dumps(data, default=str)
                }
            )
            
        except Exception as e:
            print(f"Error recording analytics: {e}")
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary"""
        try:
            # Scan analytics table (in production, use better querying)
            response = self.analytics_table.scan()
            items = response.get('Items', [])
            
            # Basic analytics
            total_requests = len([item for item in items if item['event_type'] == 'request'])
            total_coupons = len([item for item in items if item['event_type'] == 'coupon_issued'])
            
            # Tier distribution
            tier_counts = {}
            for item in items:
                if item['event_type'] == 'coupon_issued':
                    data = json.loads(item.get('data', '{}'))
                    tier = data.get('tier', 'unknown')
                    tier_counts[tier] = tier_counts.get(tier, 0) + 1
            
            return {
                'total_requests': total_requests,
                'total_coupons_issued': total_coupons,
                'tier_distribution': tier_counts,
                'conversion_rate': (total_coupons / total_requests * 100) if total_requests > 0 else 0
            }
            
        except Exception as e:
            print(f"Error getting analytics: {e}")
            return {}
    
    def cleanup_old_data(self, days_old: int = 30):
        """Clean up old data (optional maintenance)"""
        try:
            cutoff_date = datetime.now(timezone.utc).timestamp() - (days_old * 24 * 60 * 60)
            
            # This is a simplified cleanup - in production, use better date filtering
            response = self.analytics_table.scan()
            items = response.get('Items', [])
            
            deleted_count = 0
            for item in items:
                item_timestamp = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00')).timestamp()
                if item_timestamp < cutoff_date:
                    self.analytics_table.delete_item(Key={'event_id': item['event_id']})
                    deleted_count += 1
            
            print(f"✅ Cleaned up {deleted_count} old analytics records")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")

# Global DynamoDB manager instance
dynamodb_manager = None

def get_dynamodb_manager() -> DynamoDBManager:
    """Get or create DynamoDB manager instance"""
    global dynamodb_manager
    if dynamodb_manager is None:
        dynamodb_manager = DynamoDBManager()
    return dynamodb_manager

if __name__ == "__main__":
    print("🚀 Testing DynamoDB integration...")
    
    try:
        db = get_dynamodb_manager()
        
        # Create tables if needed
        db.create_tables_if_not_exist()
        
        # Test basic operations
        test_user = "test_user_123"
        
        # Test state management
        db.set_user_state(test_user, "waiting_for_story")
        state = db.get_user_state(test_user)
        print(f"✅ State test: {state}")
        
        # Test coupon management
        db.mark_coupon_issued(test_user, "TEST-COUPON-123", "PREMIUM", 9, "Test story")
        has_coupon = db.has_user_received_coupon(test_user)
        coupon_code = db.get_user_coupon(test_user)
        print(f"✅ Coupon test: has_coupon={has_coupon}, code={coupon_code}")
        
        # Test analytics
        db.record_analytics_event("test_event", test_user, {"test": "data"})
        analytics = db.get_analytics_summary()
        print(f"✅ Analytics test: {analytics}")
        
        print("\n✅ DynamoDB integration working correctly!")
        
    except Exception as e:
        print(f"❌ DynamoDB test failed: {e}")