from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .forms import RegistrationForm, ProfileUpdateForm, SettingsForm
from .models import Profile

# --- AUTH & ROUTING VIEWS ---

def home_view(request):
    """
    Acts as a smart router.
    - If a user is authenticated, it sends them to their correct dashboard.
    - If a user is NOT authenticated, it sends them to the login page.
    """
    if request.user.is_authenticated:
        # Check if the user has a profile and what their user_type is
        if hasattr(request.user, 'profile') and request.user.profile.user_type == 'student':
            return redirect('core:student_dashboard')
        elif hasattr(request.user, 'profile') and request.user.profile.user_type == 'alumni':
            return redirect('core:alumni_dashboard')
        else:
            # Fallback for authenticated users without a valid profile type
            # You could redirect to a profile creation page or just logout
            return redirect('core:logout')
    else:
        # If no one is logged in, show the login page
        return redirect('core:login')

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # The form is valid, so we can access its cleaned data
            cleaned_data = form.cleaned_data
            
            # --- THIS IS THE CORRECTED LOGIC ---
            
            # Step 1: Manually create the User object.
            # We use create_user() because it correctly handles password hashing.
            full_name = cleaned_data.get('full_name', '')
            first_name = full_name.split()[0] if full_name else ''
            last_name = ' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else ''

            new_user = User.objects.create_user(
                username=cleaned_data['username'],
                email=cleaned_data['email'],
                password=cleaned_data['password'],
                first_name=first_name,
                last_name=last_name
            )

            # Step 2: Manually create the Profile object, linking it to the new user.
            # We use .get() for optional fields to avoid errors if they are not submitted.
            Profile.objects.create(
                user=new_user,
                user_type=cleaned_data['user_type'],
                department=cleaned_data['department'],
                graduation_year=cleaned_data.get('graduation_year'),
                # Add all other profile fields from your form
                currently_employed=cleaned_data.get('currently_employed', False),
                job_title=cleaned_data.get('job_title', ''),
                company_name=cleaned_data.get('company_name', ''),
                had_past_job=cleaned_data.get('had_past_job', False),
                past_job_title=cleaned_data.get('past_job_title', ''),
                past_company_name=cleaned_data.get('past_company_name', '')
            )
            
            messages.success(request, 'Welcome aboard! Please sign in to continue.')
            return redirect('core:login')
    else:
        form = RegistrationForm()
        
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    # This view is correct. Redirects to the home_view router on success.
    if request.method == 'POST':
        # Your login logic using authenticate and login
        # Example logic:
        username = request.POST.get('username') # Assuming you use username/email in form
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('core:home') # This sends the user to the home_view router
        else:
            messages.error(request, "Invalid username/email or password.")
            return redirect('core:login')
    return render(request, 'core/login.html')

def logout_view(request):
    # This view is correct. Redirects to login page on success.
    logout(request)
    return redirect('core:login')


# --- USER-SPECIFIC DASHBOARD AND PROFILE VIEWS ---
# (No changes are needed for the views below this line)

@login_required
def student_dashboard_view(request):
    profile = request.user.profile
    suggested_alumni = Profile.objects.filter(
        user_type='alumni', is_verified=True, department=profile.department
    ).exclude(user=request.user)
    context = {
        'profile': profile,
        'alumni_count': Profile.objects.filter(user_type='alumni', is_verified=True).count(),
        'suggested_alumni': suggested_alumni
    }
    return render(request, 'core/student_dashboard.html', context)

@login_required
def alumni_dashboard_view(request):
    profile = request.user.profile
    recent_alumni = Profile.objects.filter(
        user_type='alumni', is_verified=True
    ).exclude(user=request.user).order_by('-user__date_joined')[:5]
    context = {
        'profile': profile,
        'student_message_count': 0,
        'recent_alumni': recent_alumni
    }
    return render(request, 'core/alumni_dashboard.html', context)

@login_required
def profile_view(request):
    profile = request.user.profile
    context = {'profile': profile}
    return render(request, 'core/profile_page.html', context)

@login_required
def profile_update_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('core:profile')
    else:
        form = ProfileUpdateForm(instance=request.user.profile)
    return render(request, 'core/profile_update.html', {'form': form})

@login_required
def settings_view(request):
    if request.method == 'POST':
        form = SettingsForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your settings have been updated.')
            return redirect('core:settings')
    else:
        form = SettingsForm(instance=request.user.profile)
    return render(request, 'core/settings.html', {'form': form})