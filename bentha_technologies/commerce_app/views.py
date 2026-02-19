from django.shortcuts import render
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.forms import PasswordResetForm
from .forms import *
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
import logging
from django.http import Http404
from urllib.parse import urlparse
import datetime
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login
from django.utils import timezone
# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import *
from django.core.files.storage import FileSystemStorage
from django.core.files.storage import default_storage
from django.conf import settings
import os
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.db.models import Q
from .forms import *
import requests
from django.views.decorators.csrf import csrf_exempt
from functools import lru_cache
import re
from .mpesa import stk_push
from .models import MpesaTransaction


logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

#Module to Enable users signin
def login_view(request):
    if request.method == 'POST':
        login_form = AuthenticationForm(request, data=request.POST)
        if login_form.is_valid():
            user = login_form.get_user()
            auth_login(request, user)
            logger.warning(
                f"Login Successful at {timezone.now()} by username: {request.POST.get('username')}"
            )
            messages.success(request, f"Login Successful at {timezone.now()} by username: {request.POST.get('username')}")

            # Check if there is a 'next' parameter in the URL
            next_url = request.GET.get('next', None)
            if next_url:
                return redirect(next_url)
            else:
                return redirect('dashboard')  # Default redirect if 'next' is not provided
        else:
            logger.warning(
                f"Login attempt failed at {timezone.now()} by username: {request.POST.get('username')}"
            )
            messages.error(request, f"Login attempt failed at {timezone.now()} by username: {request.POST.get('username')}")

    else:
        login_form = AuthenticationForm()

    signup_form = SignupForm(request.POST)  # Pass the POST data to the signup form

    if request.method == 'POST' and signup_form.is_valid():
        username = signup_form.cleaned_data['username']
        email = signup_form.cleaned_data['email']
        password = signup_form.cleaned_data['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, f"This Username {request.POST.get('username')} is already in taken!")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            user = authenticate(request, username=username, password=password)
            login(request, user)
            messages.success(request, f"SignUp Successful at {timezone.now()} by username: {request.POST.get('username')}")
            return redirect('login')

    password_reset_form = PasswordResetForm(request.POST or None)

    if request.method == 'POST' and password_reset_form.is_valid():
        user_email = password_reset_form.cleaned_data['email']
        password_reset_form.save(
            request=request,
            from_email=None,  # Use the default email backend configured in settings
            email_template_name='accounts/password_reset.html',
        )
        messages.success(request, f"A password reset email has been sent to {user_email}.")
        return redirect('login')

    context = {
        'login_form': login_form,
        'signup_form': signup_form,
        'password_reset_form': password_reset_form,
    }
    return render(request, 'accounts/login.html', context)



def logout_view(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if request.method == "POST":
        logout(request)
        if request.user.is_authenticated:  # Check if the user is authenticated
            Activity.objects.create(user=request.user, activity_type="User Logout", user_logout=True)
        return redirect("/")
    return render(request, "accounts/logout.html", {'user_profile': user_profile})

# Views that don't need authentication to access them
def about(request):
    template = loader.get_template('about.html')
    return HttpResponse(template.render())

def announcement_list(request):
    announcements = Announcement.objects.all().order_by('-timestamp')
    return render(request, 'announcements.html', {'announcements': announcements})

def contact_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        # Save the contact information to the database
        contact = Contact(name=name, email=email, subject=subject, message=message)
        contact.save()

        # Redirect to the "Message Received" page
        return redirect("message_received")

    return render(request, "contact.html")

def careers_list(request):
    careers = Career.objects.all().order_by('-published_date')
    return render(request, 'careers_list.html', {'careers': careers})

def career_detail(request, pk):
    career = get_object_or_404(Career, pk=pk)

    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)

        if form.is_valid():
            # Save files and prepare application data for review
            resume_file_path = None
            cover_letter_file_path = None

            if 'resume' in request.FILES:
                resume_file = request.FILES['resume']
                resume_file_path = default_storage.save(f'resumes/{resume_file.name}', resume_file)

            if 'cover_letter' in request.FILES:
                cover_letter_file = request.FILES['cover_letter']
                cover_letter_file_path = default_storage.save(f'cover_letters/{cover_letter_file.name}', cover_letter_file)  # Corrected here

            # Store data in the session
            request.session['application_data'] = {
                'full_name': form.cleaned_data['full_name'],
                'email': form.cleaned_data['email'],
                'phone_number': form.cleaned_data['phone_number'],
                'resume': resume_file_path,
                'cover_letter': cover_letter_file_path,
            }

            return redirect('career_detail_review', pk=pk)

    else:
        form = JobApplicationForm()

    return render(request, 'career_detail.html', {'career': career, 'form': form})

def career_detail_review(request, pk):
    career = get_object_or_404(Career, pk=pk)
    application_data = request.session.get('application_data')

    if not application_data:
        return redirect('career_detail', pk=pk)

    # Generate URLs for uploaded files
    application_data['resume_url'] = default_storage.url(application_data['resume']) if application_data.get('resume') else None
    application_data['cover_letter_url'] = default_storage.url(application_data['cover_letter']) if application_data.get('cover_letter') else None

    if request.method == 'POST':
        # Save job application to the database
        JobApplication.objects.create(
            full_name=application_data['full_name'],
            email=application_data['email'],
            phone_number=application_data['phone_number'],
            career=career,
            resume=application_data.get('resume'),
            cover_letter=application_data.get('cover_letter'),
        )
        request.session.pop('application_data', None)
        messages.success(request, 'Your application has been submitted successfully!')
        return redirect('application_success', pk=pk)

    return render(request, 'review_application.html', {'career': career, 'application_data': application_data})


def application_success(request, pk):
    career = get_object_or_404(Career, pk=pk)
    return render(request, 'application_success.html', {'career': career})




def cart_view(request):
    # Assuming user authentication is enabled, get the current user
    user = request.user

    # Query the CartItem model to get the items in the user's cart
    cart_items = CartItem.objects.filter(cart__user=user)

    # Calculate the total price of items in the cart
    total_price = sum(item.image.price * item.quantity for item in cart_items)

    # Calculate subtotals and add them to cart_items
    for item in cart_items:
        item.subtotal = item.image.price * item.quantity

    # Query all images from the ItemImage model
    images = ItemImage.objects.all()

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'images': images,
    }

    return render(request, 'cart_template.html', context)




