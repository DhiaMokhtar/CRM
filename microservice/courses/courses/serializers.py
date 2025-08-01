from rest_framework import serializers
from .models import Lesson, Chapter, Course, Subject, Grade
import requests
import logging

logger = logging.getLogger(__name__)

class SubjectSerializer(serializers.ModelSerializer):
    classroom_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Subject
        fields = ['id', 'name', 'classroom_id', 'teacher_id', 'created_at', 'classroom_name', 'teacher_name']
    
    def get_classroom_name(self, obj):
        """Get classroom name from users microservice"""
        try:
            service_urls = [
                f"https://users_service:8000/api/classes/{obj.classroom_id}/",
                f"https://localhost:8001/api/classes/{obj.classroom_id}/",
            ]
            
            for url in service_urls:
                try:
                    response = requests.get(url, timeout=3, verify=False)
                    if response.status_code == 200:
                        classroom_data = response.json()
                        return classroom_data.get('name', f'Class #{obj.classroom_id}')
                except Exception:
                    continue
            
            return f'Class #{obj.classroom_id}'
        except Exception as e:
            logger.warning(f"Error fetching classroom name: {str(e)}")
            return f'Class #{obj.classroom_id}'
    
    def get_teacher_name(self, obj):
        """Get teacher name from users microservice"""
        try:
            service_urls = [
                f"https://users_service:8000/api/teachers/{obj.teacher_id}/",
                f"https://localhost:8001/api/teachers/{obj.teacher_id}/",
            ]
            
            for url in service_urls:
                try:
                    response = requests.get(url, timeout=3, verify=False)
                    if response.status_code == 200:
                        teacher_data = response.json()
                        return f"{teacher_data.get('first_name', '')} {teacher_data.get('last_name', '')}".strip() or teacher_data.get('username', f'Teacher #{obj.teacher_id}')
                except Exception:
                    continue
            
            return f'Teacher #{obj.teacher_id}'
        except Exception as e:
            logger.warning(f"Error fetching teacher name: {str(e)}")
            return f'Teacher #{obj.teacher_id}'

class GradeSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    subject_name = serializers.SerializerMethodField()
    recorded_by_name = serializers.SerializerMethodField()
    percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Grade
        fields = ['id', 'student_id', 'subject', 'grade_type', 'score', 'max_score', 
                 'notes', 'recorded_by_id', 'date_recorded', 'student_name', 
                 'subject_name', 'recorded_by_name', 'percentage']
    
    def get_student_name(self, obj):
        """Get student name from users microservice"""
        try:
            service_urls = [
                f"https://users_service:8000/api/students/{obj.student_id}/",
                f"https://localhost:8001/api/students/{obj.student_id}/",
            ]
            
            for url in service_urls:
                try:
                    response = requests.get(url, timeout=3, verify=False)
                    if response.status_code == 200:
                        student_data = response.json()
                        return f"{student_data.get('first_name', '')} {student_data.get('last_name', '')}".strip() or student_data.get('username', f'Student #{obj.student_id}')
                except Exception:
                    continue
            
            return f'Student #{obj.student_id}'
        except Exception as e:
            logger.warning(f"Error fetching student name: {str(e)}")
            return f'Student #{obj.student_id}'
    
    def get_subject_name(self, obj):
        return obj.subject.name
    
    def get_recorded_by_name(self, obj):
        """Get teacher/admin name from users microservice"""
        try:
            # Try teachers first
            service_urls = [
                f"https://users_service:8000/api/teachers/{obj.recorded_by_id}/",
                f"https://localhost:8001/api/teachers/{obj.recorded_by_id}/",
            ]
            
            for url in service_urls:
                try:
                    response = requests.get(url, timeout=3, verify=False)
                    if response.status_code == 200:
                        user_data = response.json()
                        return f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip() or user_data.get('username', f'User #{obj.recorded_by_id}')
                except Exception:
                    continue
            
            # Try administrators if teacher not found
            service_urls = [
                f"https://users_service:8000/api/administrators/{obj.recorded_by_id}/",
                f"https://localhost:8001/api/administrators/{obj.recorded_by_id}/",
            ]
            
            for url in service_urls:
                try:
                    response = requests.get(url, timeout=3, verify=False)
                    if response.status_code == 200:
                        user_data = response.json()
                        return f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip() or user_data.get('username', f'User #{obj.recorded_by_id}')
                except Exception:
                    continue
            
            return f'User #{obj.recorded_by_id}'
        except Exception as e:
            logger.warning(f"Error fetching user name: {str(e)}")
            return f'User #{obj.recorded_by_id}'

# Existing serializers
class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'

class ChapterSerializer(serializers.ModelSerializer):
    courses = CourseSerializer(many=True, read_only=True)
    
    class Meta:
        model = Chapter
        fields = '__all__'

class LessonSerializer(serializers.ModelSerializer):
    chapters = serializers.SerializerMethodField()
    classroom_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'classroom_id', 'created_at', 'chapters', 'classroom_name']
    
    def get_chapters(self, obj):
        return ChapterSerializer(obj.chapters.all(), many=True).data
    
    def get_classroom_name(self, obj):
        """Get classroom name from users microservice"""
        try:
            service_urls = [
                f"https://users_service:8000/api/classes/{obj.classroom_id}/",
                f"https://localhost:8001/api/classes/{obj.classroom_id}/",
            ]
            
            for url in service_urls:
                try:
                    response = requests.get(url, timeout=3, verify=False)
                    if response.status_code == 200:
                        classroom_data = response.json()
                        return classroom_data.get('name', f'Class #{obj.classroom_id}')
                except Exception:
                    continue
            
            return f'Class #{obj.classroom_id}'
        except Exception as e:
            logger.warning(f"Error fetching classroom name: {str(e)}")
            return f'Class #{obj.classroom_id}'