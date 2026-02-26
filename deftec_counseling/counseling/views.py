from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import logout
from django.db.models import Count
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
import openpyxl
from openpyxl.styles import Font

from .models import (
    User,
    Specialization,
    Appointment,
    ChatMessage,
    UserStatus,
    Counselor,
    CallLog,
    Book
)

from .forms import (
    StudentRegistrationForm,
    AppointmentForm,
    SpecializationForm,
    CounselorCreationForm,
    CounselorForm,
    BookUploadForm
)


# =========================
# AUTH / HOME
# =========================
def home(request):
    return render(request, 'counseling/home.html')


def logout_view(request):
    logout(request)
    return redirect('home')


# =========================
# ROLE CHECK
# =========================
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'admin')


@login_required
def dashboard_redirect(request):
    """Redirect users to their respective dashboards."""
    if request.user.role == 'admin':
        return redirect('admin_dashboard')
    elif request.user.role == 'student':
        return redirect('student_dashboard')
    elif request.user.role == 'counselor':
        return redirect('counselor_dashboard')
    return redirect('login')


# =========================
# STUDENT REGISTRATION
# =========================
def register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'student'
            user.is_approved = False
            user.save()
            messages.success(request, "Registration successful. Await admin approval.")
            return redirect('login')
    else:
        form = StudentRegistrationForm()
    return render(request, 'counseling/register.html', {'form': form})


# =========================
# ADMIN DASHBOARD
# =========================
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    context = {
        'students_count': User.objects.filter(role='student').count(),
        'counselors_count': User.objects.filter(role='counselor').count(),
        'appointments_count': Appointment.objects.count(),
        'pending_students': User.objects.filter(role='student', is_approved=False).count(),
        'students_by_school': User.objects.filter(role='student')
            .values('school').annotate(count=Count('id')),
        'students_by_class': User.objects.filter(role='student')
            .values('class_name').annotate(count=Count('id')),
    }
    return render(request, 'counseling/admin_dashboard.html', context)


# =========================
# STUDENT MANAGEMENT
# =========================
@login_required
@user_passes_test(is_admin)
def manage_students(request):
    students = User.objects.filter(role='student')

    service_query = request.GET.get('service_number', '').strip()
    rank_filter = request.GET.get('rank', '').strip()

    if service_query:
        students = students.filter(service_number__icontains=service_query)

    if rank_filter:
        students = students.filter(rank__iexact=rank_filter)

    students = students.order_by('rank', 'service_number', 'first_name', 'last_name')

    ranks = User.objects.filter(role='student') \
        .exclude(rank__isnull=True) \
        .exclude(rank__exact='') \
        .values_list('rank', flat=True) \
        .distinct()

    return render(request, 'counseling/manage_students.html', {
        'students': students,
        'ranks': ranks,
        'service_query': service_query,
        'rank_filter': rank_filter,
    })


@login_required
@user_passes_test(is_admin)
def approve_student(request, student_id):
    student = get_object_or_404(User, id=student_id, role='student')
    student.is_approved = True
    student.save()
    messages.success(request, "Student approved")
    return redirect('manage_students')


@login_required
@user_passes_test(is_admin)
def reject_student(request, student_id):
    student = get_object_or_404(User, id=student_id, role='student')
    student.is_approved = False
    student.save()
    messages.warning(request, "Student rejected")
    return redirect('manage_students')


