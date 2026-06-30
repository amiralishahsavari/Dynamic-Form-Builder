# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
import uuid

class Survey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ایجادکننده")
    title = models.CharField(max_length=200, verbose_name="عنوان نظرسنجی")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")
    slug = models.SlugField(max_length=100, unique=True, blank=True, verbose_name="شناسه URL")
    # اضافه کردن فیلد جدید
    thank_you_message = models.TextField(
        verbose_name="پیام تشکر",
        default="با تشکر از مشارکت شما در این نظرسنجی"
    )

    class Meta:
        verbose_name = "نظرسنجی"
        verbose_name_plural = "نظرسنجی‌ها"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('survey-detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            unique_suffix = uuid.uuid4().hex[:6]
            self.slug = f"{base_slug}-{unique_suffix}"
        super().save(*args, **kwargs)


class Question(models.Model):
    QUESTION_TYPES = (
        ('text', 'پاسخ متنی'),
        ('rating', 'امتیازدهی (۱-۵)'),
        ('single', 'تک انتخابی'),
        ('multiple', 'چند انتخابی'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    survey = models.ForeignKey('Survey', on_delete=models.CASCADE, related_name='questions', verbose_name="نظرسنجی")
    text = models.TextField(verbose_name="متن سوال")
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, verbose_name="نوع سوال")
    is_required = models.BooleanField(default=True, verbose_name="اجباری")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")

    class Meta:
        verbose_name = "سوال"
        verbose_name_plural = "سوالات"
        ordering = ['-created_at']  

    def __str__(self):
        return f"{self.survey.title} - {self.text[:30]}..."


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options', verbose_name="سوال")
    text = models.CharField(max_length=200, verbose_name="متن گزینه")

    class Meta:
        verbose_name = "گزینه"
        verbose_name_plural = "گزینه‌ها"

    def __str__(self):
        return self.text


class Response(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses', verbose_name="نظرسنجی")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="کاربر")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ پاسخ")

    class Meta:
        verbose_name = "پاسخ"
        verbose_name_plural = "پاسخ‌ها"
        ordering = ['-created_at']

    def __str__(self):
        return f"پاسخ به {self.survey.title}"


class Answer(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='answers', verbose_name="پاسخ")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="سوال")
    text_answer = models.TextField(blank=True, null=True, verbose_name="پاسخ متنی")
    rating_answer = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="امتیاز")
    selected_options = models.ManyToManyField(Option, blank=True, verbose_name="گزینه‌های انتخاب شده")

    class Meta:
        verbose_name = "جواب"
        verbose_name_plural = "جواب‌ها"

    def __str__(self):
        return f"جواب به {self.question.text[:20]}..."
    
class SurveyAnalytics(models.Model):
    survey = models.OneToOneField(Survey, on_delete=models.CASCADE, related_name='analytics')
    total_responses = models.PositiveIntegerField(default=0)
    average_rating = models.FloatField(default=0)
    last_response = models.DateTimeField(null=True, blank=True)

    def update_analytics(self):
        # منطق به‌روزرسانی آمار
        pass


class SurveyInvitation(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)