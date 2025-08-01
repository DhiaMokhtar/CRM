from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from .models import Lesson, Chapter, Course
from .serializers import LessonSerializer, ChapterSerializer, CourseSerializer
import requests
import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)

# Remove ClassRoomViewSet - classrooms are managed by users microservice

class CourseMaterialViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    
    def get_queryset(self):
        queryset = Course.objects.all()
        chapter = self.request.query_params.get('chapter', None)
        if chapter is not None:
            queryset = queryset.filter(chapter=chapter)
        return queryset
    
    def create(self, request, *args, **kwargs):
        # Create fileCourses directory if it doesn't exist
        upload_dir = os.path.join(settings.BASE_DIR, 'fileCourses')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        # Get the uploaded file
        file = request.FILES.get('pdf_file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate file path
        file_path = os.path.join('fileCourses', file.name)
        full_path = os.path.join(settings.BASE_DIR, file_path)

        # Save file to disk
        with open(full_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Create course record with file path (store as /fileCourses/filename.pdf)
        data = {
            'title': request.data.get('title'),
            'chapter': request.data.get('chapter'),
            'pdf': f'/fileCourses/{file.name}'  # Store with leading slash for URL
        }
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        course = serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    
    def get_queryset(self):
        queryset = Lesson.objects.all()
        classroom = self.request.query_params.get('classroom', None)
        if classroom is not None:
            queryset = queryset.filter(classroom_id=classroom)
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create a new lesson"""
        print(f"Creating lesson with data: {request.data}")  # Debug log
        
        # Validate that classroom exists in users microservice
        classroom_id = request.data.get('classroom')
        if classroom_id:
            if not self._validate_classroom_exists(classroom_id):
                return Response(
                    {'error': f'Classroom with id {classroom_id} not found in users service'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Update the data to use classroom_id field
        lesson_data = {
            'title': request.data.get('title'),
            'classroom_id': classroom_id
        }
        
        serializer = self.get_serializer(data=lesson_data)
        serializer.is_valid(raise_exception=True)
        lesson = serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def _validate_classroom_exists(self, classroom_id):
        """Validate that classroom exists in users microservice"""
        try:
            service_urls = [
                f"https://users_service:8000/api/classes/{classroom_id}/",
                f"https://localhost:8001/api/classes/{classroom_id}/",
            ]
            
            for url in service_urls:
                try:
                    response = requests.get(url, timeout=3, verify=False)
                    if response.status_code == 200:
                        return True
                except Exception:
                    continue
            
            return False
        except Exception as e:
            logger.warning(f"Error validating classroom: {str(e)}")
            return False

class ChapterViewSet(viewsets.ModelViewSet):
    queryset = Chapter.objects.all()
    serializer_class = ChapterSerializer
    
    def get_queryset(self):
        queryset = Chapter.objects.all()
        lesson = self.request.query_params.get('lesson', None)
        if lesson is not None:
            queryset = queryset.filter(lesson=lesson)
        return queryset

class StudentCoursesView(APIView):
    """Get courses for a specific student"""
    
    def get(self, request, student_id):
        try:
            # Get student's classroom from users microservice
            student_data = self._get_student_info(student_id)
            
            if not student_data:
                return Response(
                    {'error': 'Student not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            class_id = student_data.get('class_id')
            
            if not class_id:
                return Response(
                    {'error': 'Student not assigned to any class'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get lessons for the classroom
            lessons = Lesson.objects.filter(classroom_id=class_id)
            
            # Serialize the data with nested chapters and courses
            lesson_data = []
            for lesson in lessons:
                chapters_data = []
                for chapter in lesson.chapters.all():
                    courses_data = []
                    for course in chapter.courses.all():
                        courses_data.append({
                            'id': course.id,
                            'title': course.title,
                            'pdf': course.pdf
                        })
                    
                    chapters_data.append({
                        'id': chapter.id,
                        'title': chapter.title,
                        'courses': courses_data
                    })
                
                lesson_data.append({
                    'id': lesson.id,
                    'title': lesson.title,
                    'chapters': chapters_data
                })
            
            return Response(lesson_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting student courses: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_student_info(self, student_id):
        """Get student information from users microservice"""
        try:
            service_urls = [
                f"https://users_service:8000/api/students/{student_id}/",
                f"https://localhost:8001/api/students/{student_id}/",
            ]
            
            for url in service_urls:
                try:
                    response = requests.get(url, timeout=5, verify=False)
                    if response.status_code == 200:
                        return response.json()
                except Exception:
                    continue
            
            return None
        except Exception as e:
            logger.warning(f"Error fetching student info: {str(e)}")
            return None

class HealthCheckView(APIView):
    """Health check endpoint"""
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'courses'
        })