@login_required
@user_passes_test(is_admin)
def export_students_excel(request):
    students = User.objects.filter(role='student')

    service_query = request.GET.get('service_number', '').strip()
    rank_filter = request.GET.get('rank', '').strip()

    if service_query:
        students = students.filter(service_number__icontains=service_query)

    if rank_filter:
        students = students.filter(rank__iexact=rank_filter)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Students"

    headers = ["Service Number", "Rank", "Full Name", "School", "Class", "Status"]
    ws.append(headers)
    for col in ws[1]:
        col.font = Font(bold=True)

    for student in students:
        full_name = f"{student.first_name} {student.last_name}" if student.first_name or student.last_name else student.username
        status = "Approved" if student.is_approved else "Pending"
        ws.append([
            student.service_number,
            student.rank,
            full_name,
            student.school,
            student.class_name,
            status
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = 'attachment; filename=students.xlsx'
    wb.save(response)
    return response


# =========================
# COUNSELOR MANAGEMENT
# =========================
@login_required
@user_passes_test(is_admin)
def manage_counselors(request):
    counselors = Counselor.objects.select_related('user')
    return render(request, 'counseling/manage_counselors.html', {'counselors': counselors})


@login_required
@user_passes_test(is_admin)
def add_counselor(request):
    if request.method == 'POST':
        user_form = CounselorCreationForm(request.POST)
        counselor_form = CounselorForm(request.POST)

        if user_form.is_valid() and counselor_form.is_valid():
            user = user_form.save(commit=False)
            user.role = 'counselor'
            user.is_approved = True
            user.set_password(user_form.cleaned_data['password1'])
            user.save()

            counselor_form.instance.user = user
            counselor_form.save()

            messages.success(request, "Counselor added successfully")
            return redirect('manage_counselors')
    else:
        user_form = CounselorCreationForm()
        counselor_form = CounselorForm()

    return render(request, 'counseling/add_counselor.html', {
        'user_form': user_form,
        'counselor_form': counselor_form
    })


@login_required
@user_passes_test(is_admin)
def edit_counselor(request, pk):
    counselor = get_object_or_404(Counselor, pk=pk)
    form = CounselorForm(request.POST or None, instance=counselor)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Counselor updated")
        return redirect('manage_counselors')
    return render(request, 'counseling/edit_counselor.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def delete_counselor(request, pk):
    counselor = get_object_or_404(Counselor, pk=pk)
    counselor.user.delete()
    messages.success(request, "Counselor deleted")
    return redirect('manage_counselors')


@login_required
@user_passes_test(is_admin)
def view_counselor(request, id):
    counselor = get_object_or_404(Counselor, id=id)
    return render(request, 'counseling/view_counselor.html', {'counselor': counselor})


# =========================
# SPECIALIZATIONS
# =========================
@login_required
@user_passes_test(is_admin)
def manage_specializations(request):
    specs = Specialization.objects.all()
    return render(request, 'counseling/manage_specializations.html', {'specs': specs})


@login_required
@user_passes_test(is_admin)
def add_specialization(request):
    if request.method == 'POST':
        form = SpecializationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Specialization added")
            return redirect('manage_specializations')
    else:
        form = SpecializationForm()
    return render(request, 'counseling/add_specialization.html', {'form': form})


# =========================
# APPOINTMENTS
# =========================
@login_required
@user_passes_test(is_admin)
def view_appointments(request):
    appointments = Appointment.objects.all().order_by('-date', '-time')
    return render(request, 'counseling/view_appointments.html', {'appointments': appointments})


@login_required
def student_dashboard(request):
    if request.user.role != 'student' or not request.user.is_approved:
        return redirect('login')

    appointments = Appointment.objects.filter(student=request.user).order_by('date', 'time')
    books = Book.objects.all()
    form = AppointmentForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        appt = form.save(commit=False)
        appt.student = request.user
        appt.save()
        messages.success(request, "Appointment booked")
        return redirect('student_dashboard')

    return render(request, 'counseling/student_dashboard.html', {
        'appointments': appointments,
        'books': books,
        'form': form
    })


@login_required
def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.student = request.user
            appointment.save()
            messages.success(request, 'Appointment booked successfully.')
            return redirect('student_dashboard')
    return redirect('student_dashboard')


# =========================
# COUNSELOR DASHBOARD
# =========================
@login_required
def counselor_dashboard(request):
    if request.user.role != 'counselor':
        return redirect('login')

    # Get counselor profile (reverse OneToOne relation)
    try:
        counselor_profile = request.user.counselor_profile
    except Counselor.DoesNotExist:
        messages.error(request, "Counselor profile not found.")
        return redirect('login')

    appointments = Appointment.objects.filter(counselor=request.user).order_by('date', 'time')
    status, _ = UserStatus.objects.get_or_create(user=request.user)

    total_appointments = appointments.count()
    pending_count = appointments.filter(status__iexact='pending').count()
    completed_count = appointments.filter(status__iexact='completed').count()
    missed_calls = CallLog.objects.filter(receiver=request.user, status='missed')

    return render(request, 'counseling/counselor_dashboard.html', {
        'counselor_profile': counselor_profile,
        'appointments': appointments,
        'status': status,
        'missed_calls': missed_calls,
        'total_appointments': total_appointments,
        'pending_count': pending_count,
        'completed_count': completed_count,
    })


@login_required
def appointment_list(request):
    appointments = Appointment.objects.filter(counselor=request.user).order_by('date', 'time')
    return render(request, 'counseling/appointment_list.html', {'appointments': appointments})


@login_required
def appointment_detail(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if request.user not in [appointment.student, appointment.counselor]:
        return redirect('login')

    messages_qs = ChatMessage.objects.filter(appointment=appointment).select_related('sender')
    counselor_status = UserStatus.objects.filter(user=appointment.counselor).first()

    return render(request, 'counseling/appointment_detail.html', {
        'appointment': appointment,
        'messages': messages_qs,
        'counselor_status': counselor_status.is_online if counselor_status else False
    })


@login_required
def update_status(request, status):
    if request.user.role != 'counselor':
        return redirect('login')
    obj, _ = UserStatus.objects.get_or_create(user=request.user)
    obj.is_online = (status == 'online')
    obj.save()
    return redirect('counselor_dashboard')


# =========================
# CALLS
# =========================
@login_required
def start_call(request, receiver_id, call_type):
    receiver = get_object_or_404(User, id=receiver_id)
    CallLog.objects.create(
        caller=request.user,
        receiver=receiver,
        call_type=call_type,
        status='ongoing',
        started_at=timezone.now()
    )
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
def end_call(request, call_id):
    call = get_object_or_404(CallLog, id=call_id)
    call.ended_at = timezone.now()
    call.status = 'missed' if call.ended_at == call.started_at else 'completed'
    call.save()
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
@user_passes_test(is_admin)
def admin_call_logs(request):
    calls = CallLog.objects.all().order_by('-started_at')[:50]
    return render(request, 'counseling/admin_call_logs.html', {'calls': calls})


# =========================
# BOOKS
# =========================
@login_required
def upload_book(request):
    if request.user.role != 'counselor':
        return redirect('counselor_dashboard')

    if request.method == 'POST':
        form = BookUploadForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.uploaded_by = request.user
            book.save()
            messages.success(request, "Book uploaded successfully")
            return redirect('counselor_dashboard')
    else:
        form = BookUploadForm()
    return render(request, 'counseling/upload_book.html', {'form': form})


@login_required
def student_books(request):
    books = Book.objects.all()
    return render(request, 'counseling/student_books.html', {'books': books})


# =========================
# AJAX ENDPOINTS
# =========================
@login_required
def get_counselors(request):
    specialization_id = request.GET.get('specialization')
    counselors = Counselor.objects.filter(specialization_id=specialization_id).select_related('user')
    data = [
        {"id": c.id, "name": f"{c.user.first_name} {c.user.last_name}" if c.user.first_name else c.user.username}
        for c in counselors
    ]
    return JsonResponse(data, safe=False)


@login_required
def counselor_appointments_ajax(request):
    appointments = Appointment.objects.filter(counselor=request.user).order_by('date', 'time')
    data = [
        {
            'id': appt.id,
            'student_name': f"{appt.student.first_name} {appt.student.last_name}",
            'student_id': appt.student.id,
            'date': appt.date.strftime("%Y-%m-%d"),
            'time': appt.time.strftime("%H:%M"),
            'status': appt.status,
            'specialization': appt.specialization.name,
        }
        for appt in appointments
    ]
    return JsonResponse(data, safe=False)