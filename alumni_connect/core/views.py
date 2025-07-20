from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .forms import RegistrationForm, ProfileUpdateForm
from .models import Profile

# --- THIS VIEW HAS BEEN CORRECTED ---
def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Get data from the validated form
            data = form.cleaned_data
            full_name = data['full_name']
            username = data['username']
            email = data['email']
            password = data['password']

            # --- START OF NEW LOGIC ---
            # Smartly determine if the job checkboxes should be ticked
            currently_employed = bool(data['job_title'] or data['company_name'])
            had_past_job = bool(data['past_job_title'] or data['past_company_name'])
            # --- END OF NEW LOGIC ---

            # Create the user with the username they provided
            user = User.objects.create(
                username=username,
                email=email,
                password=make_password(password)
            )

            # --- START OF CORRECTED PROFILE CREATION ---
            # Create the associated profile, now including ALL job fields
            Profile.objects.create(
                user=user,
                full_name=full_name,
                user_type=data['user_type'],
                department=data['department'],
                graduation_year=data['graduation_year'],
                
                # Save the job data to the database
                currently_employed=currently_employed,
                job_title=data['job_title'],
                company_name=data['company_name'],
                
                had_past_job=had_past_job,
                past_job_title=data['past_job_title'],
                past_company_name=data['past_company_name']
            )
            # --- END OF CORRECTED PROFILE CREATION ---
            
            messages.success(request, 'Welcome aboard! Please sign in to continue.')
            return redirect('login')
    else:
        form = RegistrationForm()
        
    return render(request, 'core/register.html', {'form': form})

# --- This new "home" view is for routing users correctly ---
def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('login')

def login_view(request):
    # (Your existing login_view code... no changes needed)
    if request.method == 'POST':
        identifier = request.POST.get('username')
        password = request.POST.get('password')
        user = None
        if '@' in identifier:
            try:
                user_obj = User.objects.get(email=identifier)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        else:
            user = authenticate(request, username=identifier, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username/email or password. Please try again.")
            return redirect('login')
    return render(request, 'core/login.html')

def logout_view(request):
    # (Your existing logout_view code... no changes needed)
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    # (Your existing dashboard_view code... no changes needed)
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = None
    alumni_count = Profile.objects.filter(user_type='alumni', is_verified=True).count()
    if profile and profile.department:
        suggested_alumni = Profile.objects.filter(
            user_type='alumni', is_verified=True, department=profile.department
        ).exclude(user=request.user).order_by('-user__date_joined')[:5]
    else:
        suggested_alumni = Profile.objects.filter(
            user_type='alumni', is_verified=True
        ).exclude(user=request.user).order_by('-user__date_joined')[:5]
    context = {
        'profile': profile, 'alumni_count': alumni_count, 'message_count': 5,
        'event_count': 2, 'suggested_alumni': suggested_alumni,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def profile_update_view(request):
    # (Your existing profile_update_view code... no changes needed)
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = ProfileUpdateForm(instance=request.user.profile)
    context = {'form': form}
    return render(request, 'core/profile_update.html', context)