import os, json
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.exceptions import TokenError
from .serializers import RegisterSerializer, UserSerializer, LoginSerializer
from django.contrib.auth import get_user_model
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.generics import GenericAPIView
from rest_framework import status


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
