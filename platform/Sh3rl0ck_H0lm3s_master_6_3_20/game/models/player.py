import uuid
from player.models import Group
from .game import Clue
from django.db import models
from common.validators import Validator
from django.contrib.auth.models import User


class GroupGameCase(models.Model):
    game = models.ForeignKey('game.Game', on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    case = models.ForeignKey('game.Case', on_delete=models.CASCADE)
    start_date = models.DateTimeField(blank=True, null=True)
    finish_date = models.DateTimeField(blank=True, null=True)
    docker_image_name = models.CharField(max_length=32)
    docker_container_name = models.CharField(max_length=32, blank=True)
    protocol = models.CharField(max_length=16, default='ssh')
    username = models.CharField(max_length=64)
    password = models.CharField(max_length=64)
    total_score = models.IntegerField(validators=[Validator.validate_positive_number], default=0)

    class Meta:
        unique_together = ['game', 'group', 'case']


class GroupEvent(models.Model):
    group_game_case = models.ForeignKey(GroupGameCase, on_delete=models.CASCADE)
    event = models.ForeignKey('game.Event', on_delete=models.CASCADE)
    start_date = models.DateTimeField(blank=True, null=True)
    finish_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = ['group_game_case', 'event']


class GroupArtifactInfo(models.Model):
    group_game_case = models.ForeignKey(GroupGameCase, on_delete=models.CASCADE)
    group_event = models.ForeignKey(GroupEvent, on_delete=models.CASCADE)
    artifact = models.ForeignKey('game.Artifact', on_delete=models.CASCADE)
    hidden_info = models.ForeignKey('game.HiddenInfo', on_delete=models.CASCADE)
    info_key = models.CharField(max_length=128, default=uuid.uuid4)
    is_artifact_active = models.BooleanField(default=False)
    artifact_path = models.CharField(max_length=256)

    class Meta:
        unique_together = ['group_event', 'artifact', 'hidden_info']

class GroupClue(models.Model):
    clue=models.ForeignKey(Clue, on_delete=models.CASCADE)
    group_artifact=models.ForeignKey(GroupArtifactInfo,on_delete=models.CASCADE)
    available=models.BooleanField(default=False)
    
class GroupResponse(models.Model):
    group_artifact_info = models.OneToOneField(GroupArtifactInfo, on_delete=models.CASCADE, primary_key=True)
    group_game_case = models.ForeignKey(GroupGameCase, on_delete=models.CASCADE)
    player_comment = models.CharField(max_length=4000, blank=True, null=True)
    response_date = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(validators=[Validator.validate_positive_number], default=0)


class PlayerRating(models.Model):
    group_response = models.ForeignKey(GroupResponse, on_delete=models.CASCADE)
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(validators=[Validator.validate_positive_number], default=0)
    

class LearnActivity(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    code=models.IntegerField(validators=[Validator.validate_positive_number], default=0)
    date = models.DateTimeField(auto_now_add=True)
    related=models.IntegerField(validators=[Validator.validate_positive_number], default=0)
    description=models.CharField(max_length=4000, blank=True, null=True)
