from django.shortcuts import render
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.hashers import check_password
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.db.models import Q
from .models import Administrator, Teacher, Student, Parent, ClassRoom
from .serializers import (
    AdministratorSerializer, TeacherSerializer, 
    StudentSerializer, ParentSerializer, ClassRoomSerializer
)

class AdministratorViewSet(viewsets.ModelViewSet):
    queryset = Administrator.objects.all()
    serializer_class = AdministratorSerializer
    
    def get_queryset(self):
        queryset = Administrator.objects.all()
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                Q(username__icontains=search) | 
                Q(email__icontains=search)
            )
        return queryset

class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    
    def get_queryset(self):
        queryset = Teacher.objects.all()
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                Q(username__icontains=search) | 
                Q(email__icontains=search)
            )
        return queryset

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    
    def get_queryset(self):
        queryset = Student.objects.all()
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                Q(username__icontains=search) | 
                Q(email__icontains=search)
            )
        return queryset

class ParentViewSet(viewsets.ModelViewSet):
    queryset = Parent.objects.all()
    serializer_class = ParentSerializer
    
    def get_queryset(self):
        queryset = Parent.objects.all()
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                Q(username__icontains=search) | 
                Q(email__icontains=search)
            )
        return queryset

class ClassRoomViewSet(viewsets.ModelViewSet):
    queryset = ClassRoom.objects.all()
    serializer_class = ClassRoomSerializer

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        print(f"Login attempt - Username: {username}, Password provided: {bool(password)}")

        if not username or not password:
            return Response({
                'error': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Try each user type
        user_types = [
            (Administrator, 'admin'),
            (Teacher, 'teacher'),
            (Student, 'student'),
            (Parent, 'parent')
        ]
        
        for model, user_type in user_types:
            try:
                print(f"Trying {user_type} model...")
                user = model.objects.get(username=username)
                print(f"Found user: {user.username}, Password hash: {user.password[:20]}...")
                
                if check_password(password, user.password):
                    print(f"Password check successful for {user_type}")
                    payload = {
                        'user_id': user.id,
                        'user_type': user_type,
                        'username': user.username,
                        'exp': datetime.utcnow() + timedelta(hours=24)
                    }
                    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
                    
                    response = Response({
                        'message': 'Login successful',
                        'user_type': user_type,
                        'user_id': user.id,
                        'username': user.username,
                        'token': token
                    }, status=status.HTTP_200_OK)
                    
                    response.set_cookie(
                        'auth_token',
                        token,
                        max_age=86400,
                        httponly=True,
                        secure=False,
                        samesite='Lax'
                    )
                    return response
                else:
                    print(f"Password check failed for {user_type}")
            except model.DoesNotExist:
                print(f"User not found in {user_type} model")
                continue

        print("All login attempts failed")
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def logout_view(request):
    response = Response({'message': 'Logged out successfully'})
    response.delete_cookie('auth_token')
    return response

class ClassStudentsView(APIView):
    def get(self, request, class_id):
        try:
            classroom = ClassRoom.objects.get(id=class_id)
            students = Student.objects.filter(class_id=classroom)
            serializer = StudentSerializer(students, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ClassRoom.DoesNotExist:
            return Response(
                {'error': 'Class not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class ParentChildrenView(APIView):
    def get(self, request, parent_id):
        try:
            parent = Parent.objects.get(id=parent_id)
            children = parent.students.all()
            serializer = StudentSerializer(children, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Parent.DoesNotExist:
            return Response(
                {'error': 'Parent not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class UserSearchView(APIView):
    """Search users across all user types"""
    
    def get(self, request):
        query = request.query_params.get('q', '')
        user_type = request.query_params.get('type', None)
        
        if not query or len(query.strip()) < 2:
            return Response([])
        
        results = []
        
        # Search administrators
        if not user_type or user_type == 'administrator':
            admins = Administrator.objects.filter(
                Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
            )[:10]
            results.extend([{
                'id': admin.id,
                'username': admin.username,
                'first_name': admin.first_name,
                'last_name': admin.last_name,
                'name': f"{admin.first_name} {admin.last_name}".strip() or admin.username,
                'type': 'administrator',
                'email': admin.email
            } for admin in admins])
        
        # Search teachers
        if not user_type or user_type == 'teacher':
            teachers = Teacher.objects.filter(
                Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
            )[:10]
            results.extend([{
                'id': teacher.id,
                'username': teacher.username,
                'first_name': teacher.first_name,
                'last_name': teacher.last_name,
                'name': f"{teacher.first_name} {teacher.last_name}".strip() or teacher.username,
                'type': 'teacher',
                'email': teacher.email
            } for teacher in teachers])
        
        # Search students
        if not user_type or user_type == 'student':
            students = Student.objects.filter(
                Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
            )[:10]
            results.extend([{
                'id': student.id,
                'username': student.username,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'name': f"{student.first_name} {student.last_name}".strip() or student.username,
                'type': 'student',
                'class_name': student.class_id.name if student.class_id else None,
                'email': student.email
            } for student in students])
        
        # Search parents
        if not user_type or user_type == 'parent':
            parents = Parent.objects.filter(
                Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
            )[:10]
            results.extend([{
                'id': parent.id,
                'username': parent.username,
                'first_name': parent.first_name,
                'last_name': parent.last_name,
                'name': f"{parent.first_name} {parent.last_name}".strip() or parent.username,
                'type': 'parent',
                'email': parent.email
            } for parent in parents])
        
        return Response(results)

class HealthCheckView(APIView):
    """Health check endpoint for users microservice"""
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'users'
        })
