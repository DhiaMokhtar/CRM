from django.contrib import admin
from .models import Message, Conversation

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender_type', 'sender_id', 'recipient_type', 'recipient_id', 'content', 'is_read', 'created_at']
    list_filter = ['sender_type', 'recipient_type', 'is_read', 'created_at']
    search_fields = ['content']

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['participant1_type', 'participant1_id', 'participant2_type', 'participant2_id', 'updated_at']
    list_filter = ['participant1_type', 'participant2_type', 'updated_at']
