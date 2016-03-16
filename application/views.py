from django.shortcuts import render,render_to_response

# Create your views here.

def index(request):
    return render_to_response('application-index.html')

def management(request):
    return render_to_response('application-management.html')