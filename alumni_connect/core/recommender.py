# core/recommender.py

from .models import Profile, Connection, SearchHistory
from django.db.models import Q
import re
from collections import Counter

# A comprehensive dictionary of keywords relevant to each department.
# This is the "knowledge base" for the AI.
DEPARTMENT_KEYWORDS = {
    'Computer Science': [
        'software', 'developer', 'engineer', 'data', 'programmer', 'tech', 'ai', 'ml', 
        'web', 'app', 'backend', 'frontend', 'devops', 'cloud', 'cybersecurity', 'network'
    ],
    'Information Technology': [
        'it', 'information', 'technology', 'systems', 'analyst', 'network', 'support',
        'cybersecurity', 'database', 'administrator', 'cloud'
    ],
    'Electronics and Communication': [
        'electronics', 'communication', 'ece', 'hardware', 'embedded', 'vlsi', 'signal',
        'telecom', 'rf', 'semiconductor', 'firmware'
    ],
    'Electrical Engineering': [
        'electrical', 'power', 'systems', 'grid', 'energy', 'control', 'automation',
        'robotics', 'hardware', 'instrumentation'
    ],
    'Mechanical Engineering': [
        'mechanical', 'design', 'manufacturing', 'automotive', 'hvac', 'thermal', 
        'fluid', 'robotics', 'aerospace', 'thermodynamics', 'cad'
    ],
    'Civil Engineering': [
        'civil', 'structural', 'construction', 'geotechnical', 'transportation', 
        'urban', 'planning', 'infrastructure', 'environmental', 'surveying'
    ],
    'Chemical Engineering': [
        'chemical', 'process', 'plant', 'petroleum', 'refinery', 'polymers', 'materials'
    ],
    'Aerospace Engineering': [
        'aerospace', 'aeronautical', 'propulsion', 'avionics', 'spacecraft', 'satellite',
        'aircraft', 'defense', 'uav'
    ],
    'Biotechnology': [
        'biotech', 'biotechnology', 'pharmaceutical', 'research', 'scientist', 'genetics',
        'clinical', 'lab', 'laboratory', 'molecular', 'biology'
    ],
    'Industrial Engineering': [
        'industrial', 'supply', 'chain', 'logistics', 'operations', 'quality', 'six', 'sigma',
        'manufacturing', 'process', 'improvement'
    ],
    'Materials Science': [
        'materials', 'science', 'polymers', 'ceramics', 'composites', 'nanotechnology',
        'metallurgy'
    ],
    'Architecture': [
        'architect', 'architecture', 'urban', 'design', 'planning', 'building', 'autocad',
        'revit', 'bim'
    ],
    'MCA': [ # Master of Computer Applications
        'software', 'developer', 'engineer', 'data', 'programmer', 'tech', 'ai', 'ml', 
        'web', 'app', 'backend', 'frontend', 'devops', 'cloud', 'cybersecurity', 'network',
        'analyst', 'systems', 'database'
    ],
}


