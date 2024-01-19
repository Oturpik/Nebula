from django.shortcuts import render
import requests
import aiohttp
import asyncio
from django.http import JsonResponse, HttpResponse
from django.db.models import Q

# Create your views here.

user_cache = {}

async def fetch_user(session, email ):
    user_url = f'https://labmero.com/nebula_server/api/student/{email}'
    async with session.get(user_url) as response:
        if response.status == 200:
            user_data = await response.json()
            # saving user data in cache for later retrieval
            user_cache[email] = user_data



