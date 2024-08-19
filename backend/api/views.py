from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, permissions, viewsets
from .serializers import (
    MyTokenObtainPairSerializer,
    RegisterSerializer,
    ProfileSerializer,
    CourseSerializer,
    CurriculumSerializer,
    LessonSerializer,ContactMessageSerializer,
)
from .models import CustomUser, Instructor, Student, Course, Curriculum, Lesson, Payment
from .permissions import IsPaidStudent

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import json, hmac, hashlib
from django.conf import settings

import environ

# Setting up environ variables
env = environ.Env()

environ.Env.read_env()


# Create your views here.
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


@api_view(["POST"])
def logout(request):
    refresh_token = request.data.get("refresh_token")
    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"message": "User logout successful"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(
            {"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST
        )


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    


class ProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_queryset(self):
        return CustomUser.objects.filter(pk=self.request.user.pk)

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.first()  # Assuming there's only one object per user
        return obj

    def list(self, request):
        instance = self.get_object()
        # print("Retrieved user instance:", instance)
        serializer = self.serializer_class(instance)
        # print("Serialized data:", serializer.data)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def authorizationInfo(request):
    try:
        user = request.user
        auth_level = user.user_type

        roles = {
            "student": auth_level == "1",
            "instructor": auth_level == "2",
        }
        print("User roles:", roles)

        return Response(roles)

    except Exception as e:
        print("Error:", e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CourseViewSet(viewsets.ModelViewSet):
    parser_classes = (MultiPartParser, FormParser)
    queryset = Course.objects.all()
    permission_classes = [AllowAny]
    serializer_class = CourseSerializer
    
    
    # @action(detail=True, methods=['post'])
    # def upload_image(self, request, pk=None):
    #     course = self.get_object()
    #     image_file = request.FILES.get('image')
    #     if image_file:
    #         course.image = image_file.read()
    #         course.save()
    #         return Response(status=status.HTTP_204_NO_CONTENT)
    #     return Response(status=status.HTTP_400_BAD_REQUEST)


class CurriculumViewSet(viewsets.ModelViewSet):
    queryset = Curriculum.objects.all()
    permission_classes = [AllowAny]
    serializer_class = CurriculumSerializer
    

def course_image(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    return HttpResponse(course.image, content_type="image/jpeg") 


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "student"):
            student = user.student
            if student:
                enlisted_courses = student.courses_enlisted.all()
                print(f"Courses enlisted by student: {enlisted_courses}")
                queryset = Lesson.objects.filter(
                    curriculum__course__in=student.courses_enlisted.all()
                )
                print(f"Filtered lessons for student: {queryset}")
                return queryset
            else:
                return Response(
                    {"unenrolled": "You are not enrolled in any courses."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            return Lesson.objects.none()

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        if not hasattr(user, "student"):
            return Response(
                {"detail": "You must be a student to access lessons."},
                status=status.HTTP_403_FORBIDDEN,
            )

        student = user.student
        lesson_id = kwargs.get("pk")
        print(lesson_id)

        try:
            lesson = Lesson.objects.get(pk=lesson_id)
        except Lesson.DoesNotExist:
            return Response(
                {"detail": "No Lesson matches the given query."},
                status=status.HTTP_404_NOT_FOUND,
            )

        course = lesson.curriculum.course

        if course not in student.courses_enlisted.all():
            return Response(
                {"detail": "You must be enrolled in this course to access the lesson."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().retrieve(request, *args, **kwargs)


class EnrollView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user

        if not hasattr(user, "student"):
            return Response(
                {"detail": "Sign up to enroll in courses."},
                status=status.HTTP_403_FORBIDDEN,
            )

        student = user.student
        course_id = request.data.get("course_id")

        try:
            course = Course.objects.get(id=course_id)
            if course.category == "PAID":
                if not student.paid:
                    return Response(
                        {"unpaid": "Subscribe to a payment plan."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
        except Course.DoesNotExist:
            return Response(
                {"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND
            )

        student.courses_enlisted.add(course)
        student.save()

        return Response(
            {"detail": "Successfully enrolled in course."}, status=status.HTTP_200_OK
        )


class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        duration_months = request.data.get("duration_months", 1)
        if hasattr(user, "student"):
            student = user.student
            student.subscribe(duration_months)
            return Response(
                {"detail": "Subscription updated."}, status=status.HTTP_200_OK
            )
        return Response(
            {"detail": "User is not a student."}, status=status.HTTP_404_BAD_REQUEST
        )


class ExtendSubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        duration_months = request.data.get("duration_months", 1)
        if hasattr(user, "student"):
            student = user.student
            student.extend_subscription(duration_months)
            return Response(
                {"detail": "Subscription extended."}, status=status.HTTP_200_OK
            )
        return Response(
            {"detail": "User is not a student."}, status=status.HTTP_404_BAD_REQUEST
        )


class UnSubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if hasattr(user, "student"):
            student = user.student
            student.cancel_subscription()
            return Response(
                {"detail": "Subscription cancelled."}, status=status.HTTP_200_OK
            )
        return Response(
            {"detail": "User is not a student."}, status=status.HTTP_404_BAD_REQUEST
        )


class SaveInvoiceView(APIView):
    # permission_classes = [IsAuthenticated]
    def post(self, request):
        user_id = request.data.get("user_id")
        invoice_id = request.data.get("invoice_id")
        subscription_type = request.data.get("subscription_type")
        duration_months = request.data.get("duration_months")

        try:
            user = CustomUser.objects.get(id=user_id)
            student = Student.objects.get(user=user)

            payment = Payment.objects.create(
                student=student,
                payment_id=invoice_id,
                subscription_type=subscription_type,
                duration_months=duration_months,
                order_id=f"user_{user.username}_subscribe{duration_months}",  # Corrected order_id format
                price_amount=request.data.get("price_amount", 0),
                price_currency=request.data.get(
                    "price_currency", "usd"
                ),  # Corrected default value
                payment_status="waiting",
            )

            return Response({"detail": "Invoice saved"}, status=status.HTTP_201_CREATED)
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Student.DoesNotExist:
            return Response(
                {"detail": "Student not found"}, status=status.HTTP_404_NOT_FOUND
            )


class IPNCallbackView(APIView):
    # permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        np_secret_key = env("IPN_KEY")
        np_x_signature = request.headers.get("x-nowpayments-sig", "")

        if not np_x_signature:
            return Response(
                {"detail": "Signature missing"}, status=status.HTTP_400_BAD_REQUEST
            )

        message = request.data

        # Sort and stringify the request data
        sorted_message = json.dumps(message, separators=(",", ":"), sort_keys=True)
        digest = hmac.new(
            str(np_secret_key).encode(), sorted_message.encode(), hashlib.sha512
        )
        signature = digest.hexdigest()

        if signature == np_x_signature:
            # Handle the verified IPN message here
            try:
                print("IPN received and verified:", request.data)
                # Process the notification data
                payment_status = message.get("payment_status")
                payment_id = message.get("payment_id")
                pay_amount = message.get("pay_amount")
                pay_currency = message.get("pay_currency")
                order_id = message.get("order_id")
                price_amount = message.get("price_amount")
                price_currency = message.get("price_currency")

                # Example: Find the corresponding payment object
                payment = Payment.objects.get(payment_id=payment_id)

                if payment_status == "waiting":
                    self.handle_waiting_status(
                        payment, order_id, pay_amount, pay_currency
                    )
                elif payment_status == "confirming":
                    self.handle_confirming_status(
                        payment, order_id, pay_amount, pay_currency
                    )
                elif payment_status == "confirmed":
                    self.handle_confirmed_status(
                        payment, order_id, pay_amount, pay_currency
                    )
                elif payment_status == "sending":
                    self.handle_sending_status(
                        payment, order_id, pay_amount, pay_currency
                    )
                elif payment_status == "partially_paid":
                    self.handle_partially_paid_status(
                        payment, order_id, pay_amount, pay_currency
                    )
                elif payment_status == "finished":
                    duration_months = int(
                        order_id.split("_")[2]
                    )  # Corrected order_id parsing
                    self.handle_finished_status(
                        payment, order_id, pay_amount, pay_currency, duration_months
                    )
                elif payment_status == "failed":
                    self.handle_failed_status(
                        payment, order_id, pay_amount, pay_currency
                    )
                elif payment_status == "refunded":
                    self.handle_refunded_status(
                        payment, order_id, pay_amount, pay_currency
                    )
                elif payment_status == "expired":
                    self.handle_expired_status(
                        payment, order_id, pay_amount, pay_currency
                    )
                else:
                    return Response(
                        {"detail": "Unhandled payment status"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                return Response(
                    {"detail": "IPN received and processed"}, status=status.HTTP_200_OK
                )

            except Payment.DoesNotExist:
                return Response(
                    {"detail": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        else:
            print("HMAC signature does not match")
            return Response(
                {"detail": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST
            )

    # def handle_finished_status(self, payment, duration_months):
    #     student = payment.student
    #     if student.paid:
    #         student.extend_subscription(duration_months)
    #     else:
    #         student.subscribe(duration_months)
    #     student.save()
    #     print(
    #         f"Subscription updated for student ID: {student.id} based on payment ID: {payment.payment_id}"
    #     )

    def handle_waiting_status(self, payment_id, order_id, pay_amount, pay_currency):
        payment, created = Payment.objects.get_or_create(
            payment_id=payment_id,
            defaults={
                "order_id": order_id,
                "status": "waiting",
                "pay_amount": pay_amount,
                "pay_currency": pay_currency,
            },
        )
        if not created:
            payment.status = "waiting"
            payment.save()
        print(f"Payment {payment_id} is waiting. Order ID: {order_id}")

    def handle_confirming_status(self, payment_id, order_id, pay_amount, pay_currency):
        payment, created = Payment.objects.get_or_create(
            payment_id=payment_id,
            defaults={
                "order_id": order_id,
                "status": "confirming",
                "pay_amount": pay_amount,
                "pay_currency": pay_currency,
            },
        )
        if not created:
            payment.status = "confirming"
            payment.save()
        print(f"Payment {payment_id} is confirming. Order ID: {order_id}")
        # Send confirmation email
        # send_confirmation_email(order_id)

    def handle_confirmed_status(self, payment_id, order_id, pay_amount, pay_currency):
        payment, created = Payment.objects.get_or_create(
            payment_id=payment_id,
            defaults={
                "order_id": order_id,
                "status": "confirmed",
                "pay_amount": pay_amount,
                "pay_currency": pay_currency,
            },
        )
        if not created:
            payment.status = "confirmed"
            payment.save()
        print(f"Payment {payment_id} is confirmed. Order ID: {order_id}")
        # Send confirmation email
        # send_confirmation_email(order_id)

    def handle_sending_status(self, payment_id, order_id, pay_amount, pay_currency):
        payment, created = Payment.objects.get_or_create(
            payment_id=payment_id,
            defaults={
                "order_id": order_id,
                "status": "sending",
                "pay_amount": pay_amount,
                "pay_currency": pay_currency,
            },
        )
        if not created:
            payment.status = "sending"
            payment.save()
        print(f"Payment {payment_id} is sending. Order ID: {order_id}")
        # Send confirmation email
        # send_confirmation_email(order_id)

    def handle_partially_paid_status(
        self, payment_id, order_id, pay_amount, pay_currency
    ):
        payment, created = Payment.objects.get_or_create(
            payment_id=payment_id,
            defaults={
                "order_id": order_id,
                "status": "partially_paid",
                "pay_amount": pay_amount,
                "pay_currency": pay_currency,
            },
        )
        if not created:
            payment.status = "partially_paid"
            payment.save()
        print(f"Payment {payment_id} is partially_paid. Order ID: {order_id}")
        # Send confirmation email
        # send_confirmation_email(order_id)

    def handle_finished_status(
        self, payment_id, order_id, pay_amount, pay_currency, duration_months
    ):
        payment, created = Payment.objects.get_or_create(
            payment_id=payment_id,
            defaults={
                "order_id": order_id,
                "status": "finished",
                "pay_amount": pay_amount,
                "pay_currency": pay_currency,
            },
        )
        if not created:
            payment.status = "finished"
            payment.save()
        # Update Student subscription status
        student = payment.student
        if student.paid:
            student.extend_subscription(duration_months)
        else:
            student.subscribe(duration_months)
        student.save()
        print(
            f"Subscription updated for student ID: {student.id} based on payment ID: {payment.payment_id}"
        )
        print(f"Payment {payment_id} is finished. Order ID: {order_id}")
        # Grant access to the service or product
        # grant_access(order_id)

    def handle_failed_status(self, payment_id, order_id, pay_amount, pay_currency):
        payment, created = Payment.objects.get_or_create(
            payment_id=payment_id,
            defaults={
                "order_id": order_id,
                "status": "failed",
                "pay_amount": pay_amount,
                "pay_currency": pay_currency,
            },
        )
        if not created:
            payment.status = "failed"
            payment.save()
        print(f"Payment {payment_id} failed. Order ID: {order_id}")
        # Notify the user about the failure
        # notify_failure(order_id)

    def handle_refunded_status(self, payment_id, order_id, pay_amount, pay_currency):
        payment, created = Payment.objects.get_or_create(
            payment_id=payment_id,
            defaults={
                "order_id": order_id,
                "status": "refunded",
                "pay_amount": pay_amount,
                "pay_currency": pay_currency,
            },
        )
        if not created:
            payment.status = "refunded"
            payment.save()
        print(f"Payment {payment_id} refunded. Order ID: {order_id}")
        # Notify the user about the failure
        # notify_failure(order_id)

    def handle_expired_status(self, payment_id, order_id, pay_amount, pay_currency):
        payment, created = Payment.objects.get_or_create(
            payment_id=payment_id,
            defaults={
                "order_id": order_id,
                "status": "expired",
                "pay_amount": pay_amount,
                "pay_currency": pay_currency,
            },
        )
        if not created:
            payment.status = "expired"
            payment.save()
        print(f"Payment {payment_id} expired. Order ID: {order_id}")
        # Notify the user about the failure
        # notify_failure(order_id)


class ContactMessageView(APIView):
    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # self.send_email(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def send_email(self, data):
        subject = f"New Contact Message from {data['first_name']} {data['last_name']}"
        message = f"""
        You have received a new message from the contact form:

        Name: {data['first_name']} {data['last_name']}
        Email: {data['email']}
        Phone: {data['phone']}
        Subject: {data['subject']}
        Message: {data['message']}
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            fail_silently=False,
        )