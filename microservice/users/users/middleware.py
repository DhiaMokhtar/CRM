class DisableHostCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip host validation by removing the host header check
        request.META['HTTP_HOST'] = 'localhost'
        response = self.get_response(request)
        return response