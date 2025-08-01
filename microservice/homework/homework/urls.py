from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'homework', views.HomeworkViewSet)
router.register(r'homework-submissions', views.HomeworkSubmissionViewSet)
router.register(r'student-comments', views.StudentCommentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('students/<int:student_id>/homework/', views.StudentHomeworkView.as_view(), name='student-homework'),
    path('comments/bulk/', views.BulkCommentView.as_view(), name='bulk-comments'),
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
]