from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Add to imports

from .views import (
    AdminLoginView, 
    AdministratorViewSet,
    BulkGradeCreateView,
    GradeTableView,
    GradeViewSet,
    SubjectViewSet, 
    TeacherViewSet, 
    StudentViewSet, 
    ClassRoomViewSet,
    ClassStudentsView,
    ParentViewSet,
    ParentChildrenView,
    LessonViewSet,
    ChapterViewSet,
    CourseViewSet,
    StudentCoursesView,
    StudentCommentViewSet ,
    BulkCommentView,
    HomeworkViewSet,
    HomeworkSubmissionViewSet,
    NotificationViewSet
)

from .views_messaging import (
    MessageViewSet,
    ConversationViewSet,
    UserSearchView
)
from .views_calendar import ScheduleViewSet

# Add this to your urlpatterns

router = DefaultRouter()
router.register(r'schedules', ScheduleViewSet)
router.register(r'administrators', AdministratorViewSet)
router.register(r'teachers', TeacherViewSet)
router.register(r'students', StudentViewSet)
router.register(r'classes', ClassRoomViewSet)
router.register(r'parents', ParentViewSet)
router.register(r'subjects', SubjectViewSet)  # Add this line
router.register(r'grades', GradeViewSet)      # Add this line
router.register(r'lessons', LessonViewSet)
router.register(r'chapters', ChapterViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'student-comments', StudentCommentViewSet)
router.register(r'homeworks', HomeworkViewSet)
router.register(r'homework-submissions', HomeworkSubmissionViewSet)
router.register(r'messages', MessageViewSet)
router.register(r'conversations', ConversationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('admin-login/', AdminLoginView.as_view(), name='admin-login'),
    path('classes/<int:class_id>/students/', ClassStudentsView.as_view(), name='class-students'),
    path('parents/<int:parent_id>/children/', ParentChildrenView.as_view(), name='parent-children'),
    path('students/<int:student_id>/courses/', StudentCoursesView.as_view(), name='student-courses'),
    path('comments/bulk/', BulkCommentView.as_view(), name='bulk-comments'),
    path('classes/<int:classroom_id>/grade-table/', GradeTableView.as_view(), name='grade-table'),
    path('grades/bulk-create/', BulkGradeCreateView.as_view(), name='bulk-grade-create'),
    # Add this to your existing URL patterns
 
    
    # In your urlpatterns, add:
    path('notifications/', NotificationViewSet.as_view({'get': 'list'}), name='notification-list'),
    path('notifications/<int:pk>/', NotificationViewSet.as_view({'put': 'update'}), name='notification-detail'),
    
    # Messaging endpoints
    path('search-users/', UserSearchView.as_view(), name='search-users'),
     
]
