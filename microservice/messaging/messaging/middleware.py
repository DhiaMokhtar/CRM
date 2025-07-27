import jwt
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)

class JWTMiddleware(MiddlewareMixin):
    """
    JWT Authentication Middleware for messaging service
    Extracts user information from JWT tokens and adds it to the request
    """
    
    def process_request(self, request):
        # Skip authentication for admin and health check endpoints
        skip_paths = ['/admin/', '/api/health/']
        
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Get token from Authorization header or cookies
        token = None
        
        # First try Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        # Fallback to cookies
        if not token:
            token = request.COOKIES.get('auth_token')
        
        # If no token found, return unauthorized for API endpoints
        if not token:
            if request.path.startswith('/api/'):
                logger.warning(f"No authentication token found for path: {request.path}")
                return JsonResponse(
                    {'error': 'Authentication required'}, 
                    status=401
                )
            return None
        
        # Decode and validate token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            
            # Add user information to request
            request.user_id = payload.get('user_id')
            request.user_type = payload.get('user_type')  
            request.username = payload.get('username')
            
            # Log successful authentication
            logger.info(f"Authenticated user: {request.username} ({request.user_type}) - ID: {request.user_id} (type: {type(request.user_id)})")
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return JsonResponse(
                {'error': 'Token expired'}, 
                status=401
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            return JsonResponse(
                {'error': 'Invalid token'}, 
                status=401
            )
        except Exception as e:
            logger.error(f"Unexpected error during JWT validation: {str(e)}")
            return JsonResponse(
                {'error': 'Authentication failed'}, 
                status=401
            )
        
        return None