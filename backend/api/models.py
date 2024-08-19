from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Create your models here.
from .manager import CustomUserManager

class CustomUser(AbstractUser, PermissionsMixin):
    STUDENT = 1
    INSTRUCTOR = 2

    USER_TYPE_CHOICES = (
        (INSTRUCTOR, "Instructor"),
        (STUDENT, "Student"),
    )

    user_type = models.CharField(choices=USER_TYPE_CHOICES, max_length=20)
    email = models.EmailField(_("email address"), unique=True)
    # phone_number = models.CharField(max_length=15)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def is_instructor(self):
        return self.user_type == self.INSTRUCTOR

    def is_student(self):
        return self.user_type == self.STUDENT

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Instructor(UserProfile):
    courses_taught = models.CharField(max_length=20, blank=True, null=True)

class Student(UserProfile):
    paid = models.BooleanField(default=False)
    courses_enlisted = models.ManyToManyField('Course')
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)

    @property
    def has_active_subscription(self):
        return self.paid and self.subscription_end > timezone.now()

    def update_courses_enlisted(self):
        if not self.has_active_subscription:
            self.courses_enlisted.remove(*self.courses_enlisted.filter(category="PAID"))

    def subscribe(self, duration_months):
        self.paid = True
        self.subscription_start = timezone.now()
        self.subscription_end = self.subscription_start + timezone.timedelta(days=duration_months * 30)
        self.save()

    def extend_subscription(self, duration_months):
        if self.has_active_subscription:
            print("extending")
            self.subscription_end += timezone.timedelta(days=duration_months * 30)
            self.save()

    def cancel_subscription(self):
        self.paid = False
        self.subscription_start = None
        self.subscription_end = None
        self.update_courses_enlisted()  # Clear paid courses only
        self.save()

class Course(models.Model):
       
    DIFFICULTY = (
        ("BEGINNER", "Beginner"),
        ("INTERMEDIATE", "Intermediate"),
        ("EXPERT", "Expert")
    )

    PAYMENT = (
        ("FREE", "Free"),
        ("PAID", "Paid")
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    publication_date = models.DateTimeField(auto_now_add=True)
    revision_date = models.DateTimeField('Revision Date', blank=True, null=True)
    category = models.CharField(choices=PAYMENT, max_length=4)
    image = models.BinaryField( blank=True, null=True) 
    image_blob = models.BinaryField( blank=True, null=True) 
    image1 = models.ImageField(upload_to='post_images')
    image2 = models.ImageField(upload_to='post_images')
    image3 = models.ImageField(upload_to='post_images')
    duration = models.CharField(max_length=100)
    difficulty = models.CharField(choices=DIFFICULTY, max_length=20)
  
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, blank=False, null=False)
  
    def __str__(self):
        return self.title

class Curriculum(models.Model):
   
    DIFFICULTY = (
        ("BEGINNER", "Beginner"),
        ("INTERMEDIATE", "Intermediate"),
        ("EXPERT", "Expert")
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration = models.CharField(max_length=100)
    difficulty = models.CharField(choices=DIFFICULTY, max_length=20)
    
    # instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, blank=False, null=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=False, null=False, related_name='curriculums')

    def __str__(self):
        return self.title


class Lesson(models.Model):
    title = models.CharField(max_length=200)
    sequence_number = models.IntegerField()
    content = models.TextField()
    creation_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField('Last Updated', blank=True, null=True)
    duration = models.CharField(max_length=100)
    
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='lessons')

    def __str__(self):
        return self.title
    

class Payment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=255, unique=True)
    order_id = models.CharField(max_length=255, null=True, blank=True)
    payment_status = models.CharField(max_length=50)
    subscription_type = models.CharField(max_length=50)
    duration_months = models.IntegerField()
    # pay_amount = models.DecimalField(max_digits=20, decimal_places=8)
    # pay_currency = models.CharField(max_length=50)
    price_amount = models.DecimalField(max_digits=20, decimal_places=2)
    price_currency = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def _str_(self):
        return f"{self.payment_id} - {self.status}"

class ContactMessage(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True, null=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name} - {self.subject}'
