from django import forms
from django.contrib.auth.forms import UserCreationForm # Import the magic form
from django.contrib.auth.models import User
from .models import Profile

# This is the new, robust registration form
class UserRegisterForm(UserCreationForm):
    # We add the email field here because the default UserCreationForm only has username and passwords
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Your Email Address'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        # The fields that will be displayed on the form
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Username(Real Name)'
        self.fields['password1'].widget.attrs['placeholder'] = 'Create a Password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Your Password'


# Your ProfileForm remains the same. It is perfectly fine.
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

    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, widget=forms.Select(attrs={'id': 'id_user_type'}))
    department = forms.ChoiceField(choices=DEPARTMENT_CHOICES, widget=forms.Select())
    graduation_year = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Graduation Year'}))
    currently_employed = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'id': 'id_currently_employed'}))
    had_past_job = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'id': 'id_had_past_job'}))
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