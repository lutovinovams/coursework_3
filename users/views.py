import secrets
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from config import settings

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'username')

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.verification_code = secrets.token_hex(16)
        user.save()

        verify_url = f"http://127.0.0{user.verification_code}/"
        send_mail(
            subject="Подтверждение регистрации",
            message=f"Для подтверждения email перейдите по ссылке: {verify_url}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return super().form_valid(form)

class VerifyEmailView(View):
    def get(self, request, code):
        user = get_object_or_404(User, verification_code=code)
        user.is_active = True
        user.is_verified = True
        user.verification_code = None
        user.save()
        return render(request, 'users/verify_success.html')

class PasswordResetActionView(View):
    def get(self, request):
        return render(request, 'users/password_reset.html')

    def post(self, request):
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            new_password = secrets.token_urlsafe(10)
            user.set_password(new_password)
            user.save()

            send_mail(
                subject="Восстановление пароля",
                message=f"Ваш новый временный пароль для входа: {new_password}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return render(request, 'users/password_reset_done.html', {'success': True})
        except User.DoesNotExist:
            return render(request, 'users/password_reset.html', {'error': "Пользователь с таким Email не найден."})

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Контроллер просмотра всех пользователей сервиса менеджером."""
    model = User
    template_name = 'users/user_list.html'

    def test_func(self):
        return self.request.user.groups.filter(name='Manager').exists()

class UserToggleBlockView(LoginRequiredMixin, View):
    """Контроллер блокировки и разблокировки аккаунтов пользователей менеджером."""
    def post(self, request, pk):
        if not request.user.groups.filter(name='Manager').exists():
            raise PermissionDenied("Только менеджеры могут блокировать пользователей.")
        user = get_object_or_404(User, pk=pk)
        if user.is_superuser:
            raise PermissionDenied("Невозможно заблокировать суперпользователя.")
        user.is_active = not user.is_active
        user.save()
        return redirect('users:user_list')
