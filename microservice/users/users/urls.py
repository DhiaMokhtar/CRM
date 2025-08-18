from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views  # Add this import

router = DefaultRouter()
router.register(r'administrators', views.AdministratorViewSet)
router.register(r'teachers', views.TeacherViewSet)
router.register(r'students', views.StudentViewSet)
router.register(r'parents', views.ParentViewSet)
router.register(r'classes', views.ClassRoomViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('search/users/', views.UserSearchView.as_view(), name='user-search'),
    path('health/', views.HealthCheckView.as_view(), name='health'),
    path('classes/<int:class_id>/students/', views.ClassStudentsView.as_view(), name='class-students'),
    path('parents/<int:parent_id>/children/', views.ParentChildrenView.as_view(), name='parent-children'),
    path('classrooms/<int:classroom_id>/students/', views.ClassroomStudentsView.as_view(), name='classroom-students'),
]