def add_to_cart(request, image_id):
    image = get_object_or_404(ItemImage, pk=image_id)
    user = request.user if request.user.is_authenticated else None
    cart, created = Cart.objects.get_or_create(user=user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, image=image)

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    # If the user is not authenticated, store the item details in the session
    if not user:
        item_data = {
            'image_id': image_id,
        }
        session = SessionStore(session_key=request.session.session_key)
        if 'cart_items' not in session:
            session['cart_items'] = []
        session['cart_items'].append(item_data)
        session.save()

    return redirect('cart_view')

def make_order(request):
    user = request.user

    # Check if the user has a cart
    try:
        cart = Cart.objects.get(user=user)
    except Cart.DoesNotExist:
        # Handle the case where the cart does not exist, e.g., by redirecting to the cart page
        return redirect('cart_view')  # You need to define this URL in your urls.py

    items_in_cart = CartItem.objects.filter(cart=cart)

    # Calculate the total price of items in the cart
    total_price = sum(item.image.price * item.quantity for item in items_in_cart)

    # Create an order and associate the selected items with it
    order = Order.objects.create(user=user, total_price=total_price)
    order.items.set(items_in_cart)

    # Retrieve the associated images
    ordered_images = [item.image for item in items_in_cart]

    # Clear the cart and redirect to the order confirmation view
    cart.delete()

    # Pass the ordered_images to the order_confirmation_view
    return HttpResponseRedirect(reverse('order_confirmation_view', args=(order.id,)) + f"?ordered_images={','.join([str(image.id) for image in ordered_images])}")

def order_confirmation_view(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        raise Http404("Order does not exist")

    ordered_images = request.GET.get('ordered_images', '').split(',')
    ordered_images_objects = [get_object_or_404(ItemImage, id=image_id) for image_id in ordered_images]

    context = {
        'order': order,
        'ordered_images': ordered_images_objects,
    }
    return render(request, 'order_confirmation.html', context)


#Module to help with online sales
def purchase_item(request, image_id):
    # Implement the logic to handle a purchase (e.g., deduct from user's balance)
    return redirect('success_view')  # Redirect to a success view


def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id)
    item.delete()
    return redirect('cart_view')

def success_page(request):
    return render(request, 'success_page.html')

