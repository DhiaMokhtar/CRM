from rest_framework import serializers
from .models import Lesson, Chapter, Course
import requests
import logging

logger = logging.getLogger(__name__)

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