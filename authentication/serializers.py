from datetime import timedelta
from random import random

from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', "full_name",'email', 'phone']
        read_only_fields = ['id', 'email']


class RegisterSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'password', 'phone']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):

        user_obj = User.objects.filter(email=data['email']).first()
        if not user_obj:
            raise serializers.ValidationError({"message":"Invalid email or password"})

        user = authenticate(username=user_obj.username, password=data['password'])
        if not user:
            raise serializers.ValidationError({"message":"Invalid email or password"})

        refresh = RefreshToken.for_user(user)
        return {
            "user": UserSerializer(user).data,
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        }


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    code = serializers.CharField()
    reset_token = serializers.CharField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"message": "Passwords do not match"})

        token = AccessToken(data['reset_token'])

        try:
            user = User.objects.get(id=token['user_id'])
        except User.DoesNotExist:
            raise serializers.ValidationError({"message": "User does not exist"})

        if user.reset_code != data["code"]:
            raise serializers.ValidationError({"message": "Invalid reset code"})

        # verify token
        if user.reset_token != str(token):
            raise serializers.ValidationError({"message": "Invalid reset token"})

        return data
