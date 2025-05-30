"""
Database models for Telegram messages and URLs.
Defines data structures for MongoDB collections.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Annotated
from pydantic import BaseModel, Field, BeforeValidator
from bson import ObjectId


def validate_object_id(v):
    """Validate ObjectId"""
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


# Custom ObjectId type for Pydantic v2
PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class UrlData(BaseModel):
    """URL information extracted from message"""
    url: str = Field(..., description="Extracted URL")
    url_type: str = Field(default="unknown", description="Type of URL (http, domain, media)")
    is_valid: bool = Field(default=True, description="Whether URL is valid")
    domain: Optional[str] = Field(default=None, description="Extracted domain name")
    redirect_url: Optional[str] = Field(default=None, description="Final redirect URL")
    status_code: Optional[int] = Field(default=None, description="HTTP status code")
    processed_at: Optional[datetime] = Field(default=None, description="When URL was processed")


class TelegramChannel(BaseModel):
    """Telegram channel information"""
    channel_id: int = Field(..., description="Telegram channel ID")
    channel_name: str = Field(..., description="Channel display name")
    username: Optional[str] = Field(default=None, description="Channel username")
    participants_count: int = Field(default=0, description="Number of participants")
    access_hash: Optional[int] = Field(default=None, description="Channel access hash")


class TelegramMessage(BaseModel):
    """Simplified Telegram message model with essential data only"""
    
    # MongoDB document ID
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # Essential message data
    message_id: int = Field(..., description="Telegram message ID")
    channel_name: str = Field(..., description="Channel display name")
    channel_id: int = Field(..., description="Telegram channel ID")
    
    # URLs (simplified)
    urls: List[str] = Field(default_factory=list, description="List of URLs found in message")
    url_count: int = Field(default=0, description="Total number of URLs extracted")
    
    # Timestamps
    telegram_date: datetime = Field(..., description="Original Telegram message timestamp")
    received_at: datetime = Field(default_factory=datetime.utcnow, description="When message was received")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="When message was processed")
    
    # Processing info
    processing_status: str = Field(default="processed", description="Processing status")
    processor_version: str = Field(default="1.0", description="Processor version used")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class MessageStats(BaseModel):
    """Statistics model for message processing"""
    
    # Time period
    date: datetime = Field(default_factory=datetime.utcnow, description="Statistics date")
    
    # Channel statistics
    total_channels: int = Field(default=0, description="Total channels monitored")
    active_channels: int = Field(default=0, description="Channels with messages")
    
    # Message statistics
    total_messages: int = Field(default=0, description="Total messages received")
    messages_with_urls: int = Field(default=0, description="Messages containing URLs")
    total_urls: int = Field(default=0, description="Total URLs extracted")
    
    # Processing statistics
    successfully_processed: int = Field(default=0, description="Successfully processed messages")
    processing_errors: int = Field(default=0, description="Messages with processing errors")
    
    # URL statistics
    valid_urls: int = Field(default=0, description="Valid URLs found")
    invalid_urls: int = Field(default=0, description="Invalid URLs found")
    unique_domains: int = Field(default=0, description="Unique domains discovered")


class UrlProcessingQueue(BaseModel):
    """Queue model for URL processing tasks"""
    
    # MongoDB document ID
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # URL information
    url: str = Field(..., description="URL to process")
    source_message_id: PyObjectId = Field(..., description="Reference to source message")
    
    # Processing status
    status: str = Field(default="pending", description="Processing status")
    priority: int = Field(default=1, description="Processing priority")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When queued")
    scheduled_at: datetime = Field(default_factory=datetime.utcnow, description="When to process")
    processed_at: Optional[datetime] = Field(default=None, description="When processed")
    
    # Processing attempts
    attempt_count: int = Field(default=0, description="Number of processing attempts")
    max_attempts: int = Field(default=3, description="Maximum processing attempts")
    
    # Results
    processing_result: Optional[Dict[str, Any]] = Field(default=None, description="Processing results")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}