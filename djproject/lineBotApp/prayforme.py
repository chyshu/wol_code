from calendar import SUNDAY
from cgitb import text
import json
import logging
from time import strftime,time
from flask import Flask
import datetime
from .classes import Member,Family
from .utils import next_weekday, getConnection, get_contactbase,get_contactbaseByContactName,getLineProfile,get_contactbaseByContactId,current_weekday,GroupOwner
from django.shortcuts import render
from urllib.parse import urlsplit, parse_qs,parse_qsl
from django.http import JsonResponse
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt,csrf_protect

from linebot.models import FlexSendMessage, BubbleContainer, ImageComponent
from linebot import LineBotApi, WebhookParser,WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage,JoinEvent,UnfollowEvent,FollowEvent,LeaveEvent,PostbackEvent,BeaconEvent,MemberJoinedEvent,MemberLeftEvent,AccountLinkEvent,ThingsEvent,ThingsEvent,SourceUser,SourceGroup,SourceRoom
from linebot.models import TemplateSendMessage, ButtonsTemplate, DatetimePickerTemplateAction,QuickReply,QuickReplyButton, MessageAction
import  psycopg2

app = Flask(__name__) 

def getPrayforMeMenu(contactid,displayname,psconn):

    #psconn =  getConnection()
    pycursor = psconn.cursor()
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    today   = datetime.datetime.now()
    msgcontents=  {                    
                "type": "bubble",
                "size":  "giga",
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text": "代禱",
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
                            "contents":[{
                                "type": "text",
                                "text":("" if (displayname==None) else displayname)+",請選要執行的功能",
                                "size":"md",
                                "weight":"bold",
                                "color":"#0099ff",
                                "wrap": True
                                },
                                                                                
                            ]
                        }, 
                        {
                            "type": "button",
                            "margin":"xs",
                            "style":"primary",
                            "color": "#B25068",
                            "action": {
                                "type": "postback",
                                "label":"新增代禱",
                                "data":"action=createPray"
                            }
                        },
                        {
                            "type": "button",
                            "margin":"xs",
                            "style":"primary",
                            "color": "#0E918C",
                            "action": {
                                "type": "postback",
                                "label":"我的代禱事項",
                                "data":"action=Praylist"
                            }
                        },
                        #{
                        #    "type": "button",
                        #    "margin":"xs",
                        #    "style":"primary",
                        #    "color": "#774360",
                        #    "action": {
                        #        "type": "postback",
                        #        "label":"完成代禱",
                        #        "data":"action=PrayEOD"
                        #    }
                        #},
                    ]
                },
                "footer":{
                    "type": "box",
                    "layout": "vertical",
                     "paddingAll":"xl",
                    "contents": [
                    ],

                }
            }



    msgcontents["footer"]["contents"].append(
        {
            "type": "button",            
            "style":"primary",
            "color": "#FF8000",
            "action": {
                "type": "postback",
                "label":"回上層",
                "data":"action=cherub"
            }
        }
    )
    pycursor.close()
    return msgcontents

