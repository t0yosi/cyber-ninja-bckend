from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.request import Request
from rest_framework.response import Response
from django.conf import settings
from datetime import timedelta
from . import views
from django.template.loader import render_to_string
from django.db import transaction
from django.db.models import F
from asgiref.sync import sync_to_async
from .models import (
    ContactMessage,
    CustomUser,
    Instructor,
    Student,
    Course,
    Curriculum,
    Lesson,
    ContactMessage,
)
import environ
import base64


# Setting up environ variables
# env = environ.Env()

# environ.Env.read_env()


MIN_LENGTH = 8


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token["username"] = user.username
        token["email"] = user.email
        token["user_type"] = user.user_type
        # ...
        return token

    def post(self, request: Request, *args, **kwargs) -> Response:
        response = super().post(request, *args, **kwargs)
        access_token = response.data["access"]
        response.set_cookie(
            key=settings.SIMPLE_JWT["AUTH_COOKIE"],
            value=access_token,
            domain=settings.SIMPLE_JWT["AUTH_COOKIE_DOMAIN"],
            path=settings.SIMPLE_JWT["AUTH_COOKIE_PATH"],
            expires=settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
            secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
            httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
            samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"],
        )
        return response


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(min_length=MIN_LENGTH)
    user_type = serializers.ChoiceField(choices=CustomUser.USER_TYPE_CHOICES, default=1)

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        min_length=MIN_LENGTH,
        error_messages={
            "min_length": f"Password must be longer than {MIN_LENGTH} characters."
        },
        style={"input_type": "password"},
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        min_length=MIN_LENGTH,
        error_messages={
            "min_length": f"Password must be longer than {MIN_LENGTH} characters."
        },
        style={"input_type": "password"},
    )

    # Additional fields for student profile
    paid = serializers.BooleanField(default=False)
    courses_enlisted = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Course.objects.all(), required=False
    )

    # Additional field for instructor profile
    courses_taught = serializers.CharField(max_length=20, required=False)

    class Meta:
        model = CustomUser
        fields = (
            "first_name",
            "last_name",
            "email",
            "username",
            "password",
            "password2",
            "user_type",
            "paid",
            "courses_enlisted",
            "courses_taught",
        )

    def validate(self, attrs):
        email = attrs["email"]
        username = attrs["username"]

        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "email already exists"})
        if CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "username already exists"})
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Password fields don't match"}
            )

        return attrs

    def create(self, validated_data):
        user = CustomUser.objects.create(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            user_type=validated_data["user_type"],
        )
        user.set_password(validated_data["password"])
        # if user.user_type == CustomUser.ADMIN:
        #     user.is_superuser = True
        # print(validated_data)
        if user.user_type == CustomUser.INSTRUCTOR:
            # courses_taught = validated_data.pop("courses_taught", None)  # Get courses_taught with a default value of None
            Instructor.objects.create(
                user=user,
                # courses_taught=validated_data.pop("courses_taught")
            )
        elif user.user_type == CustomUser.STUDENT:
            Student.objects.create(
                user=user,
                paid=validated_data.pop("paid"),
            )
        user.save()
        return user


# Lesson Serializer
class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"


# Curriculum Serializer
class CurriculumSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)  # Include linked lessons

    class Meta:
        model = Curriculum
        fields = (
            "id",
            "title",
            "description",
            "duration",
            "difficulty",
            "lessons",
            "course",
        )


class CourseSerializer(serializers.ModelSerializer):
    instructor_name = (
        serializers.SerializerMethodField()
    ) # Add a new field for instructor name
    
    image_base64 = serializers.SerializerMethodField()
    # image1 = (
    #     serializers.SerializerMethodField()
    # )
    # image2 = (
    #     serializers.SerializerMethodField()
    # )
    # image3 = (
    #     serializers.SerializerMethodField()
    # )

    curriculums = CurriculumSerializer(
        many=True, read_only=True
    )  # Include linked curriculums

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "description",
            "publication_date",
            "revision_date",
            "category",
            "duration",
            "difficulty",
            "instructor",
            "instructor_name",
            "image_blob",
            "image_base64",
            "image1",
            "image2",
            "image3",
            "curriculums",
        )
        
    # def get_image1(self, obj):
    #     request = self.context.get('request')
    #     if request :
    #         return request.build_absolute_uri(obj.image1.url)
    #     return obj.image1.url
    
    def get_image_base64(self, obj):
        if obj.image_blob: 
            return base64.b64encode(obj.image_blob).decode('utf-8')
        return None
    
    # def get_image_url(self, obj):
    #     request = self.context.get('request')
    #     return request.build_absolute_uri(obj.get_image_url())

    # def get_image_url(self):
    #     return reverse('course_image', args=[self.id])

    def get_instructor_name(self, obj):
        user = obj.instructor.user
        # print(user)
        return (
            obj.instructor.user.first_name + " " + obj.instructor.user.last_name
            if obj.instructor
            else None
        )  # Return instructor name if available, otherwise None
        
    def create(self, validated_data):
        image_data = validated_data.pop('image_base64', None)
        if image_data:
            validated_data['image_blob'] = base64.b64decode(image_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_data = validated_data.pop('image_base64', None)
        if image_data:
            validated_data['image_blob'] = base64.b64decode(image_data)
        return super().update(instance, validated_data)


class ProfileSerializer(serializers.ModelSerializer):
    paid = serializers.BooleanField(source="student.paid")

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "username",
            "date_joined",
            "email",
            "first_name",
            "last_name",
            "user_type",
            "paid",
            "student",  # Include the related Student model
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if hasattr(instance, "student"):  # Check if the instance has a student profile
            representation["courses_enlisted"] = CourseSerializer(
                instance.student.courses_enlisted, many=True
            ).data
        else:
            representation["courses_enlisted"] = (
                []
            )  # Provide an empty list if no courses are enrolled
        return representation

    def update(self, instance, validated_data):
        user_type = instance.user_type
        # Update student profile data if present in validated_data
        if user_type == CustomUser.STUDENT:  # Check if the user is a student
            student_profile = instance.student
            student_profile.paid = validated_data.get("student", {}).get(
                "paid", student_profile.paid
            )
            student_profile.courses_enlisted.set(
                validated_data.get("student", {}).get(
                    "courses_enlisted", student_profile.courses_enlisted.all()
                )
            )
            student_profile.save()

        # Update user details
        instance.username = validated_data.get("username", instance.username)
        instance.email = validated_data.get("email", instance.email)
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.save()

        return instance


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = "__all__"
