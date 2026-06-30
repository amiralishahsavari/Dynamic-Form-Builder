from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, update_session_auth_hash, logout, login as auth_login
from django.contrib.auth.models import User
from django_ratelimit.decorators import ratelimit 
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from matplotlib.style import context
import requests
from django.conf import settings
from django.views.generic import ListView, CreateView, DetailView  ,DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Survey, Question, Option
from .forms import SurveyForm, QuestionForm, OptionFormSet, ProfileUpdateForm, SurveyAnswerForm
from django.urls import reverse
from django.utils.text import slugify
import uuid
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.http import require_POST

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def faq(request):
    return render(request, 'faq.html')

def contact(request):
    return render(request, 'contact.html')

def terms(request):
    return render(request, 'terms.html')

@login_required
def edit_profile_modal(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user = request.user
        surveys = user.survey_set.all()
        return render(request, 'accounts/edit_profile_modal.html', {
            'user': user,
            'surveys': surveys,
        })
    return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=400)

@ratelimit(key='ip', rate='5/m', method='POST', block=False)
def login(request):
    if request.user.is_authenticated:
        return redirect('survey_list')

    if request.method == 'POST':
        if getattr(request, 'limited', False):
            messages.error(request, "تعداد تلاش‌های ورود بیش از حد مجاز است. لطفاً چند دقیقه دیگر تلاش کنید.")
            return render(request, 'accounts/login.html')

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('survey_list')
        else:
            messages.error(request, "نام کاربری یا رمز عبور نادرست است")

    return render(request, 'accounts/login.html')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password')
        password2 = request.POST.get('password2')

        if not username or not password1 or not password2:
            messages.error(request, "لطفاً همه فیلدها را پر کنید.")
            return render(request, 'accounts/register.html')

        recaptcha_response = request.POST.get('g-recaptcha-response')
        data = {
            'secret': settings.RECAPTCHA_PRIVATE_KEY,
            'response': recaptcha_response
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        try:
            result = r.json()
        except (ValueError, TypeError):
            result = {}
        
        if not result.get('success'):
            messages.error(request, "لطفاً تأیید کنید که ربات نیستید.")
            return render(request, 'accounts/register.html')

        if password1 != password2:
            messages.error(request, "رمز عبور و تکرار آن مطابقت ندارند.")
            return render(request, 'accounts/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "این نام کاربری قبلاً ثبت شده است.")
            return render(request, 'accounts/register.html')

        try:
            validate_password(password1, user=User(username=username))
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'accounts/register.html')

        user = User.objects.create_user(username=username, password=password1)
        auth_login(request, user)
        return redirect('survey_list')

    return render(request, 'accounts/register.html')

@login_required
def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        if not user.check_password(current_password):
            messages.error(request, 'رمز عبور فعلی اشتباه است.')
            return render(request, 'accounts/change_password.html')

        if new_password != confirm_password:
            messages.error(request, 'رمز عبور جدید با تکرار آن مطابقت ندارد.')
            return render(request, 'accounts/change_password.html')

        user.set_password(new_password)
        user.save()

        # حفظ نشست کاربر بعد از تغییر رمز
        update_session_auth_hash(request, user)

        messages.success(request, 'رمز عبور با موفقیت تغییر کرد.')
        return redirect('home')  

    return render(request, 'accounts/password_change_form.html')

    
class SurveyListView(LoginRequiredMixin, ListView):
    model = Survey
    template_name = 'surveys/survey_list.html'
    context_object_name = 'surveys'

    def get_queryset(self):
        return Survey.objects.filter(creator=self.request.user).order_by('-created_at')



class SurveyCreateView(LoginRequiredMixin, CreateView):
    model = Survey
    form_class = SurveyForm
    template_name = 'surveys/survey_create.html'

    def form_valid(self, form):
        form.instance.creator = self.request.user
        form.instance.slug = self.generate_unique_slug(form.instance.title)
        response = super().form_valid(form)
        self.request.session['thanks_survey_slug'] = form.instance.slug  # ذخیره اسلاگ برای پیام تشکر
        return redirect('survey-detail', slug=form.instance.slug)

    def generate_unique_slug(self, title):
        base_slug = slugify(title, allow_unicode=True)
        unique_slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
        return unique_slug
   

@login_required
def survey_list(request):
    return render(request, 'surveys/list.html')

class SurveyDetailView(DetailView):
    model = Survey
    template_name = 'surveys/survey_detail.html'
    context_object_name = 'survey'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.all()  
        # فرم افزودن سوال جدید
        if self.request.method == 'POST':
            context['question_form'] = QuestionForm(self.request.POST)
        else:
            context['question_form'] = QuestionForm()

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        question_form = QuestionForm(request.POST)

        if question_form.is_valid():
            question = question_form.save(commit=False)
            question.survey = self.object
            question.save()
            return redirect(self.object.get_absolute_url())

        # اگر فرم نامعتبر بود
        context = self.get_context_data()
        context['question_form'] = question_form
        return self.render_to_response(context)


def delete_question(request, pk):
    if request.method == 'DELETE':
        try:
            question = Question.objects.get(pk=pk)
            question.delete()
            return JsonResponse({'success': True})
        except Question.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'سوال پیدا نشد'}, status=404)
    return HttpResponseNotAllowed(['DELETE'])

