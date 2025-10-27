import os, json, random
from datetime import timedelta
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.exceptions import TokenError
from .serializers import RegisterSerializer, UserSerializer, LoginSerializer, ForgotPasswordSerializer, \
    ResetPasswordSerializer, PatientSerializer, CarePersonSerializer
from django.contrib.auth import get_user_model
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.generics import GenericAPIView
from rest_framework import status
from rest_framework.views import APIView

User = get_user_model()


# Create your views here.
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


class LogoutView(GenericAPIView):
    serializer_class = serializers.Serializer  # dummy, so schema works
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logged out successfully"}, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """
    Return the authenticated user's profile data.
    - For patients: includes patient code and medical history
    - For carepersons: includes assigned patients
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role == 'patient':
            serializer = PatientSerializer(user.patient_profile)
        elif user.role == 'careperson':
            serializer = CarePersonSerializer(user.careperson_profile)
        else:
            serializer = UserSerializer(user)

        return Response({
            "user": UserSerializer(user).data,
            "profile": serializer.data
        })


class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.get(email=email)

        # generate random 4-digit code
        code = str(random.randint(1000, 9999))
        user.reset_code = code

        # create a short-lived access token for password reset
        token = RefreshToken.for_user(user).access_token
        token.set_exp(lifetime=timedelta(minutes=10))
        user.reset_token = str(token)

        user.save()
        return Response(
            {
                "message": "Code sent to your email successfully",
                "code": code,  # for testing, in production you send via email
                "reset_token": str(token)
            },
            status=status.HTTP_200_OK
        )


class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        token = AccessToken(data['reset_token'])

        user = User.objects.get(id=token['user_id'])

        user.set_password(data["password"])
        user.reset_code = None  # clear code
        user.reset_token = None  # clear token
        user.save()

        return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)
