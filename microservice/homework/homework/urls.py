from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'homework', views.HomeworkViewSet)
router.register(r'homework-submissions', views.HomeworkSubmissionViewSet)
router.register(r'student-comments', views.StudentCommentViewSet)
router.register(r'schedules', views.ScheduleViewSet)  # Add this

urlpatterns = [
    path('', include(router.urls)),
    path('bulk-comments/', views.BulkCommentView.as_view(), name='bulk-comments'),
    path('students/<int:student_id>/homework/', views.StudentHomeworkView.as_view(), name='student-homework'),
    path('schedules/weekly_view/', views.ScheduleWeeklyView.as_view(), name='schedule-weekly'),      # Add this
    path('schedules/monthly_view/', views.ScheduleMonthlyView.as_view(), name='schedule-monthly'),    # Add this
    path('health/', views.HealthCheckView.as_view(), name='health'),
]