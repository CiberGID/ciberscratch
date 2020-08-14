import os
from player.models import Course
from django.db import models
from common.validators import Validator
from django.utils import timezone
from enum import Enum


class StoryTypeEnum(Enum):
    PDF = 'pdf'
    CHAT = 'chat'
    EMAIL = 'email'
    HTML='html'
    AUDIO='audio'
    MOVIE='movie'


def get_image_path(instance, filename):
    path = 'photos'
    if isinstance(instance, Case):
        path = 'cases'
    if isinstance(instance, Game):
        path = 'games'
    if isinstance(instance, Character):
        path = 'character'
    return os.path.join(path, str(instance.id), filename)


class StoryType(models.Model):
    name = models.CharField(max_length=64, )
    description = models.CharField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Story(models.Model):
    story_type = models.ForeignKey(StoryType, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return self.name


class Message(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    character = models.ForeignKey('Character', on_delete=models.CASCADE, null=True, blank=True)
    plane_text = models.CharField(max_length=4000, blank=True, null=True)
    file_path = models.FileField(blank=True)
    delay_to_show = models.IntegerField(validators=[Validator.validate_positive_number],
                                        verbose_name="delay to show (seconds)")
    order = models.IntegerField(validators=[Validator.validate_positive_number])

    class Meta:
        ordering = ['order']


class Game(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    description = models.TextField(max_length=4000, blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    published_date = models.DateTimeField(blank=True, null=True)
    is_published = models.BooleanField(default=False)
    game_image = models.ImageField(upload_to=get_image_path, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.is_published and not self.published_date:
            self.published_date = timezone.now()
        elif not self.is_published:
            self.published_date = None
        super(Game, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


# These two auto-delete files from filesystem when they are unneeded:
# @receiver(models.signals.post_delete, sender=Game)
# def auto_delete_file_on_delete(sender, instance, **kwargs):
#     """
#     Deletes file from filesystem
#     when corresponding `MediaFile` object is deleted.
#     """
#     if instance.game_image:
#         file = os.path.join(MEDIA_ROOT, instance.game_image.path)
#         if os.path.isfile(file):
#             os.remove(file)
#
#
# @receiver(models.signals.pre_save, sender=Game)
# def auto_delete_file_on_change(sender, instance, **kwargs):
#     """
#     Deletes old file from filesystem
#     when corresponding `MediaFile` object is updated
#     with new file.
#     """
#     if not instance.pk:
#         return False
#
#     try:
#         old_file = os.path.join(MEDIA_ROOT, Game.objects.get(pk=instance.pk).game_image.path)
#     except Game.DoesNotExist:
#         return False
#
#     new_file = os.path.join(MEDIA_ROOT, instance.game_image.path)
#     if not old_file == new_file:
#         if os.path.isfile(old_file):
#             os.remove(old_file)


class Case(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    story = models.OneToOneField(Story, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    description = models.TextField(max_length=3000, blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    published_date = models.DateTimeField(blank=True, null=True)
    is_published = models.BooleanField(default=False)
    base_img_path = models.FilePathField(path=None)
    case_image = models.ImageField(upload_to=get_image_path, blank=True, null=True)
    protocol = models.CharField(max_length=16, default='ssh')
    terminal_username = models.CharField(max_length=64, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.is_published and not self.published_date:
            self.published_date = timezone.now()
        elif not self.is_published:
            self.published_date = None
        super(Case, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class ArtifactType(models.Model):
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=2000, blank=True, null=True)

    def __str__(self):
        return self.name


class Artifact(models.Model):
    artifact_type = models.ForeignKey(ArtifactType, on_delete=models.CASCADE)
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=2000, blank=True, null=True)
    path = models.CharField(max_length=256)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class HidingType(models.Model):
    tool = models.ForeignKey('game.Tool', on_delete=models.CASCADE)
    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=2000, blank=True, null=True)

    def __str__(self):
        return self.name


class Event(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    event_intro_story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='event_intro_story_id',
                                          blank=True, null=True)
    event_end_story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='event_end_story_id',
                                        blank=True, null=True)
    previous_event = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=2000, blank=True, null=True)
    delay_start = models.IntegerField(validators=[Validator.validate_positive_number])
    onfinish_cancel_active_events = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class HiddenInfo(models.Model):
    artifact = models.ForeignKey(Artifact, on_delete=models.CASCADE)
    hiding_type = models.ForeignKey(HidingType, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=2000, blank=True, null=True)
    score = models.IntegerField(validators=[Validator.validate_positive_number])
    is_event_key = models.BooleanField(default=False)
    common_key_code = models.CharField(max_length=128, blank=True, null=True)
    prefix_key_code = models.CharField(max_length=32, blank=True, null=True)
    suffix_key_code = models.CharField(max_length=32, blank=True, null=True)
    random_key_code_word = models.BooleanField(default=False)
    random_word_maxlength = models.IntegerField(validators=[Validator.validate_positive_number])

    def __str__(self):
        return self.name

class Clue(models.Model):
    order = models.IntegerField()
    clue_text = models.CharField(max_length=1000, )
    cost=models.IntegerField(blank=True, null=True)
    hiddeninfo=models.ForeignKey(HiddenInfo,on_delete=models.CASCADE)

    def __unicode__(self):
        return "id: %s" % (self.id, )
    
class Character(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, blank=True, null=True)
    events = models.ManyToManyField(Event, related_name='characters', through='CharacterEvent')
    name = models.CharField(max_length=64)
    full_name = models.CharField(max_length=128, unique=True)
    mail_address = models.EmailField(blank=True, null=True)
    avatar = models.ImageField(upload_to=get_image_path, blank=True, null=True)


class CharacterEvent(models.Model):
    character = models.ForeignKey(Character, null=False, blank=False, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, null=False, blank=False, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("character", "event"),)
