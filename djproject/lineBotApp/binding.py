from calendar import SUNDAY
from cgitb import text
import json
import logging
from time import strftime,time
from flask import Flask
import datetime
from .classes import Member,Family,Friend
from .utils import next_weekday, getConnection, get_contactbase,get_contactbaseByContactName,getLineProfile
from django.shortcuts import render
from urllib.parse import urlsplit, parse_qs,parse_qsl
# Create your views here.
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from linebot.models import FlexSendMessage, BubbleContainer, ImageComponent
from linebot import LineBotApi, WebhookParser,WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage,JoinEvent,UnfollowEvent,FollowEvent,LeaveEvent,PostbackEvent,BeaconEvent,MemberJoinedEvent,MemberLeftEvent,AccountLinkEvent,ThingsEvent,ThingsEvent,SourceUser,SourceGroup,SourceRoom
from linebot.models import TemplateSendMessage, ButtonsTemplate, DatetimePickerTemplateAction,QuickReply,QuickReplyButton, MessageAction
import  psycopg2
from django.http import JsonResponse
 

app = Flask(__name__) 

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)

parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

#def getContactByName(anyname):

#    psconn =  getConnection()
#    pycursor = psconn.cursor()
    #pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    #today   = datetime.datetime.now() 
    
def getBindingMenu(contactid,displayname,userid,psconn):

    #useridjspon=json.dumps({"userid":userid})
    #print (useridjspon)
    msgcontents={
        "type": "carousel",  
        "contents": [
            {
                "type": "bubble",
                "size":  "mega",
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text" : "綁定",
                        "size":"xl",
                        "weight":"bold",
                        "color":"#1a5276FF",
                    }],
                    "backgroundColor": "#f1c40fF0",
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents":[ 
                                {
                                    "type": "button",
                                    "margin":"xs",
                                    "style":"primary",
                                    "color": "#B25068",
                                    "action": {
                                        "type": "postback",
                                        "label":"帳戶綁定",
                                        "data":"action=bindingme"
                                    }
                                },
                                {
                                    "type": "button",
                                    "margin":"xs",
                                    "style":"primary",
                                    "color": "#0E918C",
                                    "action": {
                                        "type": "postback",
                                        "label":"家人名單",
                                        "data":"action=myfamily"
                                    }
                                },     
                                 {
                                    "type": "button",
                                    "margin":"xs",
                                    "style":"primary",
                                    "color": "#0E918C",
                                    "action": {
                                        "type": "uri",
                                        "label":"新增家人",
                                        "uri":settings.SERVER_URL+"closefriend?userid="+userid
                                    }
                                },                                                                           
                            ]
                        },                                                                                                 
                    ]
                },
                "footer":{
                    "type": "box",
                    "layout": "vertical",
                    "paddingAll":"xl",
                    "contents": [
                    ],

                }
            },                              
        ]
    }
    msgcontents["contents"][0]["footer"]["contents"].append(
        {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color": "#FF8000",
            "action": {
                "type": "postback",
                "label":"回上層",
                "data":"action=cherub"
            }
        }
    )
    return msgcontents

