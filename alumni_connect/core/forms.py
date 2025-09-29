# C:\project\alumni_connect\core\forms.py

from django import forms
from django.contrib.auth.models import User
from .models import Profile

# --- REGISTRATION FORM ---
class RegistrationForm(forms.Form):
    DEPARTMENT_CHOICES = [
        ('', 'Select your Department'),
        ('MCA', 'Master of Computer Applications'),
        ('Computer Science', 'Computer Science'), 
        ('Electrical Engineering', 'Electrical Engineering'),
        ('Mechanical Engineering', 'Mechanical Engineering'),
        ('Civil Engineering', 'Civil Engineering'),
        ('Biotechnology', 'Biotechnology'),
        ('Information Technology', 'Information Technology'),
        ('Electronics and Communication', 'Electronics and Communication'),
        ('Industrial Engineering', 'Industrial Engineering'),
        ('Materials Science', 'Materials Science'),
        ('Architecture', 'Architecture'),
        ('Other', 'Other'),
    ]

    full_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'Your Full Name (e.g., Shine Paul)'}))
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'Admission No.(no space needed)'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Your Email Address'}))
    password = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'placeholder': 'Create a Password'}), label="Password")
    password2 = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Your Password'}), label="Confirm Password")

    user_type = forms.ChoiceField(choices=[('student', 'Student'), ('alumni', 'Alumni')], widget=forms.Select(attrs={'id': 'id_user_type'}))
    department = forms.ChoiceField(choices=DEPARTMENT_CHOICES)
    department_other = forms.CharField(
        max_length=100, 
        required=False, # This field is not required by default
        label="Your Department Name",
        widget=forms.TextInput(attrs={'placeholder': 'Please specify your department'})
    )
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
        department_choice = cleaned_data.get('department')
        department_other_text = cleaned_data.get('department_other')

        if department_choice == 'Other' and not department_other_text:
            self.add_error('department_other', 'This field is required when you select "Other".')
        
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

class ProfileUpdateForm(forms.ModelForm):
    # --- THIS IS THE FIX ---
    # We explicitly define the full_name field to control its label and placeholder
    full_name = forms.CharField(
        max_length=150, 
        required=True, 
        label="Full Name",
        widget=forms.TextInput(attrs={'placeholder': 'Your Full Name'})
    )

    class Meta:
        model = Profile
        # --- MODIFICATION: Add 'full_name' to the beginning of the list ---
        fields = [
            'full_name', 'avatar', 'bio', 
            'currently_employed', 'job_title', 'company_name', 
            'had_past_job', 'past_job_title', 'past_company_name'
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
        # The list now only contains our one, correct field
        fields = ['email_on_connection_accepted']
        
        labels = { 
            # This is now the only label
            'email_on_connection_accepted': 'Email me when a connection request is accepted',
        }
        
        widgets = { 
            # This is now the only widget
            'email_on_connection_accepted': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }

class AccountUserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ['username', 'email']
        help_texts = { 'username': 'This is your unique Admission No. and cannot be changed.', }
        widgets = { 'username': forms.TextInput(attrs={'class': 'form-control'}), 'email': forms.EmailInput(attrs={'class': 'form-control'}), }

    def __init__(self, *args, **kwargs):
        super(AccountUserUpdateForm, self).__init__(*args, **kwargs)
        # self.fields['username'].disabled = True
        self.fields['username'].required = False

class AccountProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['graduation_year']

# --- NEW FORM ADDED FOR SETTINGS PAGE ---
class AccountProfileSettingsForm(forms.ModelForm):
    DEPARTMENT_CHOICES = [
        ('', 'Select your Department'), 
        ('Computer Science', 'Computer Science'), 
        ('Electrical Engineering', 'Electrical Engineering'),
        ('Mechanical Engineering', 'Mechanical Engineering'),
    ]
    department = forms.ChoiceField(choices=DEPARTMENT_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    graduation_year = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2024'}))

    class Meta:
        model = Profile
        fields = ['department', 'graduation_year']