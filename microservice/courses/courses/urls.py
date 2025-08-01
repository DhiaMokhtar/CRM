from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'lessons', views.LessonViewSet)
router.register(r'chapters', views.ChapterViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'subjects', views.SubjectViewSet)  # Add this
router.register(r'grades', views.GradeViewSet)      # Add this

urlpatterns = [
    path('', include(router.urls)),
    path('classes/<int:classroom_id>/grade-table/', views.GradeTableView.as_view(), name='grade-table'),  # Add this
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
]