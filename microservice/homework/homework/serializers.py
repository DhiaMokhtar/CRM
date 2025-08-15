from rest_framework import serializers
from .models import Homework, HomeworkSubmission, StudentComment ,Schedule
import requests
import logging

logger = logging.getLogger(__name__)

class HomeworkSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()
    classroom_name = serializers.SerializerMethodField()
    submission_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Homework
        fields = ['id', 'title', 'description', 'classroom_id', 'teacher_id', 
                 'due_date', 'created_at', 'updated_at', 'teacher_name', 
                 'classroom_name', 'submission_count']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_teacher_name(self, obj):
        return self._get_user_name('teacher', obj.teacher_id)
    
    def get_classroom_name(self, obj):
        return self._get_classroom_name(obj.classroom_id)
    
    def get_submission_count(self, obj):
        return obj.submissions.count()
    
    def _get_user_name(self, user_type, user_id):
        """Get user name from users microservice"""
        try:
            service_urls = [
                f"https://users_service:8000/api/{user_type}s/{user_id}/",
                f"https://localhost:8001/api/{user_type}s/{user_id}/",
            ]
            
            for url in service_urls:
                try:
                    response = requests.get(url, timeout=3, verify=False)
                    if response.status_code == 200:
                        user_data = response.json()
                        return user_data.get('username', f'{user_type.title()} #{user_id}')
                except Exception:
                    continue
            
            return f'{user_type.title()} #{user_id}'
        except Exception as e:
            logger.warning(f"Error fetching {user_type} name: {str(e)}")
            return f'{user_type.title()} #{user_id}'
    
    def _get_classroom_name(self, classroom_id):
        """Get classroom name from users microservice"""
        try:
            service_urls = [
                f"https://users_service:8000/api/classes/{classroom_id}/",
                f"https://localhost:8001/api/classes/{classroom_id}/",
            ]
            
            for url in service_urls:
                try:
                    response = requests.get(url, timeout=3, verify=False)
                    if response.status_code == 200:
                        classroom_data = response.json()
                        return classroom_data.get('name', f'Class #{classroom_id}')
                except Exception:
                    continue
            
            return f'Class #{classroom_id}'
        except Exception as e:
            logger.warning(f"Error fetching classroom name: {str(e)}")
            return f'Class #{classroom_id}'

class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    homework_title = serializers.CharField(source='homework.title', read_only=True)
    graded_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = HomeworkSubmission
        fields = ['id', 'homework', 'student_id', 'student_name', 'homework_title',
                 'file', 'submission_date', 'comments', 'grade', 'graded_at', 
                 'graded_by', 'graded_by_name']
        read_only_fields = ['submission_date']
    
    def get_student_name(self, obj):
        return self._get_user_name('student', obj.student_id)
    
    def get_graded_by_name(self, obj):
        if obj.graded_by:
            return self._get_user_name('teacher', obj.graded_by)
        return None
    
    def _get_user_name(self, user_type, user_id):
        """Get user name from users microservice"""
        try:
            service_urls = [
                f"https://users_service:8000/api/{user_type}s/{user_id}/",
                f"https://localhost:8001/api/{user_type}s/{user_id}/",
            ]
            
            for url in service_urls:
                try:
                    response = requests.get(url, timeout=3, verify=False)
                    if response.status_code == 200:
                        user_data = response.json()
                        return user_data.get('username', f'{user_type.title()} #{user_id}')
                except Exception:
                    continue
            
            return f'{user_type.title()} #{user_id}'
        except Exception as e:
            logger.warning(f"Error fetching {user_type} name: {str(e)}")
            return f'{user_type.title()} #{user_id}'