@login_required
def dashboard(request):
    user_profile = UserProfile.objects.get(user=request.user)

    categories = Category.objects.all()
    selected_category = request.GET.get('category', 'All')

    if selected_category == 'All':
        images = ItemImage.objects.all()
    else:
        category = Category.objects.get(name=selected_category)
        images = ItemImage.objects.filter(categories=category)

    categorized_images = {}
    for category in categories:
        categorized_images[category] = images.filter(categories=category)
    if request.user.is_authenticated:
        request.session['last_activity'] = datetime.datetime.now().isoformat()  # Convert to string

    return render(request, 'dashboard.html', {'categorized_images': categorized_images, 'selected_category': selected_category, 'categories': categories, 'user_profile': user_profile})
    # Retrieve or create the user_profile


def services(request):
    categories = Category.objects.all()
    selected_category = request.GET.get('category', 'All')

    if selected_category == 'All':
        images = ItemImage.objects.all()
    else:
        category = Category.objects.get(name=selected_category)
        images = ItemImage.objects.filter(categories=category)

    categorized_images = {}
    for category in categories:
        categorized_images[category] = images.filter(categories=category)

    return render(request, 'services.html', {'categorized_images': categorized_images, 'selected_category': selected_category, 'categories': categories})

@login_required
def request_software(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        form = SoftwareRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your software request has been successfully submitted!')
            return redirect('request_software')  # Redirect to the same page after form submission
    else:
        form = SoftwareRequestForm()
    return render(request, 'request_software.html', {'form': form, 'user_profile': user_profile})

@login_required
def enroll_student(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        form = StudentEnrollForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('courses_dashboard')   # Redirect to a success page or URL
        else:
            # Handle invalid form submission
            # Check if the error is due to duplicate email
            if 'email' in form.errors:
                messages.error(request, "Student enrollment with this Email already exists.")
            return render(request, 'enroll_student.html', {'form': form})
    else:
        # If the request method is not POST, render the form
        form = StudentEnrollForm()

    # If form is not valid or it's a GET request, render the form with errors or empty form
    return render(request, 'enroll_student.html', {'form': form, 'user_profile': user_profile})

@login_required
def courses_dashboard(request):
    user_profile = UserProfile.objects.get(user=request.user)
    courses = Course.objects.all()
    upcoming_classes = Course.objects.filter(start_date__gte=datetime.date.today()).order_by('start_date')
    student_progress = StudentProgress.objects.filter(user=request.user)
    user_enrollments = Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True)

    context = {
        'courses': courses,
        'upcoming_classes': upcoming_classes,
        'student_progress': student_progress,
        'user_profile': user_profile,
        'user_enrollments': user_enrollments,  # Pass this context
    }
    return render(request, 'courses_dashboard.html', context)

@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        Enrollment.objects.create(user=request.user, course=course)
    return redirect('learning_management_platform', course_id=course.id)  # Redirect to the learning management platform

@login_required
def learning_management_platform(request, course_id):
    user_profile = UserProfile.objects.get(user=request.user)
    course = get_object_or_404(Course, id=course_id)

    # Ensure user is enrolled
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        return redirect('enroll_course', course_id=course.id)

    # Get materials and paginate
    materials = course.materials.all().order_by('id')  # Ensure consistent order
    paginator = Paginator(materials, 1)  # 1 material per page
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)

    # Get user progress (but don't restrict access)
    progress = StudentProgress.objects.filter(user=request.user, course=course).first()
    allowed_index = progress.modules_completed if progress else 0

    # Calculate current index
    current_index = int(page_number) - 1

    context = {
        'user_profile': user_profile,
        'course': course,
        'materials': page_obj,
        'quizzes': course.quizzes.all(),
        'assignments': course.assignments.all(),
        'exams': course.exams.all(),
        'grades': Grade.objects.filter(user=request.user, course=course),
        'progress': progress,
        'page_obj': page_obj,
        'current_index': current_index,
        'allowed_index': allowed_index,
        'paginator': paginator,
    }

    return render(request, 'learning_management.html', context)





@login_required
def course_details(request, course_id):
    user_profile = UserProfile.objects.get(user=request.user)
    course = get_object_or_404(Course, id=course_id)
    materials = course.materials.all()
    quizzes = course.quizzes.all()
    assignments = course.assignments.all()
    exams = course.exams.all()

    context = {
        'user_profile': user_profile,
        'course': course,
        'materials': materials,
        'quizzes': quizzes,
        'assignments': assignments,
        'exams': exams,
    }
    return render(request, 'course_details.html', context)

