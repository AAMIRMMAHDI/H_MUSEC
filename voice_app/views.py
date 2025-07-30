from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import VoiceUser
from django.contrib.auth.models import User

@login_required
def dashboard(request):
    users = VoiceUser.objects.all().order_by('-last_connection')
    return render(request, 'voice_app/dashboard.html', {'users': users})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def manage_user(request, user_id, action):
    voice_user = VoiceUser.objects.get(id=user_id)
    
    if action == 'ban':
        voice_user.is_banned = True
        voice_user.is_active = False
    elif action == 'unban':
        voice_user.is_banned = False
    elif action == 'activate':
        voice_user.is_active = True
    elif action == 'deactivate':
        voice_user.is_active = False
    elif action == 'delete':
        voice_user.user.delete()
        return redirect('dashboard')
        
    voice_user.save()
    return redirect('dashboard')