# Add Student Comment Serializer
class StudentCommentSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentComment
        fields = ['id', 'student_id', 'teacher_id', 'content', 'created_at', 'teacher_name', 'student_name']
        read_only_fields = ['created_at']
    
    def get_teacher_name(self, obj):
        return self._get_user_name('teacher', obj.teacher_id)
    
    def get_student_name(self, obj):
        return self._get_user_name('student', obj.student_id)
    
    def _get_user_name(self, user_type, user_id):
        """Get user name from users microservice"""
        try:
            service_urls = [
                f"https://users_service:8000/api/{user_type}s/{user_id}/",
                f"https://localhost:8001/api/{user_type}s/{user_id}/",
            ]
            
            for url in service_urls:
                try:
                    response = requests.get(url, timeout=3, verify=False)
                    if response.status_code == 200:
                        user_data = response.json()
                        return user_data.get('username', f'{user_type.title()} #{user_id}')
                except Exception:
                    continue
            
            return f'{user_type.title()} #{user_id}'
        except Exception as e:
            logger.warning(f"Error fetching {user_type} name: {str(e)}")
            return f'{user_type.title()} #{user_id}'

# Add Schedule Serializer
class ScheduleSerializer(serializers.ModelSerializer):
    classroom_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    lesson_title = serializers.SerializerMethodField()
    
    class Meta:
        model = Schedule
        fields = ['id', 'title', 'description', 'schedule_type', 'classroom_id', 'teacher_id', 
                 'lesson_id', 'start_datetime', 'end_datetime', 'is_recurring', 'recurrence_pattern',
                 'user_type', 'user_id', 'created_at', 'updated_at', 'classroom_name', 
                 'teacher_name', 'lesson_title']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_classroom_name(self, obj):
        if not obj.classroom_id:
            return None
        return self._get_classroom_name(obj.classroom_id)
    
    def get_teacher_name(self, obj):
        if not obj.teacher_id:
            return None
        return self._get_user_name('teacher', obj.teacher_id)
    
    def get_lesson_title(self, obj):
        if not obj.lesson_id:
            return None
        return self._get_lesson_title(obj.lesson_id)
    
    def _get_classroom_name(self, classroom_id):
        """Get classroom name from users microservice"""
        try:
            service_urls = [
                f"https://users_service:8000/api/classes/{classroom_id}/",
                f"https://localhost:8001/api/classes/{classroom_id}/",
            ]
            
            for url in service_urls:
                try:
                    response = requests.get(url, timeout=3, verify=False)
                    if response.status_code == 200:
                        classroom_data = response.json()
                        return classroom_data.get('name', f'Class #{classroom_id}')
                except Exception:
                    continue
            
            return f'Class #{classroom_id}'
        except Exception as e:
            logger.warning(f"Error fetching classroom name: {str(e)}")
            return f'Class #{classroom_id}'
    
    def _get_user_name(self, user_type, user_id):
        """Get user name from users microservice"""
        try:
            service_urls = [
                f"https://users_service:8000/api/{user_type}s/{user_id}/",
                f"https://localhost:8001/api/{user_type}s/{user_id}/",
            ]
            
            for url in service_urls:
                try:
                    response = requests.get(url, timeout=3, verify=False)
                    if response.status_code == 200:
                        user_data = response.json()
                        return user_data.get('username', f'{user_type.title()} #{user_id}')
                except Exception:
                    continue
            
            return f'{user_type.title()} #{user_id}'
        except Exception as e:
            logger.warning(f"Error fetching {user_type} name: {str(e)}")
            return f'{user_type.title()} #{user_id}'
    
    def _get_lesson_title(self, lesson_id):
        """Get lesson title from courses microservice"""
        try:
            service_urls = [
                f"https://courses_service:8000/api/lessons/{lesson_id}/",
                f"https://localhost:8002/api/lessons/{lesson_id}/",
            ]
            
            for url in service_urls:
                try:
                    response = requests.get(url, timeout=3, verify=False)
                    if response.status_code == 200:
                        lesson_data = response.json()
                        return lesson_data.get('title', f'Lesson #{lesson_id}')
                except Exception:
                    continue
            
            return f'Lesson #{lesson_id}'
        except Exception as e:
            logger.warning(f"Error fetching lesson title: {str(e)}")
            return f'Lesson #{lesson_id}'