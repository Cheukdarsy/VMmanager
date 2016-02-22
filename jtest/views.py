from django.shortcuts import render
from django.http import HttpResponse

from jumpserver.api import *
from jumpserver.models import Setting

# Create your views here.

def test_list():
    return HttpResponse('hello jumpserver!')
