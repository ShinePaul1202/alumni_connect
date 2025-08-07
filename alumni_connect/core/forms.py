# C:\project\alumni_connect\core\forms.py

from django import forms
from django.contrib.auth.models import User
from .models import Profile

# --- REGISTRATION FORM ---
class RegistrationForm(forms.Form):
    DEPARTMENT_CHOICES = [
        ('', 'Select your Department'), 
        ('Computer Science', 'Computer Science'), 
        ('Electrical Engineering', 'Electrical Engineering'),
        ('Mechanical Engineering', 'Mechanical Engineering'),
    ]

    full_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'Your Full Name (e.g., Shine Paul)'}))
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'Admission No.(no space needed)'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Your Email Address'}))
    password = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'placeholder': 'Create a Password'}), label="Password")
    password2 = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Your Password'}), label="Confirm Password")

    user_type = forms.ChoiceField(choices=[('student', 'Student'), ('alumni', 'Alumni')], widget=forms.Select(attrs={'id': 'id_user_type'}))
    department = forms.ChoiceField(choices=DEPARTMENT_CHOICES)
    graduation_year = forms.IntegerField(required=True, widget=forms.NumberInput(attrs={'placeholder': 'Graduation Year'}))
    currently_employed = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'id': 'id_currently_employed'}))
    job_title = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Current Job Title'}))
    company_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Current Company Name'}))
    had_past_job = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'id': 'id_had_past_job'}))
    past_job_title = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Past Job Title'}))
    past_company_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Past Company Name'}))

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if ' ' in username:
            raise forms.ValidationError("Username cannot contain spaces.")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("password2"):
            raise forms.ValidationError("Passwords do not match. Please try again.")
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

# --- FORM FOR UPDATING USER'S FIRST/LAST NAME ---
class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name']

# --- THIS IS THE CORRECTED FORM ---
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        # Add the editable work-related fields to the list
        fields = [
            'bio', 
            'avatar', 
            'currently_employed', 
            'job_title', 
            'company_name', 
            'had_past_job', 
            'past_job_title', 
            'past_company_name'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'placeholder': 'A short bio to appear on your profile...'}),
            'job_title': forms.TextInput(attrs={'placeholder': 'e.g., Software Engineer'}),
            'company_name': forms.TextInput(attrs={'placeholder': 'e.g., Google'}),
            'past_job_title': forms.TextInput(attrs={'placeholder': 'e.g., Junior Developer'}),
            'past_company_name': forms.TextInput(attrs={'placeholder': 'e.g., Microsoft'}),
        }
        labels = {
            'avatar': 'Change Profile Picture',
            'currently_employed': 'I am currently employed',
            'job_title': 'Current Job Title',
            'company_name': 'Current Company',
            'had_past_job': 'I have past work experience',
            'past_job_title': 'Past Job Title',
            'past_company_name': 'Past Company',
        }

# --- SETTINGS FORM ---
class SettingsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['email_on_new_message']
        labels = {
            'email_on_new_message': 'Email me when I receive a new message',
        }