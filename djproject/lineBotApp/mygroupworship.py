from calendar import SUNDAY
from cgitb import text
import json
import logging
from pickle import NONE
from time import strftime,time
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

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)

parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

#psconn =  getConnection()
#pycursor = psconn.cursor()
#pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")


@csrf_protect
def index(requet):
    today   = datetime.datetime.now()  
        #with app.test_request_context():
    # 
    #        userid = requet.GET.get('userid',None)
    #        app.logger.debug(userid)
    #    
    contactid = requet.GET.get('cid',None)
    listid = requet.GET.get('listid',None)
    psconn=getConnection()
    with psconn.cursor() as pycursor:   
      pycursor.execute("""select listbase.ListId,listbase.listName , group_place, group_time
                    from  listbase
                    where listbase.ListId=%s    """ ,[ listid   ])
      listbase_row = pycursor.fetchone()

      next_sunday = current_weekday( datetime.date(today.year, today.month, today.day) , 6)
    
      weeklist = []
      pycursor.execute("""select distinct worship_date   from worshipdate where worship_date<=%s order by worship_date desc limit 4""" ,[ next_sunday.strftime('%Y-%m-%d') ])
      worship_date_rows = pycursor.fetchall()
      for row in worship_date_rows:
        weeklist.append(   row[0].strftime('%Y-%m-%d') )

      pycursor.execute("""select  ContactBase.LastName,ContactBase.ContactId
                    from ListMemberBase inner  join listbase on listbase.ListId = ListMemberBase.ListId
                    inner join ContactBase on ContactBase.ContactId= ListMemberBase.EntityId
                    where purpose='小組名單' and listbase.ListId=%s  and disp_yn='Y' order by disp_order """ ,[  listid ])
 
      ListMember_rows = pycursor.fetchall()
      listMember=[]
      for member in ListMember_rows:
        allWeeks=[]
        for worship_date in worship_date_rows: 
            pycursor.execute(""" select worship_date,session from worshipdate where worship_date=%s """,[ worship_date[0]  ] )
            worshipdateRows= pycursor.fetchall()
            session=[]
            for wdate in worshipdateRows:
                pycursor.execute(""" select worship_date,session from worship where worship_date=%s and session=%s and contactid=%s and del_flag='N' """,[ wdate[0], wdate[1] ,  member[1]  ] )
                row =pycursor.fetchone()  
                if row!=None:  
                    session.append( {"session":wdate[1] ,"attended":"Y" })                    
                else:
                    session.append( { "session":wdate[1],"attended":"N" })                    
            allWeeks.append({"worship_date": worship_date[0].strftime('%Y-%m-%d')  ,"sessions": session })    
        listMember.append({"ContactId":member[1] , "lastname":member[0] ,"worshipdata":allWeeks  })
      #print(listMember)
    return render(requet, "mygroupworship.html",{ "weeklist":weeklist ,"listbase":listbase_row ,"listmember":listMember  ,"listid":listid ,"contactid":contactid,
     "safe_weeklist": json.dumps(weeklist,default=str) ,"safe_listmember": json.dumps(listMember,default=str)   })

