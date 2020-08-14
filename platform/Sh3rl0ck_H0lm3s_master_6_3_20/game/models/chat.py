from django.db import models
from .player import GroupGameCase
from .game import Character, Message


class Contact(models.Model):
    group_game_case = models.ForeignKey(GroupGameCase, on_delete=models.CASCADE)
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    avatar = models.CharField(max_length=512, blank=True, null=True)
    is_online = models.BooleanField(default=True)
    last_login = models.DateTimeField(blank=True, null=True)


class Conversation(models.Model):
    group_game_case = models.ForeignKey(GroupGameCase, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)


class ChatMessage(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    story_message = models.ForeignKey(Message, on_delete=models.CASCADE, blank=True, null=True)
    is_bot_message = models.BooleanField(default=True)
    text_message = models.CharField(max_length=4000)
    date_message = models.DateTimeField(auto_now_add=True)
    unread_message = models.BooleanField(default=True)