def edit_question(request, pk):
    question = get_object_or_404(Question, pk=pk)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            saved_question = form.save()
            return JsonResponse({
                'success': True,
                'question': {
                    'id': saved_question.id,
                    'text': saved_question.text,
                    'type': saved_question.question_type,
                    'question_type_display': saved_question.get_question_type_display(),
                    'is_required': saved_question.is_required,
                    'options': [
                        {'id': opt.id, 'text': opt.text}
                        for opt in saved_question.options.all()
                    ] if saved_question.question_type in ['single', 'multiple'] else []
                }
            })
        else:
            return JsonResponse({
                'success': False, 
                'errors': form.errors
            }, status=400)
    else:
        form = QuestionForm(instance=question)
        return render(request, 'surveys/edit_question_form.html', {'form': form})
@require_POST
def add_question_ajax(request, slug):
    survey = get_object_or_404(Survey, slug=slug)
    question_form = QuestionForm(request.POST)

    if question_form.is_valid():
        question = question_form.save(commit=False)
        question.survey = survey
        question.save()

        # سوال بدون گزینه ذخیره می‌شود - گزینه‌ها بعداً اضافه می‌شوند

        # پاسخ موفقیت‌آمیز، می‌توانیم اطلاعات سوال را برگردانیم (مثلاً id و متن)
        return JsonResponse({
            'success': True,
            'question': {
                'id': question.id,
                'text': question.text,
                'type': question.question_type,
                'question_type_display': question.get_question_type_display(),  # ← فارسی‌شده
                'is_required': question.is_required,
                'options': [
                    {'id': opt.id, 'text': opt.text}
                    for opt in question.options.all()
                ] if question.question_type in ['single', 'multiple'] else []

            }
        })

    else:
        return JsonResponse({'success': False, 'errors': question_form.errors}, status=400)
    
# در بخش views.py این توابع را اضافه/اصلاح کنید:

