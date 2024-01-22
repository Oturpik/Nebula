from django.shortcuts import render
import requests
import aiohttp
import asyncio
from django.http import JsonResponse, HttpResponse
from django.db.models import Q

# Create your views here.

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



    

