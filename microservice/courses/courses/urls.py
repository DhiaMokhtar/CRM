from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'courses', views.CourseMaterialViewSet)
router.register(r'lessons', views.LessonViewSet)
router.register(r'chapters', views.ChapterViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('students/<int:student_id>/courses/', views.StudentCoursesView.as_view(), name='student-courses'),
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
]