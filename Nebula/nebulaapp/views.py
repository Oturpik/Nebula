from base64 import encode
from email import message
from pydoc_data.topics import topics
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.views import LoginView
from nebulaapp.models import Student, Cohort
from django.shortcuts import render
import requests
from requests import request
import aiohttp
import asyncio
from django.http import JsonResponse, HttpResponse


user_cache = {}
async def fetch_student(session, email ):
    user_url = f'https://labmero.com/nebula_server/api/student/{email}'
    async with session.get(user_url) as response:
        if response.status == 200:
            user_data = await response.json()
            # saving user data in cache for later retrieval
            user_cache[email] = user_data

            # Getting the specific details for each student
            for user in user_data:
                if user['id'] == user['weeklyAttendance']['student_id']:
                    return user

async def fetch_students():
    url = f'https://labmero.com/nebula_server/api/students'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response == 200:
                students = await response.json() 


## Getting details on Cohort stats
cohort_stats_cache = {}
async def fetch_cohort_stats(session, cohort_name):
    cohort_stats_url = f'https://labmero.com/nebula_server/api/cohort/stats/{cohort_name}'
    async with session.get(cohort_stats_url) as response:
        if response.status == 200:
            cohort_stats_data = await response.json()
            cohort_stats_cache[cohort_name] = cohort_stats_data


## Getting  details on cohort attendance details
cohort_attendance_cache = {}
async def fetch_cohort_attendance_stats(session, cohort_name):
    cohort_attendance_url = f'https://labmero.com/nebula_server/api/cohort/attendance/{cohort_name}'
    async with session.get(cohort_attendance_url) as response:
        if response.status == 200:
            cohort_attendance_data = await response.json()
            cohort_attendance_cache[cohort_name] = cohort_attendance_data


def login(request):
    if request.method == "POST":
        ## We will use the email as the username and the cohort as the password
        username = request.POST.get('username')
        password = request.POST.get('password')

        students_url = "https://labmero.com/nebula_server/api/students"
        response = requests.get(students_url)
        students_data = response.json()

        ## Finding users with a matching email address and a cohort name
        authenticated_student = None
        for student in students_data:
            if student['email'] == username and student['cohort'] == password:
                authenticated_student = student
                break
        if authenticated_student:
            return JsonResponse({'student': authenticated_student}, safe=False)
        
        else:
            return JsonResponse({'student': '0'}, safe=False)
    return render(request, 'index.html')


async def fetch_health_check(request):
    url = 'https://labmero.com/nebula_server/api/health-check'    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                messages.add_message(request, messages.SUCCESS, "Your APIs are Healthy and Good to Go!")
                return HttpResponse("Your APIs are Healthy and Good to Go!") 
            else:
                messages.add_message(request, messages.ERROR, f"Failed to fetch health check. Status code: {response.status}")
                return HttpResponse(f"Error: Failed to fetch health check. Status code: {response.status}")