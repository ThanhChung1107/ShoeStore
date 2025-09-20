import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import ChatRoom, Message, User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        
        # Kiểm tra xem user có được phép tham gia phòng chat không
        user = self.scope["user"]
        if user == AnonymousUser():
            await self.close()
        else:
            # Tham gia room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()

    async def disconnect(self, close_code):
        # Rời khỏi room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Nhận message từ WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender_id = text_data_json['sender_id']
        
        # Lưu message vào database
        room = await self.get_room(self.room_name)
        sender = await self.get_user(sender_id)
        saved_message = await self.save_message(room, sender, message)
        
        # Gửi message đến room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': sender_id,
                'sender_name': sender.username,
                'timestamp': saved_message.timestamp.isoformat()
            }
        )

    # Nhận message từ room group
    async def chat_message(self, event):
        message = event['message']
        sender_id = event['sender_id']
        sender_name = event['sender_name']
        timestamp = event['timestamp']
        
        # Gửi message đến WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender_id': sender_id,
            'sender_name': sender_name,
            'timestamp': timestamp
        }))
    
    @database_sync_to_async
    def get_room(self, room_name):
        return ChatRoom.objects.get(name=room_name)
    
    @database_sync_to_async
    def get_user(self, user_id):
        return User.objects.get(id=user_id)
    
    @database_sync_to_async
    def save_message(self, room, sender, content):
        return Message.objects.create(room=room, sender=sender, content=content)