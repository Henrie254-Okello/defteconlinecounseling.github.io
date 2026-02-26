from django.urls import path
from . import views

urlpatterns = [

    # =======================
    # Home & Authentication
    # =======================
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),

    # =======================
    # Admin
    # =======================
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage_students/', views.manage_students, name='manage_students'),
    path('approve_student/<int:student_id>/', views.approve_student, name='approve_student'),
    path('reject_student/<int:student_id>/', views.reject_student, name='reject_student'),

    path('manage_counselors/', views.manage_counselors, name='manage_counselors'),
    path('add_counselor/', views.add_counselor, name='add_counselor'),
    path('edit_counselor/<int:pk>/', views.edit_counselor, name='edit_counselor'),
    path('delete_counselor/<int:pk>/', views.delete_counselor, name='delete_counselor'),
    path('view_counselor/<int:id>/', views.view_counselor, name='view_counselor'),

    path('specializations/', views.manage_specializations, name='manage_specializations'),
    path('add_specialization/', views.add_specialization, name='add_specialization'),

    path('admin_appointments/', views.view_appointments, name='view_appointments'),
    path('admin_call_logs/', views.admin_call_logs, name='admin_call_logs'),
    path('export-students/', views.export_students_excel, name='export_students_excel'),

    # =======================
    # Student
    # =======================
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),

    # =======================
    # Counselor
    # =======================
    path('counselor_dashboard/', views.counselor_dashboard, name='counselor_dashboard'),
    path('status/<str:status>/', views.update_status, name='update_status'),

    # =======================
    # Appointment & Chat
    # =======================
    path('appointment/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/', views.appointment_list, name='appointment_list'),

    # AJAX for counselor dashboard
    path('ajax/counselor_appointments/', views.counselor_appointments_ajax, name='counselor_appointments_ajax'),
    path('ajax/get_counselors/', views.get_counselors, name='get_counselors'),

    # =======================
    # Calls
    # =======================
    path('start_call/<int:receiver_id>/<str:call_type>/', views.start_call, name='start_call'),
    path('end_call/<int:call_id>/', views.end_call, name='end_call'),

    # =======================
    # Books
    # =======================
    path('upload-book/', views.upload_book, name='upload_book'),
    path('books/', views.student_books, name='student_books'),
]