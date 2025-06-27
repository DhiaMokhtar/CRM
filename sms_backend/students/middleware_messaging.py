import jwt
from django.conf import settings

class JWTUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract JWT token from Authorization header or cookies
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        elif 'auth_token' in request.COOKIES:
            token = request.COOKIES.get('auth_token')
        
        if token:
            try:
                # Decode the JWT token
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                
                # Add user information to the request object
                request.user_type = payload.get('user_type')
                request.user_id = payload.get('user_id')
                request.username = payload.get('username')
            except jwt.ExpiredSignatureError:
                # Token has expired
                pass
            except jwt.InvalidTokenError:
                # Invalid token
                pass
        
        response = self.get_response(request)
        return response