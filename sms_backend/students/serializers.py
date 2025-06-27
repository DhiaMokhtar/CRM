# students/serializers.py
from rest_framework import serializers
from django.db import models
from .models import (Administrator, ClassRoom, Student, 
Teacher, Parent, Lesson, Chapter, Course, 
StudentComment, Homework, HomeworkSubmission, 
Notification, Message, Conversation,Schedule, ScheduleNotification,
Subject,Grade)

# Add these serializers at the end of the file

class ScheduleSerializer(serializers.ModelSerializer):
    classroom_name = serializers.CharField(source='classroom.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.username', read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Schedule
        fields = ['id', 'title', 'description', 'schedule_type', 'classroom', 'classroom_name',
                 'teacher', 'teacher_name', 'lesson', 'lesson_title', 'start_datetime', 'end_datetime',
                 'is_recurring', 'recurrence_pattern', 'recurrence_end_date', 'created_by', 
                 'created_by_name', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at']

class ScheduleNotificationSerializer(serializers.ModelSerializer):
    schedule_title = serializers.CharField(source='schedule.title', read_only=True)
    
    class Meta:
        model = ScheduleNotification
        fields = ['id', 'schedule', 'schedule_title', 'recipient_type', 'recipient_id', 
                 'is_sent', 'sent_at']
class NotificationSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    chapter_title = serializers.CharField(source='course.chapter.title', read_only=True)
    lesson_title = serializers.CharField(source='course.chapter.lesson.title', read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'is_read', 'created_at', 'sender_name', 'course_title', 'chapter_title', 'lesson_title']

class ClassRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassRoom
        fields = '__all__'


class AdministratorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Administrator
        fields = '__all__'


class TeacherSerializer(serializers.ModelSerializer):
    classes = ClassRoomSerializer(many=True, read_only=True)
    class_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=ClassRoom.objects.all(), source='classes'
    )

    class Meta:
        model = Teacher
        fields = ['id', 'username', 'email', 'password', 'classes', 'class_ids']


class StudentSerializer(serializers.ModelSerializer):
    class_id = serializers.PrimaryKeyRelatedField(queryset=ClassRoom.objects.all())
    class_name = serializers.CharField(source='class_id.name', read_only=True)

    class Meta:
        model = Student
        fields = ['id', 'username', 'password', 'email', 'class_id', 'class_name']
        extra_kwargs = {'password': {'write_only': True}}


class ParentSerializer(serializers.ModelSerializer):
    students = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Student.objects.all(),
        required=False
    )

    class Meta:
        model = Parent
        fields = ['id', 'username', 'password', 'email', 'students']


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'

class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'


class StudentCommentSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.username', read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    
    class Meta:
        model = StudentComment
        fields = ['id', 'student', 'teacher', 'teacher_name', 'content', 'created_at']
        read_only_fields = ['created_at']

# Add to serializers.py
class HomeworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Homework
        fields = ['id', 'title', 'description', 'classroom', 'teacher', 'due_date', 'created_at']

# Add to serializers.py after HomeworkSerializer
class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.username', read_only=True)
    homework_title = serializers.CharField(source='homework.title', read_only=True)
    
    class Meta:
        model = HomeworkSubmission
        fields = ['id', 'homework', 'student', 'student_name', 'homework_title', 'file', 'submission_date', 'comments']
        read_only_fields = ['submission_date']

# Message serializer for the messaging system
class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    recipient_name = serializers.SerializerMethodField()
    created_at_formatted = serializers.DateTimeField(source='created_at', format="%Y-%m-%d %H:%M:%S", read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender_type', 'sender_id', 'recipient_type', 'recipient_id', 
                 'content', 'is_read', 'created_at', 'created_at_formatted', 
                 'sender_name', 'recipient_name']
        read_only_fields = ['created_at']
    
    def get_sender_name(self, obj):
        return self._get_user_name(obj.sender_type, obj.sender_id)
    
    def get_recipient_name(self, obj):
        return self._get_user_name(obj.recipient_type, obj.recipient_id)
    
    def _get_user_name(self, user_type, user_id):
        try:
            if user_type == 'admin':
                return Administrator.objects.get(id=user_id).username
            elif user_type == 'teacher':
                return Teacher.objects.get(id=user_id).username
            elif user_type == 'student':
                return Student.objects.get(id=user_id).username
            elif user_type == 'parent':
                return Parent.objects.get(id=user_id).username
            return "Unknown"
        except Exception:
            return "Unknown"

