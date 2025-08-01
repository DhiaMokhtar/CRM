from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from django.db import transaction
from django.shortcuts import get_object_or_404
import logging
import requests

from .models import Message, Conversation
from .serializers import MessageSerializer, ConversationSerializer

logger = logging.getLogger(__name__)

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        # Filter messages based on the authenticated user
        if not hasattr(self.request, 'user_type') or not hasattr(self.request, 'user_id'):
            return Message.objects.none()
        
        user_type = self.request.user_type
        user_id = self.request.user_id
        
        # Return messages where the user is either sender or recipient
        return Message.objects.filter(
            Q(sender_type=user_type, sender_id=user_id) | 
            Q(recipient_type=user_type, recipient_id=user_id)
        )
    
    def create(self, request, *args, **kwargs):
        # Check if user is authenticated
        if not hasattr(request, 'user_type') or not hasattr(request, 'user_id'):
            logger.error("Authentication required - no user info in request")
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Log the user info for debugging
        logger.info(f"Creating message from authenticated user: {request.username} (ID: {request.user_id}, Type: {request.user_type})")
        
        # Prepare data with sender information
        data = request.data.copy()
        data['sender_type'] = request.user_type
        data['sender_id'] = int(request.user_id)  # Ensure it's an integer
        
        # Also ensure recipient_id is an integer
        try:
            data['recipient_id'] = int(data.get('recipient_id', 0))
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid recipient_id: {data.get('recipient_id')} - {str(e)}")
            return Response({"error": "Invalid recipient ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Log the complete data being sent to serializer
        logger.info(f"Message data before serializer: {data}")
        
        serializer = self.get_serializer(data=data)
        
        # Log serializer validation
        logger.info(f"Serializer is_valid check...")
        if not serializer.is_valid():
            logger.error(f"Serializer validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Log validated data
        logger.info(f"Serializer validated_data: {serializer.validated_data}")
        
        with transaction.atomic():
            try:
                message = serializer.save()
                logger.info(f"Message created successfully with ID: {message.id}, sender_id: {message.sender_id}")
                self._update_conversation(message)
            except Exception as e:
                logger.error(f"Error saving message: {str(e)}")
                raise
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def _update_conversation(self, message):
        # Find or create a conversation between these two users
        conversation = Conversation.objects.filter(
            (
                Q(participant1_type=message.sender_type, participant1_id=message.sender_id) &
                Q(participant2_type=message.recipient_type, participant2_id=message.recipient_id)
            ) | 
            (
                Q(participant1_type=message.recipient_type, participant1_id=message.recipient_id) &
                Q(participant2_type=message.sender_type, participant2_id=message.sender_id)
            )
        ).first()
        
        if not conversation:
            # Create new conversation with consistent participant ordering
            type_hierarchy = {
                'administrator': 1,
                'teacher': 2, 
                'parent': 3,
                'student': 4
            }
            
            sender_priority = type_hierarchy.get(message.sender_type, 5)
            recipient_priority = type_hierarchy.get(message.recipient_type, 5)
            
            if sender_priority < recipient_priority or \
               (sender_priority == recipient_priority and message.sender_id < message.recipient_id):
                participant1_type = message.sender_type
                participant1_id = message.sender_id
                participant2_type = message.recipient_type
                participant2_id = message.recipient_id
            else:
                participant1_type = message.recipient_type
                participant1_id = message.recipient_id
                participant2_type = message.sender_type
                participant2_id = message.sender_id
            
            conversation = Conversation.objects.create(
                participant1_type=participant1_type,
                participant1_id=participant1_id,
                participant2_type=participant2_type,
                participant2_id=participant2_id,
                last_message=message
            )
        else:
            # Update existing conversation
            conversation.last_message = message
            conversation.save()
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        message = self.get_object()
        
        # Only the recipient can mark a message as read
        if not hasattr(request, 'user_type') or not hasattr(request, 'user_id') or \
           request.user_type != message.recipient_type or int(request.user_id) != message.recipient_id:
            return Response({"error": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
        
        message.is_read = True
        message.save()
        
        return Response({"status": "Message marked as read"}, status=status.HTTP_200_OK)

class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        # Filter conversations based on the authenticated user
        if not hasattr(self.request, 'user_type') or not hasattr(self.request, 'user_id'):
            return Conversation.objects.none()
        
        user_type = self.request.user_type
        user_id = self.request.user_id
        
        # Return conversations where the user is either participant1 or participant2
        return Conversation.objects.filter(
            Q(participant1_type=user_type, participant1_id=user_id) | 
            Q(participant2_type=user_type, participant2_id=user_id)
        )
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        
        # Verify the user is part of this conversation
        if not hasattr(request, 'user_type') or not hasattr(request, 'user_id') or \
           not ((request.user_type == conversation.participant1_type and int(request.user_id) == conversation.participant1_id) or \
                (request.user_type == conversation.participant2_type and int(request.user_id) == conversation.participant2_id)):
            return Response({"error": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
        
        # Get all messages for this conversation
        messages = Message.objects.filter(
            (
                Q(sender_type=conversation.participant1_type, sender_id=conversation.participant1_id,
                  recipient_type=conversation.participant2_type, recipient_id=conversation.participant2_id) |
                Q(sender_type=conversation.participant2_type, sender_id=conversation.participant2_id,
                  recipient_type=conversation.participant1_type, recipient_id=conversation.participant1_id)
            )
        ).order_by('created_at')
        
        # Mark messages as read if the current user is the recipient
        for message in messages:
            if message.recipient_type == request.user_type and int(message.recipient_id) == int(request.user_id) and not message.is_read:
                message.is_read = True
                message.save()
        
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)

class UserSearchView(APIView):
    def get(self, request):
        query = request.query_params.get('q', '')
        user_type = request.query_params.get('type', None)
        
        if not query or len(query.strip()) < 2:
            return Response([])
        
        # Forward the search request to users microservice
        try:
            # Try different service URLs
            service_urls = [
                f"http://users_service:8000/api/search/users/?q={query}",  # Docker internal
                f"https://localhost:8001/api/search/users/?q={query}",      # External
                f"http://localhost:8001/api/search/users/?q={query}",       # HTTP fallback
            ]
            
            if user_type:
                service_urls = [url + f"&type={user_type}" for url in service_urls]
            
            for url in service_urls:
                try:
                    print(f"Trying URL: {url}")  # Debug log
                    response = requests.get(url, timeout=10, verify=False)
                    print(f"Response status: {response.status_code}")  # Debug log
                    
                    if response.status_code == 200:
                        users_data = response.json()
                        print(f"Users data received: {users_data}")  # Debug log
                        
                        # Format the response to include proper name fields
                        formatted_users = []
                        for user in users_data:
                            formatted_user = {
                                'id': user.get('id'),
                                'username': user.get('username'),
                                'name': user.get('name') or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user.get('username'),
                                'full_name': f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                                'type': user.get('type'),
                                'class_name': user.get('class_name'),
                                'email': user.get('email')
                            }
                            formatted_users.append(formatted_user)
                        
                        print(f"Formatted users: {formatted_users}")  # Debug log
                        return Response(formatted_users)
                        
                except Exception as e:
                    print(f"Request failed for {url}: {str(e)}")  # Debug log
                    continue
            
            # If all requests fail, return empty list
            print("All service URLs failed")  # Debug log
            return Response([])
            
        except Exception as e:
            logger.error(f"Error in user search: {str(e)}")
            print(f"Error in user search: {str(e)}")  # Debug log
            return Response([])

class HealthCheckView(APIView):
    """
    Simple health check endpoint
    """
    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'messaging'
        })
