from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from .models import Lesson, Chapter, Course, Subject, Grade
from .serializers import LessonSerializer, ChapterSerializer, CourseSerializer, SubjectSerializer, GradeSerializer
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
        classroom_id = self.request.query_params.get('classroom', None)
        if classroom_id is not None:
            queryset = queryset.filter(classroom_id=classroom_id)
        return queryset
    
    def create(self, request, *args, **kwargs):
        classroom_id = request.data.get('classroom')
        
        if not classroom_id:
            return Response({'error': 'Classroom is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate classroom exists
        if not self._validate_classroom_exists(classroom_id):
            return Response({'error': 'Classroom not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create lesson with classroom_id
        lesson_data = {
            'title': request.data.get('title'),
            'classroom_id': classroom_id
        }
        
        serializer = self.get_serializer(data=lesson_data)
        if serializer.is_valid():
            lesson = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
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
        lesson_id = self.request.query_params.get('lesson', None)
        if lesson_id is not None:
            queryset = queryset.filter(lesson_id=lesson_id)
        return queryset

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    
    def get_queryset(self):
        queryset = Course.objects.all()
        chapter_id = self.request.query_params.get('chapter', None)
        if chapter_id is not None:
            queryset = queryset.filter(chapter_id=chapter_id)
        return queryset

# Add grading viewsets
class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    
    def get_queryset(self):
        queryset = Subject.objects.all()
        classroom_id = self.request.query_params.get('classroom', None)
        teacher_id = self.request.query_params.get('teacher', None)
        
        if classroom_id is not None:
            queryset = queryset.filter(classroom_id=classroom_id)
        if teacher_id is not None:
            queryset = queryset.filter(teacher_id=teacher_id)
            
        return queryset

class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    
    def get_queryset(self):
        queryset = Grade.objects.select_related('subject')
        classroom_id = self.request.query_params.get('classroom', None)
        student_id = self.request.query_params.get('student', None)
        subject_id = self.request.query_params.get('subject', None)
        
        if classroom_id is not None:
            queryset = queryset.filter(subject__classroom_id=classroom_id)
        if student_id is not None:
            queryset = queryset.filter(student_id=student_id)
        if subject_id is not None:
            queryset = queryset.filter(subject_id=subject_id)
            
        return queryset

class GradeTableView(APIView):
    """Get complete grade table for a classroom"""
    
    def get(self, request, classroom_id):
        try:
            # Get classroom info from users microservice
            classroom_data = self._get_classroom_data(classroom_id)
            if not classroom_data:
                return Response({'error': 'Classroom not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Get students from users microservice
            students_data = self._get_classroom_students(classroom_id)
            
            # Get subjects for this classroom
            subjects = Subject.objects.filter(classroom_id=classroom_id)
            subjects_data = SubjectSerializer(subjects, many=True).data
            
            # Get all grades for this classroom
            grades = Grade.objects.filter(subject__classroom_id=classroom_id).select_related('subject')
            
            # Organize grades by student and subject
            grades_by_student = {}
            for grade in grades:
                if grade.student_id not in grades_by_student:
                    grades_by_student[grade.student_id] = {}
                if grade.subject_id not in grades_by_student[grade.student_id]:
                    grades_by_student[grade.student_id][grade.subject_id] = []
                grades_by_student[grade.student_id][grade.subject_id].append(GradeSerializer(grade).data)
            
            return Response({
                'classroom_id': classroom_id,
                'classroom_name': classroom_data.get('name', f'Class #{classroom_id}'),
                'subjects': subjects_data,
                'students': students_data,
                'grades': grades_by_student
            })
            
        except Exception as e:
            logger.error(f"Error in grade table view: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_classroom_data(self, classroom_id):
        """Get classroom data from users microservice"""
        try:
            service_urls = [
                f"https://users_service:8000/api/classes/{classroom_id}/",
                f"https://localhost:8001/api/classes/{classroom_id}/",
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
            logger.warning(f"Error fetching classroom data: {str(e)}")
            return None
    
    def _get_classroom_students(self, classroom_id):
        """Get students from users microservice"""
        try:
            service_urls = [
                f"https://users_service:8000/api/classes/{classroom_id}/students/",
                f"https://localhost:8001/api/classes/{classroom_id}/students/",
            ]
            
            for url in service_urls:
                try:
                    response = requests.get(url, timeout=5, verify=False)
                    if response.status_code == 200:
                        return response.json()
                except Exception:
                    continue
            
            return []
        except Exception as e:
            logger.warning(f"Error fetching classroom students: {str(e)}")
            return []

class HealthCheckView(APIView):
    """Health check endpoint for courses microservice"""
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'courses'
        })