@login_required
def submit_assignment(request, assignment_id):
    # Retrieve the user profile for the logged-in user
    user_profile = UserProfile.objects.get(user=request.user)
    # Get the assignment or return a 404 error if not found
    assignment = get_object_or_404(Assignment, id=assignment_id)

    if request.method == 'POST':
        # Get the uploaded file and submission text from the request
        submission_file = request.FILES.get('submission_file')
        submission_text = request.POST.get('submission_text')

        # Create a new submission instance
        submission = Submission.objects.create(
            user=request.user,
            assignment=assignment,
            submission_file=submission_file,
            submission_text=submission_text
        )

        # Redirect to the assignment details page after submission
        return redirect('assignment_details', assignment_id=assignment.id)

    # Render the template and include the user profile in the context
    return render(request, 'submit_assignment.html', {
        'assignment': assignment,
        'user_profile': user_profile,
        'course_id': assignment.course.id  # Assuming assignment has a related course
    })



@login_required
def take_quiz(request, quiz_id):
    user_profile = UserProfile.objects.get(user=request.user)  # Fetch the user's profile
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()
    course_id = quiz.course.id  # Assuming Quiz has a ForeignKey to Course

    if request.method == 'POST':
        score = sum(1 for question in questions if request.POST.get(f'question_{question.id}') == question.correct_answer)
        submission = Submission.objects.create(user=request.user, quiz=quiz, score=score, graded=True)
        # Update progress
        progress, created = StudentProgress.objects.get_or_create(user=request.user, course=quiz.course)
        progress.progress = min(progress.progress + 100 // quiz.course.quizzes.count(), 100)
        progress.save()
        return redirect('quiz_results', quiz_id=quiz.id)

    # Include user_profile in the render context
    return render(request, 'take_quiz.html', {
        'quiz': quiz,
        'questions': questions,
        'course_id': course_id,
        'user_profile': user_profile  # Add user_profile to the context
    })



def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    user_profile = UserProfile.objects.get(user=request.user)

    # ✅ Already submitted check
    if Submission.objects.filter(user=request.user, exam=exam).exists():
        return render(request, "already_taken.html", {
            "exam": exam,
            "user_profile": user_profile,
        })

    # 🔐 Session key
    session_key = f"exam_access_{exam.id}"

    # STEP A: Password check
    if exam.access_password and not request.session.get(session_key):

        if request.method == "POST" and "exam_password" in request.POST:
            entered_password = request.POST.get("exam_password")

            if exam.check_password(entered_password):
                request.session[session_key] = True  # ✅ Grant access
                return redirect("take_exam", exam_id=exam.id)
            else:
                messages.error(request, "Invalid exam password.")

        return render(request, "exam_password.html", {
            "exam": exam
        })

    # STEP B: Exam submission
    if request.method == "POST":
        score = 0
        for question in exam.questions.all():
            answer = request.POST.get(f"question_{question.id}")
            if answer == question.correct_answer:
                score += 1

        submission = Submission.objects.create(
            user=request.user,
            exam=exam,
            score=score,
            graded=True
        )

        # 🔒 Lock exam after submission
        request.session.pop(session_key, None)

        return redirect("exam_results", exam_id=exam.id, submission_id=submission.id)

    return render(request, "take_exam.html", {
        "exam": exam,
        "user_profile": user_profile,
        "questions": exam.questions.all()
    })


def exam_results(request, exam_id, submission_id):
    exam = get_object_or_404(Exam, id=exam_id)
    user_profile = UserProfile.objects.get(user=request.user)

    submission = get_object_or_404(Submission, id=submission_id, exam=exam, user=request.user)

    percentage_score = (
        round((submission.score / exam.max_score) * 100, 2)
        if submission and exam.max_score > 0 else 0
    )

    context = {
        "exam": exam,
        "submission": submission,
        "percentage_score": percentage_score,
        "user_profile": user_profile
    }
    return render(request, "exam_results.html", context)

@login_required
def view_grades(request):
    user_profile = UserProfile.objects.get(user=request.user)  # Fetch the user's profile
    submissions = Submission.objects.filter(user=request.user)
    return render(request, 'view_grades.html', {'submissions': submissions, 'user_profile': user_profile})



@login_required
def quiz_results(request, quiz_id):
    user_profile = UserProfile.objects.get(user=request.user)  # Fetch the user's profile
    quiz = get_object_or_404(Quiz, id=quiz_id)
    course = quiz.course  # Assuming a ForeignKey relationship exists
    submission = Submission.objects.filter(user=request.user, quiz=quiz).first()

    # Calculate the percentage score if submission exists
    percentage_score = (submission.score / quiz.max_score) * 100 if submission and quiz.max_score > 0 else None

    return render(request, 'quiz_results.html', {
        'quiz': quiz,
        'submission': submission,
        'percentage_score': percentage_score,
        'course': course,  # Pass the course to the template
        'user_profile': user_profile  # Add user_profile to the context
    })


def quiz_list(request):
    quizzes = Quiz.objects.all()  # Fetch all quizzes
    user_profile = UserProfile.objects.get(user=request.user)  # Fetch the user's profile
    return render(request, 'quiz_list.html', {
        'quizzes': quizzes,
        'user_profile': user_profile  # Add user_profile to the context

    })
@login_required
def assignment_details(request, assignment_id):
    user_profile = UserProfile.objects.get(user=request.user)  # Fetch the user's profile
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submission = Submission.objects.filter(user=request.user, assignment=assignment).first()
    # Assume assignment has a related course, and we get the course_id from it
    course_id = assignment.course.id  # Update this according to your data model

    return render(request, 'assignment_details.html', {
        'assignment': assignment,
        'submission': submission,
        'course_id': course_id,
        'user_profile': user_profile  # Add user_profile to the context
    })


@login_required
def access_module(request, course_id, module_number):
    user_profile = UserProfile.objects.get(user=request.user)  # Fetch the user's profile
    course = get_object_or_404(Course, id=course_id)
    progress = get_object_or_404(StudentProgress, user=request.user, course=course)

    if progress.module_completed < module_number - 1:
        return render(request, 'module_locked.html', {'message': "Complete the previous module to access this one."})

    # Fetch the module materials, quizzes, assignments, etc.
    materials = course.materials.filter(module=module_number)
    quizzes = course.quizzes.filter(module=module_number)
    assignments = course.assignments.filter(module=module_number)
    exams = course.exams.filter(module=module_number)

    context = {
        'course': course,
        'materials': materials,
        'quizzes': quizzes,
        'assignments': assignments,
        'exams': exams,
        'module_number': module_number,
        'user_profile': user_profile  # Add user_profile to the context
    }
    return render(request, 'module_details.html', context)


# View for listing all services

def cyber_service_list(request):
    services = Cyber_Service.objects.all()
    user_profile = UserProfile.objects.get(user=request.user)  # Fetch the user's profile

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        services = services.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))

    # Sorting functionality
    sort_option = request.GET.get('sort', '')
    if sort_option == 'price_asc':
        services = services.order_by('price')
    elif sort_option == 'price_desc':
        services = services.order_by('-price')
    elif sort_option == 'duration_asc':
        services = services.order_by('duration')
    elif sort_option == 'duration_desc':
        services = services.order_by('-duration')

    return render(request, 'cyber_service_list.html', {'services': services, 'user_profile': user_profile})
