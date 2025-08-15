from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from django.utils import timezone
from .models import Homework, HomeworkSubmission, StudentComment, Schedule
from .serializers import HomeworkSerializer, HomeworkSubmissionSerializer, StudentCommentSerializer, ScheduleSerializer
from datetime import datetime, timedelta
import requests
import logging

logger = logging.getLogger(__name__)

class HomeworkViewSet(viewsets.ModelViewSet):
    queryset = Homework.objects.all()
    serializer_class = HomeworkSerializer
    
    def get_queryset(self):
        queryset = Homework.objects.all()
        
        # Filter by classroom
        classroom_id = self.request.query_params.get('classroom', None)
        if classroom_id:
            queryset = queryset.filter(classroom_id=classroom_id)
        
        # Filter by teacher
        teacher_id = self.request.query_params.get('teacher', None)
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        
        # Filter by student (get homework for student's classroom)
        student_id = self.request.query_params.get('student', None)
        if student_id:
            # Get student's classroom from users microservice
            classroom_id = self._get_student_classroom(student_id)
            if classroom_id:
                queryset = queryset.filter(classroom_id=classroom_id)
            else:
                return Homework.objects.none()
        
        return queryset.order_by('-created_at')
    
    def _get_student_classroom(self, student_id):
        """Get student's classroom from users microservice"""
        try:
            service_urls = [
                f"https://users_service:8000/api/students/{student_id}/",
                f"https://localhost:8001/api/students/{student_id}/",
            ]
            
            for url in service_urls:
                try:
                    response = requests.get(url, timeout=3, verify=False)
                    if response.status_code == 200:
                        student_data = response.json()
                        return student_data.get('class_id')
                except Exception:
                    continue
            
            return None
        except Exception as e:
            logger.warning(f"Error fetching student classroom: {str(e)}")
            return None
    
    @action(detail=True, methods=['get'])
    def submissions(self, request, pk=None):
        """Get all submissions for a homework"""
        homework = self.get_object()
        submissions = homework.submissions.all()
        serializer = HomeworkSubmissionSerializer(submissions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_class(self, request):
        """Get homework assignments by classroom"""
        classroom_id = request.query_params.get('classroom_id')
        if not classroom_id:
            return Response({'error': 'classroom_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        homework = self.get_queryset().filter(classroom_id=classroom_id)
        serializer = self.get_serializer(homework, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        logger.debug("[HomeworkViewSet.create] DATA=%s", dict(request.data))
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            obj = serializer.save()
            logger.debug("[HomeworkViewSet.create] Created id=%s", obj.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning("[HomeworkViewSet.create] Errors=%s", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class HomeworkSubmissionViewSet(viewsets.ModelViewSet):
    queryset = HomeworkSubmission.objects.all()
    serializer_class = HomeworkSubmissionSerializer
    
    def get_queryset(self):
        queryset = HomeworkSubmission.objects.all()
        
        # Filter by homework
        homework_id = self.request.query_params.get('homework', None)
        if homework_id:
            queryset = queryset.filter(homework_id=homework_id)
        
        # Filter by student
        student_id = self.request.query_params.get('student', None)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        return queryset.order_by('-submission_date')
    
    def create(self, request, *args, **kwargs):
        """Create or update homework submission"""
        homework_id = request.data.get('homework')
        student_id = request.data.get('student_id')
        
        # Check if submission already exists
        existing_submission = HomeworkSubmission.objects.filter(
            homework_id=homework_id, 
            student_id=student_id
        ).first()
        
        if existing_submission:
            # Update existing submission
            serializer = self.get_serializer(existing_submission, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Create new submission
            return super().create(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def grade(self, request, pk=None):
        """Grade a homework submission"""
        submission = self.get_object()
        grade = request.data.get('grade')
        graded_by = request.data.get('graded_by')
        
        if grade is None:
            return Response({'error': 'Grade is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        submission.grade = grade
        submission.graded_by = graded_by
        submission.graded_at = timezone.now()
        submission.save()
        
        serializer = self.get_serializer(submission)
        return Response(serializer.data)

# Add Student Comment ViewSet
class StudentCommentViewSet(viewsets.ModelViewSet):
    queryset = StudentComment.objects.all()
    serializer_class = StudentCommentSerializer
    
    def get_queryset(self):
        queryset = StudentComment.objects.all()
        
        # Filter by student
        student_id = self.request.query_params.get('student', None)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        # Filter by teacher
        teacher_id = self.request.query_params.get('teacher', None)
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        
        return queryset.order_by('-created_at')

class BulkCommentView(APIView):
    """Add comments to all students in a classroom"""
    
    def post(self, request):
        classroom_id = request.data.get('classroom_id')
        content = request.data.get('content')
        teacher_id = request.data.get('teacher_id')
        
        if not all([classroom_id, content, teacher_id]):
            return Response({
                'error': 'classroom_id, content, and teacher_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get students from users microservice
            students = self._get_classroom_students(classroom_id)
            
            if not students:
                return Response({
                    'error': 'No students found in this classroom'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Create comments for all students
            comments = []
            for student in students:
                comment = StudentComment.objects.create(
                    student_id=student['id'],
                    teacher_id=teacher_id,
                    content=content
                )
                comments.append(comment)
            
            serializer = StudentCommentSerializer(comments, many=True)
            return Response({
                'message': f'Comments added to {len(comments)} students',
                'comments': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating bulk comments: {str(e)}")
            return Response({
                'error': 'Failed to create comments'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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

class StudentHomeworkView(APIView):
    """Get homework assignments for a specific student"""
    
    def get(self, request, student_id):
        try:
            # Get student's classroom from users microservice
            classroom_id = self._get_student_classroom(student_id)
            if not classroom_id:
                return Response({'error': 'Student classroom not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Get homework for the classroom
            homework_assignments = Homework.objects.filter(classroom_id=classroom_id)
            
            # Serialize with submission status
            result = []
            for hw in homework_assignments:
                hw_data = HomeworkSerializer(hw).data
                
                # Check if student has submitted
                submission = HomeworkSubmission.objects.filter(
                    homework=hw, 
                    student_id=student_id
                ).first()
                
                if submission:
                    hw_data['submission'] = HomeworkSubmissionSerializer(submission).data
                else:
                    hw_data['submission'] = None
                
                result.append(hw_data)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting student homework: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_student_classroom(self, student_id):
        """Get student's classroom from users microservice"""
        try:
            service_urls = [
                f"https://users_service:8000/api/students/{student_id}/",
                f"https://localhost:8001/api/students/{student_id}/",
            ]
            
            for url in service_urls:
                try:
                    response = requests.get(url, timeout=3, verify=False)
                    if response.status_code == 200:
                        student_data = response.json()
                        return student_data.get('class_id')
                except Exception:
                    continue
            
            return None
        except Exception as e:
            logger.warning(f"Error fetching student classroom: {str(e)}")
            return None

class HealthCheckView(APIView):
    """Health check endpoint"""
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'homework'
        })

class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    
    def get_queryset(self):
        queryset = Schedule.objects.all()
        
        # Filter by classroom
        classroom_id = self.request.query_params.get('classroom', None)
        if classroom_id:
            queryset = queryset.filter(classroom_id=classroom_id)
        
        # Filter by teacher
        teacher_id = self.request.query_params.get('teacher', None)
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        
        # Filter by schedule type
        schedule_type = self.request.query_params.get('type', None)
        if schedule_type:
            queryset = queryset.filter(schedule_type=schedule_type)
        
        return queryset.order_by('start_datetime')

class ScheduleWeeklyView(APIView):
    """Get schedules for a specific week"""
    
    def get(self, request):
        week_start = request.query_params.get('week_start')
        if not week_start:
            return Response({'error': 'week_start parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            start_date = datetime.strptime(week_start, '%Y-%m-%d')
            end_date = start_date + timedelta(days=7)
            
            schedules = Schedule.objects.filter(
                start_datetime__gte=start_date,
                start_datetime__lt=end_date
            ).order_by('start_datetime')
            
            serializer = ScheduleSerializer(schedules, many=True)
            return Response({'schedules': serializer.data})
            
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in weekly schedule view: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ScheduleMonthlyView(APIView):
    """Get schedules for a specific month"""
    
    def get(self, request):
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        
        if not year or not month:
            return Response({'error': 'year and month parameters are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            year = int(year)
            month = int(month)
            
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            schedules = Schedule.objects.filter(
                start_datetime__gte=start_date,
                start_datetime__lt=end_date
            ).order_by('start_datetime')
            
            serializer = ScheduleSerializer(schedules, many=True)
            return Response({'schedules': serializer.data})
            
        except ValueError:
            return Response({'error': 'Invalid year or month'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in monthly schedule view: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