@require_POST
@login_required
def add_option(request):
    try:
        question_id = request.POST.get('question_id')
        text = request.POST.get('text')
        
        if not question_id or not text:
            return JsonResponse({
                'success': False,
                'error': 'پارامترهای ضروری ارسال نشده‌اند'
            }, status=400)

        question = get_object_or_404(Question, pk=question_id, survey__creator=request.user)
        option = Option.objects.create(question=question, text=text)
        
        return JsonResponse({
            'success': True,
            'option': {
                'id': option.id,
                'text': option.text,
                'question_id': question.id
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_POST
@login_required
def edit_option(request, pk):
    try:
        option = get_object_or_404(Option, pk=pk, question__survey__creator=request.user)
        new_text = request.POST.get('text')
        
        if not new_text:
            return JsonResponse({
                'success': False,
                'error': 'متن گزینه نمی‌تواند خالی باشد'
            }, status=400)
            
        option.text = new_text
        option.save()
        
        return JsonResponse({
            'success': True,
            'option': {
                'id': option.id,
                'text': option.text,
                'question_id': option.question.id
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def delete_option(request, pk):
    if request.method == 'DELETE':
        try:
            option = get_object_or_404(Option, pk=pk, question__survey__creator=request.user)
            option_id = option.id
            question_id = option.question.id
            option.delete()
            return JsonResponse({
                'success': True,
                'option_id': option_id,
                'question_id': question_id
            })
        except Option.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'گزینه پیدا نشد'
            }, status=404)
    return HttpResponseNotAllowed(['DELETE'])


class SurveyDeleteView(LoginRequiredMixin, DeleteView):
    model = Survey
    template_name = 'surveys/survey_confirm_delete.html'
    success_url = reverse_lazy('survey_list')
    
    def get_queryset(self):
        return Survey.objects.filter(creator=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        referer = self.request.META.get('HTTP_REFERER')
        context['cancel_url'] = referer or reverse_lazy('survey_list')
        return context


def survey_info(request, slug):
    survey = get_object_or_404(Survey, slug=slug)
    questions = survey.questions.all()
    # اگر مدل Answer داری، اینجا جایگزین کن:
    answers_count = getattr(survey, 'answers', []).count() if hasattr(survey, 'answers') else 0
    share_url = request.build_absolute_uri(survey.get_absolute_url())
    context = {
        'survey': survey,
        'questions': questions,
        'answers_count': answers_count,
        'share_url': share_url,
    }
    return render(request, 'surveys/survey_info.html', context)

def fill_survey(request, slug):
    survey = get_object_or_404(Survey, slug=slug)

    # فقط اگر نظرسنجی فعال است
    if not survey.is_active:
        return render(request, 'surveys/survey_inactive.html', {'survey': survey})

    # اگر فرم ارسال شده
    if request.method == 'POST':
        form = SurveyAnswerForm(survey=survey, data=request.POST)
        if form.is_valid():
            form.save()
            request.session['thanks_survey_slug'] = survey.slug  # ذخیره اسلاگ برای پیام تشکر
            return redirect('survey_thank_you')
    else:
        form = SurveyAnswerForm(survey=survey)

    return render(request, 'surveys/fill_survey.html', {
        'survey': survey,
        'form': form
    })

def survey_thank_you(request):
    survey_slug = request.session.pop('thanks_survey_slug', None)
    survey = None
    thank_you_message = None
    survey_title = None
    if survey_slug:
        survey = Survey.objects.filter(slug=survey_slug).first()
        if survey:
            thank_you_message = survey.thank_you_message
            survey_title = survey.title
    return render(request, 'surveys/thank_you.html', {
        'survey_title': survey_title,
        'thank_you_message': thank_you_message
    })

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Survey, Response, Question, Option
from collections import Counter
from django.db.models import Max
from django.utils import timezone

@login_required
def survey_results(request, slug):
    survey = get_object_or_404(Survey, slug=slug)
    questions = survey.questions.all()
    
    # دریافت پاسخ‌ها به ترتیب قدیمی به جدید
    responses = survey.responses.all().order_by('created_at')
    
    total_responses = responses.count()
    last_response = responses.aggregate(Max('created_at'))['created_at__max']
    
    # محاسبه آمار برای هر سوال
    for q in questions:
        q.chart_data = []
        
        if q.question_type in ['single', 'multiple']:
            # محاسبه برای سوالات چندگزینه‌ای
            option_counts = Counter()
            total_answers = 0
            
            for r in responses:
                for ans in r.answers.filter(question=q):
                    for opt in ans.selected_options.all():
                        option_counts[opt.text] += 1
                        total_answers += 1
            
            for opt in q.options.all():
                count = option_counts[opt.text]
                percent = round((count / total_answers) * 100, 1) if total_answers > 0 else 0
                q.chart_data.append({
                    'option': opt.text,
                    'count': count,
                    'percent': percent
                })
                
        elif q.question_type == 'rating':
            # محاسبه برای سوالات امتیازی
            rating_counts = Counter()
            
            for r in responses:
                for ans in r.answers.filter(question=q):
                    if ans.rating_answer:
                        rating_counts[str(ans.rating_answer)] += 1
            
            total = sum(rating_counts.values())
            
            for rate in range(1, 6):
                count = rating_counts.get(str(rate), 0)
                percent = round((count / total) * 100, 1) if total else 0
                q.chart_data.append({
                    'option': f'امتیاز {rate}',
                    'count': count,
                    'percent': percent
                })

    context = {
        'survey': survey,
        'questions': questions,
        'responses': responses,
        'total_responses': total_responses,
        'last_response': last_response,
    }
    
    return render(request, 'surveys/survey_results.html', context)