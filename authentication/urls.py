from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .views import ForgotPasswordView, ResetPasswordView, ProfileView

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('token/refresh/', TokenRefreshView.as_view(), name='refresh_token'),
    path("forgot_password/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("reset_password/", ResetPasswordView.as_view(), name="reset_password"),

    # path('', include('dj_rest_auth.urls')), # password reset/change
    #
    # path('', include('django.contrib.auth.urls')),

]
