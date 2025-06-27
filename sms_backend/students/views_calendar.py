from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from datetime import datetime, timedelta
from django.utils import timezone

from .models import Schedule, ScheduleNotification, ClassRoom, Teacher, Student, Parent,Administrator
from .serializers import ScheduleSerializer, ScheduleNotificationSerializer

class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    
    def get_queryset(self):
        if not hasattr(self.request, 'user_type') or not hasattr(self.request, 'user_id'):
            return Schedule.objects.none()
        
        user_type = self.request.user_type
        user_id = self.request.user_id
        
        if user_type == 'admin':
            # Admins can see all schedules
            return Schedule.objects.all()
        elif user_type == 'teacher':
            # Teachers can see schedules for their classes
            teacher = Teacher.objects.get(id=user_id)
            return Schedule.objects.filter(classroom__in=teacher.classes.all())
        elif user_type == 'student':
            # Students can see schedules for their class
            student = Student.objects.get(id=user_id)
            return Schedule.objects.filter(classroom=student.class_id)
        elif user_type == 'parent':
            # Parents can see schedules for their children's classes
            parent = Parent.objects.get(id=user_id)
            student_classes = parent.students.values_list('class_id', flat=True)
            return Schedule.objects.filter(classroom__in=student_classes)
        
        return Schedule.objects.none()
    
    def perform_create(self, serializer):
        user_type = self.request.data.get('user_type')
        if user_type != 'admin':
            raise PermissionError("Only administrators can create schedules")
        
        user_id = self.request.data.get('user_id')
        print(user_id)
        admin = Administrator.objects.get(id=user_id)
        serializer.save(created_by=admin)
        
        # Create notifications for relevant users
        self._create_notifications(serializer.instance)
    
    def _create_notifications(self, schedule):
        # Notify teachers assigned to the classroom
        for teacher in schedule.classroom.teachers.all():
            ScheduleNotification.objects.get_or_create(
                schedule=schedule,
                recipient_type='teacher',
                recipient_id=teacher.id
            )
        
        # Notify students in the classroom
        for student in schedule.classroom.students.all():
            ScheduleNotification.objects.get_or_create(
                schedule=schedule,
                recipient_type='student',
                recipient_id=student.id
            )
        
        # Notify parents of students in the classroom
        for student in schedule.classroom.students.all():
            for parent in student.parents.all():
                ScheduleNotification.objects.get_or_create(
                    schedule=schedule,
                    recipient_type='parent',
                    recipient_id=parent.id
                )
    
    @action(detail=False, methods=['get'])
    def weekly_view(self, request):
        """Get schedules for a specific week"""
        week_start = request.query_params.get('week_start')
        if week_start:
            start_date = datetime.strptime(week_start, '%Y-%m-%d').date()
        else:
            start_date = timezone.now().date()
            start_date = start_date - timedelta(days=start_date.weekday())
        
        end_date = start_date + timedelta(days=6)
        
        schedules = Schedule.objects.filter(
            start_datetime__date__range=[start_date, end_date]
        )
        
        serializer = self.get_serializer(schedules, many=True)
        return Response({
            'week_start': start_date,
            'week_end': end_date,
            'schedules': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def monthly_view(self, request):
        """Get schedules for a specific month"""
        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))
        
        schedules = Schedule.objects.filter(
            start_datetime__year=year,
            start_datetime__month=month
        )
        
        serializer = self.get_serializer(schedules, many=True)
        return Response({
            'year': year,
            'month': month,
            'schedules': serializer.data
        })