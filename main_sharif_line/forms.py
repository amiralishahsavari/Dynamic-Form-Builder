from django import forms
from django.core.exceptions import ValidationError
from .models import Survey, Question, Option
from django.forms import inlineformset_factory
from django.contrib.auth.models import User

class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = ['title', 'description', 'is_active', 'thank_you_message']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: نظرسنجی رضایت از دوره برنامه‌نویسی'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'توضیح مختصر درباره هدف نظرسنجی'
            }),
            'thank_you_message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'پیام تشکر پس از تکمیل نظرسنجی'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'عنوان نظرسنجی*',
            'description': 'توضیحات',
            'is_active': 'نظرسنجی فعال باشد',
            'thank_you_message': 'پیام تشکر*'
        }

    def clean_title(self):
        title = self.cleaned_data['title']
        if len(title) < 2:
            raise ValidationError("عنوان باید حداقل ۱۰ کاراکتر باشد")
        return title
    
class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'is_required']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'text': 'متن سؤال',
            'question_type': 'نوع سؤال',
            'is_required': 'پاسخ اجباری است.',
        }

# فرم چندتایی برای گزینه‌ها
OptionFormSet = inlineformset_factory(
    Question,
    Option,
    fields=('text',),
    extra=1,
    can_delete=False,
    widgets={
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'متن گزینه'}),
        }
    )

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خانوادگی'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ایمیل'}),
        }

class SurveyAnswerForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.survey = kwargs.pop('survey')
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.field_question_types = {}  # اضافه کردن دیکشنری برای نگهداری نوع سوال هر فیلد

        for question in self.survey.questions.all():
            field_name = f"question_{question.id}"
            self.field_question_types[field_name] = question.question_type  # ذخیره نوع سوال

            if question.question_type == 'text':
                self.fields[field_name] = forms.CharField(
                    label=question.text,
                    required=question.is_required,
                    widget=forms.Textarea(attrs={'class': 'form-control'})
                )
            elif question.question_type == 'rating':
                self.fields[field_name] = forms.IntegerField(
                    label=question.text,
                    required=question.is_required,
                    min_value=1,
                    max_value=5,
                    widget=forms.NumberInput(attrs={'class': 'form-control', 'type': 'range', 'min': 1, 'max': 5})
                )
            elif question.question_type == 'single':
                self.fields[field_name] = forms.ModelChoiceField(
                    label=question.text,
                    queryset=question.options.all(),
                    widget=forms.RadioSelect,
                    required=question.is_required
                )
            elif question.question_type == 'multiple':
                self.fields[field_name] = forms.ModelMultipleChoiceField(
                    label=question.text,
                    queryset=question.options.all(),
                    widget=forms.CheckboxSelectMultiple,
                    required=question.is_required
                )

    def save(self, response=None):
        from .models import Answer, Response
        if response is None:
            response = Response.objects.create(survey=self.survey, user=self.user)

        for question in self.survey.questions.all():
            field_name = f"question_{question.id}"
            answer_value = self.cleaned_data.get(field_name)

            if question.question_type == 'text':
                Answer.objects.create(
                    response=response,
                    question=question,
                    text_answer=answer_value
                )
            elif question.question_type == 'rating':
                Answer.objects.create(
                    response=response,
                    question=question,
                    rating_answer=answer_value
                )
            elif question.question_type == 'single':
                ans = Answer.objects.create(
                    response=response,
                    question=question
                )
                if answer_value:
                    ans.selected_options.add(answer_value)
            elif question.question_type == 'multiple':
                ans = Answer.objects.create(
                    response=response,
                    question=question
                )
                if answer_value:
                    ans.selected_options.set(answer_value)
