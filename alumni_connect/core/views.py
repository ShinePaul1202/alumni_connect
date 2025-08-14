from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .forms import RegistrationForm, UserUpdateForm, ProfileUpdateForm, SettingsForm
from .models import Profile

# --- AUTH & ROUTING VIEWS ---

# === THIS VIEW IS THE ONLY ONE WE ARE MODIFYING ===
def home_view(request):
    if request.user.is_authenticated:
        # This part for logged-in users remains exactly the same
        if hasattr(request.user, 'profile') and request.user.profile.user_type == 'student':
            return redirect('core:student_dashboard')
        elif hasattr(request.user, 'profile') and request.user.profile.user_type == 'alumni':
            return redirect('core:alumni_dashboard')
        else:
            return redirect('core:logout')
    else:
        # THIS IS THE ONLY CHANGE:
        # Instead of redirecting to login, we now show the animated homepage.
        return render(request, 'core/index.html') 

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            
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

            Profile.objects.create(
                user=new_user,
                user_type=cleaned_data['user_type'],
                department=cleaned_data['department'],
                graduation_year=cleaned_data.get('graduation_year'),
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
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('core:home')
        else:
            messages.error(request, "Invalid username/email or password.")
            return redirect('core:login')
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    # This is the only change: adding a specific message for the logout action.
    messages.success(request, "You have been successfully logged out.")
    return redirect('core:login')


# --- USER-SPECIFIC DASHBOARD AND PROFILE VIEWS (THESE ARE ALL UNCHANGED) ---

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
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('core:profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'core/profile_update.html', context)

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