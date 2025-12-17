from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
import requests

API_ROOT = "http://localhost:8000"
TIMEOUT = 5


class RegisterPageView(View):
    template_name = 'registration/register.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        email = request.POST.get('email')

        if not username or not password:
            messages.error(request, 'Please provide username and password')
            return render(request, self.template_name, {
                'username': username,
                'email': email,
            })
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, self.template_name, {
                'username': username,
                'email': email,
            })

        try:
            r = requests.post(f"{API_ROOT}/api/register/", json={
                'username': username,
                'password': password,
                'password2': password2,
                'email': email or ''
            }, timeout=TIMEOUT)
        except requests.RequestException:
            messages.error(request, 'Registration service is unavailable')
            return render(request, self.template_name)

        if r.status_code in (200, 201):
            messages.success(request, 'Registration successful. Please sign in.')
            return redirect('login')
        else:
            try:
                data = r.json()
            except Exception:
                data = {}
            non_field = data.get('detail') or data
            messages.error(request, f'Registration failed: {non_field}')
            return render(request, self.template_name, {
                'username': username,
                'email': email,
            })


class SiteLoginView(LoginView):
    """
    Custom login that also obtains JWT tokens and stores them in session
    for subsequent API calls.
    """

    template_name = 'registration/login.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        try:
            r = requests.post(f"{API_ROOT}/api/token/", json={
                'username': username,
                'password': password,
            }, timeout=TIMEOUT)
            if r.status_code == 200:
                data = r.json()
                self.request.session['jwt_access'] = data.get('access')
                self.request.session['jwt_refresh'] = data.get('refresh')
            else:
                messages.warning(self.request, 'Signed in, but failed to obtain API token')
        except requests.RequestException:
            messages.warning(self.request, 'Signed in, but token service is unavailable')
        return response


class SiteLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        request.session.pop('jwt_access', None)
        request.session.pop('jwt_refresh', None)
        return super().dispatch(request, *args, **kwargs)
