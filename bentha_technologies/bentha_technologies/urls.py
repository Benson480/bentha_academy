"""
URL configuration for bentha_technologies project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from commerce_app.views import *



urlpatterns = [
    path('', index, name='index'),
    path('login/', login_view, name='login'),
    path('about/', about, name='about'),
    path('admin/', admin.site.urls),
    path('announcements/', announcement_list, name='announcements'),
    path('contacts/', contact_view, name='contacts'),
    path('message-received/', lambda request: render(request, 'message_received.html'), name='message_received'),

    path('careers/', careers_list, name='careers_list'),
    path('career/<int:pk>/', career_detail, name='career_detail'),
    path('career/review/<int:pk>/', career_detail_review, name='career_detail_review'),
    path('career/success/<int:pk>/', application_success, name='application_success'),

    path('add_to_cart/<int:image_id>/', add_to_cart, name='add_to_cart'),
    path('purchase_item/<int:image_id>/', purchase_item, name='purchase_item'),
    path('make_order/', make_order, name='make_order'),
    path('cart_view/', cart_view, name='cart_view'),

    path('dashboard/', dashboard, name='dashboard'),
    path('logout/', logout_view, name='logout'),

    path('services/', services, name='services'),
    path('request_software/', request_software, name='request_software'),

    path('enroll_student/', enroll_student, name='enroll_student'),
    path('courses_dashboard/', courses_dashboard, name='courses_dashboard'),
    path('enroll/<int:course_id>/', enroll_course, name='enroll_course'),
    path('course/<int:course_id>/learn/', learning_management_platform, name='learning_management_platform'),
    path('course/<int:course_id>/', course_details, name='course_details'),

    path('quizzes/', quiz_list, name='quiz_list'),
    path('quiz/<int:quiz_id>/', take_quiz, name='take_quiz'),
    path('quiz/<int:quiz_id>/results/', quiz_results, name='quiz_results'),

    path('assignment/<int:assignment_id>/', submit_assignment, name='submit_assignment'),
    path('assignment/<int:assignment_id>/details/', assignment_details, name='assignment_details'),

    path('exam/<int:exam_id>/', take_exam, name='take_exam'),
    path('exam/<int:exam_id>/results/', exam_results, name='exam_results'),
    path("exam/<int:exam_id>/results/<int:submission_id>/", exam_results, name="exam_results"),

    path('view-grades/', view_grades, name='view_grades'),

    path('accounts/', include('allauth.urls')),  # Social login

    path('cyber_services/', cyber_service_list, name='cyber_service_list'),
    path('cyber_service_add/add/', cyber_service_add, name='cyber_service_add'),
    path('cyber_service_detail/<int:pk>/', cyber_service_detail, name='cyber_service_detail'),
    path('cyber_service_edit/<int:pk>/edit/', cyber_service_edit, name='cyber_service_edit'),
    path('services/<int:pk>/order/', cyber_service_order, name='cyber_service_order'),
    path('services/<int:pk>/confirm/', cyber_confirm_payment, name='confirm_payment'),
    path('mpesa_callback/', cyber_mpesa_callback, name='mpesa_callback'),
    path('order_success/<int:pk>/', cyber_order_success, name='order_success'),
    path('order_failed/<int:pk>/', cyber_order_failed, name='order_failed'),

    path('coming_soon/', coming_soon, name='coming_soon'),
    path('robot_simulation/', robot_simulation, name='robot_simulation'),
    path('send/', send_sms_view, name='send_sms'),

    path("gemini-chat/", gemini_chat, name="gemini_chat"),

    path("pay/", initiate_payment, name="mpesa-pay"),
    path("callback/", mpesa_callback, name="mpesa-callback"),
    path("mpesa/", include("commerce_app.urls")),

    path("order/<int:service_id>/", place_order, name="place_order"),
    path("mpesa/callback/", mpesa_callback, name="mpesa_callback"),





]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)