def getBindingData(userid,psconn):
    #psconn =  getConnection()
    pycursor = psconn.cursor()
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    today   = datetime.datetime.now()
    #print(contactid+";"+userid )
    msgcontents={
            "type": "carousel",  
            "contents": [
                {
                    "type": "bubble",
                    "size":  "mega",
                    "header" :{
                        "type": "box",
                        "layout": "vertical",
                        "contents":[{
                            "type" : "text",
                            "text" : "綁定資料",
                            "size" :"xl",
                            "weight":"bold",
                            "color":"#1a5276FF",
                        }],
                        "backgroundColor": "#f1c40fF0",
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                        ],
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "paddingAll":"xl",
                        "contents": [
                        ],
                    },
                }
            ]
        }
    listName=""  
    contactid=""  
    birthdate=""  
    mobilephone=""  
    display_name=""
    isediting=""
    input_name=""
    contactid=""
    pycursor.execute("""select   groupId,user_id, contactid,displayname,sid,input_name,isediting  from Id2contact  where user_id=%s   """ ,[   userid  ])
    Id2contact_row = pycursor.fetchone()    
    if Id2contact_row==None:
        try:
            profile = line_bot_api.get_profile(userid)        
            if profile:                                     
                app.logger.info("profile:"+ profile.display_name )
                app.logger.info("profile:"+ profile.user_id )
                display_name=profile.display_name                   
            
        except LineBotApiError as e:
            app.logger.error("profile err " + e.message)        
        if display_name!="":        
            pycursor.execute("""select   contactid,lastname, birthdate,mobilephone  from contactbase  where new_line_displayname like '%"""+display_name+"""%'   """ )
            contactbaserow = pycursor.fetchone()    
            if contactbaserow:
                contactid=str(contactbaserow[0])
                if contactbaserow[1]!=None:
                    listName=str(contactbaserow[1]) 
                if contactbaserow[2]!=None:
                    birthdate=contactbaserow[2].strftime('%Y/%m/%d') 
                if contactbaserow[3]!=None:
                    mobilephone=str(contactbaserow[3] )
        pycursor.execute("""insert into id2contact (groupId, user_id,displayname,contactid) values (%s,%s,%s,%s) """ ,["",userid,display_name,contactid  ])  
    else:    
        if Id2contact_row[2]!=None:
            contactid=str(Id2contact_row[2])
        if Id2contact_row[3]!=None:
            display_name=str(Id2contact_row[3])  
        if Id2contact_row[5]!=None:
            input_name=str(Id2contact_row[5])  
        if Id2contact_row[6]!=None:
            isediting=str(Id2contact_row[6])                          
        if contactid!="":        
            pycursor.execute("""select   contactid,lastname, birthdate,mobilephone  from contactbase  where contactid =%s  """,[contactid ] )
            contactbaserow = pycursor.fetchone()    
            if contactbaserow:
                if contactbaserow[1]!=None:
                    listName=str(contactbaserow[1])
                if contactbaserow[2]!=None:
                    birthdate=contactbaserow[2].strftime('%Y/%m/%d') 
                if contactbaserow[3]!=None:
                    mobilephone=contactbaserow[3]
        else:
            # ID2Contact contactid=""
            if display_name!="":
                pycursor.execute("""select   contactid,lastname, birthdate,mobilephone  from contactbase  where new_line_displayname like '%"""+display_name+"""%'   """ )
                contactbaserow = pycursor.fetchone() 
                if contactbaserow:
                    contactid=str(contactbaserow[0])
                    if contactbaserow[1]!=None:
                        listName=str(contactbaserow[1]) 
                    if contactbaserow[2]!=None:
                        birthdate=contactbaserow[2].strftime('%Y/%m/%d') 
                    if contactbaserow[3]!=None:
                        mobilephone=str(contactbaserow[3] )   
                    if contactid!="":
                        pycursor.execute("""update id2contact  set displayname=%s,contactid=%s where sid=%s """ ,[display_name,contactid, Id2contact_row[4]  ])  

    if input_name!="" and isediting=="Y":
        listName=input_name
        birthdate=""
        contactid=""
    msgcontents["contents"][0]["body"]["contents"].append(
        { "type": "box",
            "layout": "vertical",
            "contents":[
                {
                    "type": "text",
                    "text": "Line用戶ID: "+ userid ,
                    "size":"md",
                    "weight":"bold",
                    "wrap" : True,
                    "color":"#000000",
                    "margin":"xs",
                },
                {
                    "type": "text",
                    "text": "Line用戶名: "+ display_name ,
                    "size":"md",
                    "weight":"bold",
                    "wrap" : True,
                    "color":"#000000",
                    "margin":"xs",
                },
                {
                    "type": "text",
                    "text": "代碼: "+ contactid[:13] ,
                    "size":"md",
                    "weight":"bold",
                    "wrap" : True,
                    "color":"#000000",
                    "margin":"xs",
                },
                {
                    "type": "text",
                    "text": "姓名: "+listName ,
                    "size":"md",
                    "weight":"bold",
                    "wrap" : True,
                    "color":"#000000",
                    "margin":"xs",
                },
                {
                    "type": "text",
                    "text": "生日: "+birthdate ,
                    "size":"md",
                    "weight":"bold",
                    "wrap" : True,
                    "color":"#000000",
                    "margin":"xs",
                },
            ]
        }             
    )    
    if isediting!='Y':
        msgcontents["contents"][0]["footer"]["contents"].append(
            {
                "type": "button",
                "margin":"xs",
                "style":"primary",
                "color": "#A64B2A",
                "action": {
                    #"type": "postback",
                    "type":"uri",
                    "label":"重新綁定",
                    #"data":"action=bindingName"
                    "uri":settings.SERVER_URL+"bindingMe?userid="+userid
                }
            }
        )
    #if isediting=='Y':
        #msgcontents["contents"][0]["footer"]["contents"].append(
        #    {
        #        "type": "button",
        #        "margin":"xs",
        #        "style":"primary",
        #        "color": "#A64B2A",
        #        "action": {
        #            "type": "postback",
        #            "label":"與資料庫綁定",
        #            "data":"action=bindingData"
        #        }
        #    }
        #)
    

        #msgcontents["contents"][0]["footer"]["contents"].append(
        #    {
        #        "type": "button",
        #       "margin":"xs",
        #       "style":"primary",
        #       "color": "#7C99AC",
        #       "action": {
        #            "type": "postback",
        #            "label":"放棄綁定",
        #            "data":"action=bindingAbort"
        #        }
        #    }
        #)
        
    msgcontents["contents"][0]["footer"]["contents"].append(
        {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color": "#FF8000",
            "action": {
                "type": "postback",
                "label":"回上層",
                "data":"action=bindingMenu"
            }
        }
    )
    pycursor.close()
    return msgcontents

