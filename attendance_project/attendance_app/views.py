from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Sum

from .models import Teacher, Student, Subject, Attendance
from django.http import HttpResponse


# ✅ Teacher Login
def teacher_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                teacher = Teacher.objects.get(user=user)
                login(request, user)
                return redirect('dashboard')
            except Teacher.DoesNotExist:
                return render(request, 'login.html', {'error': 'Not a registered teacher'})
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')


# ✅ Logout
def teacher_logout(request):
    logout(request)
    return redirect('login')


# ✅ Dashboard
@login_required
def dashboard(request):
    teacher = Teacher.objects.get(user=request.user)
    return render(request, 'dashboard.html', {'teacher': teacher})


# ✅ Mark Attendance
@login_required
def mark_attendance(request):
    teacher = Teacher.objects.get(user=request.user)
    students = Student.objects.all()

    if request.method == 'POST':
        date = request.POST.get('date')
        for student in students:
            status = request.POST.get(f'status_{student.id}')
            Attendance.objects.update_or_create(
                student=student,
                subject=teacher.subject,
                date=date,
                defaults={'status': status}
            )
        messages.success(request, "Attendance successfully saved!")
        return redirect('mark_attendance')

    today = timezone.now().date()
    return render(request, 'mark_attendance.html', {
        'students': students,
        'today': today,
    })


# ✅ View Attendance Summary (Teacher)
@login_required
def view_attendance(request):
    teacher = Teacher.objects.get(user=request.user)
    subject = teacher.subject
    students = Student.objects.all()

    attendance_data = []
    for student in students:
        total = Attendance.objects.filter(subject=subject, student=student).count()
        present = Attendance.objects.filter(subject=subject, student=student, status='Present').count()
        percentage = round((present / total) * 100, 2) if total > 0 else 0

        attendance_data.append({
            'student': student,
            'total': total,
            'present': present,
            'percentage': percentage,
        })

    return render(request, 'view_attendance.html', {'data': attendance_data, 'subject': subject})


# ✅ View Attendance Summary (Student)
def student_profile(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    subjects = Subject.objects.all()
    data = []

    for subject in subjects:
        attendance_qs = Attendance.objects.filter(student=student, subject=subject)
        total = attendance_qs.count()
        present = attendance_qs.filter(status='Present').count()
        percentage = round((present / total) * 100, 2) if total > 0 else 0

        data.append({
            'subject': subject,
            'present': present,
            'total': total,
            'percentage': percentage
        })

    context = {
        'student': student,
        'data': data,
    }
    return render(request, 'student_profile.html', context)

def terms_view(request):
    return render(request, 'terms.html')

def home(request):
    return render(request, 'home.html')

def student_login(request):
    return render(request, 'student_login.html')


from django.shortcuts import render, redirect
from .models import Student, Attendance, Subject

def student_dashboard(request):
    reg_no = request.session.get('reg_no')
    if not reg_no:
        return redirect('student_login')  # not logged in

    try:
        student = Student.objects.get(registration_number=reg_no)
    except Student.DoesNotExist:
        return HttpResponse("Student not found")

    attendance_records = Attendance.objects.filter(student=student)
    data = []

    # ✅ just take all subjects (no classroom filter)
    subjects = Subject.objects.all()
    for subject in subjects:
        subject_attendance = attendance_records.filter(subject=subject)
        total = subject_attendance.count()
        present = subject_attendance.filter(status='Present').count()
        percentage = round((present / total) * 100, 2) if total > 0 else 0
        data.append({
            'subject': subject.name,
            'total': total,
            'present': present,
            'percentage': percentage
        })

    return render(request, 'student_dashboard.html', {
        'student': student,
        'data': data
    })



from django.shortcuts import render, redirect
from .models import Student

def student_login(request):
    if request.method == 'POST':
        reg_no = request.POST.get('registration_number')
        password = request.POST.get('password')

        try:
            student = Student.objects.get(registration_number=reg_no, password=password)
            # ✅ Save reg_no in session
            request.session['reg_no'] = student.registration_number
            return redirect('student_dashboard')

        except Student.DoesNotExist:
            error = "Invalid registration number or password"
            return render(request, 'student_login.html', {'error': error})

    return render(request, 'student_login.html')

def student_logout(request):
    try:
        del request.session['student_id']
    except KeyError:
        pass
    return redirect('student_login')
