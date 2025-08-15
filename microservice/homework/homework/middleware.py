import jwt
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)

class JWTMiddleware(MiddlewareMixin):
    """JWT Authentication Middleware for homework service"""
    
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
        
        # Fallback to cookies - be more flexible with cookie names
        if not token:
            token = request.COOKIES.get('auth_token') or request.COOKIES.get('authToken')
        
        # Debug logging for SSL/cookie issues
        logger.debug(f"[JWTMiddleware] Path: {request.path}")
        logger.debug(f"[JWTMiddleware] All cookies: {list(request.COOKIES.keys())}")
        logger.debug(f"[JWTMiddleware] Token found: {bool(token)}")
        logger.debug(f"[JWTMiddleware] User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
        logger.debug(f"[JWTMiddleware] Origin: {request.META.get('HTTP_ORIGIN', 'Unknown')}")
        
        # If no token found, return unauthorized for API endpoints
        if not token:
            if request.path.startswith('/api/'):
                logger.warning(f"[JWTMiddleware] No token found for {request.path}")
                logger.warning(f"[JWTMiddleware] Available cookies: {request.COOKIES}")
                return JsonResponse({'error': 'Authentication required'}, status=401)
            return None
        
        # Decode and validate token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            
            # Add user information to request
            request.user_id = payload.get('user_id')
            request.user_type = payload.get('user_type')  
            request.username = payload.get('username')
            
            logger.debug(f"[JWTMiddleware] Successfully authenticated: {request.username} ({request.user_type}) - ID: {request.user_id}")
            
        except jwt.ExpiredSignatureError:
            logger.warning(f"[JWTMiddleware] Token expired for {request.path}")
            return JsonResponse({'error': 'Token expired'}, status=401)
        except jwt.InvalidSignatureError:
            logger.error(f"[JWTMiddleware] Invalid signature for {request.path}")
            logger.error(f"[JWTMiddleware] SECRET_KEY preview: {settings.SECRET_KEY[:10]}...")
            return JsonResponse({'error': 'Invalid token'}, status=401)
        except jwt.InvalidTokenError as e:
            logger.error(f"[JWTMiddleware] Invalid token for {request.path}: {str(e)}")
            logger.error(f"[JWTMiddleware] Token preview: {token[:20] if len(token) > 20 else token}...")
            return JsonResponse({'error': 'Invalid token'}, status=401)
        except Exception as e:
            logger.error(f"[JWTMiddleware] Unexpected error for {request.path}: {str(e)}")
            return JsonResponse({'error': 'Authentication failed'}, status=401)
        
        return None