def get_recommendations(profile_to_recommend_for, base_queryset=None):
    """
    Generates a scored and sorted list of recommendations for any given profile.
    This is a Hybrid Recommender using:
    1. Content-Based Filtering (department, job, bio)
    2. Behavioral Personalization (search history)
    3. Collaborative Filtering (connections of connections - "friends-of-friends")
    """
    
    is_searching = base_queryset is not None
    current_user = profile_to_recommend_for.user

    # --- 1. GATHER DATA FOR PERSONALIZATION ---
    
    # Get IDs of people the user is already connected to (Level 1 connections)
    user_connections_qs = Connection.objects.filter(
        (Q(sender=current_user) | Q(receiver=current_user)),
        status=Connection.Status.ACCEPTED
    )
    level1_connection_ids = {
        conn.sender_id if conn.receiver == current_user else conn.receiver_id 
        for conn in user_connections_qs
    }
    
    # --- NEW: LinkedIn-style "Friends-of-Friends" Logic ---
    # Find who the user's connections are connected to (Level 2 connections)
    level2_connections_qs = Connection.objects.filter(
        (Q(sender_id__in=level1_connection_ids) | Q(receiver_id__in=level1_connection_ids)),
        status=Connection.Status.ACCEPTED
    )
    level2_profile_ids = Counter()
    for conn in level2_connections_qs:
        friend_of_friend_id = conn.sender_id if conn.receiver_id in level1_connection_ids else conn.receiver_id
        # Exclude the user themselves and their direct connections
        if friend_of_friend_id != current_user.id and friend_of_friend_id not in level1_connection_ids:
            level2_profile_ids[friend_of_friend_id] += 1 # Count mutual connections

    # Analyze connections to find preferred departments and companies
    connected_profiles = Profile.objects.filter(user_id__in=level1_connection_ids)
    connected_departments = Counter(p.department for p in connected_profiles)
    connected_companies = Counter(p.company_name for p in connected_profiles if p.company_name)

    # Analyze search history
    recent_searches = current_user.search_history.all()[:10]
    searched_departments = Counter(s.department for s in recent_searches if s.department)
    searched_companies = Counter(s.company for s in recent_searches if s.company)

    # --- 2. GET THE ALUMNI TO SCORE ---
    if is_searching:
        profiles_to_score = base_queryset
    else:
        # By default, don't recommend people the user is already connected to
        profiles_to_score = Profile.objects.filter(user_type='alumni', is_verified=True).exclude(user=current_user).exclude(user_id__in=level1_connection_ids)
    
    # --- 3. SCORE EACH ALUMNUS ---
    user_department = (profile_to_recommend_for.department or "").strip().lower()
    user_company = (profile_to_recommend_for.company_name or "").strip().lower()
    user_bio_words = set(re.findall(r'\b\w+\b', profile_to_recommend_for.bio.lower())) if profile_to_recommend_for.bio else set()
    user_dept_keywords = set(DEPARTMENT_KEYWORDS.get(profile_to_recommend_for.department, []))
            
    scored_profiles = []
    for target_profile in profiles_to_score:
        score = 0
        
        # --- A. CONTENT-BASED SCORING ---
        target_department = (target_profile.department or "").strip().lower()
        target_company = (target_profile.company_name or "").strip().lower()
        target_bio_words = set(re.findall(r'\b\w+\b', target_profile.bio.lower())) if target_profile.bio else set()

        if profile_to_recommend_for.user_type == 'student':
            if target_department and user_department and target_department == user_department: score += 50
            if user_dept_keywords and target_profile.job_title:
                job_words = set(re.findall(r'\b\w+\b', target_profile.job_title.lower()))
                score += len(user_dept_keywords.intersection(job_words)) * 15
        else: # User is an Alumnus
            if target_company and user_company and target_company == user_company: score += 40
            if user_dept_keywords and target_profile.job_title:
                job_words = set(re.findall(r'\b\w+\b', target_profile.job_title.lower()))
                score += len(user_dept_keywords.intersection(job_words)) * 20
            if target_department and user_department and target_department == user_department: score += 15

        if user_bio_words and target_bio_words:
            score += len(user_bio_words.intersection(target_bio_words)) * 5
        if target_profile.job_title: score += 5

        # --- B. BEHAVIORAL & COLLABORATIVE SCORING ---
        score += connected_departments.get(target_profile.department, 0) * 20
        score += searched_departments.get(target_profile.department, 0) * 10
        if target_profile.company_name:
            score += connected_companies.get(target_profile.company_name, 0) * 20
            score += searched_companies.get(target_profile.company_name, 0) * 10
            
        # Add a major score boost for "friends of friends"
        # Each mutual connection gives 30 points.
        score += level2_profile_ids.get(target_profile.user.id, 0) * 30

        if is_searching:
            scored_profiles.append({'profile': target_profile, 'score': score})
        elif score > 0:
            scored_profiles.append({'profile': target_profile, 'score': score})
            
    # --- 4. SORT AND RETURN ---
    sorted_profiles = sorted(scored_profiles, key=lambda x: x['score'], reverse=True)
    return sorted_profiles