from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'homework', views.HomeworkViewSet)
router.register(r'homework-submissions', views.HomeworkSubmissionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('students/<int:student_id>/homework/', views.StudentHomeworkView.as_view(), name='student-homework'),
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
]