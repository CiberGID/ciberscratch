from django.db import models
from common.validators import Validator


class Tool(models.Model):
    name = models.CharField(max_length=64, )
    description = models.CharField(max_length=1000, blank=True, null=True)
    command = models.CharField(max_length=1000, )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class ToolParameter(models.Model):
    name = models.CharField(max_length=64, )
    description = models.CharField(max_length=1000, blank=True, null=True)
    parameter = models.CharField(max_length=1000, blank=True, null=True)
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class ToolParameterValue(models.Model):
    param = models.ForeignKey(ToolParameter, on_delete=models.CASCADE)
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE)
    hidden_info = models.ForeignKey('game.HiddenInfo', on_delete=models.CASCADE)
    value = models.CharField(max_length=512)
    add_key_code = models.BooleanField(default=False)
    order = models.IntegerField(validators=[Validator.validate_positive_number], default=0)

