from base64 import encode
from email import message
from pydoc_data.topics import topics
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from nebulaapp.models import Student, Cohort


def home(request):
    # Search for the students and the specific cohorts
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    #Filter students in the search based on name email and cohort
    students = Student.objects.filter(
        Q(name__icontains = q) |
        Q(email__icontains = q) |
        Q(cohort__icontains = q)
    )
    # Filter Cohorts based on names searched
    cohorts = Cohort.objects.filter(
        Q(name__icontains = q)
    )
    total_students = students.count()
    #all_attendance_average = 
    #all_assignment_completion =
    #cohort_performance_over_time =

    context = {'students':students, 'cohorts':cohorts, 'total_students':total_students}
    return render(request, 'index.html', context)



