from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import check_password, make_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
import jwt
from datetime import datetime, timedelta
from django.conf import settings
import os
from django.conf import settings
from .models import (Administrator, Teacher, Student, ClassRoom, Parent, 
Lesson, Chapter, Course,Homework,HomeworkSubmission,Subject, Grade)
from .serializers import (
    AdministratorSerializer,
    TeacherSerializer,
    StudentSerializer,
    ClassRoomSerializer,
    ParentSerializer,
    LessonSerializer,
    ChapterSerializer,
    CourseSerializer,
    HomeworkSerializer,
    HomeworkSubmissionSerializer,
    SubjectSerializer, GradeSerializer, GradeTableSerializer
)

from rest_framework.decorators import action
from django.db.models import Prefetch

# Add to imports at the top
from .models import (Administrator, ClassRoom, Student, Teacher, Parent, 
                    Lesson, Chapter, Course, StudentComment, Homework, HomeworkSubmission, Notification)
from .serializers import (AdministratorSerializer, ClassRoomSerializer, StudentSerializer, 
                         TeacherSerializer, ParentSerializer, LessonSerializer, ChapterSerializer, 
                         CourseSerializer, StudentCommentSerializer, HomeworkSerializer, HomeworkSubmissionSerializer, NotificationSerializer)

class AdministratorViewSet(viewsets.ModelViewSet):
    queryset = Administrator.objects.all()
    serializer_class = AdministratorSerializer


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer


class ClassRoomViewSet(viewsets.ModelViewSet):
    queryset = ClassRoom.objects.all()
    serializer_class = ClassRoomSerializer

class ParentViewSet(viewsets.ModelViewSet):
    queryset = Parent.objects.all()
    serializer_class = ParentSerializer

class AdminLoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({
                'error': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Try Admin login
        try:
            admin = Administrator.objects.get(username=username)
            # Use proper password checking (assuming passwords are hashed)
            if check_password(password, admin.password):
                # Generate JWT token
                payload = {
                    'user_id': admin.id,
                    'user_type': 'admin',
                    'username': admin.username,
                    'exp': datetime.utcnow() + timedelta(hours=24)
                }
                token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
                
                response = Response({
                    'message': 'Login successful',
                    'user_type': 'admin',
                    'user_id': admin.id,
                    'username': admin.username,
                    'token': token
                }, status=status.HTTP_200_OK)
                
                # Set secure HTTP-only cookie
                response.set_cookie(
                    'auth_token',
                    token,
                    max_age=86400,  # 24 hours
                    httponly=True,
                    secure=True,  # Only send over HTTPS
                    samesite='Strict'
                )
                return response
        except Administrator.DoesNotExist:
            pass

        # Try Student login
        try:
            student = Student.objects.get(username=username)
            if check_password(password, student.password):
                payload = {
                    'user_id': student.id,
                    'user_type': 'student',
                    'username': student.username,
                    'exp': datetime.utcnow() + timedelta(hours=24)
                }
                token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
                
                response = Response({
                    'message': 'Login successful',
                    'user_type': 'student',
                    'user_id': student.id,
                    'username': student.username,
                    'token': token
                }, status=status.HTTP_200_OK)
                
                response.set_cookie(
                    'auth_token',
                    token,
                    max_age=86400,
                    httponly=True,
                    secure=True,
                    samesite='Strict'
                )
                return response
        except Student.DoesNotExist:
            pass

        # Try Teacher login
        try:
            teacher = Teacher.objects.get(username=username)
            if check_password(password, teacher.password):
                payload = {
                    'user_id': teacher.id,
                    'user_type': 'teacher',
                    'username': teacher.username,
                    'exp': datetime.utcnow() + timedelta(hours=24)
                }
                token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
                
                response = Response({
                    'message': 'Login successful',
                    'user_type': 'teacher',
                    'user_id': teacher.id,
                    'username': teacher.username,
                    'token': token
                }, status=status.HTTP_200_OK)
                
                response.set_cookie(
                    'auth_token',
                    token,
                    max_age=86400,
                    httponly=True,
                    secure=True,
                    samesite='Strict'
                )
                return response
        except Teacher.DoesNotExist:
            pass
        # Try Parent login
        try:
            parent = Parent.objects.get(username=username)
            if check_password(password, parent.password):
                payload = {
                    'user_id': parent.id,
                    'user_type': 'parent',
                    'username': parent.username,
                    'exp': datetime.utcnow() + timedelta(hours=24)
                }
                token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
                response = Response({
                    'message': 'Login successful',
                    'user_type': 'parent',
                    'user_id': parent.id,
                    'username': parent.username,
                    'token': token
                }, status=status.HTTP_200_OK)
                response.set_cookie(
                    'auth_token',
                    token,
                    max_age=86400,
                    httponly=True,
                    secure=True,
                    samesite='Strict'
                )
                return response
        except Parent.DoesNotExist:
            pass


        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)

class ClassStudentsView(APIView):
    def get(self, request, class_id):
        try:
            classroom = ClassRoom.objects.get(id=class_id)
            students = Student.objects.filter(class_id=classroom)
            serializer = StudentSerializer(students, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ClassRoom.DoesNotExist:
            return Response(
                {'error': 'Class not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class ParentChildrenView(APIView):
    def get(self, request, parent_id):
        try:
            parent = Parent.objects.get(id=parent_id)
            children = parent.students.all()
            serializer = StudentSerializer(children, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Parent.DoesNotExist:
            return Response(
                {'error': 'Parent not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    def get_queryset(self):
            queryset = super().get_queryset()
            class_room = self.request.query_params.get('class_room', None)
            if class_room is not None:
                queryset = queryset.filter(classroom=class_room)
            return queryset

class ChapterViewSet(viewsets.ModelViewSet):
    queryset = Chapter.objects.all()
    serializer_class = ChapterSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        lesson = self.request.query_params.get('lesson', None)
        if lesson is not None:
            queryset = queryset.filter(lesson=lesson)
        return queryset

# Update the CourseViewSet create method
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    
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

        # Create course record with file path
        data = {
            'title': request.data.get('title'),
            'chapter': request.data.get('chapter'),
            'pdf': '/' + file_path.replace('\\', '/')  # Store relative path with forward slashes
        }

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        course = serializer.save()

        # Get teacher_id from request
        teacher_id = request.data.get('teacher_id')
        if teacher_id:
            try:
                teacher = Teacher.objects.get(id=teacher_id)
                chapter = Chapter.objects.get(id=data['chapter'])
                classroom = chapter.lesson.classroom
                
                # Get all students in the classroom
                students = Student.objects.filter(class_id=classroom)
                
                # Create notifications for all students
                notifications = []
                for student in students:
                    notification = Notification(
                        recipient=student,
                        sender=teacher,
                        title=f"New Course Material: {course.title}",
                        message=f"A new course material '{course.title}' has been uploaded to {chapter.lesson.title} - {chapter.title}.",
                        course=course
                    )
                    notifications.append(notification)
                
                # Bulk create notifications
                Notification.objects.bulk_create(notifications)
                
            except (Teacher.DoesNotExist, Chapter.DoesNotExist) as e:
                # Log error but don't fail the course creation
                print(f"Error creating notifications: {e}")

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        chapter = self.request.query_params.get('chapter', None)
        if chapter is not None:
            queryset = queryset.filter(chapter=chapter)
        return queryset

# Add NotificationViewSet
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()  # 🔥 Required for detail routes (PUT, PATCH, DELETE)
    serializer_class = NotificationSerializer

    def get_queryset(self):
        if self.request.method == 'GET':
            student_id = self.request.query_params.get('student_id')
            if student_id:
                return Notification.objects.filter(recipient_id=student_id)
            return Notification.objects.none()
        return super().get_queryset()

    def update(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})

class StudentCoursesView(APIView):
    def get(self, request, student_id):
        try:
            student = Student.objects.get(id=student_id)
            lessons = Lesson.objects.filter(classroom=student.class_id)
            
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
            
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

# Add this class at the end of the file
class StudentCommentViewSet(viewsets.ModelViewSet):
    queryset = StudentComment.objects.all()
    serializer_class = StudentCommentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        student_id = self.request.query_params.get('student', None)
        if student_id is not None:
            queryset = queryset.filter(student=student_id)
        return queryset.order_by('-created_at')  # Most recent comments first


class BulkCommentView(APIView):
    def post(self, request):
        class_id = request.data.get('class_id')
        content = request.data.get('content')
        teacher_id = request.data.get('teacher')  # Assuming the teacher is authenticated
        teacher = Teacher.objects.filter(id=teacher_id).first()
        if not class_id or not content:
            return Response({'error': 'Class ID and content are required'}, status=status.HTTP_400_BAD_REQUEST)

        students = Student.objects.filter(class_id=class_id)
        comments = []
        print(students)
        for student in students:
            comment = StudentComment(student=student, teacher=teacher, content=content)
            comment.save()
            comments.append(comment)

        serializer = StudentCommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class HomeworkViewSet(viewsets.ModelViewSet):
    queryset = Homework.objects.all()
    serializer_class = HomeworkSerializer
    
    def get_queryset(self):
        queryset = Homework.objects.all()
        classroom_id = self.request.query_params.get('classroom', None)
        student_id = self.request.query_params.get('student', None)
        
        if classroom_id:
            queryset = queryset.filter(classroom=classroom_id)
        
        if student_id:
            # Get the student's classroom
            try:
                student = Student.objects.get(id=student_id)
                queryset = queryset.filter(classroom=student.class_id)
            except Student.DoesNotExist:
                return Homework.objects.none()
                
        return queryset.order_by('-due_date')  # Most recent due dates first


# Add to views.py after HomeworkViewSet
class HomeworkSubmissionViewSet(viewsets.ModelViewSet):
    queryset = HomeworkSubmission.objects.all()
    serializer_class = HomeworkSubmissionSerializer
    
    def get_queryset(self):
        queryset = HomeworkSubmission.objects.all()
        homework_id = self.request.query_params.get('homework', None)
        student_id = self.request.query_params.get('student', None)
        
        if homework_id:
            queryset = queryset.filter(homework=homework_id)
        
        if student_id:
            queryset = queryset.filter(student=student_id)
                
        return queryset


# Add these new ViewSets
class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    
    def get_queryset(self):
        queryset = Subject.objects.all()
        classroom_id = self.request.query_params.get('classroom', None)
        if classroom_id is not None:
            queryset = queryset.filter(classroom=classroom_id)
        return queryset

class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    
    def perform_create(self, serializer):
        # Automatically set the recorded_by field to the current admin
        # You'll need to implement proper authentication to get the admin user
        serializer.save(recorded_by_id=1)  # Replace with actual admin ID from token
    
    def get_queryset(self):
        queryset = Grade.objects.select_related('student', 'subject', 'recorded_by')
        classroom_id = self.request.query_params.get('classroom', None)
        student_id = self.request.query_params.get('student', None)
        subject_id = self.request.query_params.get('subject', None)
        
        if classroom_id is not None:
            queryset = queryset.filter(subject__classroom=classroom_id)
        if student_id is not None:
            queryset = queryset.filter(student=student_id)
        if subject_id is not None:
            queryset = queryset.filter(subject=subject_id)
            
        return queryset

class GradeTableView(APIView):
    """View for getting the complete grade table for a classroom"""
    
    def get(self, request, classroom_id):
        try:
            classroom = ClassRoom.objects.get(id=classroom_id)
            subjects = Subject.objects.filter(classroom=classroom)
            students = Student.objects.filter(class_id=classroom)
            grades = Grade.objects.filter(
                subject__classroom=classroom
            ).select_related('student', 'subject', 'recorded_by')
            
            data = {
                'classroom_id': classroom_id,
                'classroom_name': classroom.name,
                'subjects': subjects,
                'students': students,
                'grades': grades
            }
            
            serializer = GradeTableSerializer(data)
            return Response(serializer.data)
            
        except ClassRoom.DoesNotExist:
            return Response(
                {'error': 'Classroom not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class BulkGradeCreateView(APIView):
    """View for creating multiple grades at once"""
    
    def post(self, request):
        grades_data = request.data.get('grades', [])
        created_grades = []
        errors = []
        
        for grade_data in grades_data:
            serializer = GradeSerializer(data=grade_data)
            if serializer.is_valid():
                grade = serializer.save(recorded_by_id=1)  # Replace with actual admin ID
                created_grades.append(GradeSerializer(grade).data)
            else:
                errors.append({
                    'data': grade_data,
                    'errors': serializer.errors
                })
        
        return Response({
            'created_grades': created_grades,
            'errors': errors,
            'success_count': len(created_grades),
            'error_count': len(errors)
        })
