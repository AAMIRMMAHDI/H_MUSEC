import json
import pyaudio
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from .models import VoiceUser

class VoiceConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None
        self.audio = None
        self.stream = None

    async def connect(self):
        self.room_name = "voice_room"
        self.room_group_name = f"voice_{self.room_name}"
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            output=True,
            frames_per_buffer=1024,
            start=False
        )
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # ثبت کاربر
        if self.scope["user"].is_authenticated:
            await self.register_user()

    async def disconnect(self, close_code):
        # غیرفعال کردن کاربر
        if self.scope["user"].is_authenticated:
            await self.unregister_user()
            
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()

    @sync_to_async
    def register_user(self):
        user = self.scope["user"]
        VoiceUser.objects.update_or_create(
            user=user,
            defaults={
                'is_active': True,
                'ip_address': self.scope["client"][0]
            }
        )

    @sync_to_async
    def unregister_user(self):
        user = self.scope["user"]
        VoiceUser.objects.filter(user=user).update(is_active=False)

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data:
            # بررسی وضعیت کاربر
            user = self.scope["user"]
            if not user.is_authenticated:
                await self.close()
                return
                
            # ارسال صدا به همه کاربران
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'voice_message',
                    'bytes': bytes_data,
                    'sender': user.username
                }
            )

    async def voice_message(self, event):
        await self.send(bytes_data=event['bytes'])