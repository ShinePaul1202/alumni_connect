from django.contrib import admin
from django.contrib.auth.models import User
from .models import Profile

@admin.action(description='Verify selected users')
def verify_selected_users(modeladmin, request, queryset):
    queryset.update(is_verified=True)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'user_type',
        'department',
        'graduation_year',
        'is_verified',
        'currently_employed',
        'had_past_job'
    )
    list_filter = (
        'user_type',
        'department',
        'graduation_year',
        'is_verified',
        'currently_employed',
        'had_past_job'
    )
    search_fields = (
        'user__username',
        'user__email',
        'department',
        'job_title',
        'company_name',
        'past_job_title',
        'past_company_name'
    )
    # ✅ Add this to show all fields in the form
    fields = (
        'user',
        'user_type',
        'department',
        'graduation_year',
        'is_verified',
        'currently_employed',
        'job_title',
        'company_name',
        'had_past_job',
        'past_job_title',
        'past_company_name'
    )
    actions = [verify_selected_users] 


