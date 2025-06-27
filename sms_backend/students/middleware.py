import jwt
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .models import Administrator, Teacher, Student

class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Skip authentication for login endpoint
        if request.path == '/api/admin-login/':
            return None
            
        # Get token from cookie or Authorization header
        token = request.COOKIES.get('auth_token')
        if not token:
            auth_header = request.META.get('HTTP_AUTHORIZATION')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if token:
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                request.user_id = payload['user_id']
                request.user_type = payload['user_type']
                request.username = payload['username']
            except jwt.ExpiredSignatureError:
                return JsonResponse({'error': 'Token expired'}, status=401)
            except jwt.InvalidTokenError:
                return JsonResponse({'error': 'Invalid token'}, status=401)
        
        return None