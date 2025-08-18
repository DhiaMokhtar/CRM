from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class Message(models.Model):
    SENDER_TYPES = (
        ('administrator', 'Administrator'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    )
    
    sender_type = models.CharField(max_length=15, choices=SENDER_TYPES)
    sender_id = models.IntegerField()  # Make sure this is IntegerField, not CharField
    recipient_type = models.CharField(max_length=15, choices=SENDER_TYPES)
    recipient_id = models.IntegerField()  # Make sure this is IntegerField, not CharField
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message from {self.sender_type}({self.sender_id}) to {self.recipient_type}({self.recipient_id})"

class Conversation(models.Model):
    participant1_type = models.CharField(max_length=15, choices=Message.SENDER_TYPES)
    participant1_id = models.IntegerField()
    participant2_type = models.CharField(max_length=15, choices=Message.SENDER_TYPES)
    participant2_id = models.IntegerField()
    last_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversation_last_message')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['participant1_type', 'participant1_id', 'participant2_type', 'participant2_id'],
                name='unique_conversation'
            )
        ]
        indexes = [
            models.Index(fields=['participant1_type', 'participant1_id']),
            models.Index(fields=['participant2_type', 'participant2_id']),
            models.Index(fields=['updated_at']),
        ]
    
    def __str__(self):
        return f"Conversation: {self.participant1_type}({self.participant1_id}) <-> {self.participant2_type}({self.participant2_id})"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('course_material', 'Course Material'),
        ('homework', 'Homework'),
        ('announcement', 'Announcement'),
        ('grade', 'Grade'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='announcement')
    classroom_id = models.IntegerField()
    teacher_id = models.IntegerField()
    student_id = models.IntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.notification_type}"

class StudentNotification(models.Model):
    """Junction table to track which students have read which notifications"""
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    student_id = models.IntegerField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['notification', 'student_id']
    
    def __str__(self):
        return f"Student {self.student_id} - {self.notification.title}"
