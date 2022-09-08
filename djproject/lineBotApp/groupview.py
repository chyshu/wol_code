import json
import  psycopg2
from django.shortcuts import render

# Create your views here.
def index(request):
    
    return render(request, "groupreport.html")
