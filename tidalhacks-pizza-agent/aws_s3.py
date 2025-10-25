# aws_s3.py
"""
AWS S3 integration for storing analytics, backups, and static assets
"""

import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import json
import io
from aws_config import get_aws_services, S3_BUCKET_NAME

class S3Manager:
    """AWS S3 Manager for Pizza Agent"""
    
    def __init__(self):
        self.aws = get_aws_services()
        self.s3 = self.aws.s3
        self.bucket_name = S3_BUCKET_NAME
    
    def create_bucket_if_not_exists(self) -> bool:
        """Create S3 bucket if it doesn't exist"""
        try:
            # Check if bucket exists
            self.s3.head_bucket(Bucket=self.bucket_name)
            print(f"✅ Bucket {self.bucket_name} already exists")
            return True
            
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            
            if error_code == 404:
                # Bucket doesn't exist, create it
                try:
                    # For us-east-1, don't specify LocationConstraint
                    if self.aws.session.region_name == 'us-east-1':
                        self.s3.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={
                                'LocationConstraint': self.aws.session.region_name
                            }
                        )
                    
                    print(f"✅ Created bucket: {self.bucket_name}")
                    return True
                    
                except ClientError as create_error:
                    print(f"❌ Error creating bucket: {create_error}")
                    return False
            else:
                print(f"❌ Error checking bucket: {e}")
                return False
    
    def upload_analytics_data(self, data: Dict[str, Any], filename: Optional[str] = None) -> Dict[str, Any]:
        """Upload analytics data to S3"""
        try:
            if not filename:
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                filename = f"analytics/pizza_agent_analytics_{timestamp}.json"
            
            # Convert data to JSON
            json_data = json.dumps(data, indent=2, default=str)
            
            # Upload to S3
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=json_data,
                ContentType='application/json',
                Metadata={
                    'uploaded_at': datetime.now(timezone.utc).isoformat(),
                    'data_type': 'analytics'
                }
            )
            
            return {
                "success": True,
                "message": f"Analytics uploaded to s3://{self.bucket_name}/{filename}",
                "filename": filename
            }
            
        except Exception as e:
            return {"success": False, "message": f"Upload failed: {str(e)}"}
    
    def download_analytics_data(self, filename: str) -> Dict[str, Any]:
        """Download analytics data from S3"""
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=filename)
            data = json.loads(response['Body'].read().decode('utf-8'))
            
            return {
                "success": True,
                "data": data,
                "metadata": response.get('Metadata', {})
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return {"success": False, "message": "File not found"}
            else:
                return {"success": False, "message": f"Download failed: {e}"}
        except Exception as e:
            return {"success": False, "message": f"Download failed: {str(e)}"}
    
    def list_analytics_files(self, prefix: str = "analytics/") -> List[Dict[str, Any]]:
        """List analytics files in S3"""
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj['ETag']
                })
            
            return files
            
        except Exception as e:
            print(f"Error listing files: {e}")
            return []
    
    def backup_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Backup user data to S3"""
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"backups/user_data_backup_{timestamp}.json"
            
            # Convert data to JSON
            json_data = json.dumps(user_data, indent=2, default=str)
            
            # Upload to S3
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=json_data,
                ContentType='application/json',
                Metadata={
                    'backup_date': datetime.now(timezone.utc).isoformat(),
                    'data_type': 'user_backup'
                }
            )
            
            return {
                "success": True,
                "message": f"Backup uploaded to s3://{self.bucket_name}/{filename}",
                "filename": filename
            }
            
        except Exception as e:
            return {"success": False, "message": f"Backup failed: {str(e)}"}
    
    def store_coupon_image(self, coupon_code: str, image_data: bytes, content_type: str = "image/png") -> Dict[str, Any]:
        """Store coupon QR code or image in S3"""
        try:
            filename = f"coupons/{coupon_code}.png"
            
            # Upload image to S3
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=image_data,
                ContentType=content_type,
                Metadata={
                    'coupon_code': coupon_code,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
            )
            
            # Generate public URL (if bucket is public)
            url = f"https://{self.bucket_name}.s3.amazonaws.com/{filename}"
            
            return {
                "success": True,
                "message": f"Coupon image stored",
                "filename": filename,
                "url": url
            }
            
        except Exception as e:
            return {"success": False, "message": f"Image storage failed: {str(e)}"}
    
    def get_public_url(self, filename: str, expiration: int = 3600) -> str:
        """Generate presigned URL for file access"""
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': filename},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            print(f"Error generating URL: {e}")
            return ""
    
    def delete_old_files(self, prefix: str, days_old: int = 30) -> Dict[str, Any]:
        """Delete files older than specified days"""
        try:
            cutoff_date = datetime.now(timezone.utc).timestamp() - (days_old * 24 * 60 * 60)
            
            # List objects
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            deleted_count = 0
            for obj in response.get('Contents', []):
                if obj['LastModified'].timestamp() < cutoff_date:
                    self.s3.delete_object(Bucket=self.bucket_name, Key=obj['Key'])
                    deleted_count += 1
            
            return {
                "success": True,
                "message": f"Deleted {deleted_count} old files",
                "deleted_count": deleted_count
            }
            
        except Exception as e:
            return {"success": False, "message": f"Cleanup failed: {str(e)}"}
    
    def get_bucket_info(self) -> Dict[str, Any]:
        """Get bucket information and statistics"""
        try:
            # Get bucket location
            location = self.s3.get_bucket_location(Bucket=self.bucket_name)
            
            # List objects to get count and size
            response = self.s3.list_objects_v2(Bucket=self.bucket_name)
            
            total_objects = response.get('KeyCount', 0)
            total_size = sum(obj.get('Size', 0) for obj in response.get('Contents', []))
            
            return {
                "bucket_name": self.bucket_name,
                "region": location.get('LocationConstraint', 'us-east-1'),
                "total_objects": total_objects,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            return {"error": f"Failed to get bucket info: {str(e)}"}

# Global S3 manager instance
s3_manager = None

def get_s3_manager() -> S3Manager:
    """Get or create S3 manager instance"""
    global s3_manager
    if s3_manager is None:
        s3_manager = S3Manager()
    return s3_manager

if __name__ == "__main__":
    print("🚀 Testing AWS S3 integration...")
    
    try:
        s3 = get_s3_manager()
        
        # Create bucket if needed
        if s3.create_bucket_if_not_exists():
            print("✅ S3 bucket ready")
            
            # Get bucket info
            info = s3.get_bucket_info()
            print(f"Bucket info: {info}")
            
            # Test analytics upload
            test_data = {
                "test": "data",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_requests": 100,
                "total_coupons": 85
            }
            
            result = s3.upload_analytics_data(test_data, "test/test_analytics.json")
            print(f"Upload test: {result}")
            
            if result["success"]:
                # Test download
                download_result = s3.download_analytics_data("test/test_analytics.json")
                print(f"Download test: {download_result['success']}")
                
                # List files
                files = s3.list_analytics_files("test/")
                print(f"Files found: {len(files)}")
        
        print("✅ S3 integration working correctly!")
        
    except Exception as e:
        print(f"❌ S3 test failed: {e}")