# View for adding a new service
def cyber_service_add(request):
    user_profile = UserProfile.objects.get(user=request.user)  # Fetch the user's profile
    if request.method == 'POST':
        form = Cyber_ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('cyber_service_list')
    else:
        form = Cyber_ServiceForm()
    return render(request, 'cyber_service_form.html', {'form': form, 'user_profile': user_profile})

# View for editing an existing service
def cyber_service_edit(request, pk=None):
    user_profile = UserProfile.objects.get(user=request.user)  # Fetch the user's profile
    service = None
    if pk:
        service = Cyber_Service.objects.get(id=pk)

    if request.method == 'POST':
        form = Cyber_ServiceForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            form.save()
            return redirect('cyber_service_list')
    else:
        form = Cyber_ServiceForm(instance=service)

    return render(request, 'cyber_service_form.html', {'form': form, 'user_profile': user_profile})
# View for displaying service details
def cyber_service_detail(request, pk):
    user_profile = UserProfile.objects.get(user=request.user)  # Fetch the user's profile
    service = get_object_or_404(Cyber_Service, pk=pk)
    return render(request, 'cyber_service_detail.html', {'service': service, 'user_profile': user_profile})

# View for ordering a service
@login_required
def cyber_service_order(request, pk):
    user_profile = UserProfile.objects.get(user=request.user)
    service = get_object_or_404(Cyber_Service, pk=pk)

    if request.method == "POST":
        form = OrderForm(request.POST)
        if not form.is_valid():
            return JsonResponse({
                "status": "error",
                "message": "Invalid form data"
            }, status=400)

        order = form.save(commit=False)
        order.service = service
        order.is_paid = False
        order.save()

        phone = order.customer_phone

        response = stk_push(
            phone=phone,
            amount=service.price,
            account_ref=f"ORDER-{order.id}",
            description=service.name
        )

        if response.get("ResponseCode") == "0":
            order.payment_id = response.get("CheckoutRequestID")
            order.save()

            return JsonResponse({
                "status": "success",
                "message": "STK push sent",
                "order_id": order.id
            })

        return JsonResponse({
            "status": "error",
            "message": response.get("errorMessage", "Payment initiation failed")
        }, status=400)

    # GET request
    form = OrderForm()
    return render(
        request,
        "cyber_service_order.html",
        {
            "service": service,
            "form": form,
            "user_profile": user_profile
        }
    )

