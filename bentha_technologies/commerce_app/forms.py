from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import *

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['full_name', 'profile_picture', 'bio', 'location', 'website', 'date_of_birth']
# Create your forms here.
class SignupForm(forms.Form):
    username = forms.CharField(label='Username', max_length=150)
    email = forms.EmailField(label='Email')
    phone_number = forms.CharField(label='Phone Number')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match")

class LoginForm(AuthenticationForm):
    # currently Not in use -- Hard to implement
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class NewUserForm(UserCreationForm):
	email = forms.EmailField(required=True)

	class Meta:
		model = User
		fields = ("username", "email", "password1", "password2")

	def save(self, commit=True):
		user = super(NewUserForm, self).save(commit=False)
		user.email = self.cleaned_data['email']
		if commit:
			user.save()
		return user

class SoftwareRequestForm(forms.ModelForm):
    class Meta:
        model = SoftwareRequest
        fields = '__all__'

class StudentEnrollForm(forms.ModelForm):
    class Meta:
        model = Student_Enrollment
        fields = '__all__'



class JobApplicationForm(forms.Form):
    full_name = forms.CharField(max_length=200, required=True, label="Full Name")
    email = forms.EmailField(required=True, label="Email Address")
    phone_number = forms.CharField(max_length=20, required=True, label="Phone Number")
    resume = forms.FileField(required=False, label="Upload Resume")
    cover_letter = forms.FileField(required=False, label="Upload Cover Letter")

class Cyber_ServiceForm(forms.ModelForm):
    class Meta:
        model = Cyber_Service
        fields = '__all__'

class OrderForm(forms.ModelForm):
    customer_phone = forms.CharField(label="Phone Number")

    class Meta:
        model = Cyber_Order
        fields = '__all__'

class LoanRecipientForm(forms.ModelForm):
    class Meta:
        model = LoanRecipient
        fields = ['name', 'payroll_number', 'phone_number', 'loan_amount']