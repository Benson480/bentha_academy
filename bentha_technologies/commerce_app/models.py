from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.files import File
import textwrap
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
import random
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password

# Main model for items
class Item(models.Model):
    name = models.CharField(max_length=255)
    Date = models.DateField(null=True,db_index=True)
    Supplier = models.CharField(max_length=255, null=True, db_index=True)
    def __str__(self):
            return f"{self.name}"

class Item_Price(models.Model):
    Date = models.DateField(null=True,db_index=True)
    Item_Product = models.ForeignKey(Item,on_delete=models.CASCADE, db_index=True)
    Unit_Of_Measure_Choices = (
    ("Kg", "Kg"),
    ("Ltr", "Ltr"),
    ("Bag", "Bag"),
    ("Pcs", "Pcs"),
    ("Pcs", "Pc"),
    ("Carton", "Carton"),
    ("Pkt", "Pkt"),
    ("Tons", "Tons"),
    ("Bottles", "Bottles"),
    ("Dose", "Dose"),
    ("Course", "Course"),
    ("Square Meter", "Square Meter"),
    ("Case", "Case"),
    ("Custom Software", "Custom Software"),
    )
    Unit_Of_Measure = models.CharField(max_length=255,null=True,db_index=True,
                  choices=Unit_Of_Measure_Choices
                  )
    price_ksh = models.FloatField(blank=True, db_index=True, null=True, default=0)
    Duration = models.CharField(max_length=255, null=True, db_index=True)
    Price_Negotiable = models.CharField(max_length=255, null=True, db_index=True)


    def __str__(self):
        return str(self.Item_Product)



# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name



