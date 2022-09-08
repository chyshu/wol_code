from calendar import SUNDAY
from cgitb import text
import json
import logging
from pickle import NONE
from time import strftime,time
from flask import Flask
import datetime
from .classes import Member,Family,Friend
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
def myworship(requet):

    result=""
    today   = datetime.datetime.now()  
    #with app.test_request_context():
# 
#        userid = requet.GET.get('userid',None)
#        app.logger.debug(userid)
#    
#    userid = requet.GET.get('userid',None)
#    member=get_contactbase( userid)
    contactName=""
#    if(member!=None):
#        contactName=member.contactname

 #   requet.session["userid"] =userid
    next_sunday = current_weekday( datetime.date(today.year, today.month, today.day) , 6)

    weeklist=[]
    #pycursor.execute("""select distinct worship_date   from worshipdate where worship_date<=%s order by worship_date desc limit 4""" ,[ next_sunday.strftime('%Y-%m-%d') ])
    #worshipdate_rows = pycursor.fetchall()
    #for  worshipdate in worshipdate_rows:
    #    weeklist.append({"worshipdate": worshipdate[0].strftime('%Y-%m-%d')})    
    return render(requet, "myworship.html",{"contactname":contactName , "weeklist":weeklist  })

@csrf_protect
def worship(request):
    result="UNKNOWN SOURCE"  
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    today   = datetime.datetime.now()
    the_sunday = current_weekday( datetime.date(today.year, today.month, today.day) , 6)
    #print ("is_ajax=" + str(is_ajax))
    if is_ajax and request.method == "POST":    
    # with app.test_request_context():
 
        listid = request.POST.get('grouplist',None)
        contactid = request.POST.get('contactid',None)
        contactname = request.POST.get('contactname',None)
        worshipdate = request.POST.get('worshipdate',None)
        worshipsession= request.POST.get('worshipsession',None)
        spiritual_times_str= request.POST.get('spiritual_times',None)
        worship_group_date= request.POST.get('groupworship',None)
        user_id= request.POST.get('user_id',None)
        description= request.POST.get('prayforme',None)
        prayid= request.POST.get('prayforme_id',None)
        tdate = request.POST.get('prayforme_tdate',None)

        spiritual_times=int(spiritual_times_str)
        psconn=getConnection()
        with psconn.cursor() as pycursor:
           app.logger.info("grouplist=" +  contactid+" "+contactname+" " +listid+" "+worshipdate+ " "+worshipsession+" "+ spiritual_times_str+" gt="+worship_group_date +" "+ user_id +" prayid="+ prayid+" tdate="+tdate+" "+  description)
           pycursor.execute("""select  sid,session  from worship  where contactid=%s and worship_date=%s and del_flag='N' """ ,[  contactid , worshipdate ])
           worshipdate_rows = pycursor.fetchone()
           if worshipdate_rows:
              if worshipsession=="":
                  pycursor.execute("""update worship  set del_flag='Y' ,upd_no=%s,upd_date=%s  where sid=%s """ ,[  contactid , datetime.datetime.now() , worshipdate_rows[0] ])
              else:
                pycursor.execute("""update worship  set session=%s  ,upd_no=%s,upd_date=%s where sid=%s  """ ,[  worshipsession,  contactid , datetime.datetime.now() , worshipdate_rows[0] ])
           else:
              pycursor.execute("""insert into worship ( contactid,user_id,worship_date,session,crt_no,crt_date,del_flag) values (%s ,%s,%s,%s,%s,%s,'N') """ ,
                                        [ contactid ,  user_id , worshipdate ,   worshipsession  , contactid , datetime.datetime.now() ])

           pycursor.execute("""select sid,contactid,user_id,worship_date,worship_times from personalworship where contactid=%s and worship_date=%s   and del_flag='N' """ ,
                    [ contactid , worshipdate  ])
           personalworship_row = pycursor.fetchone()
           if personalworship_row:
              pycursor.execute("""update personalworship set  worship_times=%s , del_flag='N' ,upd_date=%s, upd_no=%s  where sid=%s """ ,
                                [ spiritual_times,    datetime.datetime.now(),contactid  ,personalworship_row[0]  ])
           else:
              pycursor.execute("""insert into  personalworship (worship_date,contactid,user_id,worship_times,del_flag, crt_no,crt_date ) values (%s,%s,%s,%s,'N',%s,%s) """ ,
                                [ worshipdate ,contactid, user_id   ,spiritual_times , contactid , datetime.datetime.now()  ])
        
