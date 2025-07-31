from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from django.utils import timezone
from .models import Homework, HomeworkSubmission
from .serializers import HomeworkSerializer, HomeworkSubmissionSerializer
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
        student_id = request.data.get('student')
        
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
