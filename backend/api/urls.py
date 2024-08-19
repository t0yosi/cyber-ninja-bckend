from django.urls import path, include
from rest_framework import routers
from . import views

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

router = routers.DefaultRouter()
router.register(r'profile', views.ProfileViewSet, basename='profile')
router.register(r'course', views.CourseViewSet, basename='course')
router.register(r'lesson', views.LessonViewSet, basename='lesson')
router.register(r'curriculum', views.CurriculumViewSet, basename='curriculum')
    

urlpatterns = [
    path('token/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.RegisterView.as_view(), name='auth_register'),
    path('logout/', views.logout, name='logout'),
    path('enroll/', views.EnrollView.as_view(), name='enroll'),
    path('subscribe/', views.SubscribeView.as_view(), name='subscribe'),
    path('extend_subscription/', views.ExtendSubscribeView.as_view(), name='extend_subscription'),
    path('unsubscribe/', views.UnSubscribeView.as_view(), name='unsubscribe'),
    path('ipn/', views.IPNCallbackView.as_view(), name='ipn-callback'),
    path('save-invoice/', views.SaveInvoiceView.as_view(), name='save_invoice'),
    path('contact/', views.ContactMessageView.as_view(), name='contact'),
    path('course/<int:course_id>/image/', views.course_image, name='course_image'),
    # path('authorization/', views.authorizationInfo, name='authorization_info'),
    path('', include(router.urls)),
    # path('', views.getRoutes)
]
