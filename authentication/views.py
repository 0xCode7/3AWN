import random
from datetime import timedelta
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.exceptions import TokenError
from .serializers import RegisterSerializer, UserSerializer, LoginSerializer, ForgotPasswordSerializer, \
    ResetPasswordSerializer, PatientSerializer, CarePersonSerializer, LogoutSerializer
from django.contrib.auth import get_user_model
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.generics import GenericAPIView
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

User = get_user_model()


# Create your views here.
@extend_schema(tags=["Authentication"])
class RegisterView(generics.CreateAPIView):
    """
        POST register → Create User
    """

    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            "message": "User created successfully",
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Authentication"])
class LoginView(GenericAPIView):
    serializer_class = LoginSerializer  # ✅ important

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        return Response({
            "success": True,
            "message": "Login successful",
            "user": data["user"],
            "tokens": data["tokens"],
        }, status=status.HTTP_200_OK)


@extend_schema(tags=["Authentication"])
class LogoutView(GenericAPIView):
    serializer_class = LogoutSerializer  # dummy, so schema works
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logged out successfully"}, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Authentication"])
class ProfileView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request):
        user = request.user

        if user.role == 'patient':
            profile = getattr(user, "patient_profile", None)
            profile_data = PatientSerializer(profile).data if profile else None

        elif user.role == 'careperson':
            profile = getattr(user, "careperson_profile", None)
            profile_data = CarePersonSerializer(profile).data if profile else None

        else:
            profile_data = None

        return Response({
            "user": UserSerializer(user).data,
            "profile": profile_data,
            "role": user.role
        })


@extend_schema(tags=["Authentication"])
class ForgotPasswordView(GenericAPIView):
    serializer_class = ForgotPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Email not found"}, status=status.HTTP_404_NOT_FOUND)

        code = str(random.randint(1000, 9999))
        user.reset_code = code
        user.save()

        # TODO: send code via email

        return Response(
            {"message": "Reset code sent to your email"},
            status=status.HTTP_200_OK
        )


@extend_schema(tags=["Authentication"])
class ResetPasswordView(APIView):
    serializer_class = ResetPasswordSerializer

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        # Validate token
        try:
            token = AccessToken(validated_data['reset_token'])
        except Exception:
            return Response({"error": "Invalid or expired reset token"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(id=token['user_id']).first()

        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(validated_data["password"])
        user.reset_code = None
        user.reset_token = None
        user.save()

        return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)


@extend_schema(tags=["Authentication"])
class TokenRefreshView(TokenRefreshView):
    pass
