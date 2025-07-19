from django import forms
from django.contrib.auth.models import User
from django.utils.text import slugify

class RegistrationForm(forms.Form):
    DEPARTMENT_CHOICES = [
        ('', 'Select your Department'), 
        ('Computer Science', 'Computer Science'), 
        ('Electrical Engineering', 'Electrical Engineering'),
        ('Mechanical Engineering', 'Mechanical Engineering'),
    ]

    # --- User Account Fields ---
    full_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'Your Full Name (e.g., Shine Paul)'}))
    
    # ✅ ADD THE USERNAME FIELD
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'Admission No.(no space needed)'}))
    
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Your Email Address'}))
    password = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'placeholder': 'Create a Password'}), label="Password")
    password2 = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Your Password'}), label="Confirm Password")

    # --- Profile Fields ---
    user_type = forms.ChoiceField(choices=[('student', 'Student'), ('alumni', 'Alumni')], widget=forms.Select(attrs={'id': 'id_user_type'}))
    department = forms.ChoiceField(choices=DEPARTMENT_CHOICES)
    graduation_year = forms.IntegerField(required=True, widget=forms.NumberInput(attrs={'placeholder': 'Graduation Year'}))
    
    # ... (rest of your profile fields) ...
    currently_employed = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'id': 'id_currently_employed'}))
    job_title = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Current Job Title'}))
    company_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Current Company Name'}))
    had_past_job = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'id': 'id_had_past_job'}))
    past_job_title = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Past Job Title'}))
    past_company_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Past Company Name'}))


    # ✅ ADD VALIDATION FOR THE USERNAME
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Check for spaces
        if ' ' in username:
            raise forms.ValidationError("Username cannot contain spaces.")
        # Check if username is already taken
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