# View to confirm payment status
def cyber_confirm_payment(request, pk):
    user_profile = UserProfile.objects.get(user=request.user)  # Fetch the user's profile
    order = get_object_or_404(Cyber_Order, pk=pk)
    if order.is_paid:
        return redirect('order_success', pk=order.pk)
    else:
        return redirect('order_failed', pk=order.pk)

@csrf_exempt
def cyber_mpesa_callback(request):
    data = json.loads(request.body)
    result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
    checkout_request_id = data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')

    try:
        order = Cyber_Order.objects.get(payment_id=checkout_request_id)
        if result_code == 0:  # Payment successful
            order.is_paid = True
            order.save()
        return JsonResponse({"Result": "Success"}, status=200)
    except Cyber_Order.DoesNotExist:
        return JsonResponse({"Result": "Order Not Found"}, status=404)

# View for successful payment
def cyber_order_success(request, pk):
    user_profile = UserProfile.objects.get(user=request.user)  # Fetch the user's profile
    order = get_object_or_404(Cyber_Order, pk=pk)
    context = {
        'order': order,
        'user_profile': user_profile  # Add user_profile to the context
    }
    return render(request, 'cyber_order_success.html', context)

# View for failed payment
def cyber_order_failed(request, pk):
    order = get_object_or_404(Cyber_Order, pk=pk)
    context = {
        'order': order
    }
    return render(request, 'cyber_order_failed.html', context)

def robot_simulation(request):
    robot, _ = Robot.objects.get_or_create(pk=1)

    if request.method == "POST":
        if "simulate" in request.POST and robot.is_active:
            robot.simulate_work_hour()
        elif "recharge" in request.POST:
            robot.recharge()
        return redirect('robot_simulation')

    context = {
        'robot': robot,
    }
    return render(request, 'robot_simulation.html', context)

# Simulate SMS sending (replace this with Safaricom or other API call)
def send_sms_simulation(name, phone, amount):
    print(f"Sending SMS to {phone}: Dear {name}, your loan of {amount} has been approved.")
    return True

def send_sms_view(request):
    if request.method == 'POST':
        form = LoanRecipientForm(request.POST)
        if form.is_valid():
            recipient = form.save(commit=False)
            sms_success = send_sms_simulation(recipient.name, recipient.phone_number, recipient.loan_amount)
            if sms_success:
                recipient.message_sent = True
                recipient.save()
                messages.success(request, f"SMS sent to {recipient.name}")
                return redirect('send_sms')
            else:
                messages.error(request, "Failed to send SMS.")
    else:
        form = LoanRecipientForm()

    return render(request, 'send_sms.html', {'form': form})


# =====================================================
# INDEX / HOME PAGE
# =====================================================
def index(request):
    """
    Updated Index View for Bentha Technologies
    - Loads all categories
    - Supports category filtering
    - Generates categorized image lists
    - Handles redirect for next URL (login required paths)
    """

    categories = Category.objects.all()
    selected_category = request.GET.get('category', 'All')

    # FILTER IMAGES
    if selected_category == 'All':
        images = ItemImage.objects.all()
    else:
        images = ItemImage.objects.filter(categories__name=selected_category)

    # STRUCTURE IMAGES BY CATEGORY
    categorized_images = {
        category.name: images.filter(categories=category)
        for category in categories
    }

    # HANDLE ?next=/request_software/
    next_url = request.GET.get("next")
    if next_url:
        login_url = f"{reverse('login')}?next={next_url}"
        return redirect(login_url)

    return render(request, 'index.html', {
        'categorized_images': categorized_images,
        'selected_category': selected_category,
        'categories': categories,
    })


