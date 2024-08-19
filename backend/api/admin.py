from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser,
    Instructor,
    Student,
    Course,
    Curriculum,
    Lesson,
    Payment,
    ContactMessage,
)


admin.site.register(CustomUser, UserAdmin)
admin.site.register(Lesson)
admin.site.register(Instructor)
admin.site.register(Curriculum)
admin.site.register(Course)
admin.site.register(Payment)
admin.site.register(ContactMessage)


# Register your models here.
class StudentAdmin(admin.ModelAdmin):
    filter_horizontal = ("courses_enlisted",)


admin.site.register(Student, StudentAdmin)
