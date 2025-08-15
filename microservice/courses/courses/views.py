from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Lesson, Chapter, Course, Subject, Grade
from .serializers import LessonSerializer, ChapterSerializer, CourseSerializer, SubjectSerializer, GradeSerializer
import os
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

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
        chapter_id = self.request.query_params.get('chapter')
        if chapter_id:
            queryset = queryset.filter(chapter_id=chapter_id)
        return queryset

    def create(self, request, *args, **kwargs):
        # Accept either pdf_file (uploaded file) or already-built pdf path
        uploaded_file = request.FILES.get('pdf_file')
        provided_path = request.data.get('pdf')

        title = request.data.get('title')
        chapter_id = request.data.get('chapter')

        if not title:
            return Response({'error': 'title field is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not chapter_id:
            return Response({'error': 'chapter field is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not uploaded_file and not provided_path:
            return Response({'error': 'pdf_file field is required'}, status=status.HTTP_400_BAD_REQUEST)

        # If client supplied a path already (rare), just validate & save
        if not uploaded_file and provided_path:
            data = {
                'title': title,
                'chapter': chapter_id,
                'pdf': provided_path
            }
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                obj = serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Handle file upload
        file_courses_dir = os.path.join(settings.BASE_DIR, 'fileCourses')
        os.makedirs(file_courses_dir, exist_ok=True)

        file_path = os.path.join(file_courses_dir, uploaded_file.name)
        try:
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
        except Exception as e:
            logger.exception("Failed to save uploaded file")
            return Response({'error': f'Failed to save file: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        relative_path = f'/fileCourses/{uploaded_file.name}'
        course_data = {
            'title': title,
            'chapter': chapter_id,
            'pdf': relative_path
        }

        serializer = self.get_serializer(data=course_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # Cleanup on validation failure
        try:
            os.remove(file_path)
        except OSError:
            pass
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# REMOVE (or comment out) the old CourseMaterialViewSet to prevent router conflicts
# class CourseMaterialViewSet(...):
#     pass

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

class StudentCoursesView(APIView):
    """Get courses for a specific student"""

    def get(self, request, student_id):
        try:
            logger.info(f"[StudentCoursesView] student_id={student_id}")
            classroom_id = self._get_student_classroom(student_id)
            logger.info(f"[StudentCoursesView] resolved classroom_id={classroom_id}")

            if classroom_id is None:
                return Response({'error': 'Student classroom not found'}, status=status.HTTP_404_NOT_FOUND)

            lessons = Lesson.objects.filter(classroom_id=classroom_id)
            logger.info(f"[StudentCoursesView] lessons count={lessons.count()}")

            lesson_data = []
            for lesson in lessons:
                chapters = Chapter.objects.filter(lesson=lesson)
                chapters_data = []
                for chapter in chapters:
                    courses = Course.objects.filter(chapter=chapter)
                    courses_data = [{
                        'id': c.id,
                        'title': c.title,
                        'pdf': c.pdf
                    } for c in courses]
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
            logger.exception(f"[StudentCoursesView] Unexpected error: {e}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_student_classroom(self, student_id: int):
        """
        Fetch student from users microservice and return classroom id.
        IMPORTANT: Do NOT use localhost inside a container to reach another container.
        """
        base_url = os.getenv('USERS_SERVICE_BASE_URL', 'https://users_service:8000')
        # Ensure no trailing slash
        base_url = base_url.rstrip('/')

        urls = [
            f"{base_url}/api/students/{student_id}/",
        ]

        for url in urls:
            try:
                logger.info(f"[_get_student_classroom] GET {url}")
                resp = requests.get(url, timeout=5, verify=False)
                logger.info(f"[_get_student_classroom] status={resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    logger.info(f"[_get_student_classroom] payload keys={list(data.keys())}")
                    classroom_id = data.get('class_id')
                    logger.info(f"[_get_student_classroom] class_id raw={classroom_id}")
                    if classroom_id is not None:
                        try:
                            return int(classroom_id)
                        except (TypeError, ValueError):
                            logger.warning(f"[_get_student_classroom] cannot cast class_id={classroom_id}")
                    return None
            except requests.RequestException as e:
                logger.warning(f"[_get_student_classroom] request failed {url}: {e}")
                continue
        logger.warning(f"[_get_student_classroom] all attempts failed for student {student_id}")
        return None