@login_required(login_url='/login/')
def coming_soon(request):
    """Coming soon page – always safe even if user has no profile."""

    # Safety check: If something goes wrong, NEVER crash!
    if request.user.is_anonymous:
        return redirect(f"/login/?next=/coming_soon/")

    # Try to get or create UserProfile automatically
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    return render(request, "coming_soon.html", {
        "user_profile": user_profile
    })


# =====================================================
# SIMPLE CACHE
# =====================================================
CACHE_SIZE = 128


@lru_cache(maxsize=CACHE_SIZE)
def get_cached_reply(message):
    return None


def cache_reply(message, reply):
    get_cached_reply.cache_clear()
    get_cached_reply(message)


# =====================================================
# RULE-BASED AI LOGIC (NO ML, NO API)
# =====================================================
def rule_based_ai(user_message: str) -> str:
    msg = user_message.lower()

    # Greetings
    if re.search(r"\b(hi|hello|hey|good morning|good evening)\b", msg):
        return "Hello 👋 How can I help you today?"

    # Company info
    if "bentha" in msg or "company" in msg:
        return (
            "Bentha Technologies is an IT solutions company offering "
            "software development, web applications, and digital services."
        )

    # Services
    if "services" in msg or "what do you do" in msg:
        return (
            "We offer web development, software engineering, system design, "
            "and IT consulting services."
        )

    # Pricing
    if "price" in msg or "cost" in msg:
        return (
            "Pricing depends on project requirements. "
            "Please contact us with details so we can give you an accurate quote."
        )

    # Contact
    if "contact" in msg or "reach" in msg:
        return "You can contact Bentha Technologies via email or our website contact form."

    # Fallback
    return (
        "I’m here to help 😊 Could you please clarify your question "
        "or tell me what you’d like to know about Bentha Technologies?"
    )


# =====================================================
# CHAT ENDPOINT (NO GEMINI, NO ML)
# =====================================================
@csrf_exempt
def gemini_chat(request):
    if request.method != "POST":
        return JsonResponse(
            {"reply": "Only POST requests are allowed."},
            status=405
        )

    try:
        body = json.loads(request.body)
        user_message = body.get("message", "").strip()
    except json.JSONDecodeError:
        return JsonResponse(
            {"reply": "Invalid JSON body."},
            status=400
        )

    if not user_message:
        return JsonResponse(
            {"reply": "Message cannot be empty."},
            status=400
        )

    cached = get_cached_reply(user_message)
    if cached:
        return JsonResponse({"reply": cached})

    reply = rule_based_ai(user_message)

    cache_reply(user_message, reply)

    return JsonResponse({"reply": reply})

def initiate_payment(request):
    if request.method == "POST":
        phone = request.POST.get("phone")
        amount = request.POST.get("amount")

        txn = MpesaTransaction.objects.create(
            phone_number=phone,
            amount=amount
        )

        response = stk_push(
            phone=phone,
            amount=amount,
            reference=f"ORDER-{txn.id}",
            description="Payment"
        )

        txn.merchant_request_id = response.get("MerchantRequestID")
        txn.checkout_request_id = response.get("CheckoutRequestID")
        txn.save()

        return JsonResponse(response)

    return HttpResponse(status=405)


@csrf_exempt
def mpesa_callback(request):
    data = json.loads(request.body)

    callback = data["Body"]["stkCallback"]
    checkout_id = callback["CheckoutRequestID"]
    result_code = callback["ResultCode"]

    order = Order.objects.filter(checkout_request_id=checkout_id).first()

    if result_code == 0 and order:
        order.is_paid = True
        order.save()

    return JsonResponse({"status": "ok"})



def place_order(request, service_id):
    service = get_object_or_404(Service, id=service_id)

    if request.method == "POST":
        order = Order.objects.create(
            service=service,
            customer_name=request.POST["customer_name"],
            customer_email=request.POST["customer_email"],
            customer_phone=request.POST["customer_phone"],
            amount=service.price
        )

        response = stk_push(
            phone=order.customer_phone,
            amount=order.amount,
            account_ref=f"ORDER-{order.id}",
            description=service.name
        )

        order.checkout_request_id = response.get("CheckoutRequestID")
        order.save()

        return JsonResponse({"status": "pending"})

    return render(request, "place_order.html", {"service": service})
