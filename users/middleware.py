# middleware.py
class RedirectToPreviousMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Lưu trữ đường dẫn hiện tại nếu không phải là trang auth
        if (not request.path.startswith('/login/') and 
            not request.path.startswith('/register/') and
            not request.path.startswith('/admin/') and
            not request.path.startswith('/static/') and
            not request.path.startswith('/media/') and
            request.method == 'GET'):
            request.session['next_url'] = request.get_full_path()
        
        response = self.get_response(request)
        return response