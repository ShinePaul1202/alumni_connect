from django import forms
from django.contrib.auth.models import User # Import the User model
from .models import Profile # Import your Profile model

# This is the CORRECTED version of your registration form
class UserRegisterForm(forms.ModelForm):
    # We add password and confirm_password fields manually because the User model only stores the hashed password
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Create a Password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm Your Password'
        })
    )

    class Meta:
        model = User # Tell the form to use the built-in User model
        fields = ['username', 'email'] # The fields we want from the User model

        # Add placeholders for the fields from the User model
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Choose a Username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Your Email Address'}),
        }
    
    # This is a special function to check if the two password fields match
    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return confirm_password


# Your ProfileForm is likely correct, but here it is for completeness
class ProfileForm(forms.ModelForm):
    DEPARTMENT_CHOICES = [
        ('', 'Select your Department'), 
        ('Computer Science', 'Computer Science'), 
        ('Electrical Engineering', 'Electrical Engineering'),
        ('Mechanical Engineering', 'Mechanical Engineering'),
    ]
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('alumni', 'Alumni'),
    ]

    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.Select(attrs={'id': 'id_user_type'})
    )
    department = forms.ChoiceField(
        choices=DEPARTMENT_CHOICES, 
        widget=forms.Select()
    )
    graduation_year = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Graduation Year'})
    )
    currently_employed = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'id': 'id_currently_employed'})
    )
    had_past_job = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'id': 'id_had_past_job'})
    )
    job_title = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Current Job Title'}))
    company_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Current Company Name'}))
    past_job_title = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Past Job Title'}))
    past_company_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Past Company Name'}))

    class Meta:
        model = Profile
        fields = [
            'user_type', 'department', 'graduation_year', 
            'currently_employed', 'had_past_job',
            'job_title', 'company_name', 'past_job_title', 'past_company_name'
        ]