def getPrayforMeListMenu(contactid,displayname,psconn):
    
    #psconn =  getConnection()
    with psconn.cursor() as pycursor:
      pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
      today   = datetime.datetime.now()
      msgcontents={
        "type": "carousel",  
        "contents": [
            {
                "type": "bubble",
                "size":  "giga",
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text": "我的代禱事項",
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
                            "contents":[{
                                "type": "text",
                                "text":("" if (displayname==None) else displayname)+"請選代禱事項",
                                "size":"md",
                                "weight":"bold",
                                "color":"#0099ff",
                                "wrap": True
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

      pycursor.execute("""select prayid,tdate,contactid,description,sid  from prayforme where contactid=%s  and del_flag='N'  and isclose=''  order by prayid   """ ,
                    [ contactid  ])
      prayforme_rows = pycursor.fetchall()
      for prayforme in prayforme_rows:
            msgcontents["contents"][0]["body"]["contents"].append(
                {
                    "type": "button",
                    "margin":"xs",
                    "style":"primary",
                    "color": "#A64B2A",
                    "action": {
                        "type": "postback",
                        "label":prayforme[1].strftime("%m-%d")+" "+( "" if prayforme[3]==None else prayforme[3][0:10]) ,
                        "data":"action=prayitem&prayid="+ str(prayforme[4])
                    }
                }
            )
      app.logger.info( msgcontents["contents"][0]["body"]["contents"] )
      msgcontents["contents"][0]["footer"]["contents"].append(
        {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color": "#FF8000",
            "action": {
                "type": "postback",
                "label":"回上層",
                "data":"action=praymenu"
            }
        }
      )
  

    return msgcontents

def getPrayforMeByNo(contactid,displayname,prayid,psconn):

    #psconn =  getConnection()
    pycursor = psconn.cursor()
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    today   = datetime.datetime.now()
    
    msgcontents={
        "type": "carousel",  
        "contents": [
            {
                "type": "bubble",
                "size":  "giga",
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text": "代禱項目"+prayid +"",
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
                        "type": "text",
                        "text":"建立日期：",
                        "margin":"xs",
                        "size":"md",
                        "weight":"bold",
                        "color":"#0099ff",
                        "wrap": True
                        },
                        {
                        "type": "text",
                        "text":"代禱內容",
                        "size":"md",
                        "weight":"bold",
                        "color":"#0099ff",
                        "wrap": True
                        },
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "paddingAll":"xl",
                    "contents": []
                },
            }
        ]
    }
    pycursor.execute("""select prayid,tdate,contactid,description  from prayforme where contactid=%s  and del_flag='N'  and sid=%s  """ ,
                    [ contactid ,prayid ])
    prayformerow = pycursor.fetchone()
    if prayformerow:
        pid =str(prayformerow[0])
        msgcontents["contents"][0]['header']['contents'][0]['text']= "代禱項目: "+pid 
        tdate = prayformerow[1].strftime("%Y-%m-%d") 
        msgcontents["contents"][0]["body"]["contents"][0]["text"]="建立日期："+tdate

        desciption="--- 還沒寫代禱內容 ---"
        if prayformerow[3]!=None:
            desciption=str(prayformerow[3])

        msgcontents["contents"][0]["body"]["contents"].append(
            {
                
                   "type": "text",
                   "size":"md",
                   "weight":"bold",
                   "text": desciption, 
                   "color":"#000000",
                   "wrap": True                           
            }
        )

    msgcontents["contents"][0]["footer"]["contents"].append(
        {
            "type": "box",
            "layout": "vertical",
            "contents":[{
                "type": "button",
                "margin":"xs",
                "style":"primary",
               "color": "#5E454B",
               "action": {
                   "type": "uri",
                   "label":"編輯代禱內容",
                   #"data":"action=PrayEdit&prayid="+prayid
                   "uri": settings.SERVER_URL+"PrayEdit?sid="+prayid+"&contactid="+contactid
               }
           }]
       }
    )
    msgcontents["contents"][0]["footer"]["contents"].append(
        {
            "type": "button",
           "margin":"xs",
            "style":"primary",
            "color": "#243D25",
            "action": {
                "type": "postback",
                "label":"結案",
                "data":"action=PrayEOD&prayid="+prayid
           }
        }
    )    
    msgcontents["contents"][0]["footer"]["contents"].append(
        {
            "type": "box",
            "layout": "vertical",
            "contents":[{
                "type": "button",
                "margin":"xs",
                "style":"primary",
                "color": "#FF8000",
                "action": {
                    "type": "postback",
                    "label":"回上層",
                    "data":"action=Praylist"
                }
            }]
        }
    )
    pycursor.close()
    return msgcontents

@csrf_protect
def PrayEdit(request):
    app = Flask(__name__)    
    result=""
    with app.test_request_context(): 
        contactid = request.GET.get('contactid',None)
        strsid = request.GET.get('sid',None)
        app.logger.debug(contactid)
    contactid = request.GET.get('contactid',None)
    prayid = request.GET.get('prayid',None)
    psconn=getConnection()
    member=get_contactbaseByContactId( contactid,psconn)
    contactName=""
    description=""
    if(member!=None):
        contactName=member.contactname
        request.session["userid"] =member.user_id
        #print(member.user_id)
        sid = int(strsid) if strsid!='' else 0
        #psconn =  getConnection()
        with  psconn.cursor() as pycursor:
          pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")        
          pycursor.execute("""select sid,prayid,tdate,contactid,description  from prayforme where contactid=%s and sid=%s and del_flag='N'  """ ,  [ member.contactid , sid ])
          row = pycursor.fetchone() 
          if row:
             description=str(row[4])
         
    psconn.close()
    return render(request, "prayedit.html",{"contactname":contactName ,"description":description   ,"sid":strsid  })

@csrf_protect
def PostPray(request):
    result=""	
    member  = Member(None,None,None,None,None,None)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax and request.method == "POST":
        description = request.POST.get('prayforme',None)
        strsid = request.POST.get('sid',None)
        # print( contactname)
        userid=request.session["userid"] 
        #print(userid)
        psconn=getConnection()       
        member= get_contactbase(userid,psconn)
        if member.contactid!=None:
#            psconn =  getConnection()
          with  psconn.cursor() as pycursor:
            pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
            sid=0
            sid = ( int(strsid) if strsid!='' else  0)
            pycursor.execute("""select sid,prayid,tdate,contactid,description  from prayforme where contactid=%s and sid=%s and del_flag='N'  """ ,  [ member.contactid ,sid ])
            row = pycursor.fetchone()
            if row:
                pycursor.execute(""" update prayforme set description=%s,upd_no=%s, upd_date=%s where sid=%s """ , [description, member.contactid,datetime.datetime.now() ,str(row[0]) ])

                result="代禱內容存檔成功"
            else:                
              #  pycursor.execute("""insert into id2contact (groupId, user_id,displayname,contactid) values (%s,%s,%s,%s) """ ,[ "", userid ,  "" ,    member.contactid ]) 
               # profile= getLineProfile( userid )
               # if profile:                        
               #     pycursor.execute("""update id2contact set displayname=%s where user_id =%s """ ,[  profile.display_name ,userid ])

                today   = datetime.datetime.now()

                n=1
                pycursor.execute(""" select max(prayid) as sid from prayforme where contactid=%s """, [ member.contactid  ])
                row = pycursor.fetchone() 
                if row:                    
                    if row[0]!=None:
                        strnum=row[0]
                        n=int(strnum)+1
                prayid=f'{n:04}'
                pycursor.execute("""select prayid,tdate,contactid,description  from prayforme where contactid=%s  and del_flag='N' and isediting is null """ ,   [ member.contactid  ])
                row = pycursor.fetchone()                     
                if row==None:                                           
                    pycursor.execute("""insert into prayforme( prayid,tdate,contactid,description,isediting,isclose,del_flag,crt_no,crt_date,upd_no,upd_date)
                       values (%s,%s,%s,%s,'Y','','N',%s,%s,%s,%s  )""" ,
                    [ prayid , today.strftime("%Y-%m-%d") , member.contactid, description , member.contactid  ,   datetime.datetime.now() ,member.contactid  ,   datetime.datetime.now() ])

                result="代禱內容新增成功"
            pycursor.close()
        else:
            result="找不到使用者的資料"
            
        return JsonResponse({ "result": { "familymember":   json.dumps(member.__dict__) , "error":result}  }, status=200)
    return JsonResponse( {"result": {"error": "UNKNOWN SOURCE" , "member" : json.dumps(member.__dict__) } } , status=200)   


def getPrayItemByOwner(ownerid,prayid,psconn):
#    psconn =  getConnection()
  with  psconn.cursor() as pycursor:
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
 
    today   = datetime.datetime.now()
   #groupdata = GroupOwner(ownerid )
   # lists=""
   # comma=""
   # for group in groupdata:
   #     print(group.listid+","+group.listname+","+group.role)
        #if (group.role!="member"):
    
    pycursor.execute(""" select prayforme.tdate,prayforme.contactid,contactbase.lastname,
                                prayforme.sid,prayforme.description ,prayforme.isclose, prayforme.upd_date,prayforme.crt_date
                        from prayforme                        
                        left outer join contactbase on prayforme.contactid=contactbase.contactid
                        where  prayforme.sid=%s  """ ,
                    [ prayid ])
    columns = []

    for col in pycursor.description:
           columns.append(col[0])                    
    msgcontents={
                "type": "bubble",
                "size":  "mega",
                "header":
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text": "代禱事項",
                        "size":"xl",
                        "weight":"bold",
                        "color":"#1a5276FF",
                    }],
                    "backgroundColor": "#f1c40fF0",
                },
                "body": 
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": []
                },
                "footer":
                {
                    "type": "box",
                    "layout": "vertical",
                    "paddingAll":"xl",
                    "contents": [
                         {
                                "type": "button",
                                "margin":"xs",
                                "style":"primary",
                                "color": "#FF8000",
                                "action": {
                                    "type": "postback",
                                    "label":"回上層",
                                    "data":"action=getPrayListByOwner&cid="+ownerid
                                }
                        }
                    ]
                }
            }
    prayforme = pycursor.fetchone()
    if prayforme!=None:
        upd_date=" "
        if prayforme[columns.index("upd_date") ]:
            upd_date=prayforme[columns.index("upd_date") ].strftime("%Y-%m-%d, %H:%M:%S")
        lname=" "
        if prayforme[columns.index("lastname")  ]:
            lname=(prayforme[columns.index("lastname")  ])
        msgcontents["body"]["contents"].append(
            {
                "type": "box",
                "layout": "vertical",                
                "contents": [
                    {
                    "type": "text",
                    "text":  upd_date,
                    "size":"md",
                    "weight":"bold",
                    "color":"#1a5276FF",  
                    },
                     {
                    "type": "text",
                    "text":lname ,
                    "size":"md",
                    "weight":"bold",
                    "color":"#1a5276FF",  
                    },
                    {
                    "type": "text",
                    "text":"代禱內容",
                    "size":"md",
                    "weight":"bold",
                    "color":"#1a5276FF",  
                    },
                    {
                        "type": "box",
                        "layout": "vertical",                         
                        "margin"   : "md",    
                        "borderColor":"#154360",
                        "borderWidth":"normal",   
                        "height":"400px",
                        "paddingAll": "8px",
                        "contents": [
                            {
                            "type": "text",
                            "text": "___(未編輯)___" if prayforme[columns.index("description") ]==None else prayforme[ columns.index("description")]  ,
                            "size":"lg",
                            "spacing": "20px",   
                            "weight":"bold",
                            "wrap": True,
                            "color":"#1a5276FF",  
                            "margin"   : "md"
                            }]
                    }
                ]
            }
        )
    else:
        msgcontents["body"]["contents"].append(
            {
                "type": "box",
                "layout": "vertical",                
                "contents": [
                    {
                    "type": "text",
                    "text":  " ",
                    "size":"md",
                    "weight":"bold",
                    "color":"#1a5276FF",  
                    },
                     {
                    "type": "text",
                    "text": " " ,
                    "size":"md",
                    "weight":"bold",
                    "color":"#1a5276FF",  
                    },
                    {
                    "type": "text",
                    "text":"代禱內容",
                    "size":"md",
                    "weight":"bold",
                    "color":"#1a5276FF",  
                    },
                    {
                        "type": "box",
                        "layout": "vertical",                         
                        "margin"   : "md",    
                        "borderColor":"#154360",
                        "borderWidth":"normal",   
                        "height":"400px",
                        "paddingAll": "8px",
                        "contents": [
                            {
                            "type": "text",
                            "text": "___(未編輯)___" ,
                            "size":"lg",
                            "spacing": "20px",   
                            "weight":"bold",
                            "wrap": True,
                            "color":"#1a5276FF",  
                            "margin"   : "md"
                            }]
                    }
                ]
            }
        )
