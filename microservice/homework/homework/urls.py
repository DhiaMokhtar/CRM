from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'homework', views.HomeworkViewSet)
router.register(r'homework-submissions', views.HomeworkSubmissionViewSet)
router.register(r'student-comments', views.StudentCommentViewSet)
router.register(r'schedules', views.ScheduleViewSet)

urlpatterns = [
    path('bulk-comments/', views.BulkCommentView.as_view(), name='bulk-comments'),
    path('students/<int:student_id>/homework/', views.StudentHomeworkView.as_view(), name='student-homework'),
    path('schedule-views/weekly/', views.ScheduleWeeklyView.as_view(), name='schedule-weekly'),
    path('schedule-views/monthly/', views.ScheduleMonthlyView.as_view(), name='schedule-monthly'),
    path('health/', views.HealthCheckView.as_view(), name='health'),
    path('', include(router.urls)),  # Move this to the end
]