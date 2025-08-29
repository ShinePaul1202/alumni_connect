from django.shortcuts import redirect
from django.urls import resolve, Resolver404
from django.contrib import messages

class AccessControlMiddleware:
    """
    This middleware checks if a user is verified before allowing them
    to access certain pages.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
        # --- IMPORTANT ---
        # List the 'name' of each URL you want to restrict.
        # Find these names in your urls.py file.
        # For example: path('find/', find_alumni_view, name='find_alumni')
        self.RESTRICTED_URL_NAMES = [
            'find_alumni',      # Replace with your actual URL name for searching
            'messages',         # Replace with your actual URL name for messaging
            'view_other_profile'# Replace with your URL name for viewing another user's profile
        ]

    def __call__(self, request):
        # Allow all requests to proceed initially
        response = self.get_response(request)

        # Only run checks for logged-in users who are not administrators
        if not request.user.is_authenticated or request.user.is_staff:
            return response

        # Check if the user's profile is verified
        try:
            is_verified = request.user.profile.is_verified
        except AttributeError:
            # This handles the rare case where a user has no profile
            # In this scenario, we treat them as unverified
            is_verified = False

        # If the user is not verified, check if they are trying to access a restricted page
        if not is_verified:
            try:
                current_url_name = resolve(request.path_info).url_name
            except Resolver404:
                current_url_name = None

            if current_url_name in self.RESTRICTED_URL_NAMES:
                # User is unverified and trying to access a restricted page.
                # Send a warning message.
                messages.warning(request, 'You must be a verified user to access this page.')
                
                # Redirect them to their correct dashboard.
                if request.user.profile.user_type == 'student':
                    return redirect('core:student_dashboard')
                else:
                    return redirect('core:alumni_dashboard')
        
        return response