# Conversation serializer
class ConversationSerializer(serializers.ModelSerializer):
    participant1_name = serializers.SerializerMethodField()
    participant2_name = serializers.SerializerMethodField()
    last_message_content = serializers.CharField(source='last_message.content', read_only=True)
    last_message_time = serializers.DateTimeField(source='last_message.created_at', format="%Y-%m-%d %H:%M:%S", read_only=True)
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'participant1_type', 'participant1_id', 'participant2_type', 'participant2_id',
                 'participant1_name', 'participant2_name', 'last_message_content', 'last_message_time',
                 'updated_at', 'unread_count']
        read_only_fields = ['updated_at']
    
    def get_participant1_name(self, obj):
        return self._get_user_name(obj.participant1_type, obj.participant1_id)
    
    def get_participant2_name(self, obj):
        return self._get_user_name(obj.participant2_type, obj.participant2_id)
    
    def get_unread_count(self, obj):
        # Get the current user from the context
        request = self.context.get('request')
        if not request or not hasattr(request, 'user_type') or not hasattr(request, 'user_id'):
            return 0
        
        user_type = request.user_type
        user_id = request.user_id
        
        # Count unread messages where the current user is the recipient
        return Message.objects.filter(
            ((models.Q(sender_type=obj.participant1_type) & models.Q(sender_id=obj.participant1_id)) |
             (models.Q(sender_type=obj.participant2_type) & models.Q(sender_id=obj.participant2_id))),
            recipient_type=user_type,
            recipient_id=user_id,
            is_read=False
        ).count()
    
    def _get_user_name(self, user_type, user_id):
        try:
            if user_type == 'admin':
                return Administrator.objects.get(id=user_id).username
            elif user_type == 'teacher':
                return Teacher.objects.get(id=user_id).username
            elif user_type == 'student':
                return Student.objects.get(id=user_id).username
            elif user_type == 'parent':
                return Parent.objects.get(id=user_id).username
            return "Unknown"
        except Exception:
            return "Unknown"

# Add these new serializers
class SubjectSerializer(serializers.ModelSerializer):
    classroom_name = serializers.CharField(source='classroom.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.username', read_only=True)
    
    class Meta:
        model = Subject
        fields = ['id', 'name', 'classroom', 'classroom_name', 'teacher', 'teacher_name', 'created_at']
        read_only_fields = ['created_at']

class GradeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.username', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.username', read_only=True)
    percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Grade
        fields = ['id', 'student', 'student_name', 'subject', 'subject_name', 'grade_type', 
                 'score', 'max_score', 'percentage', 'date_recorded', 'notes', 'recorded_by', 'recorded_by_name']
        read_only_fields = ['date_recorded', 'recorded_by']

class GradeTableSerializer(serializers.Serializer):
    """Serializer for the grade table view"""
    classroom_id = serializers.IntegerField()
    subjects = SubjectSerializer(many=True, read_only=True)
    students = StudentSerializer(many=True, read_only=True)
    grades = serializers.SerializerMethodField()
    
    def get_grades(self, obj):
        # Return grades organized by student and subject
        grades_dict = {}
        for grade in obj.get('grades', []):
            student_id = grade.student.id
            subject_id = grade.subject.id
            if student_id not in grades_dict:
                grades_dict[student_id] = {}
            if subject_id not in grades_dict[student_id]:
                grades_dict[student_id][subject_id] = []
            grades_dict[student_id][subject_id].append(GradeSerializer(grade).data)
        return grades_dict
