"""djproject URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.conf.urls.static import static
from django.conf import settings
from django.http import HttpResponse
import datetime
from flask import Flask, request, abort
import lineBotApp.views,lineBotApp.closefriend,lineBotApp.userdata,lineBotApp.mygroupworship
import lineBotApp.prayforme,lineBotApp.groupview, lineBotApp.binding,lineBotApp.myworship


app = Flask(__name__)

#app.logger.info("URL CALL");

def  index(request):
	tdate=  datetime.datetime.now()
	return HttpResponse("Hello Nuts! current time is "+ tdate.strftime('%Y-%m-%d %H:%M:%S'))

app_name = 'bot_of_wolapp'

urlpatterns = [
    path('webhook/',lineBotApp.views.webhook,name="webhook"),
    path('closefriend/',lineBotApp.closefriend.index,name="closefriend"),
    path('addCloseMember/' , lineBotApp.closefriend.addCloseMember,name="addCloseMember"), 
    path('admin/', admin.site.urls),
    path('addCloseMember/' ,lineBotApp.closefriend.addCloseMember,name="addCloseMember"), 
    path('bindingMe/' , lineBotApp.binding.bindingMe),
    path('addMe/' , lineBotApp.binding.addMe,name="addMe"),
    path('findMe/' , lineBotApp.binding.findContactByName,name="findMe"),    
    path('myworship/' , lineBotApp.myworship.myworship,name="myworship"),
    path('mygroupworship/' , lineBotApp.mygroupworship.index,name="mygroupworship"),
    path('getMemberProfile/',lineBotApp.mygroupworship.getMemberProfile ,name="getMemberProfile"),
    path('setMemberWorship/',lineBotApp.mygroupworship.setMemberWorship ,name="setMemberWorship"),
    path('worship/' , lineBotApp.myworship.worship,name="worship"),
    path('PrayEdit/' , lineBotApp.prayforme.PrayEdit),
    path('PostPray/' , lineBotApp.prayforme.PostPray,name="PostPray"),
    path('getProfile/',lineBotApp.userdata.getProfile ,name="getProfile"),
    path('',index),
]

#app.logger.info("URL SEND")

urlpatterns+=static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
