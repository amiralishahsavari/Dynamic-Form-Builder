from django.urls import path
from . import views

from django.urls import re_path
urlpatterns = [
    #صفحات اصلی
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('faq/', views.faq, name='faq'),
    path('contact/', views.contact, name='contact'),
    path('terms/', views.terms, name='terms'),
    
    # صفحات کاربری
    path('surveys/', views.SurveyListView.as_view(), name='survey_list'),
    path('survey/create/', views.SurveyCreateView.as_view(), name='survey_create'),
    path('survey/thank-you/', views.survey_thank_you, name='survey_thank_you'),
    re_path(r'^survey/(?P<slug>[\w\u0600-\u06FF-]+)/$', views.SurveyDetailView.as_view(), name='survey-detail'),
    path('question/<int:pk>/delete/', views.delete_question, name='delete_question'),
    path('survey/question/<int:pk>/edit/', views.edit_question, name='edit-question'),
    re_path(r'^survey/(?P<slug>[\w\u0600-\u06FF-]+)/add-question/$', views.add_question_ajax, name='add-question-ajax'),
    re_path(r'^survey/(?P<slug>[\w\u0600-\u06FF-]+)/delete/$', views.SurveyDeleteView.as_view(), name='survey-delete'),
    re_path(r'^survey/(?P<slug>[\w\u0600-\u06FF-]+)/info/$', views.survey_info, name='survey_info'),
    re_path(r'^survey/(?P<slug>[\w\u0600-\u06FF-]+)/fill/$', views.fill_survey, name='fill_survey'),
    # در urls.py
    path('option/add/', views.add_option, name='add_option'),
    path('option/<int:pk>/edit/', views.edit_option, name='edit_option'),
    path('option/<int:pk>/delete/', views.delete_option, name='delete_option'),

    #صفحات اکانت
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('edit-profile-modal/', views.edit_profile_modal, name='edit_profile_modal'),
    re_path(r'^survey/(?P<slug>[\w\u0600-\u06FF-]+)/results/$', views.survey_results, name='survey_results'),

]