class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    contact_details = models.OneToOneField(Contact, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    announcement_type = models.CharField(max_length=20, choices=[
        ('news', 'News'),
        ('advertisement', 'Advertisement'),
        ('video', 'Video Upload'),
        ('Update', 'Update'),
    ])
    image = models.ImageField(upload_to='announcement_images/', blank=True, null=True)
    image_description = models.CharField(max_length=255, blank=True, null=True, help_text="Description of the image")
    video_url = models.URLField(blank=True, null=True)
    countdown_to = models.DateTimeField(blank=True, null=True)
    venue = models.CharField(max_length=100, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title



class ItemImage(models.Model):
    Product = models.ForeignKey(Item,on_delete=models.CASCADE, db_index=True, blank=True, null=True)
    categories = models.ManyToManyField(Category, related_name='images', blank=True)
    Date = models.DateField(null=True, db_index=True, blank=True)
    image = models.ImageField(upload_to='images/')
    uploaded_at = models.DateTimeField(auto_now_add=True) # Auto generated with datetime.now()
    title = models.CharField(max_length=200, null=True, db_index=True, blank=True)
    about_Image = models.TextField(max_length=2000, null=True, blank=True)

    def availability_description(self):
        if self.Date:
            return f"Available in {self.Date.strftime('%B %d, %Y')}"
        else:
            return "Availability not specified"
    Status_Choices = (
    ("default", "Select availability..."),
    ("available", "Available now"),
    ("Service available", " Service Available now"),
    ("Course available", "Course available"),
    ("Out of Stock", "Out of Stock"),
    ("future", availability_description),
    )

    status = models.CharField(max_length=255,null=True,db_index=True,
                  choices=Status_Choices
                  )

    def save(self, *args, **kwargs):
        # Wrap the about_Image text before saving
        if self.about_Image:
            self.about_Image = textwrap.fill(self.about_Image, width=40)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.Product} Image uploaded at {self.uploaded_at}"


    @property
    def UnitOfMeasure(self):
        getUnitOfMeasure = Item_Price.objects.all()
        for uom in getUnitOfMeasure:
            if uom.Item_Product == self.Product:
                return str(uom.Unit_Of_Measure)

    @property
    def price(self):
        getprice = Item_Price.objects.all()
        for a in getprice:
            if a.Item_Product == self.Product:
                Price = round(a.price_ksh, 2)
                formatted_price = "{:,.2f}".format(Price)
                # Remove commas from the formatted price string and then convert to float
                formatted_price = formatted_price.replace(',', '')
                return float(formatted_price)

        # If no matching price is found, return 0.0 as a float
        return 0.0


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Add fields for user profile details like name, picture, etc.
    full_name = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.user.username

# Create the UserProfile instance when a new User is registered
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# Save the UserProfile instance when the User is saved
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        # Create a UserProfile instance if it doesn't exist
        UserProfile.objects.create(user=instance)


#Student enrollment in the course model
class Student_Enrollment(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    nationality = models.CharField(max_length=100)
    guardian_name = models.CharField(max_length=100)
    guardian_phone = models.CharField(max_length=20)
    guardian_email = models.EmailField()
    previous_school = models.CharField(max_length=100)
    year_of_study = models.IntegerField()
    date_enrolled = models.DateField(auto_now_add=True)
    Do_you_have_smartphone_or_computer = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Career(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField()
    responsibilities = models.TextField()
    published_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class JobApplication(models.Model):
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    cover_letter = models.FileField(upload_to='cover_letter/', null=True, blank=True)
    career = models.ForeignKey(Career, on_delete=models.CASCADE)

    def __str__(self):
        return f"Application for {self.career.title} by {self.full_name}"


class SoftwareRequest(models.Model):
    CUSTOMER_TYPE_CHOICES = (
        ('Individual', 'Individual'),
        ('Small Business', 'Small Business'),
        ('Enterprise', 'Enterprise'),
    )
    SOFTWARE_TYPE_CHOICES = (
        ('Mobile Application', 'Mobile Application'),
        ('Website', 'Website'),
        ('Desktop Application', 'Desktop Application'),
        ('Other', 'Other'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    customer_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)  # New field for phone contact
    address = models.CharField(max_length=255, blank=True)  # New field for physical address

    customer_type = models.CharField(max_length=50, choices=CUSTOMER_TYPE_CHOICES)
    software_type = models.CharField(max_length=50, choices=SOFTWARE_TYPE_CHOICES)

    project_description = models.TextField(blank=True, null=True)  # New field for a detailed project description
    budget_in_Ksh = models.DecimalField(max_digits=10, decimal_places=2)
    preferred_deadline = models.DateField(blank=True, null=True)  # New field for a preferred deadline
    target_customers = models.TextField(blank=True, null=True)
    additional_specifications = models.TextField(blank=True)

    is_urgent = models.BooleanField(default=False)  # New field to indicate urgency
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.software_type}"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    # Add any other fields you need

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    image = models.ForeignKey(ItemImage, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    # Add any other fields you need


class Activity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    user_logout = models.BooleanField(default=False)
    url = models.CharField(max_length=255, blank=True, null=True)  # Add a URL field

    def __str__(self):
        return f'{self.user} - {self.activity_type} - {self.timestamp}'

class Course(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=255)
    instructor = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_on = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user.username} - {self.course.name}"

class Material(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='course_materials/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

class StudentProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    progress = models.IntegerField(default=0)  # Percentage of course completed
    last_updated = models.DateField(auto_now=True)
    modules_completed = models.IntegerField(default=0)  # Track completed modules

    def __str__(self):
        return f"{self.user.username} - {self.course.name} - {self.modules_completed} modules completed"

class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    max_score = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.title

class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField()
    max_score = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.title

class Exam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    max_score = models.IntegerField(blank=True, null=True)

    # 🔐 Exam access password (hashed)
    access_password = models.CharField(max_length=255, blank=True, null=True)

    def set_password(self, raw_password):
        self.access_password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.access_password)

    def __str__(self):
        return self.title

    def calculate_max_score(self):
        # Assuming each question is worth 1 point; adjust as needed
        return self.questions.count()

    def save(self, *args, **kwargs):
        creating = self.pk is None  # Check if it's a new object (no primary key yet)
        super().save(*args, **kwargs)  # First, save normally (assigns a primary key)
        if creating:
            self.max_score = self.calculate_max_score()
            super().save(update_fields=['max_score'])  # Save again only updating max_score


class Question(models.Model):
    quiz = models.ForeignKey(
        "Quiz", on_delete=models.CASCADE, related_name="questions",
        blank=True, null=True
    )
    exam = models.ForeignKey(
        "Exam", on_delete=models.CASCADE, related_name="questions",
        blank=True, null=True
    )
    question_text = models.TextField(blank=True, null=True)
    correct_answer = models.CharField(max_length=255,blank=True, null=True)
    incorrect_answers = models.JSONField(
        default=list,  # Ensure it defaults to an empty list
        help_text="Provide incorrect answers as a list of strings",
        blank=True, null=True
    )

    def __str__(self):
        return f"Q{self.id}: {self.question_text[:50]}..."

    def get_shuffled_answers(self):
        """Return all answers (correct + incorrect) shuffled."""
        answers = list(self.incorrect_answers) + [self.correct_answer]
        random.shuffle(answers)
        return answers

    def clean(self):
        """
        Validation to ensure:
        - A question must belong to either a Quiz or Exam (not both, not neither).
        - No duplicate answers (correct shouldn't appear in incorrect list).
        """
        if not self.quiz and not self.exam:
            raise ValidationError("Question must belong to either a Quiz or an Exam.")
        if self.quiz and self.exam:
            raise ValidationError("Question cannot belong to both a Quiz and an Exam.")
        if self.correct_answer in self.incorrect_answers:
            raise ValidationError("Correct answer cannot be in incorrect answers list.")

    class Meta:
        ordering = ["id"]

@receiver(post_save, sender=Question)
@receiver(post_delete, sender=Question)
def update_exam_max_score(sender, instance, **kwargs):
    try:
        exam = instance.exam
        exam.max_score = exam.calculate_max_score()
        exam.save()
    except ObjectDoesNotExist:
        # Related exam does not exist, safe to ignore
        pass

class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    assignment = models.ForeignKey("Assignment", on_delete=models.CASCADE, blank=True, null=True)
    quiz = models.ForeignKey("Quiz", on_delete=models.CASCADE, blank=True, null=True)
    exam = models.ForeignKey("Exam", on_delete=models.CASCADE, blank=True, null=True)
    submission_file = models.FileField(upload_to='submissions/', blank=True, null=True)
    submission_text = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(blank=True, null=True)
    graded = models.BooleanField(default=False, blank=True, null=True)

    class Meta:
        unique_together = ('user', 'exam')  # ✅ restrict multiple submissions per exam

    def __str__(self):
        return f"Submission by {self.user.username} - {self.exam.title if self.exam else 'N/A'} - Score: {self.score}"

class Grade(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, null=True, blank=True, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, null=True, blank=True, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    passed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.assignment.title if self.assignment else self.exam.title}: {self.score}%"

class Cyber_Service(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    category = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=True, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        # Return a fallback string if name is None
        return self.name if self.name else "Unnamed Service"


class Cyber_Order(models.Model):
    service = models.ForeignKey(Cyber_Service, on_delete=models.CASCADE, null=True, blank=True)
    customer_name = models.CharField(max_length=100, null=True, blank=True)
    customer_email = models.EmailField(null=True, blank=True)
    customer_phone = models.CharField(max_length=15, null=True, blank=True)  # New field for the customer's phone number
    order_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=100, blank=True, null=True)  # To store payment reference

    def __str__(self):
        return f"Order {self.id} - {self.customer_name}" or "Unnamed Service"  # Prevent NoneType error

# Trial version 1 for payment pushback

class Service(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Order(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=True)
    customer_name = models.CharField(max_length=100, null=True)
    customer_email = models.EmailField(null=True)
    customer_phone = models.CharField(max_length=15, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    is_paid = models.BooleanField(default=False)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.customer_name} - {self.service.name}"
    
class NewOrder(models.Model):
    items = models.ManyToManyField(CartItem)
    Item_image = models.ForeignKey(ItemImage, on_delete=models.CASCADE, null=True)  # Establish the relationship
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    # Add any other fields you need


class Robot(models.Model):
    MODEL_CHOICES = [
        ('A1', 'Alpha-1'),
        ('B2', 'Beta-2'),
        ('X9', 'Xenon-9'),
    ]

    model_name = models.CharField(max_length=10, choices=MODEL_CHOICES, default='A1')
    battery_level = models.IntegerField(default=100)
    battery_full = 100
    battery_critical = 10
    working_hours = models.IntegerField(default=0)
    working_hours_limit = models.IntegerField(default=8)
    is_active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_model_name_display()} | Battery: {self.battery_level}%"

    def simulate_work_hour(self):
        if self.is_active:
            self.working_hours += 1
            self.battery_level -= 12  # consume more per task
            if self.working_hours >= self.working_hours_limit or self.battery_level <= self.battery_critical:
                self.is_active = False
            self.save()

    def recharge(self):
        self.battery_level = self.battery_full
        self.working_hours = 0
        self.is_active = True
        self.save()


#Sample model to help send personalized loan messages to clients
class LoanRecipient(models.Model):
    name = models.CharField(max_length=100)
    payroll_number = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15)
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    message_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.loan_amount}"

# Model to store chat messages
class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    user_message = models.TextField()
    bot_reply = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat #{self.id} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
#Mpesa payment option using daraja API
class MpesaTransaction(models.Model):
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    merchant_request_id = models.CharField(max_length=100, blank=True, null=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    result_code = models.CharField(max_length=10, blank=True, null=True)
    result_desc = models.TextField(blank=True, null=True)
    mpesa_receipt = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('SUCCESS', 'Success'),
            ('FAILED', 'Failed'),
            ('TIMEOUT', 'Timeout'),
        ],
        default='PENDING'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone_number} - {self.amount} - {self.status}"