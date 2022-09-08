
from calendar import SUNDAY
from cgitb import text
from email.policy import default
from hashlib import new
import json
import logging
from time import strftime,time
from flask import Flask
import datetime
from .classes import Member,Family,Friend,Worshipdata
from .utils import next_weekday, getConnection, get_contactbase,get_contactbaseByContactName,getLineProfile,current_weekday
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

#psconn =  getConnection()

#pycursor = psconn.cursor()
#pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")

@csrf_protect
def getProfile(request):
    result=""
    today   = datetime.datetime.now()  
    member  = Member(None,None,None,None,None,None)
    # worshipdata   =  Worshipdata (None,None,None,None,None,None)
    the_sunday = current_weekday( datetime.date(today.year, today.month, today.day) , 6)
    
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax and request.method == "POST":
                
        data  = request.body.decode('utf-8')
        body = json.loads( data )
        worship=[]
        worshipgroup=[]
        prayforme=[]
        listid=""
        listname=""
        psconn=getConnection()
        with  psconn.cursor() as pycursor:
          pycursor.execute("""select distinct worship_date   from worshipdate where worship_date<=%s order by worship_date desc limit 4""" ,[ the_sunday.strftime('%Y-%m-%d') ])
          worshipdate_rows = pycursor.fetchall()
          for  worshipdate in worshipdate_rows:
            worship.append({"worshipdate": worshipdate[0].strftime('%Y-%m-%d'),
                            "week":[] ,
                            "session":"未回報", 
                            "worship_times":"0",
                            "prayforme":{"prayid":"","tdate":"","description":"" },
                            "groupworship":{"worshipdate":"","listid":"","listname":"" }
             })
            weekdate= worshipdate[0]
            d=0            
            while d<=6:
                adate  =  weekdate+ datetime.timedelta(d)
                worship[ len(worship)-1  ]["week"].append( adate  )
                d=d+1
          member= get_contactbase(body["UserID"],psconn)
          #print( member.contactid) 
          if member.contactid!="":
            
            pycursor.execute("""select listbase.ListId,listbase.listName , group_place, group_time
                   from ListMemberBase inner  join listbase on listbase.ListId = ListMemberBase.ListId 
                   where ListMemberBase.EntityId=%s   and purpose='小組名單' """ ,[ member.contactid    ])
            listbase_rows = pycursor.fetchall()
            for listbase in listbase_rows:
                worshipgroup.append( {"listid":listbase[0] , "listName":listbase[1]  }  )

            for wdate in worship:
                # print(wdate["worshipdate"]   ) 
                pycursor.execute("""select contactid,user_id,worship_date,session from worship where contactid=%s and worship_date=%s and del_flag='N' """ ,[ member.contactid ,wdate["worshipdate"] ])
                worship_row = pycursor.fetchone()                
                if worship_row:                    
                    wdate["session"]=worship_row[3]
            

                pycursor.execute("""select contactid,user_id,worship_date,worship_times from personalworship where contactid=%s and worship_date=%s and del_flag='N' """ ,[ member.contactid , wdate["worshipdate"]   ])
                personalworship_row = pycursor.fetchone()
                if personalworship_row:                    
                    wdate["worship_times"]= personalworship_row[3]
                            
                next_sunday = next_weekday( datetime.datetime.strptime( wdate["worshipdate"]  , '%Y-%m-%d' ) , 6)
                #print(    next_sunday.strftime('%Y-%m-%d'))
                pycursor.execute("""select contactid,listid,worship_date from groupship where contactid=%s and week_date = %s   and del_flag='N' """ ,
                                [ member.contactid , datetime.datetime.strptime( wdate["worshipdate"]  , '%Y-%m-%d' )  ])
                
                groupworship_row = pycursor.fetchone()
                if groupworship_row:                    
                    listid=groupworship_row[1]
                    print( groupworship_row[2] )
                    wdate["groupworship"]["worshipdate"]= groupworship_row[2]
                    wdate["groupworship"]["listid"]= groupworship_row[1]

                    pycursor.execute("""select  listname from listbase  where  listid =%s   """ ,[ listid ])
                    listbase_row = pycursor.fetchone() 
                    if listbase_row:
                        wdate["groupworship"]["listname"]= listbase_row[0]
                print(wdate["worshipdate"]   ) 
                print(next_sunday  )
                pycursor.execute("""select prayid,tdate,description from prayforme  where contactid=%s and week_date= %s   and del_flag='N' and isclose<>'Y'  order by sid """ ,
                                [ member.contactid , datetime.datetime.strptime( wdate["worshipdate"]  , '%Y-%m-%d' )      ])
                prayforme_row = pycursor.fetchone()
                if prayforme_row: 
                    wdate["prayforme"]["prayid"]=prayforme_row[0]
                    wdate["prayforme"]["tdate"]=prayforme_row[1]
                    wdate["prayforme"]["description"]=prayforme_row[2]


            #print(json.dumps(worship,default=str) )
            #print(json.dumps(worshipgroup,default=str) )
            return JsonResponse({ "result": { "member":   json.dumps(member.__dict__,default=str) , "worship":  json.dumps(worship,default=str),"worshipgroup":  json.dumps(worshipgroup,default=str) , "error":result}  }, status=200)
        psconn.close()
    return JsonResponse( {"result": {"error": "UNKNOWN SOURCE" , "member" : json.dumps(member.__dict__), "worship":  json.dumps(worship,default=str) ,"worshipgroup":  json.dumps(worshipgroup,default=str)   } } , status=200)    
