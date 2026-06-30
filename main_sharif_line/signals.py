from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Question, Option

@receiver([post_save, post_delete], sender=Question)
def update_survey_on_question_change(sender, instance, **kwargs):
    survey = instance.survey
    survey.save()  # این باعث آپدیت شدن updated_at می‌شود

@receiver([post_save, post_delete], sender=Option)
def update_survey_on_option_change(sender, instance, **kwargs):
    if hasattr(instance, 'question') and instance.question:
        survey = instance.question.survey
        survey.save()  # این باعث آپدیت شدن updated_at می‌شود 