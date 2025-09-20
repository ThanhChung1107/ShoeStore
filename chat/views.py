from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import ChatRoom, Message
from users.models import User
import json

@login_required
def chat_room(request, room_name):
    room = get_object_or_404(ChatRoom, name=room_name)
    messages = room.messages.all().order_by('timestamp')[:50]
    
    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'messages': messages
    })

@login_required
def admin_chat_dashboard(request):
    if not request.user.is_admin:
        return redirect('home')
    
    # Lấy tất cả các phòng chat
    chat_rooms = ChatRoom.objects.filter(is_active=True)
    
    return render(request, 'admin_dashboard.html', {
        'chat_rooms': chat_rooms
    })

@require_POST
@login_required
def create_chat_room(request):
    if request.user.is_admin:
        return JsonResponse({'error': 'Admins cannot create chat rooms'}, status=403)
    
    # Tạo room name dựa trên user id
    room_name = f'user_{request.user.id}_room'
    
    # Kiểm tra xem room đã tồn tại chưa
    room, created = ChatRoom.objects.get_or_create(
        name=room_name,
        defaults={'is_active': True}
    )
    
    # Thêm user vào room nếu chưa có
    if request.user not in room.participants.all():
        room.participants.add(request.user)
    
    # Thêm admin vào room
    admin_users = User.objects.filter(is_admin=True)
    for admin in admin_users:
        if admin not in room.participants.all():
            room.participants.add(admin)
    
    return JsonResponse({'room_name': room_name})