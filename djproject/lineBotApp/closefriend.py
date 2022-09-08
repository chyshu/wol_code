#from hello import views
from django.shortcuts import render
from urllib.parse import urlsplit, parse_qs,parse_qsl
import json
from django.http import JsonResponse
from requests import session

from django.conf import settings
from .utils import get_contactbase,get_contactbaseByContactName,addCloseGroup,getConnection
import  psycopg2
from flask import Flask, current_app
import _thread
from django.views.decorators.csrf import csrf_protect
from .classes import CloseFriend

app = Flask(__name__) 

#app.logger.info(settings.BASE_DIR )

def bindingPerson(sid):
    userid = request.args.get('userid',None)
    member=get_contactbase( userid)

@csrf_protect
def index(requet):
#    app = Flask(__name__)    
    result=""
    with app.test_request_context():
 
        userid = requet.GET.get('userid',None)
        app.logger.debug(userid)
    conn=getConnection()
    userid = requet.GET.get('userid',None)
    member=get_contactbase( userid, conn)
    familyname=requet.POST.get('familyname',None)
    if(familyname!=None):
        familymember=get_contactbaseByContactName( familyname,conn)
        if familymember.contactid!=None:
            #print(familymember.contactname)
            #print(familymember.contactid)
            result=addCloseGroup(member, familymember,conn)
            familyname=familymember.contactname
            
        else:
            result="找不到他的資料"
            print(familyname +" NOT FOUND")
    

    app.logger.debug(userid)
    requet.session["userid"] =userid
    return render(requet, "closefriend.html",{"member":member , "familyname":"","addResult": result })

@csrf_protect
def addFriend(request):
    result=""
    userid=request.session["userid"] 
    #print(userid)
    conn=getConnection()
    member=get_contactbase( userid,conn )
    familyname=request.POST.get('familyname',None)
    familymember=get_contactbaseByContactName( familyname,conn)
         
    
    if familymember.contactid!=None:
        #print(familymember.contactname)
        #print(familymember.contactid)
        result=addCloseGroup(member, familymember,conn )
        familyname=familymember.contactname
        result="新增成功"
    else:
        result="找不到他的資料"
        print(familyname +" NOT FOUND")
        
    return render(request, "closefriend.html",{"member":member,"familyname":familyname,"addResult": result })

@csrf_protect
def addCloseMember(request):
    result=""	
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax and request.method == "POST":
        familyname = request.POST.get('familyname',None)
        print( familyname)
        userid=request.session["userid"] 
        print(userid)
        conn =getConnection()
        member=get_contactbase( userid ,conn )        
        familymember=get_contactbaseByContactName( familyname,conn)
        if familymember.contactid!=None:
            print(familymember.contactname)
            print(familymember.contactid)
            result=addCloseGroup(member, familymember,conn)
            familyname=familymember.contactname
            result="新增成功"
        else:
            result="找不到他的資料"
            print(familyname +" NOT FOUND")            
        return JsonResponse({ "result": { "familymember":   json.dumps(familymember.__dict__) , "error":result}  }, status=200)
    return JsonResponse( {"result": {"error": "" , "familymember" :None } } , status=400)
