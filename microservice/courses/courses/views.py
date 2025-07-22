from django.shortcuts import render
import os
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from .models import ClassRoom, Lesson, Chapter, Course
from .serializers import ClassRoomSerializer, LessonSerializer, ChapterSerializer, CourseSerializer

class ClassRoomViewSet(viewsets.ModelViewSet):
    queryset = ClassRoom.objects.all()
    serializer_class = ClassRoomSerializer

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    
    def get_queryset(self):
        queryset = Lesson.objects.all()
        class_room = self.request.query_params.get('class_room', None)
        if class_room is not None:
            queryset = queryset.filter(classroom=class_room)
        return queryset

class ChapterViewSet(viewsets.ModelViewSet):
    queryset = Chapter.objects.all()
    serializer_class = ChapterSerializer
    
    def get_queryset(self):
        queryset = Chapter.objects.all()
        lesson = self.request.query_params.get('lesson', None)
        if lesson is not None:
            queryset = queryset.filter(lesson=lesson)
        return queryset

class CourseViewSet(viewsets.ModelViewSet):
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

class StudentCoursesView(APIView):
    def get(self, request, student_id):
        try:
            # Get student's classroom from users microservice
            import requests
            users_service_url = "https://localhost:8001/api"  # Use HTTPS
            
            try:
                # Disable SSL verification for development with self-signed certificates
                response = requests.get(f"{users_service_url}/students/{student_id}/", verify=False)
                if response.status_code == 200:
                    student_data = response.json()
                    class_id = student_data.get('class_id')
                    
                    if class_id:
                        lessons = Lesson.objects.filter(classroom_id=class_id)
                        
                        # Serialize the data with nested chapters and courses
                        lesson_data = []
                        for lesson in lessons:
                            chapters_data = []
                            for chapter in lesson.chapters.all():
                                courses_data = [{
                                    'title': course.title,
                                    'pdf': course.pdf
                                } for course in chapter.courses.all()]
                                
                                chapters_data.append({
                                    'title': chapter.title,
                                    'courses': courses_data
                                })
                            
                            lesson_data.append({
                                'title': lesson.title,
                                'chapters': chapters_data
                            })
                        
                        return Response(lesson_data, status=status.HTTP_200_OK)
                    else:
                        return Response([], status=status.HTTP_200_OK)
                else:
                    return Response(
                        {'error': 'Student not found'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
            except requests.RequestException:
                return Response(
                    {'error': 'Unable to connect to users service'}, 
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
