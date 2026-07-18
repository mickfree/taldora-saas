from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    return render(request, 'index.html')
