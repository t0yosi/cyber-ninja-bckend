from rest_framework.permissions import BasePermission
from .models import Lesson, Student

class IsPaidStudent(BasePermission):
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Check if user is a student
        if not hasattr(request.user, 'student'):
            return False

        return True

    def has_object_permission(self, request, view, obj):
        # obj here is a Lesson instance
        course = obj.curriculum.course
        student = request.user.student

        # If the course is paid, ensure the student has paid
        if course.category == "PAID":
            return student.paid and course in student.courses_enlisted.all()
        
        return True
