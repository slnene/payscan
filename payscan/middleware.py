# middleware.py
from django.http import HttpResponse
from django_ratelimit.exceptions import Ratelimited 
from django.http import HttpResponseForbidden
import requests

class RestrictIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_ip = request.META.get('REMOTE_ADDR')
        if not self.is_ip_from_eswatini(user_ip):
            return HttpResponseForbidden("Access restricted to users in Eswatini.")
        response = self.get_response(request)
        return response

    def is_ip_from_eswatini(self, ip):
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}")
            data = response.json()
            return data['country'] == 'Eswatini'
        except Exception as e:
            return False




