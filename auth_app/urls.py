# auth_app/urls.py

from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from . import views 
from . import api_views
from .views import SurveyStatisticsAPIView
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('', views.home_view, name='home'),
    path('surveys/', views.survey_list_view, name='survey_list'),
    path('surveys/<int:survey_pk>/', views.survey_detail_view, name='survey_detail'),
    path('api/surveys/<int:survey_pk>/submit/', views.submit_survey_api_view, name='submit_survey_api'),
    path('api/surveys/<int:survey_pk>/statistics/', SurveyStatisticsAPIView.as_view(), name='survey_statistics_api'),
    path('surveys/<int:survey_pk>/statistics/', views.survey_statistics_view, name='survey_statistics'),
]
api_urlpatterns = [
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('surveys/', api_views.SurveyListView.as_view(), name='api_survey_list'),
    path('surveys/<int:pk>/', api_views.SurveyDetailView.as_view(), name='api_survey_detail'),
    path('surveys/<int:pk>/submit/', api_views.SurveySubmitView.as_view(), name='api_survey_submit'),
]
urlpatterns += [
    path('api/', include(api_urlpatterns)),
]

urlpatterns += [
    path("responsibles/", views.ResponsiblePersonListView.as_view(), name="responsible_list"),
    path("messages/", views.MessageListView.as_view(), name="message_list"),
    path("messages/create/", views.MessageCreateView.as_view(), name="message_create"),
    path("messages/<int:pk>/", views.MessageDetailView.as_view(), name="message_detail"),
    path("messages/<int:pk>/reply/", views.MessageReplyView.as_view(), name="message_reply"),
]