def getFamily(userid,psconn):
    #psconn =  getConnection()
    app.logger.info(userid)
    pycursor = psconn.cursor()
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    today   = datetime.datetime.now()
    msgcontents={
        "type": "carousel",  
        "contents": [
            {
                "type": "bubble",
                "size":  "mega",
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text" : "家人名單",
                        "size":"xl",
                        "weight":"bold",
                        "color":"#1a5276FF",
                    }],
                    "backgroundColor": "#f1c40fF0",
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents":[ 
                                                                                     
                            ]
                        },                                                                                                 
                    ]
                },
                "footer":{
                    "type": "box",
                    "layout": "vertical",
                    "paddingAll":"xl",
                    "contents": [
                    ],

                }
            },                              
        ]
    }
    pycursor.execute("""select   groupId,user_id, contactid,displayname,sid,input_name,isediting  from Id2contact  where user_id=%s   """ ,[   userid  ])
    Id2contact_row = pycursor.fetchone() 
    if Id2contact_row[2]!=None and str(Id2contact_row[2])  !="" :
        pycursor.execute("""select  sid,contactid, familyid  from closegroup  where contactid=%s   """ ,[   str(Id2contact_row[2])   ])
        for closegroup_row in  pycursor.fetchall() :
            if closegroup_row[2]!=None and str (closegroup_row[2])  !="" :
                pycursor.execute("""select   contactid,lastname, birthdate,mobilephone  from contactbase  where contactid =%s  """,[(closegroup_row[2]) ] )
                contactbaserow = pycursor.fetchone() 
                if  contactbaserow:
                    msgcontents["contents"][0]["body"]["contents"].append(
                        {
                            "type": "box",
                            "layout": "horizontal",                            
                            "margin":"xs",
                            "contents":[
                                {
                                    "type": "text",
                                    "text": ""+ str(contactbaserow[1]) ,
                                    "size":"md",
                                    "weight":"bold",
                                    "wrap" : True,
                                    "color":"#000000",
                                    "margin":"xs",
                                    "gravity": "center",
                                    "flex":3
                                },
                                 {
                                    "type": "button",                                    
                                    "height":"sm",
                                    "style":"primary",
                                    "color": "#134F5C",
                                    "width":"60px",
                                    "flex":1,
                                    "action": {
                                        "type": "postback",
                                        "label":"X",
                                        "data":"action=removeFriend&friendid="+str(contactbaserow[0]) ,
                                    }
                                }
                            ]
                        }
                    )

    msgcontents["contents"][0]["footer"]["contents"].append(
        {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color": "#FF8000",
            "action": {
                "type": "postback",
                "label":"回上層",
                "data":"action=bindingMenu"
            }
        }
    )
    pycursor.close()
    return msgcontents

@csrf_protect
def addMe(request):
    result=""	
    member  = Member(None,None,None,None,None,None)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax and request.method == "POST":
        contactname = request.POST.get('contactname',None)
        # print( contactname)
        userid=request.session["userid"] 
        # print(userid)
        psconn=getConnection()
        member= get_contactbaseByContactName(contactname,psconn)
        if member.contactid!=None:
           # psconn =  getConnection()
            pycursor = psconn.cursor()
            pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")

            pycursor.execute("""select contactid,user_id,displayname,sid from Id2contact where user_id=%s""" ,[ userid ])
            row = pycursor.fetchone()
            if row:
                pycursor.execute(""" update Id2contact set contactid=%s where sid=%s""" ,[   member.contactid, str(row[3])	 ])	
                result="綁定資料成功"
            else:                
                pycursor.execute("""insert into id2contact (groupId, user_id,displayname,contactid) values (%s,%s,%s,%s) """ ,[ "", userid ,  "" ,    member.contactid ]) 
                profile= getLineProfile( userid )
                if profile:                        
                    pycursor.execute("""update id2contact set displayname=%s where user_id =%s """ ,[  profile.display_name ,userid ])
                result="綁定資料成功"
            pycursor.close()                
        else:
            result="找不到"+contactname+"的資料"
            
        return JsonResponse({ "result": { "familymember":   json.dumps(member.__dict__) , "error":result}  }, status=200)
    return JsonResponse( {"result": {"error": "UNKNOWN SOURCE" , "member" : json.dumps(member.__dict__) } } , status=200)    


@csrf_protect
def bindingMe(requet):
    app = Flask(__name__)    
    result=""
    with app.test_request_context():
 
        userid = requet.GET.get('userid',None)
        app.logger.debug(userid)
    
    userid = requet.GET.get('userid',None)
    contactName=""

    requet.session["userid"] =userid
    return render(requet, "bindingMe.html",{"contactname":contactName  })

@csrf_protect
def findContactByName(request):    
    result=""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax and request.method == "POST":
        json_data = json.loads(request.body)
        contactname = json_data["contactname"]
        psconn = getConnection()
        member= get_contactbaseByContactName(contactname ,psconn )
        if member.contactid==None:        
            result="找不到"+ contactname+"的資料"
            
        return JsonResponse({ "result": { "member":   json.dumps(member.__dict__) , "error":result}  }, status=200)
    return JsonResponse( {"result": {"error": "UNKNOWN SOURCE" , "member" : json.dumps(member.__dict__) } } , status=200)    