@csrf_protect
def getMemberProfile(request):
    result=""
    listMember=[]
    weeklist = []
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax and request.method == "POST":
        data  = request.body.decode('utf-8')
        body = json.loads( data )
        contactid = body["contactid"]
        listid =  body["listid"]
        #print(listid)
        psconn=getConnection()
        with psconn.cursor() as pycursor:  
          pycursor.execute("""select listbase.ListId,listbase.listName , group_place, group_time
                    from  listbase
                    where listbase.ListId=%s    """ ,[ listid   ])
          listbase_row = pycursor.fetchone()
          today   = datetime.datetime.now()  
          the_sunday = current_weekday( datetime.date(today.year, today.month, today.day) , 6)
        
          pycursor.execute("""select distinct worship_date   from worshipdate where worship_date<=%s order by worship_date desc limit 4""" ,[ the_sunday.strftime('%Y-%m-%d') ])
          worship_date_rows = pycursor.fetchall()
          for row in worship_date_rows:
            weeklist.append(   row[0].strftime('%Y-%m-%d') )

          pycursor.execute("""select  ContactBase.LastName,ContactBase.ContactId
                        from ListMemberBase inner  join listbase on listbase.ListId = ListMemberBase.ListId
                        inner join ContactBase on ContactBase.ContactId= ListMemberBase.EntityId
                        where purpose='小組名單' and listbase.ListId=%s  and disp_yn='Y' order by disp_order """ ,[  listid ])
    
          ListMember_rows = pycursor.fetchall()
          for member in ListMember_rows:
            allWeeks=[]
            for worship_date in worship_date_rows: 
                pycursor.execute(""" select worship_date,session from worshipdate where worship_date=%s """,[ worship_date[0]  ] )
                worshipdateRows= pycursor.fetchall()
                session=[]
                for wdate in worshipdateRows:
                    pycursor.execute(""" select worship_date,session from worship where worship_date=%s and session=%s and contactid=%s and del_flag='N' """,[ wdate[0], wdate[1] ,  member[1]  ] )
                    row =pycursor.fetchone()  
                    if row!=None:  
                        session.append( {"session":wdate[1] ,"attended":"Y" })                    
                    else:
                        session.append( { "session":wdate[1],"attended":"N" })                    
                allWeeks.append({"worship_date": worship_date[0].strftime('%Y-%m-%d')  ,"sessions": session })    
            listMember.append({"ContactId":member[1] , "lastname":member[0] ,"worshipdata":allWeeks  })
          result=""
          return JsonResponse({ 
            "result": { 
            "weeklist":   json.dumps(weeklist,default=str) ,
            "listid":listid ,
            "contactid":contactid, 
            "listmember":  json.dumps(listMember,default=str),
  
            "error":result}  }, status=200)        
        psconn.close()
    return JsonResponse( 
        {"result": {"error": "UNKNOWN SOURCE" , 
        "weeklist" : json.dumps(weeklist,default=str)  ,
        "listmember":  json.dumps(listMember,default=str)  ,
        "listid":listid ,
        "contactid":contactid
   
      } } , status=200)    

def setMemberWorship(request):
    result={"message":"主機回應錯誤" ,"contactid":"" ,"user_id":"" ,"listid":"" ,"worshipdate":"","session":"","attended":"" }
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax and request.method == "POST":        
        data  = request.body.decode('utf-8')
        print(data)
        body = json.loads( data )
        result["contactid"] = body["contactid"]
        result["listid"] =  body["listid"]
        result["worshipdate"] =  body["worshipdate"]
        result["session"] =  body["session"]
        result["attended"] =  body["attended"]
        result["datakey"]  = body["datakey"]
        result["user_id"]=""
        psconn=getConnection()
        with   psconn.cursor() as pycursor:
           pycursor.execute("""select  contactid,new_lineid  from contactbase  where contactid=%s  """ ,[  result["datakey"] ])
           contactbase_row = pycursor.fetchone()
           if contactbase_row!=None:
              result["user_id"]=contactbase_row[1]
           if result["attended"]=="N":
              pycursor.execute("""select  sid,session  from worship  where contactid=%s and worship_date=%s and session=%s and del_flag='N' """ ,[  result["datakey"] ,result["worshipdate"], result["session"] ])
              worshipdate_row = pycursor.fetchone()
              if worshipdate_row==None:
                pycursor.execute("""insert into worship ( contactid,user_id,worship_date,session,crt_no,crt_date,del_flag) values (%s ,%s,%s,%s,%s,%s,'N') """ ,
                                  [ result["datakey"] ,  result["user_id"] , result["worshipdate"] ,   result["session"]  , result["contactid"] , datetime.datetime.now() ])
              result["message"]="回報完成" 
           elif result["attended"]=="Y":
              pycursor.execute("""select  sid,session  from worship  where contactid=%s and worship_date=%s and session=%s and del_flag='N' """ ,[  result["datakey"] ,result["worshipdate"], result["session"] ])
              worshipdate_row = pycursor.fetchone()
              if worshipdate_row:
                  pycursor.execute("""update worship  set del_flag='Y' ,upd_no=%s,upd_date=%s  where sid=%s """ ,[  result["contactid"] , datetime.datetime.now() , worshipdate_row[0] ])
              result["message"]="取消回報完成" 
        psconn.close()
    return JsonResponse( {"result":json.dumps(result, default=str ) },status=200 )
