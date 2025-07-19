from django.contrib import admin
from .models import Profile

@admin.action(description='Verify selected users')
def verify_selected_users(modeladmin, request, queryset):
    """
    Custom admin action to mark selected profiles as verified.
    """
    queryset.update(is_verified=True)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for the Profile model.
    """
    
    # --- Columns to display in the main list view ---
    list_display = (
        'full_name',
        'user',
        'is_verified',
        'user_type',
        'department',
        'graduation_year',
        'currently_employed',
        'had_past_job',
    )

    # --- Search functionality ---
    # This adds a search bar at the top of the admin page.
    search_fields = (
        'full_name',          # Search by the user's real name
        'user__username',     # Search by the unique username
        'user__email',        # Search by email address
        'department',         # Search by department
        'graduation_year',    # Search by graduation year
    )

    # --- Filter functionality ---
    # ✅ THIS IS THE SECTION THAT ANSWERS YOUR QUESTION.
    # It adds the filter sidebar on the right.
    list_filter = (
        # Filter by boolean fields (Yes/No options)
        'is_verified',
        'currently_employed',
        'had_past_job',

        # Filter by choice fields (Dropdown of choices)
        'user_type',
        'department',

        # Filter by a numeric field (Will show options like 'Any date', 'Today', 'Past 7 days', etc. for dates, or ranges for numbers)
        'graduation_year',
    )

    # --- Custom Actions ---
    # This adds the "Verify selected users" option to the "Actions" dropdown.
    actions = [verify_selected_users]

    # --- Customize the Profile Edit Page ---
    # This organizes the fields into logical sections when you edit a profile.
    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'full_name', 'is_verified')
        }),
        ('Academic Details', {
            'fields': ('user_type', 'department', 'graduation_year')
        }),
        ('Professional History', {
            'fields': ('currently_employed', 'job_title', 'company_name', 'had_past_job', 'past_job_title', 'past_company_name')
        }),
    )
    
    # Make the 'user' field non-editable on the profile page to prevent accidental changes.
    readonly_fields = ('user',)