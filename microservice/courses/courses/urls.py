from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'lessons', views.LessonViewSet)
router.register(r'chapters', views.ChapterViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'subjects', views.SubjectViewSet)
router.register(r'grades', views.GradeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('classes/<int:classroom_id>/grade-table/', views.GradeTableView.as_view(), name='grade-table'),
    path('students/<int:student_id>/courses/', views.StudentCoursesView.as_view(), name='student-courses'),  # Add this line
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
]