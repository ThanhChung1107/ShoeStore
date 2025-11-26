# middleware.py
class RedirectToPreviousMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Lưu trữ đường dẫn hiện tại nếu không phải là trang auth
        if (
            request.method == 'GET'
            and not request.user.is_authenticated  # Chỉ lưu khi chưa đăng nhập
            and not request.path.startswith('/login/')
            and not request.path.startswith('/register/')
            and not request.path.startswith('/logout/')
            and not request.path.startswith('/admin/')
            and not request.path.startswith('/static/')
            and not request.path.startswith('/media/')
            and request.path != '/favicon.ico'
        ):
            # Chỉ lưu next_url an toàn (bắt đầu bằng '/')
            full_path = request.get_full_path()
            if full_path.startswith('/'):
                request.session['next_url'] = full_path
        
        response = self.get_response(request)
        return response