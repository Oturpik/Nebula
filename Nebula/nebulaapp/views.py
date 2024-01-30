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

async def fetch_student(request, email):
    cached_user_data = user_cache.get(email)
    if cached_user_data:
        return JsonResponse(cached_user_data, safe=False)

    user_url = f'https://labmero.com/nebula_server/api/student/{email}'
    async with aiohttp.ClientSession() as session:
        async with session.get(user_url) as response:
            if response.status == 200:
                user_data = await response.json()

                # Extract attendance average and assignment completion from the response
                attendance_average = user_data.get('attendance_average', 0)
                assignment_completion = user_data.get('assignment_completion', 0)

                # Add attendance average and assignment completion to the response
                user_data['attendance_average'] = attendance_average
                user_data['assignment_completion'] = assignment_completion

                # Cache the result
                user_cache[email] = user_data

                return JsonResponse(user_data, safe=False)
            else:
                return JsonResponse({"error": f"Failed to fetch student data. Status code: {response.status}"}, status=500)
            

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
                #total_students = students[id].count()
                
                for student in students:
                    student['email'] = user_cache.get(student['email'])
                    #print(students)
                return JsonResponse(students, safe=False)
                
                
            else:
                messages.add_message(request, messages.ERROR, f"Failed to fetch Students Details. Status code: {response.status}")
                return HttpResponse(f"Error: Failed to fetch Students Details. Status code: {response.status}")
            

## Getting details on Cohort stats
cohort_stats_cache = {}

async def fetch_cohort_stats(request, cohort_name):
    search_query = request.GET.get('search', None)

    # If a search query is provided, modify the cohort_stats_url accordingly
    if search_query:
        cohort_stats_url = f'https://labmero.com/nebula_server/api/cohort/stats/{cohort_name}?search={search_query}'
    else:
        cohort_stats_url = f'https://labmero.com/nebula_server/api/cohort/stats/{cohort_name}'

    # Check if the data is cached
    cached_stats_data = cohort_stats_cache.get(cohort_name)
    if cached_stats_data:
        return JsonResponse(cached_stats_data, safe=False)

    # Fetch cohort statistics from the API
    async with aiohttp.ClientSession() as session:
        async with session.get(cohort_stats_url) as response:
            if response.status == 200:
                stats_data = await response.json()

                # Calculate the sum of attendance averages across unique weeks
                attendance_averages = [week.get('attendanceAverage', 0) for week in stats_data.get('weeks', [])]
                total_attendance_average = sum(attendance_averages)

                # Add the total attendance average to the response
                stats_data['totalAttendanceAverage'] = total_attendance_average

                # Include total_students, assignment_completion, and attendance_average in the response
                stats_data['total_students'] = stats_data.get('total_students', 0)
                stats_data['assignment_completion'] = stats_data.get('assignment_completion', 0)
                stats_data['attendance_average'] = stats_data.get('attendance_average', 0)

                # Cache the result
                cohort_stats_cache[cohort_name] = stats_data

                return JsonResponse(stats_data, safe=False)
            else:
                return JsonResponse({"error": f"Failed to fetch cohort stats. Status code: {response.status}"}, status=500)


## Getting  details on cohort attendance details
cohort_attendance_cache = {}
async def fetch_cohort_attendance_stats(request, cohort_name):
    search_query = request.GET.get('search', None)

    # If a search query is provided, modify the cohort_stats_url accordingly
    if search_query:
        cohort_attendance_url = f'https://labmero.com/nebula_server/api/cohort/attendance/{cohort_name}?search={search_query}'
    else:
        cohort_attendance_url = f'https://labmero.com/nebula_server/api/cohort/attendance/{cohort_name}'

    # Check if the data is cached
    cached_attendance_data = cohort_attendance_cache.get(cohort_name)
    if cached_attendance_data:
        return JsonResponse(cached_attendance_data, safe=False)

    # Fetch cohort statistics from the API
    async with aiohttp.ClientSession() as session:
        async with session.get(cohort_attendance_url) as response:
            if response.status == 200:
                stats_data = await response.json()

                # Calculate the sum of attendance averages across unique weeks
                attendance_averages = [week.get('attendanceAverage', 0) for week in stats_data.get('week', [])]
                total_attendance_average = sum(attendance_averages)

                # Add the total attendance average to the response
                stats_data['totalAttendanceAverage'] = total_attendance_average

                # Cache the result
                cohort_attendance_cache[cohort_name] = stats_data

                return JsonResponse(stats_data, safe=False)
            else:
                return JsonResponse({"error": f"Failed to fetch cohort stats. Status code: {response.status}"}, status=500)


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
def fetch_health_check(request):
    #url = 'https://labmero.com/nebula_server/api/health-check'
    url = 'http://127.0.0.1:8000/api/health-check'

    try:
        response = requests.get(url)

        if response.status_code == 200:
            messages.add_message(request, messages.SUCCESS, "Your APIs are Healthy and Good to Go!")
            return HttpResponse("Your APIs are Healthy and Good to Go!")
        else:
            messages.add_message(request, messages.ERROR, f"Failed. Your APIs are Sick and need Fixing. Status code: {response.status_code}")
            return HttpResponse(f"Error: Failed. Your APIs are Sick and need Fixing. Status code: {response.status_code}")

    except requests.RequestException as e:
        messages.add_message(request, messages.ERROR, f"Error during health check: {str(e)}")
        return HttpResponse(f"Error: {str(e)}")


## Checking the status of the Database connection        
def fetch_dbconnection_check(request):
    try:        
        connections['default'].ensure_connection()        
        messages.add_message(request, messages.SUCCESS, "Your DB Connections are Healthy and Good to Go!")
        return HttpResponse("Your DB Connections are Healthy and Good to Go!")
    except OperationalError as e:        
        messages.add_message(request, messages.ERROR, f"Failed to fetch health check. Error: {str(e)}")
        return HttpResponse(f"Error: Failed to fetch health check. {str(e)}")            
    

def index(request):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    students = loop.run_until_complete(fetch_students(request))
    
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    if q:
        students = [student for student in students if q.lower() in student['name'].lower() or q.lower() in student['cohort'].lower()]

        if students is not None:
            context = {'students': students, 'q': q}
            return render(request, 'assets/index.html', context)
        else:
            context = {'error_message': 'failed to fetch data from the API'}
            return render(request, 'error.html', context)