#    print ( msgcontents["body"]["contents"])
    pycursor.close()
    return msgcontents


def getPrayWeekByOwner(ownerid,sender=None,psconn=None):  
    goBackAction="action=ninjia&page=3"
    if sender!=None:
        goBackAction="action=getPrayListByOwner&cid="+ownerid  
    msgcontents={
        "type": "carousel",  
        "contents": [
            {
                "type": "bubble",
                "size":  "giga",
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text": "代禱事項",
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
    weeklist = []
#    psconn =  getConnection()
    with  psconn.cursor() as pycursor:
      today   = datetime.datetime.now()  
      next_sunday = current_weekday( datetime.date(today.year, today.month, today.day) , 6)
      pycursor.execute("""select distinct worship_date   from worshipdate where worship_date<=%s order by worship_date desc limit 8""" ,[ next_sunday.strftime('%Y-%m-%d') ])
      worship_date_rows = pycursor.fetchall()
      for row in worship_date_rows:
        #weeklist.append(   row[0].strftime('%Y-%m-%d') )
        msgcontents["contents"][0]["body"]["contents"].append(
        {
            "type": "button",
            "margin":"xs",
            "style": "primary" ,
            "color":"#BABD42",
            "action": {
                "type": "postback",
                "label": row[0].strftime('%Y-%m-%d'),
                "data": "action=getPrayListByOwner&worshipdate="+ row[0].strftime('%Y-%m-%d')+"&ownerid="+ownerid+"&subject=praylist",
            }
        })    
      msgcontents["contents"][0]["footer"]["contents"].append(
            {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color": "#FF8000",
            "action": {
                "type": "postback",
                "label":"回上層",
                "data":goBackAction
            }
        }
      )
    
    return msgcontents

def getPrayListByOwner(ownerid,sender=None,tdate=None,psconn=None):  

    goBackAction="action=getPrayListByOwner&cid="+ownerid
    if sender!=None:
        goBackAction="action=ninjia&page=3"

#    psconn =  getConnection()
    pycursor = psconn.cursor()
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    today   = datetime.datetime.now()
    if tdate!=None:
        today   =  datetime.datetime. strptime(tdate,'%Y-%m-%d')
    weekend = next_weekday(today,6)
    
  
    msgcontents={
        "type": "carousel",  
        "contents": [
            {
                "type": "bubble",
                "size":  "giga",
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text": "代禱事項",
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

    pycursor.execute("""  select prayforme.contactid, prayforme.tdate, prayforme.sid,prayforme.description ,prayforme.isclose, prayforme.upd_date,prayforme.crt_date ,contactbase.lastname
                     from prayforme
                     left outer join contactbase on contactbase.contactid=prayforme.contactid
                     where   prayforme.sid is not null  and tdate between %s and %s     order by prayforme.tdate  """ ,[today,weekend] )

    columns = []

    for col in pycursor.description:
        columns.append(col[0])       

    prayforme_rows = pycursor.fetchall()   
    
    
    for prayforme in prayforme_rows:
            pycursor.execute("""  select listbase.list_leader,listbase.chief,listbase.assistant,listbase.family_leader,listmemberbase.entityid
                       from listmemberbase 
                       left outer join listbase on listbase.listid=listmemberbase.listid and listbase.purpose ='小組名單' and listbase.inuse='1'
                       where listmemberbase.entityid=%s and (  listbase.list_leader=%s or listbase.chief=%s or listbase.assistant =%s or listbase.family_leader=%s ) """,
                       [prayforme[0],ownerid,ownerid,ownerid,ownerid ] )
            listmemberbase = pycursor.fetchone()
            if listmemberbase:
                 msgcontents["contents"][0]["body"]["contents"].append(
                    {
                        "type": "button",
                        "margin":"xs",
                        "style":"primary",
                        "color": "#A64B2A",
                        "action": {
                            "type": "postback",
                            "label":prayforme[ columns.index("lastname")  ] +" "+( "" if prayforme[columns.index("description") ]==None else prayforme[columns.index("description")][0:10]) ,
                            "data":"action=getPrayItemByOwner&prayid="+ str(prayforme[ columns.index("sid") ]) +"&cid="+ownerid
                        }
                    }
                )
    if( len(msgcontents["contents"][0]["body"]["contents"])==0 ):
        msgcontents["contents"][0]["body"]["contents"].append(
            {
                  "type": "text",
                        "text": "沒有代禱事項",
                        "size":"xl",
                        "weight":"bold",
                        "color":"#1a5276FF",
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
                "data":goBackAction
            }
        }
    )
    pycursor.close()
    return msgcontents
