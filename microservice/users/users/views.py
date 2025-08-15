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
                        secure=True,      # Changed to True for HTTPS
                        samesite='None'   # Changed to None for cross-site
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
    def get(self, request):
        query = request.query_params.get('q', '')
        user_type = request.query_params.get('type', None)
        
        print(f"[Users UserSearchView] Query: '{query}', Type: '{user_type}'")
        
        if len(query) < 2:
            return Response([])
        
        users = []
        
        # Search teachers
        teachers = Teacher.objects.filter(
            username__icontains=query
        ).values('id', 'username', 'email')
        for teacher in teachers:
            users.append({
                'id': teacher['id'],
                'username': teacher['username'],
                'name': teacher['username'],
                'type': 'teacher',
                'email': teacher['email'],
                'class_name': None
            })
        
        # Search students
        students = Student.objects.filter(
            username__icontains=query
        ).select_related('class_id').values(
            'id', 'username', 'email', 'class_id__name'
        )
        for student in students:
            users.append({
                'id': student['id'],
                'username': student['username'],
                'name': student['username'],
                'type': 'student',
                'email': student['email'],
                'class_name': student['class_id__name']
            })
        
        # Search parents
        parents = Parent.objects.filter(
            username__icontains=query
        ).values('id', 'username', 'email')
        for parent in parents:
            users.append({
                'id': parent['id'],
                'username': parent['username'],
                'name': parent['username'],
                'type': 'parent',
                'email': parent['email'],
                'class_name': None
            })
        
        print(f"[Users UserSearchView] Found {len(users)} users")
        return Response(users)

class HealthCheckView(APIView):
    def get(self, request):
        return Response({'status': 'healthy'}, status=status.HTTP_200_OK)
