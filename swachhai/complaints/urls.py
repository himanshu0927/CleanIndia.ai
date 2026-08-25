from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('report/', views.report_complaint, name='report'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('export-csv/', views.export_complaints_csv, name='export_complaints_csv'),
    path('my-complaints/', views.my_complaints, name='my_complaints'),
    path('complaint/<int:complaint_id>/', views.complaint_detail, name='complaint_detail'),
    path('feedback/<int:complaint_id>/', views.submit_feedback, name='submit_feedback'),
    path('resolve/<int:complaint_id>/', views.resolve_complaint, name='resolve_complaint'),
    path('resolve-proof/<int:complaint_id>/', views.resolve_with_proof, name='resolve_with_proof'),
    path('delete/<int:complaint_id>/', views.delete_complaint, name='delete_complaint'),
    path('update-status/<int:complaint_id>/<str:status>/', views.update_status, name='update_status'),
    path('update-operation-status/<int:complaint_id>/<str:operation_status>/', views.update_operation_status, name='update_operation_status'),
    path('signup/', views.user_signup_view, name='signup'),
    path('login/', views.user_login_view, name='login'),
    path('user-signup/', views.user_signup_view, name='user_signup'),
    path('user-login/', views.user_login_view, name='user_login'),
    path('authority-signup/', views.authority_signup_view, name='authority_signup'),
    path('authority-login/', views.authority_login_view, name='authority_login'),
    path('logout/', views.logout_view, name='logout'),
]
