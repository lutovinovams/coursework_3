from django.contrib.auth import views as auth_views
from django.urls import path
from users import views

app_name = 'users'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify/<str:code>/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('password-reset/', views.PasswordResetActionView.as_view(), name='password_reset'),
    path('users-list/', views.UserListView.as_view(), name='user_list'),
    path('users-list/<int:pk>/block/', views.UserToggleBlockView.as_view(), name='user_block'),
]
