from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Message, Conversation, Administrator, Teacher, Student, Parent
from .serializers import MessageSerializer, ConversationSerializer

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    
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
        # Add sender information from the authenticated user
        if not hasattr(request, 'user_type') or not hasattr(request, 'user_id'):
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        data = request.data.copy()
        data['sender_type'] = request.user_type
        data['sender_id'] = request.user_id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Update or create conversation
        self._update_conversation(serializer.instance)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def _update_conversation(self, message):
        # Find or create a conversation between these two users
        conversation = None
        
        # Try to find existing conversation
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
        
        # Create new conversation if it doesn't exist
        if not conversation:
            # Define user type hierarchy: admin > teacher > parent > student
            type_hierarchy = {
                'administrator': 1,
                'teacher': 2, 
                'parent': 3,
                'student': 4
            }
            
            sender_priority = type_hierarchy.get(message.sender_type, 5)
            recipient_priority = type_hierarchy.get(message.recipient_type, 5)
            
            # Always put higher priority user as participant1
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
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Add user info to context for unread count calculation
        if hasattr(self.request, 'user_type') and hasattr(self.request, 'user_id'):
            context['user_type'] = self.request.user_type
            context['user_id'] = self.request.user_id
        return context
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        
        # Verify the user is part of this conversation
        if not hasattr(request, 'user_type') or not hasattr(request, 'user_id') or \
           not (request.user_type == conversation.participant1_type and int(request.user_id) == conversation.participant1_id or \
                request.user_type == conversation.participant2_type and int(request.user_id) == conversation.participant2_id):
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
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

class UserSearchView(APIView):
    def get(self, request):
        query = request.query_params.get('q', '')
        user_type = request.query_params.get('type', None)
        
        results = []
        
        # Search administrators
        if not user_type or user_type == 'admin':
            admins = Administrator.objects.filter(username__icontains=query)[:10]
            results.extend([{
                'id': admin.id,
                'username': admin.username,
                'type': 'admin'
            } for admin in admins])
        
        # Search teachers
        if not user_type or user_type == 'teacher':
            teachers = Teacher.objects.filter(username__icontains=query)[:10]
            results.extend([{
                'id': teacher.id,
                'username': teacher.username,
                'type': 'teacher'
            } for teacher in teachers])
        
        # Search students
        if not user_type or user_type == 'student':
            students = Student.objects.filter(username__icontains=query)[:10]
            results.extend([{
                'id': student.id,
                'username': student.username,
                'type': 'student',
                'class_name': student.class_id.name if student.class_id else None
            } for student in students])
        
        # Search parents
        if not user_type or user_type == 'parent':
            parents = Parent.objects.filter(username__icontains=query)[:10]
            results.extend([{
                'id': parent.id,
                'username': parent.username,
                'type': 'parent'
            } for parent in parents])
        
        return Response(results)