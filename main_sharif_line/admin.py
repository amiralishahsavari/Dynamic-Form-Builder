
# Register your models here.

from django.contrib import admin
from .models import Survey, Question, Option, Response, Answer

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

class OptionInline(admin.TabularInline):
    model = Option
    extra = 2

@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('title', 'description')
    inlines = [QuestionInline]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'survey', 'question_type', 'is_required')
    list_filter = ('question_type', 'is_required')
    inlines = [OptionInline]

admin.site.register([Response, Answer])
