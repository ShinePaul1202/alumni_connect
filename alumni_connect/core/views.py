from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .forms import RegistrationForm, ProfileUpdateForm # Import both forms
from .models import Profile

def register_view(request):
    # (Your existing register_view code... no changes needed here)
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            full_name = form.cleaned_data['full_name']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = User.objects.create(username=username, email=email, password=make_password(password))
            Profile.objects.create(
                user=user, full_name=full_name, user_type=form.cleaned_data['user_type'],
                department=form.cleaned_data['department'], graduation_year=form.cleaned_data['graduation_year']
            )
            messages.success(request, 'Welcome aboard! Please sign in to continue.')
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    # (Your existing login_view code... no changes needed here)
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
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    # (Your existing dashboard_view code... no changes needed here)
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

# --- ADD THIS ENTIRE NEW VIEW FOR UPDATING THE PROFILE ---
@login_required
def profile_update_view(request):
    if request.method == 'POST':
        # Pass request.POST for form data and request.FILES for image uploads
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        # For a GET request, show the form pre-filled with the user's current data
        form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'form': form
    }
    return render(request, 'core/profile_update.html', context)

# ADD THIS NEW VIEW
def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('login')