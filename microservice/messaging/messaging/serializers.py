from rest_framework import serializers
from .models import Message, Conversation
import logging
from django.db import connections
from django.db.models import Q
import requests

logger = logging.getLogger(__name__)

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    recipient_name = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'sender_type', 'sender_id', 'recipient_type', 'recipient_id', 
                 'content', 'is_read', 'created_at', 'created_at_formatted', 
                 'sender_name', 'recipient_name']
        read_only_fields = ['id', 'created_at', 'sender_name', 'recipient_name', 'created_at_formatted']
    
    def get_sender_name(self, obj):
        return self._get_user_name(obj.sender_type, obj.sender_id)
    
    def get_recipient_name(self, obj):
        return self._get_user_name(obj.recipient_type, obj.recipient_id)
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    
    def _get_user_name(self, user_type, user_id):
        # First check if this is the current authenticated user
        request = self.context.get('request')
        if request and hasattr(request, 'username') and hasattr(request, 'user_id'):
            if int(request.user_id) == int(user_id) and request.user_type == user_type:
                return request.username

        endpoint_map = {
            'administrator': 'administrators',
            'teacher': 'teachers',
            'student': 'students',
            'parent': 'parents'
        }
        
        endpoint = endpoint_map.get(user_type)
        if not endpoint:
            logger.warning(f"Unknown user type: {user_type}")
            return f"{user_type.title()} #{user_id}"

        # Use HTTPS for both internal and external requests
        service_urls = [
            f"https://users_service:8000/api/{endpoint}/{user_id}/",     # Docker internal HTTPS
            f"https://localhost:8001/api/{endpoint}/{user_id}/",        # External HTTPS
        ]
        
        for url in service_urls:
            try:
                logger.info(f"Requesting user info from: {url}")
                
                response = requests.get(
                    url, 
                    timeout=3, 
                    verify=False  # For development with self-signed certificates
                )
                
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    user_data = response.json()
                    username = user_data.get('username')
                    if username:
                        logger.info(f"Successfully got username: {username} for {user_type}:{user_id}")
                        return username
                    
            except Exception as e:
                logger.warning(f"Request failed for {url}: {str(e)}")
                continue

        # Fallback to formatted display
        logger.warning(f"All requests failed for {user_type}:{user_id}, using fallback")
        type_display = {
            'administrator': 'Admin',
            'teacher': 'Teacher',
            'student': 'Student',
            'parent': 'Parent'
        }
        display_type = type_display.get(user_type, user_type.title())
        return f"{display_type} #{user_id}"

class ConversationSerializer(serializers.ModelSerializer):
    participant1_name = serializers.SerializerMethodField()
    participant2_name = serializers.SerializerMethodField()
    last_message_content = serializers.SerializerMethodField()
    last_message_time = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'participant1_type', 'participant1_id', 'participant2_type', 'participant2_id',
                 'participant1_name', 'participant2_name', 'last_message_content', 'last_message_time',
                 'updated_at', 'unread_count']
        read_only_fields = ['id', 'updated_at']
    
    def get_participant1_name(self, obj):
        return self._get_user_name(obj.participant1_type, obj.participant1_id)
    
    def get_participant2_name(self, obj):
        return self._get_user_name(obj.participant2_type, obj.participant2_id)
    
    def get_last_message_content(self, obj):
        if obj.last_message:
            return obj.last_message.content
        return ""
    
    def get_last_message_time(self, obj):
        if obj.last_message:
            return obj.last_message.created_at.strftime('%Y-%m-%d %H:%M:%S')
        return ""
    
    def get_unread_count(self, obj):
        # Get the current user from the request context
        request = self.context.get('request')
        if not request or not hasattr(request, 'user_type') or not hasattr(request, 'user_id'):
            return 0
        
        user_type = request.user_type
        user_id = int(request.user_id)
        
        # Count unread messages where the current user is the recipient
       
        return Message.objects.filter(
            # Message is between these two participants
            (
                # Sender is participant1, recipient is participant2
                Q(sender_type=obj.participant1_type, sender_id=obj.participant1_id,
                  recipient_type=obj.participant2_type, recipient_id=obj.participant2_id) |
                # Sender is participant2, recipient is participant1  
                Q(sender_type=obj.participant2_type, sender_id=obj.participant2_id,
                  recipient_type=obj.participant1_type, recipient_id=obj.participant1_id)
            ),
            # Current user is the recipient
            recipient_type=user_type,
            recipient_id=user_id,
            is_read=False
        ).count()
    
    def _get_user_name(self, user_type, user_id):
        # Use the same method as MessageSerializer
        return MessageSerializer(context=self.context)._get_user_name(user_type, user_id)