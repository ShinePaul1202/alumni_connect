# C:\project\alumni_connect\core\views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
# MODIFICATION: Imported the new form
from .forms import (
    RegistrationForm, UserUpdateForm, ProfileUpdateForm, SettingsForm, 
    AccountUserUpdateForm, AccountProfileUpdateForm, AccountProfileSettingsForm
)
from .models import Profile

# --- AUTH & ROUTING VIEWS ---
def home_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile.user_type == 'student':
            return redirect('core:student_dashboard')
        elif hasattr(request.user, 'profile') and request.user.profile.user_type == 'alumni':
            return redirect('core:alumni_dashboard')
        else:
            return redirect('core:logout')
    else:
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
                username=cleaned_data['username'], email=cleaned_data['email'],
                password=cleaned_data['password'], first_name=first_name, last_name=last_name
            )
            Profile.objects.create(
                user=new_user, full_name=full_name, user_type=cleaned_data['user_type'],
                department=cleaned_data['department'], graduation_year=cleaned_data.get('graduation_year'),
                currently_employed=cleaned_data.get('currently_employed', False),
                job_title=cleaned_data.get('job_title', ''), company_name=cleaned_data.get('company_name', ''),
                had_past_job=cleaned_data.get('had_past_job', False),
                past_job_title=cleaned_data.get('past_job_title', ''), past_company_name=cleaned_data.get('past_company_name', '')
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
    messages.success(request, "You have been successfully logged out.")
    return redirect('core:login')

# --- USER-SPECIFIC DASHBOARD AND PROFILE VIEWS ---
@login_required
def student_dashboard_view(request):
    profile = request.user.profile
    suggested_alumni = []
    if profile.is_verified:
        suggested_alumni = Profile.objects.filter(
            user_type='alumni', is_verified=True, department=profile.department
        ).exclude(user=request.user)
    context = {
        'profile': profile, 'alumni_count': Profile.objects.filter(user_type='alumni', is_verified=True).count(),
        'suggested_alumni': suggested_alumni
    }
    return render(request, 'core/student_dashboard.html', context)

@login_required
def alumni_dashboard_view(request):
    profile = request.user.profile
    recent_alumni = []
    if profile.is_verified:
        recent_alumni = Profile.objects.filter(
            user_type='alumni', is_verified=True
        ).exclude(user=request.user).order_by('-user__date_joined')[:5]
    context = { 'profile': profile, 'student_message_count': 0, 'recent_alumni': recent_alumni }
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
    profile = request.user.profile 
    context = { 'u_form': u_form, 'p_form': p_form, 'profile': profile }
    return render(request, 'core/profile_update.html', context)

# --- MODIFIED VIEW TO HANDLE NEW PROFILE FIELDS ---
@login_required
def account_settings_view(request):
    if request.method == 'POST':
        if 'update_account' in request.POST:
            user_form = AccountUserUpdateForm(request.POST, instance=request.user)
            profile_form = AccountProfileSettingsForm(request.POST, instance=request.user.profile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Your account information has been updated successfully!')
            else:
                messages.error(request, 'Please correct the errors below.')
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was successfully updated!')
            else:
                messages.error(request, 'There was an error updating your password.')
        elif 'update_notifications' in request.POST:
            settings_form = SettingsForm(request.POST, instance=request.user.profile)
            if settings_form.is_valid():
                settings_form.save()
                messages.success(request, 'Your notification settings have been updated.')
            else:
                messages.error(request, 'Could not update notification settings.')
        return redirect('core:account_settings')
    else:
        user_form = AccountUserUpdateForm(instance=request.user)
        profile_form = AccountProfileSettingsForm(instance=request.user.profile)
        password_form = PasswordChangeForm(request.user)
        settings_form = SettingsForm(instance=request.user.profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form,
        'settings_form': settings_form
    }
    return render(request, 'core/account/account_settings.html', context)

# --- UNUSED VIEWS (CAN BE REMOVED LATER) ---
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

@login_required
def account_update_view(request):
    if request.method == 'POST':
        user_form = AccountUserUpdateForm(request.POST, instance=request.user)
        profile_form = AccountProfileUpdateForm(request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your account information has been updated successfully!')
            return redirect('core:account_settings')
    else:
        user_form = AccountUserUpdateForm(instance=request.user)
        profile_form = AccountProfileUpdateForm(instance=request.user.profile)
    context = { 'user_form': user_form, 'profile_form': profile_form }
    return render(request, 'core/account/account_update.html', context)