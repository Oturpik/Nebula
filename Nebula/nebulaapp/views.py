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
from django.db import connections
from django.db.utils import OperationalError


## Getting the details of a specific student, using their email as their identifier
user_cache = {}
async def fetch_student(session, email):
    cached_user_data = user_cache.get(email)
    if cached_user_data:
        return JsonResponse(cached_user_data, safe=False)

    user_url = f'https://labmero.com/nebula_server/api/student/{email}'
    async with aiohttp.ClientSession() as session:
        async with session.get(user_url) as response:
            if response.status == 200:
                user_data = await response.json()
                user_cache[email] = user_data
                return JsonResponse(user_data, safe=False)
            

## getting a list of all the students in the program as per DB. 
async def fetch_students(request):
    url = 'https://labmero.com/nebula_server/api/students'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                students = await response.json()               
                ## fetching individual students from the data returned from the API call and combine them
                tasks = [fetch_student(session, student['email']) for student in students]
                await asyncio.gather(*tasks)
                
                for student in students:
                    student['email'] = user_cache.get(student['email'])
                return JsonResponse(students, safe=False)
                
            else:
                messages.add_message(request, messages.ERROR, f"Failed to fetch Students Details. Status code: {response.status}")
                return HttpResponse(f"Error: Failed to fetch Students Details. Status code: {response.status}")
            

## Getting details on Cohort stats
cohort_stats_cache = {}
async def fetch_cohort_stats(session, cohort_name):
    cached_stats_data = cohort_stats_cache.get(cohort_name)
    if cached_stats_data:
        return JsonResponse(cached_stats_data, safe=False)
    
    cohort_stats_url = f'https://labmero.com/nebula_server/api/cohort/stats/{cohort_name}'
    async with aiohttp.ClientSession() as session:
        async with session.get(cohort_stats_url) as response:
            if response.status == 200:
                stats_data = await response.json()
                cohort_stats_cache[cohort_name] = stats_data
                return JsonResponse(stats_data, safe=False)


## Getting  details on cohort attendance details
cohort_attendance_cache = {}
async def fetch_cohort_attendance_stats(session, cohort_name):
    cohort_attendance_url = f'https://labmero.com/nebula_server/api/cohort/attendance/{cohort_name}'
    async with session.get(cohort_attendance_url) as response:
        if response.status == 200:
            cohort_attendance_data = await response.json()
            cohort_attendance_cache[cohort_name] = cohort_attendance_data


##  Getting a Login view for students based on their information in the system. 
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


## Checking the status of the APIs
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


## Checking the status of the Database connection        
def fetch_dbconnection_check(request):
    try:        
        connections['default'].ensure_connection()        
        messages.add_message(request, messages.SUCCESS, "Your DB Connections are Healthy and Good to Go!")
        return HttpResponse("Your DB Connections are Healthy and Good to Go!")
    except OperationalError as e:        
        messages.add_message(request, messages.ERROR, f"Failed to fetch health check. Error: {str(e)}")
        return HttpResponse(f"Error: Failed to fetch health check. {str(e)}")            