#           app.logger.info(worship_group_date+" "+ listid +" "+ contactid )
           if worship_group_date!="":
             pycursor.execute(""" select * from groupship where week_date=%s and listid=%s and contactid=%s and  del_flag='N' """,[ worshipdate, listid , contactid   ] )
             groupship_row =pycursor.fetchone()
             if groupship_row==None:
                pycursor.execute("""insert into groupship (  contactid, listid, worship_date, crt_no, crt_date, del_flag,week_date) values (%s ,%s,%s,%s,%s,'N',%s) """ ,
                    [ contactid,  listid  , worship_group_date , contactid  , datetime.datetime.now() , worshipdate ])
             else:
                pycursor.execute(""" update groupship  set   del_flag='Y' where week_date=%s and listid=%s and contactid=%s and  worship_date<>%s """,[ worshipdate, listid , contactid,worship_group_date   ] )

           if tdate!="":
              pycursor.execute("""select sid,prayid,tdate,contactid,description  from prayforme where contactid=%s and prayid=%s and del_flag='N'  """ ,  [ contactid ,prayid ])
              row = pycursor.fetchone()
              if row:
                 pycursor.execute(""" update prayforme set description=%s,upd_no=%s, upd_date=%s where sid=%s """ , [description, contactid,datetime.datetime.now() ,str(row[0]) ])

                 result="代禱內容存檔成功"
            #else:                
              #  pycursor.execute("""insert into id2contact (groupId, user_id,displayname,contactid) values (%s,%s,%s,%s) """ ,[ "", userid ,  "" ,    member.contactid ]) 
               # profile= getLineProfile( userid )
               # if profile:                        
               #     pycursor.execute("""update id2contact set displayname=%s where user_id =%s """ ,[  profile.display_name ,userid ])

#                today   = datetime.datetime.now()
#
#                n=1
                #pycursor.execute(""" select max(prayid) as sid from prayforme where contactid=%s """, [ contactid  ])
                #row = pycursor.fetchone() 
                #if row:                    
                #    if row[0]!=None:
                #        strnum=row[0]
                #        n=int(strnum)+1
                #prayid=f'{n:04}'
                #pycursor.execute("""select prayid,tdate,contactid,description  from prayforme where contactid=%s  and del_flag='N' and isediting is null """ ,   [ contactid  ])
                #row = pycursor.fetchone()                     
                #if row==None:                                           
                #    pycursor.execute("""insert into prayforme( prayid,tdate,contactid,description,isediting,isclose,del_flag,crt_no,crt_date,upd_no,upd_date,week_date)
                #       values (%s,%s,%s,%s,'Y','','N',%s,%s,%s,%s  )""" ,
                #    [ prayid , today.strftime("%Y-%m-%d") , contactid, description , contactid  ,   datetime.datetime.now() ,contactid  ,   datetime.datetime.now(), worshipdate ])

                #result="代禱內容新增成功"
           else:
              n=1

              pycursor.execute(""" select max(prayid) as sid from prayforme where contactid=%s """, [ contactid  ])
              row = pycursor.fetchone() 
              if row:                    
                if row[0]!=None:
                    strnum=row[0]
                    n=int(strnum)+1
              prayid=f'{n:04}'
              pycursor.execute(""" select max(tdate)  from prayforme where contactid=%s  and week_date=%s and del_flag='N'   """, [ contactid , worshipdate  ])
              pray_tdate= datetime.datetime.strptime( worshipdate,"%Y-%m-%d")
              row = pycursor.fetchone()                     
              if row:
                if(row[0]!=None):
                    pray_tdate=row[0]

              pycursor.execute(""" insert into  prayforme 
                            ( prayid, tdate, contactid, description, isediting, isclose, del_flag, crt_no, crt_date, upd_no, upd_date, week_date)
                            values  
                            (%s,%s,%s,%s,%s,%s,'N',%s,%s,%s,%s,%s ) """ , [prayid, pray_tdate,contactid, description,'N','N', contactid,datetime.datetime.now() , contactid,datetime.datetime.now()  ,worshipdate ])

           result="回報完成" 

           worship=[]
           worshipgroup=[]
           prayforme=[]
           listid=""
           listname=""
           pycursor.execute("""select distinct worship_date   from worshipdate where worship_date<=%s order by worship_date desc limit 4""" ,[ the_sunday  ])
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
           member= get_contactbase( user_id ,psconn )
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
                       #print( groupworship_row[2] )
                       wdate["groupworship"]["worshipdate"]= groupworship_row[2]
                       wdate["groupworship"]["listid"]= groupworship_row[1]

                       pycursor.execute("""select  listname from listbase  where  listid =%s   """ ,[ listid ])
                       listbase_row = pycursor.fetchone() 
                       if listbase_row:
                           wdate["groupworship"]["listname"]= listbase_row[0]
                   #print(wdate["worshipdate"]   ) 
                   #print(next_sunday  )
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

 
    
    return JsonResponse( {"result": {"error": result  } } , status=200)    
