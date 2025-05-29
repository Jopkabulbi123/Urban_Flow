from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('home/', views.home_view, name='home_alt'),
    path('logged_home/', views.logged_home_view, name='logged_home'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('profile/', views.profile_view, name='profile'),
    path('api/analyze/', views.analyze_area, name='analyze_area'),
    path('city-changer/', views.city_changer_view, name='city_changer'),
    path('myprojects/', views.my_projects, name='myprojects'),
    path('logout_projects/', views.logout_view, name='logout_projects'),
    path('api/save-project/', views.save_project, name='save_project'),
    path('myprojects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('api/delete-project/<int:project_id>/', views.delete_project, name='delete_project'),
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]