from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from .models import Specialization, Appointment, Counselor, Book

User = get_user_model()


# =========================
# STUDENT REGISTRATION
# =========================
class StudentRegistrationForm(UserCreationForm):
    service_number = forms.CharField(max_length=50)
    rank = forms.CharField(max_length=50)
    first_name = forms.CharField(max_length=50, label="First Name")
    last_name = forms.CharField(max_length=50, label="Last Name")
    school = forms.CharField(max_length=100)
    class_name = forms.CharField(max_length=50)

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'password1',
            'password2',
            'service_number',
            'rank',
            'first_name',
            'last_name',
            'school',
            'class_name',
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'
        user.is_approved = False
        if commit:
            user.save()
        return user


# =========================
# COUNSELOR USER CREATION
# =========================
class CounselorCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, label="First Name")
    last_name = forms.CharField(max_length=50, label="Last Name")
    service_number = forms.CharField(max_length=50, required=False)
    rank = forms.CharField(max_length=50, required=False)
    specialization = forms.ModelChoiceField(
        queryset=Specialization.objects.all(),
        required=True
    )

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'password1',
            'password2',
            'first_name',
            'last_name',
            'service_number',
            'rank',
            'specialization',
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'counselor'
        user.is_approved = True
        if commit:
            user.save()
        return user


# =========================
# COUNSELOR PROFILE FORM
# =========================
class CounselorForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(label="First Name", required=True)
    last_name = forms.CharField(label="Last Name", required=True)

    class Meta:
        model = Counselor
        fields = ['specialization', 'phone', 'bio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if getattr(self.instance, 'user', None):
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        counselor = super().save(commit=False)
        if counselor.user:
            counselor.user.email = self.cleaned_data['email']
            counselor.user.first_name = self.cleaned_data['first_name']
            counselor.user.last_name = self.cleaned_data['last_name']
            counselor.user.save()
        if commit:
            counselor.save()
        return counselor


# =========================
# SPECIALIZATION FORM
# =========================
class SpecializationForm(forms.ModelForm):
    class Meta:
        model = Specialization
        fields = '__all__'


# =========================
# APPOINTMENT FORM
# =========================
class AppointmentForm(forms.ModelForm):
    specialization = forms.ModelChoiceField(
        queryset=Specialization.objects.all(),
        required=True
    )
    counselor = forms.ModelChoiceField(
        queryset=User.objects.filter(role='counselor'),
        required=True
    )

    class Meta:
        model = Appointment
        fields = ('specialization', 'counselor', 'date', 'time')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default: no counselors until specialization selected
        self.fields['counselor'].queryset = User.objects.none()

        if 'specialization' in self.data:
            try:
                spec_id = int(self.data.get('specialization'))
                self.fields['counselor'].queryset = User.objects.filter(
                    role='counselor',
                    counselor_profile__specialization_id=spec_id,
                    is_approved=True
                )
            except (ValueError, TypeError):
                pass

# =========================
# BOOKS
# =========================
class BookUploadForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'file']