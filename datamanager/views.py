from django.shortcuts import render
from django.http import HttpResponse
from jumpserver.api import *

# Create your views here.
def list(request):
    return my_render('datamanager/list.html', locals(), request)

def file_sync(request):
    if request.method == "POST":
        print request.POST
    return HttpResponse("hello") 
