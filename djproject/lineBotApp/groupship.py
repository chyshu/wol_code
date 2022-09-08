from calendar import SUNDAY
from hashlib import new
import json
import logging
from time import  strftime,time

#from .models import Greeting
from flask import Flask
import datetime
from .classes import GroupPresent, Member,Family,MyGroup, WeekPresent,GroupPresent
from .utils import next_weekday, getConnection,current_weekday,GroupOwner
from django.shortcuts import render
from urllib.parse import urlsplit, parse_qs,parse_qsl
# Create your views here.
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from linebot.models import FlexSendMessage, BubbleContainer, ImageComponent
from linebot import LineBotApi, WebhookParser,WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage,JoinEvent,UnfollowEvent,FollowEvent,LeaveEvent,PostbackEvent,BeaconEvent,MemberJoinedEvent,MemberLeftEvent,AccountLinkEvent,ThingsEvent,ThingsEvent,SourceUser,SourceGroup,SourceRoom
from linebot.models import TemplateSendMessage, ButtonsTemplate, DatetimePickerTemplateAction,QuickReply,QuickReplyButton, MessageAction
import  psycopg2

app = Flask(__name__) 

# 小組回報MENU
def getGroupListMenu(contactid, displayname,psconn):
#    psconn =  getConnection()    
    pycursor = psconn.cursor()
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    today   = datetime.datetime.now()
    msgcontents={
 
                "type": "bubble",
                "size":  "mega",
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text":  "小組回報",
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
                                "text": ("" if displayname==None else displayname)+",請選小組", 
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
    }
    pycursor.execute("""select listbase.ListId,listbase.listName , group_place, group_time
                    from ListMemberBase inner  join listbase on listbase.ListId = ListMemberBase.ListId 
                    where ListMemberBase.EntityId=%s   and purpose='小組名單' """ ,[ contactid   ])
    listbase_rows = pycursor.fetchall()
    for listbase in listbase_rows:
        btnlabel=listbase[1]+"(個人)"
        btndata ="action=selectgroup&listid="+listbase[0]+"&cid="+ contactid +"&sender=personal"
        btnstyle="primary"
        btncolor="#BABD42"
        msgcontents["body"]["contents"].append(
                {
                    "type": "button",
                    "margin":"xs",
                    "style":btnstyle,
                    "color":btncolor,
                    "action": {
                        "type": "postback",
                        "label":btnlabel,
                        "data":btndata,
                    }
                })  
        btnlabel=listbase[1]+"(群組)"
        btndata ="action=selectgroup&listid="+listbase[0]+"&cid="+ contactid +"&sender=group"
        btnstyle="primary"
        btncolor="#BABD42"
        msgcontents["body"]["contents"].append(
                {
                    "type": "button",
                    "margin":"xs",
                    "style":btnstyle,
                    "color":btncolor,
                    "action": {
                        "type": "postback",
                        "label":btnlabel,
                        "data":btndata,
                    }
                })  
    msgcontents["footer"]["contents"].append(
            {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color": "#FF8000",
            "action": {
                "type": "postback",
                "label":"回上層",
                "data":"action=Cherub" 
            }
        }
    )
    return msgcontents                

def getGroupListMenuV2(contactid, displayname,psconn):
#    psconn =  getConnection()
    pycursor = psconn.cursor()
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    today   = datetime.datetime.now()
    msgcontents={
 
                "type": "bubble",
                "size":  "mega",
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text":  "小組回報",
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
                                "text":("" if (displayname==None) else displayname)+",請選小組", 
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
    }
    pycursor.execute("""select listbase.ListId,listbase.listName , group_place, group_time
                    from ListMemberBase inner  join listbase on listbase.ListId = ListMemberBase.ListId 
                    where ListMemberBase.EntityId=%s   and purpose='小組名單' """ ,[ contactid   ])
    listbase_rows = pycursor.fetchall()
    for listbase in listbase_rows:
        btnlabel=listbase[1]+"(個人)"
        btndata ="action=selectgroup&listid="+listbase[0]+"&cid="+ contactid +"&sender=personal"
        btnstyle="primary"
        btncolor="#BABD42"
        msgcontents["body"]["contents"].append(
                {
                    "type": "button",
                    "margin":"xs",
                    "style":btnstyle,
                    "color":btncolor,
                    "action": {
                        "type": "postback",
                        "label":btnlabel,
                        "data":btndata,
                    }
                })  
        btnlabel=listbase[1]+"(群組)"
        btndata ="action=selectgroup&listid="+listbase[0]+"&cid="+ contactid +"&sender=group"
        btnstyle="primary"
        btncolor="#BABD42"
        msgcontents["body"]["contents"].append(
                {
                    "type": "button",
                    "margin":"xs",
                    "style":btnstyle,
                    "color":btncolor,
                    "action": {
                        "type": "postback",
                        "label":btnlabel,
                        "data":btndata,
                    }
                })  
    

    groupdata = GroupOwner(contactid)    
    appendItems=[]
    for group in groupdata:
        #print(group.listid+","+group.listname+","+group.role)
        #if (group.role!="member"):
        btnlabel=group.listname
        btndata ="action=getGroupMemberList&listid="+group.listid+"&cid="+ contactid 
        btnstyle="primary"
        btncolor="#4277bd"
        appendItems.append(
            {
                "type": "button",
                "margin":"xs",
                "style":btnstyle,
                "color":btncolor,
                "action": {
                    "type": "postback",
                    "label":btnlabel,
                    "data":btndata,
                }
            })  
    if  len(appendItems)>0:
        msgcontents["body"]["contents"].append(
             {"type": "box",
                "layout": "vertical",
                "contents":[{
                    "type": "text",
                    "text":"小組名單", 
                    "size":"md",
                    "weight":"bold",
                    "color":"#0099ff",
                    "wrap": True
                    },
                ]
            })
        for btns in appendItems:
            msgcontents[ "body"]["contents"].append(btns)

    appendItems=[]
    for group in groupdata:
        #print(group.listid+","+group.listname+","+group.role)
        #if (group.role!="member"):
        btnlabel=group.listname
        btndata ="action=getGroupMemberListforMove&listid="+group.listid+"&cid="+ contactid 
        btnstyle="primary"
        btncolor="#4277bd"
        appendItems.append(
            {
                "type": "button",
                "margin":"xs",
                "style":btnstyle,
                "color":btncolor,
                "action": {
                    "type": "postback",
                    "label":btnlabel,
                    "data":btndata,
                }
            })  
    if  len(appendItems)>0:            

        msgcontents["body"]["contents"].append(
             {"type": "box",
                "layout": "vertical",
                "contents":[{
                    "type": "text",
                    "text":"小組名單顯示順序", 
                    "size":"md",
                    "weight":"bold",
                    "color":"#0099ff",
                    "wrap": True
                    },
                ]
            })
        for btns in appendItems:
            msgcontents[ "body"]["contents"].append(btns)
    
    appendItems=[]
    for group in groupdata:
        #print(group.listid+","+group.listname+","+group.role)
        #if (group.role!="member"):
        btnlabel=group.listname
        btndata ="action=worshipReport&listid="+group.listid+"&cid="+ contactid 
        btnstyle="primary"
        btncolor="#4277bd"
        appendItems.append(
            {
                "type": "button",
                "margin":"xs",
                "style":btnstyle,
                "color":btncolor,
                "action": {
                    "type": "postback",
                    "label":btnlabel,
                    "data":btndata,
                }
            })  
    if  len(appendItems)>0:
        msgcontents["body"]["contents"].append(
             {"type": "box",
                "layout": "vertical",
                "contents":[{
                    "type": "text",
                    "text":"主日出席狀況", 
                    "size":"md",
                    "weight":"bold",
                    "color":"#0099ff",
                    "wrap": True
                    },
                ]
            })
        for btns in appendItems:
            msgcontents["body"]["contents"].append(btns)  

    appendItems=[]
    for group in groupdata:
        #print(group.listid+","+group.listname+","+group.role)
        #if (group.role!="member"):
        btnlabel=group.listname
        btndata ="action=groupReport&listid="+group.listid+"&cid="+ contactid 
        btnstyle="primary"
        btncolor="#4277bd"
        appendItems.append(
            {
                "type": "button",
                "margin":"xs",
                "style":btnstyle,
                "color":btncolor,
                "action": {
                    "type": "postback",
                    "label":btnlabel,
                    "data":btndata,
                }
            })  
    if  len(appendItems)>0:
        msgcontents["body"]["contents"].append(
             {"type": "box",
                "layout": "vertical",
                "contents":[{
                    "type": "text",
                    "text":"小組出席狀況", 
                    "size":"md",
                    "weight":"bold",
                    "color":"#0099ff",
                    "wrap": True
                    },
                ]
            })
        for btns in appendItems:
            msgcontents["body"]["contents"].append(btns)

    appendItems=[]
    for group in groupdata:
        #print(group.listid+","+group.listname+","+group.role)
        #if (group.role!="member"):
        btnlabel=group.listname
        btndata ="action=personalWorshipReport&listid="+group.listid+"&cid="+ contactid 
        btnstyle="primary"
        btncolor="#4277bd"
        appendItems.append(
            {
                "type": "button",
                "margin":"xs",
                "style":btnstyle,
                "color":btncolor,
                "action": {
                    "type": "postback",
                    "label":btnlabel,
                    "data":btndata,
                }
            })  
    if  len(appendItems)>0:
        msgcontents["body"]["contents"].append(
             {"type": "box",
                "layout": "vertical",
                "contents":[{
                    "type": "text",
                    "text":"靈修狀況", 
                    "size":"md",
                    "weight":"bold",
                    "color":"#0099ff",
                    "wrap": True
                    },
                ]
            })
        for btns in appendItems:
            msgcontents["body"]["contents"].append(btns)             

    msgcontents["footer"]["contents"].append(
            {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color": "#FF8000",
            "action": {
                "type": "postback",
                "label":"回上層",
                "data":"action=Cherub" 
            }
        }
    )
    return msgcontents

def getGroupDateDialog(contactid, displayname,listid,sender,psconn):
#    psconn =  getConnection()
    pycursor = psconn.cursor()
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    today   = datetime.datetime.now()    
    pycursor.execute("""select listbase.ListId,listbase.listName , group_place, group_time
                                    from   listbase     where ListId=%s   """ ,[   listid  ])
    listName=""                
    row = pycursor.fetchone()    
    if row:
       listName=row[1]
                    
                    
    msgcontents={
 
                "type": "bubble",
                "size":  "mega",
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text":  listName+"聚會回報",
                        
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
                                "text":("" if (displayname==None) else displayname)+"請點選小組聚會日期", 
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
                            "color":"#BABD42",
                            "action": {
                                "type": "datetimepicker",
                                "label":"請點選小組聚會日期",
                                "mode" :"date",
                                "initial": today.strftime("%Y-%m-%d"),
                                "min": '2022-06-01',
                                "max": '2099-12-31',
                                "data":"action=selectgroupdate&cid="+contactid+"&listid="+listid+"&sender="+sender,
                            }     
                        }  
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
            "margin":"xs",
            "style":"primary",
            "color": "#FF8000",
            "action": {
                "type": "postback",
                "label":"回上層",
                "data":"action=groupshipMenu&cid="+contactid
            }
        }
    )

    return msgcontents

def getGroupDateList(contactid, displayname,listid,worship_date,sender,psconn):
 #   psconn =  getConnection()
    pycursor = psconn.cursor()
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    today   = datetime.datetime.now()   
    pycursor.execute("""select listbase.ListId,listbase.listName , group_place, group_time
                                    from   listbase     where ListId=%s   """ ,[  listid ])
    listName=""                
    row = pycursor.fetchone()    
    if row:
        listName=row[1]

    msgcontents={
  
          
                "type": "bubble",
                "size":  "mega",
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text":  listName+ datetime.datetime.strptime( worship_date , '%Y-%m-%d').strftime("%y%m%d")  +"聚會回報",
                        "wrap": True,
                        "size":"md",
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
                                "text": "請點選出席成員", 
                                "size":"md",
                                "weight":"bold",
                                "color":"#0099ff",
                                "wrap": True
                                },
                                                                                    
                            ]
                        }                                                
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
    pycursor.execute("""select listbase.ListId, listbase.listName  ,ContactBase.LastName,ContactBase.ContactId
                    from ListMemberBase inner  join listbase on listbase.ListId = ListMemberBase.ListId
                    inner join ContactBase on ContactBase.ContactId= ListMemberBase.EntityId
                    where purpose='小組名單' and listbase.ListId=%s  and disp_yn='Y' order by disp_order """ ,[  listid ])
    listName=""                
    ListMember_rows = pycursor.fetchall()
    for listmember in ListMember_rows:
        pycursor.execute(""" select * from groupship where worship_date=%s and listid=%s and contactid=%s and del_flag='N' """,[ worship_date , listid , listmember[3]  ] )
        row =pycursor.fetchone()
        btndata="action=setGroupDate"
        btnstyle ="primary" 
        btncolor="#BABD42"
        btnlabel=  listmember[2]  
        if row:                            
            btnstyle="secondary"                                            
            btnlabel=btnlabel+ "-出席"
            btndata="action=CancelGroupDate"
            btncolor="#ECA6A6"
        msgcontents["body"]["contents"].append(
                {
                    "type": "button",
                    "margin":"xs",
                    "style":btnstyle,
                    "color":btncolor,
                    "action": {
                        "type": "postback",
                        "label":btnlabel,
                        "data":btndata+"&listid="+listmember[0] + "&cid="+listmember[3] + "&opid="+ contactid +"&sender="+sender+"&worshipdate="+worship_date
                        
                    }
        })

 
    msgcontents["footer"]["contents"].append( 
        {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color": "#f1c40f",
            "action": {
                "type": "postback",
                "label":"更新名冊",

                "data":"action=selectgroupdate&listid="+listid+"&cid="+ contactid +"&sender="+sender+"&worshipdate="+worship_date
                
            }    
         })
    msgcontents[ "footer"]["contents"].append(
            {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color": "#FF8000",
            "action": {
                "type": "postback",
                "label":"回上層",
                "data":"action=selectgroup&listid="+listid+"&cid="+contactid+"&sender="+sender
            }
        }
    )

    return msgcontents

def getGroupDatePersonal(contactid, displayname,listid,worship_date,sender,psconn):
#    psconn =  getConnection()
    pycursor = psconn.cursor()
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    today   = datetime.datetime.now()   
    pycursor.execute("""select listbase.ListId,listbase.listName , group_place, group_time
                                    from   listbase     where ListId=%s   """ ,[  listid ])
    listName=""                
    row = pycursor.fetchone()    
    if row:
        listName=row[1]
    msgcontents={
 
                "type": "bubble",
                "size":  "mega",
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text":  listName+ datetime.datetime.strptime( worship_date , '%Y-%m-%d').strftime("%y%m%d")  +"聚會回報",
                        "wrap": True,
                        "size":"md",
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
 
    }
    pycursor.execute("""select listbase.ListId, listbase.listName  ,ContactBase.LastName,ContactBase.ContactId
                    from ListMemberBase inner  join listbase on listbase.ListId = ListMemberBase.ListId
                    inner join ContactBase on ContactBase.ContactId= ListMemberBase.EntityId
                    where purpose='小組名單' and listbase.ListId=%s  and  ContactBase.ContactId=%s  """ ,[  listid , contactid ])
    listName=""                
    ListMember_rows = pycursor.fetchall()
    for listmember in ListMember_rows:
        pycursor.execute(""" select * from groupship where worship_date=%s and listid=%s and contactid=%s and del_flag='N' """,[ worship_date , listid , listmember[3]  ] )
        row =pycursor.fetchone()
        btndata="action=setGroupDate"
        btnstyle ="primary" 
        btncolor="#BABD42"
        btnlabel=  listmember[2]  
        if row:                            
            btnstyle="secondary"                                            
            btnlabel=btnlabel+ "-出席"
            btndata="action=CancelGroupDate"
            btncolor="#ECA6A6"
        msgcontents["body"]["contents"].append(
                {
                    "type": "button",
                    "margin":"xs",
                    "style":btnstyle,
                    "color":btncolor,
                    "action": {
                        "type": "postback",
                        "label":btnlabel,
                        "data":btndata+"&worshipdate="+ worship_date +"&listid="+listmember[0] + "&cid="+listmember[3] + "&opid="+ contactid+"&sender="+sender,
                    }
                }
        )

    msgcontents["footer"]["contents"].append(
            {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color": "#FF8000",
            "action": {
                "type": "postback",
                "label":"回上層",
                "data":"action=selectgroup&listid="+listid+"&cid="+contactid+"&sender="+sender
            }
        }
    )
    return msgcontents

def getGroupReport(contactid,listid,sender=None,psconn=None):
  goBackAction="action=getManageGroup&subject=getGroupReport&cid="+contactid+"&listid="+listid
  if sender!=None:
      goBackAction="action=ninjia&page=3"
#    psconn =  getConnection()
  app.logger.info(goBackAction)
  with  psconn.cursor() as pycursor:
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    today   = datetime.datetime.now()   
    pycursor.execute("""select distinct worship_date   from worshipdate where worship_date<=%s order by worship_date desc limit 6""" ,[ today.strftime('%Y-%m-%d') ])
    worshipdate_rows = pycursor.fetchall()
    week=[]
    bdate=None
    edate=None
    page=0
    for  worshipdate in worshipdate_rows:
        page+=1
        edate= worshipdate[0]
        if bdate==None:
            bdate=worshipdate[0] 
        if (page %4)==0:        
            week.append( { "bdate":bdate,"edate": edate  } )
            bdate=None
    if(bdate!=None):
        week.append( { "bdate":bdate,"edate": edate  } )

   # print(week)
    
    contents=  {
       "type": "carousel",  
        "contents": []
    }
    i=0
    while (i<len( week)):
        pageContent =getGroupReportByDate(contactid,listid,week[i]["bdate"] ,goBackAction,psconn)
        contents["contents"].append(pageContent )
        i+=1

    return contents



def getGroupReportByDate(contactid,listid,thedate,goBackAction=None,psconn=None):    
   # psconn =  getConnection()
 with psconn.cursor() as pycursor:
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    
                
    week=[]
    # worshipdata   =  Worshipdata (None,None,None,None,None,None)
    the_sunday = current_weekday( datetime.date(thedate.year, thedate.month, thedate.day) , 6)
    
    pycursor.execute("""select distinct worship_date   from worshipdate where worship_date<=%s order by worship_date desc limit 4""" ,[ the_sunday.strftime('%Y-%m-%d') ])
    worshipdate_rows = pycursor.fetchall()
    for  worshipdate in worshipdate_rows:        
        nextsunday = next_weekday(  worshipdate[0] , 6)        
        week.append( { "bdate":worshipdate[0] ,"edate": nextsunday} )

    pycursor.execute("""select listbase.ListId,listbase.listName , group_place, group_time   from   listbase     where ListId=%s   """ ,[  listid ])
    listName=""                
    row = pycursor.fetchone()    
    if row:
        listName=row[1]
    msgcontents={
 
                "type": "bubble",
                "size":  "giga",
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text":  listName  +"出席狀況"+week[len(week)-1]["bdate"].strftime('%m-%d')+"~"+week[0]["bdate"].strftime('%m-%d'),
                        "wrap": True,
                        "size":"md",
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
 
    }


    report=[]
    #print(week)      
    pycursor.execute("""select listbase.ListId, listbase.listName  ,ContactBase.LastName,ContactBase.ContactId
                    from ListMemberBase inner  join listbase on listbase.ListId = ListMemberBase.ListId
                    inner join ContactBase on ContactBase.ContactId= ListMemberBase.EntityId
                    where purpose='小組名單' and listbase.ListId=%s  and  ListMemberBase.disp_yn='Y' order by  ListMemberBase.disp_order """ ,[  listid  ])
    listName=""                
    ListMember_rows = pycursor.fetchall()
    
    for listmember in ListMember_rows:
        # report.append({ "LastName": listmember[3],"ContactId":listmember[2] })
        wks =[]
        i=0
        while i<len(week):
            
            present =  WeekPresent(week[i]["bdate"], week[i]["edate"],"□" )
            #print(worship_date )            
            pycursor.execute(""" select * from groupship where listid=%s and contactid=%s and  worship_date>=%s and worship_date<%s and del_flag='N' """,[ listid , listmember[3],present.bdate,present.edate ] )
            row =pycursor.fetchone()
            if row!=None:
                present.present="■"
            wks.append( present  )
            i+=1
        report.append(  GroupPresent( listmember[3] ,listmember[2],wks  ))
    #print(report)
    msgcontents["body"]["contents"].append(
        {   "type": "box",
            "layout": "horizontal",
            "margin":"xs",              
            "contents":[{
                "type": "box",
                "layout": "horizontal",                  
                "width":"22%",
                "contents": [
                            {
                            "type": "text",
                            "text":  "姓名",
                            "size":"md",                        
                            "margin":"xs",                            
                            "color":"#1a5276FF"
                        } , {
                            "type": "separator",
                            "color": "#ff0000"
                        }]
            }]
        }
    )
    i=0
    while i<len(week):
        msgcontents["body"]["contents"][0]["contents"].append(
            {
                "type": "box",
                "layout": "horizontal",                
                "margin":"xs",      
                "width":"18%",
                "contents": [{
                    "type": "text",
                    "text":   week[i]["bdate"].strftime('%m-%d'),
                    "size":"sm",                     
                    "align":"center",
                    "color":"#1a5276FF"
                }, {
                    "type": "separator",
                    "color": "#ff0000"
                }
                ]
            })
        i+=1
    
    for grouppresent in report:
        
        msg={"type": "box",
             "layout": "horizontal",             
             "margin":"xs",
             "contents":[{
                "type": "box",
                "layout": "horizontal",                                  
                "width":"22%",
                "contents": [{
                    "type": "text",
                    "text":  grouppresent.contactname,
                    "size":"md",                    
                    "color":"#1a5276FF"
                    } , {
                    "type": "separator",
                    "color": "#ff0000"
                     } ]
            } ]
        }
        for wk in grouppresent.groupworship:  
            msg["contents"].append(
                {"type": "box",
                "margin":"xs", 
                 "layout": "horizontal",                
                 "width":"18%",
                 "contents": [{
                    "type": "text",
                    "text":  wk.present,
                    "size":"sm",                                             
                    "align":"center",
                    "color":"#1a5276FF"
                  }, {
                    "type": "separator",
                    "color": "#ff0000"
                  }]
                })
        
        
        msgcontents["body"]["contents"].append(msg)
   
    
    msgcontents["footer"]["contents"].append(
            {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color": "#FF8000",
            "action": {
                "type": "postback",
                "label":"回上層",
                "data":  goBackAction
            }
        }    
    )

    return msgcontents


def getGroupMemberList(contactid,listid,sender=None,psconn=None):
  # goBackAction="action=groupshipMenu&cid="+contactid
 goBackAction="action=ninjia&page=3"
 if sender!=None:
       goBackAction="action=groupshipMenu&cid="+contactid
 #app.logger.info("GroupMemberList "+goBackAction+" c= "+contactid+" l="+listid )
 #   psconn =  getConnection()
 with psconn.cursor() as pycursor:
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    today   = datetime.datetime.now()  
 #   app.logger.info("1111111111111111111111")
    pycursor.execute("""select listbase.ListId, listbase.listName  ,ContactBase.LastName,ContactBase.ContactId,ListMemberBase.disp_yn,ListMemberBase.disp_order,ListMemberBase.sid
                    from ListMemberBase 
                    inner  join listbase on listbase.ListId = ListMemberBase.ListId
                    inner join ContactBase on ContactBase.ContactId= ListMemberBase.EntityId
                    where purpose='小組名單' and listbase.ListId=%s  order by  ListMemberBase.disp_order """ ,[  listid  ])

    ListMember_rows = pycursor.fetchall()
#    app.logger.info(len(listMember_rows))
    disp_order=0
    for listmember in ListMember_rows:
        disp_order+=1
        pycursor.execute("""update  ListMemberBase set disp_order=%s where sid=%s    """ ,[ disp_order, listmember[6] ])
        #print ( listmember[6] )
    psconn.commit()
#    app.logger.info("Commit")
    pycursor.execute("""select listbase.ListId, listbase.listName  ,ContactBase.LastName,ContactBase.ContactId,ListMemberBase.disp_yn,ListMemberBase.disp_order,ListMemberBase.sid
                    from ListMemberBase 
                    inner  join listbase on listbase.ListId = ListMemberBase.ListId
                    inner join ContactBase on ContactBase.ContactId= ListMemberBase.EntityId
                    where purpose='小組名單' and listbase.ListId=%s  order by  ListMemberBase.disp_order """ ,[  listid  ])
 
    ListMember_rows = pycursor.fetchall()

    pycursor.execute("""select listbase.ListId,listbase.listName , group_place, group_time   from   listbase     where ListId=%s   """ ,[  listid ])
    listName=""
    row = pycursor.fetchone()    
    if row:
        listName=row[1]
#    app.logger.info(listName)
    msgcontents={
        
                "type": "bubble",
                "size":  "giga",
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text":  listName+"名單" ,
                        "wrap": True,
                        "size":"md",
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
    }
    msgcontents["body"]["contents"].append(
        {"type": "box",
            "margin":"xs",
            "layout": "horizontal",
            "contents":[{
                "type": "box",
                "layout": "horizontal",  
                "margin":"xs",              
                "width":"30%",
                "contents": [{
                    "type": "text",
                    "text": "姓名",
                    "size":"md",
                    "margin":"xs",
                    "gravity": "center",
                    "color":"#1a5276FF"
                    } ]
                },
                {
                "type": "box",
                "layout": "horizontal",  
                "margin":"xs",              
                "width":"30%",
                "contents": [{
                    "type": "text",
                    "text":  "狀態",
                    "size":"md",
                    "margin":"xs",
                    "gravity": "center",
                    "color":"#1a5276FF"
                    }]
                },
                    {
                "type": "box",
                "layout": "horizontal",
                "margin":"xs",
                "width":"35%",
                "contents": [{
                    "type": "text",
                    "text":  "功能",
                    "size":"md",
                    "margin":"xs",
                    "gravity": "center",
                    "color":"#1a5276FF"
                    }]
                }
            ]
        }    
    )
    disp_order=0
    for listmember in ListMember_rows:
        disp_order=listmember[5]
        btnlabel=listmember[2]       
        
        btncolor1="#138d75"
        btncolor2="#f1c40f"
        #if listmember[4]!="Y":
        #    btncolor="#D0D3D4"

        msg={"type": "box",
             "margin":"xs",
             "layout": "horizontal",
             "contents":
             [{
                "type": "box",
                "layout": "horizontal",  
                "margin":"xs",              
                "width":"30%",
                "contents": [{
                    "type": "text",
                    "text": btnlabel,
                    "size":"lg",
                    "margin":"xs",
                    "gravity": "center",
                    "color":"#1a5276FF"
                    } ]
                },
                {
                "type": "box",
                "layout": "horizontal",  
                "margin":"xs",              
                "width":"30%",
                "contents": [{
                    "type": "text",
                    "text":  ("☑" if listmember[4]=="Y" else "☐"),
                    "size":"lg",
                    "margin":"xs",
                    "gravity": "center",
                    "color":"#1a5276FF"
                    }]
                },
                {
                "type": "box",
                "layout": "horizontal",  
                "margin":"xs",              
                "width":"35%",
                "contents": [{
                            "type": "button",                            
                            "style":"primary", 
                            "color": (btncolor1  if listmember[4]=="Y" else btncolor2) ,
                            "height":"sm",
                            "size":"sm",
                            "action": {
                            "type": "postback",
                                "label": ("不顯示" if listmember[4]=="Y" else "顯示"),                            
                                "data": ("action=disp_no&listid="+listmember[0]+"&cid="+ listmember[3])  if listmember[4]=="Y" else ("action=disp_yes&listid="+listmember[0]+"&cid="+ listmember[3])  ,
                            }
                    }]
                }
             ]}
        msgcontents["body"]["contents"].append(msg)
     
       # msg["contents"].append({
       #     "type": "box",
       #     "layout": "horizontal",  
       #     "margin":"xs",
       #     "width":"20%",
       #     "contents": [{
       #                 "type": "button",
       #                 "margin":"xs",
       ##                 "style":"primary",
        #                "height":"sm",
        #                "color":btncolor,
        #                "size":"sm",
        #                "action": {
        #                "type": "postback",
        #                    "label": "上移",                            
        ##                    "data": "action=moveup&listid="+listmember[0]+"&cid="+ listmember[3] +"&disp_order="+ str(disp_order )
        #                }
         #       }]             
        #})
        #msg["contents"].append({
        #    "type": "box",
        #    "layout": "horizontal",  
        #   "margin":"xs",              
        #    "width":"20%",
        #    "contents": [{
        #                "type": "button",
        #                "margin":"xs",
        #                "style":"primary",
        #                "color":btncolor,
        #                "size":"sm",  
        #                "height":"sm",  
        #                "action": {
        #                "type": "postback",
        #                    "label": "下",                            
        #                    "data": "action=movedown&listid="+listmember[0]+"&cid="+ listmember[3] +"&disp_order="+ str(disp_order )
        #                }
        #        }]             
        #})
        
     
 
    msgcontents["footer"]["contents"].append( 
        {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color": "#f1c40f",
            "action": {
                "type": "postback",
                "label":"更新名冊",
                "data":"action=getGroupMemberList&listid="+listid+"&cid="+ contactid 
            }    
         })
    msgcontents["footer"]["contents"].append( {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color": "#FF8000",
            "action": {
                "type": "postback",
                "label":"回上層",
                "data":goBackAction 
            } } )
    
    

    return msgcontents 


def getGroupMemberListforMove(contactid,listid,sender=None,psconn=None):
    #if sender!=None:
  goBackAction="action=ninjia&page=3"
#  app.logger.info(goBackAction) 
#    psconn =  getConnection()
  with  psconn.cursor() as pycursor:
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    today   = datetime.datetime.now()
    pycursor.execute("""select listbase.ListId, listbase.listName  ,ContactBase.LastName,ContactBase.ContactId,ListMemberBase.disp_yn,ListMemberBase.disp_order,ListMemberBase.sid
                    from ListMemberBase 
                    inner  join listbase on listbase.ListId = ListMemberBase.ListId
                    inner join ContactBase on ContactBase.ContactId= ListMemberBase.EntityId
                    where purpose='小組名單' and listbase.ListId=%s  and disp_yn='Y' order by  ListMemberBase.disp_order """ ,[  listid  ])

    ListMember_rows = pycursor.fetchall()

    disp_order=0
    for listmember in ListMember_rows:
        disp_order+=1
        pycursor.execute("""update  ListMemberBase set disp_order=%s where sid=%s    """ ,[ disp_order, listmember[6] ])
#    app.logger.info ( 'commit' )
    psconn.commit()
    pycursor.execute("""select listbase.ListId, listbase.listName  ,ContactBase.LastName,ContactBase.ContactId,ListMemberBase.disp_yn,ListMemberBase.disp_order,ListMemberBase.sid
                    from ListMemberBase 
                    inner  join listbase on listbase.ListId = ListMemberBase.ListId
                    inner join ContactBase on ContactBase.ContactId= ListMemberBase.EntityId
                    where purpose='小組名單' and listbase.ListId=%s   and disp_yn='Y' order by  ListMemberBase.disp_order """ ,[  listid  ])

    ListMember_rows = pycursor.fetchall()

    pycursor.execute("""select listbase.ListId,listbase.listName , group_place, group_time   from   listbase     where ListId=%s   """ ,[  listid ])
    listName=""                
    row = pycursor.fetchone()    
    if row:
        listName=row[1]

    msgcontents={
 
                "type": "bubble",
                "size":  "giga",
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text":  listName+"名單" ,
                        "wrap": True,
                        "size":"md",
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
            
    }
    msgcontents["body"]["contents"].append(
        {"type": "box",
            "margin":"xs",
            "layout": "horizontal",
            "contents":[{
                "type": "box",
                "layout": "horizontal",  
                "margin":"xs",              
                "width":"25%",
                "contents": [{
                    "type": "text",
                    "text": "姓名",
                    "size":"md",
                    "margin":"xs",
                    "gravity": "center",
                    "color":"#1a5276FF"
                    } ]
                },
                {
                "type": "box",
                "layout": "horizontal",  
                "margin":"xs",              
                "width":"22%",
                "contents": [{
                    "type": "text",
                    "text":  "顯示序",
                    "size":"md",
                    "margin":"xs",
                    "gravity": "center",
                    "color":"#1a5276FF"
                    }]
                },
                {
                "type": "box",
                "layout": "horizontal",  
                "margin":"xs",              
                "width":"52%",
                "contents": [{
                    "type": "text",
                    "text":  "功能",
                    "size":"md",
                    "margin":"xs",
                    "gravity": "center",
                    "color":"#1a5276FF"
                    }]
                }
            ]
        }    
    )
    disp_order=0
    for listmember in ListMember_rows:
        disp_order=listmember[5]
        btnlabel=listmember[2]       
        
        btncolor1="#138d75"
        btncolor2="#f1c40f"
        #if listmember[4]!="Y":
        #    btncolor="#D0D3D4"
        msgcontents[ "body"]["contents"].append(
          {"type": "box",
             "margin":"xs",
             "layout": "horizontal",
             "contents":
             [{
                "type": "box",
                "layout": "horizontal",  
                "margin":"xs",              
                "width":"25%",
                "contents": [{
                    "type": "text",
                    "text": btnlabel,
                    "size":"md",
                    "margin":"xs",
                    "gravity": "center",
                    "color":"#1a5276FF"
                    } ]
                },
                {
                "type": "box",
                "layout": "horizontal",  
                "margin":"xs",              
                "width":"22%",
                "contents": [{
                    "type": "text",
                    "text":  str( listmember[5]),
                    "size":"md",
                    "margin":"xs",
                    "gravity": "center",
                    "color":"#1a5276FF"
                    }]
                },
                {
                "type": "box",
                "layout": "horizontal",  
                "margin":"xs",              
                "width":"25%",
                "contents": [{
                            "type": "button",
                            "margin":"xs",
                            "style":"primary", 
                            "color": btncolor1 ,
                            "height":"sm",
                            "size":"sm",
                            "action": {
                            "type": "postback",
                                "label": "上",
                                "data": "action=moveup&listid="+listmember[0]+"&cid="+ listmember[3] +"&disp_order="+ str(disp_order )
                            }
                    }]
                },
                 {
                "type": "box",
                "layout": "horizontal",  
                "margin":"xs",              
                "width":"25%",
                "contents": [{
                            "type": "button",
                            "margin":"xs",
                            "style":"primary", 
                            "color": btncolor2 ,
                            "height":"sm",
                            "size":"sm",
                            "action": {
                            "type": "postback",
                                "label": "下",
                                "data": "action=movedown&listid="+listmember[0]+"&cid="+ listmember[3] +"&disp_order="+ str(disp_order )
                            }
                    }]
                },
             ]}
        )
     
                    
    msgcontents["footer"]["contents"].append( 
        {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color": "#f1c40f",
            "action": {
                "type": "postback",
                "label":"更新名冊",
                "data":"action=getGroupMemberListforMove&listid="+listid+"&cid="+ contactid+ ("" if sender==None else "&sender=menu3" )
            }    
         })
    msgcontents["footer"]["contents"].append( {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color": "#FF8000",
            "action": {
                "type": "postback",
                "label":"回上層",
                "data": goBackAction 
            } } )
        
    return msgcontents 


def GroupMemberMoveUp(dict,psconn):

#    psconn =  getConnection()
    pycursor = psconn.cursor()
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    today   = datetime.datetime.now()  
    pycursor.execute("""select sid , ListId, entityid  , disp_yn,disp_order
                    from ListMemberBase                     
                    where ListId=%s  order by disp_order """ ,[  dict["listid"][0]   ])
                  
    members = pycursor.fetchall()
    the_order =int( dict["disp_order"][0])
    
    num1=-1
    num2=-1
    i=0
    while i<len(members):
        if(members[i][2]== dict["cid"][0] ):            
            num1=i
            num2=num1-1
            break
        i+=1 
    
    if ( num2>=0) and  ( num1>=0):
        pycursor.execute("""update ListMemberBase set disp_order=%s where sid=%s """,[  members[num1][4],members[num2][0]      ])
        pycursor.execute("""update ListMemberBase set disp_order=%s where sid=%s """,[ members[num2][4],members[num1][0]    ])
        psconn.commit()
    return 0
def GroupMemberMoveDown(dict,psconn):
#    psconn =  getConnection()
    pycursor = psconn.cursor()
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    today   = datetime.datetime.now()  
    pycursor.execute("""select sid , ListId, entityid  , disp_yn,disp_order
                    from ListMemberBase                     
                    where ListId=%s  order by disp_order """ ,[  dict["listid"][0]   ])
                  
    members = pycursor.fetchall()
    the_order =int( dict["disp_order"][0])
    
    num1=-1
    num2=-1
    i=0
    while i<len(members):
        if(members[i][2]== dict["cid"][0] ):            
            num1=i
            num2=num1+1
            break
        i+=1 
    
    if ( num2<len(members)) and  ( num1>=0):
        pycursor.execute("""update ListMemberBase set disp_order=%s where sid=%s """,[  members[num1][4],members[num2][0]      ])
        pycursor.execute("""update ListMemberBase set disp_order=%s where sid=%s """,[ members[num2][4],members[num1][0]    ])
        psconn.commit()
    return 0

def GroupMemberDisplay(dict,upd_no,psconn):
 #   psconn =  getConnection()
    pycursor = psconn.cursor()
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    today   = datetime.datetime.now()  
    pycursor.execute(""" update ListMemberBase set   disp_yn=%s ,upd_no=%s,upd_date=%s where ListId=%s  and entityid=%s """ ,[  
                        "Y" if dict["action"][0]=="disp_yes" else "N",                        
                        upd_no, datetime.datetime.now(),
                        dict["listid"][0],dict["cid"][0]    ])
    psconn.commit()
    return 0

def getWorshipReport(contactid,listid,sender=None,psconn=None):                
    
  goBackAction="action=ninjia&page=3"
  if sender!=None:
      goBackAction="action=groupshipMenu&cid="+contactid
  app.logger.info("getWorshipReport cid="+contactid+" lid="+listid ) 
  today   = datetime.datetime.now()  
  #  print(today ) 
#    psconn =  getConnection()
  with  psconn.cursor() as pycursor:
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    today   = datetime.datetime.now()   
#    print(today ) 
    pycursor.execute("""select distinct worship_date   from worshipdate where worship_date<=%s order by worship_date desc limit 8""" ,[ today.strftime('%Y-%m-%d') ])
    worshipdate_rows = pycursor.fetchall()
    today   = datetime.datetime.now()   
    app.logger.info(today ) 
    week=[]
    bdate=None
    edate=None
    page=0
    for  worshipdate in worshipdate_rows:       
        page+=1
        edate= worshipdate[0]
        if bdate==None:
            bdate=worshipdate[0] 
        if (page %4)==0:        
            week.append( { "bdate":bdate,"edate": edate  } )
            bdate=None
    if(bdate!=None):
        week.append( { "bdate":bdate,"edate": edate  } )

   # print(week)
    
    contents=  {
       "type": "carousel",  
        "contents": []
    }
    i=0
    while (i<len( week)):
        pageContent =getWorshipReportByDate(contactid,listid,week[i]["bdate"], goBackAction,psconn)
        contents["contents"].append(pageContent )
        i+=1

    return contents

def getWorshipReportByDate(contactid,listid,thedate ,goBackAction=None,psconn=None):  
    msgcontents={}
    #psconn =  getConnection()
    pycursor = psconn.cursor()
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    
    print("getWorshipReportByDate" )     
    week=[]
    # worshipdata   =  Worshipdata (None,None,None,None,None,None)
    the_sunday = current_weekday( datetime.date(thedate.year, thedate.month, thedate.day) , 6)
    
    pycursor.execute("""select distinct worship_date   from worshipdate where worship_date<=%s order by worship_date desc limit 4""" ,[ the_sunday.strftime('%Y-%m-%d') ])
    worshipdate_rows = pycursor.fetchall()
    for  worshipdate in worshipdate_rows:        
        nextsunday = next_weekday(  worshipdate[0] , 6)        
        week.append( { "bdate":worshipdate[0] ,"edate": nextsunday} )

    pycursor.execute("""select listbase.ListId,listbase.listName , group_place, group_time   from   listbase     where ListId=%s   """ ,[  listid ])
    listName=""                
    row = pycursor.fetchone()    
    if row:
        listName=row[1]

    msgcontents={
 
                "type": "bubble",
                "size":  "giga",
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text":  listName  +"主日崇拜"+week[len(week)-1]["bdate"].strftime('%m-%d')+"~"+week[0]["bdate"].strftime('%m-%d'),
                        "wrap": True,
                        "size":"md",
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
 
    }
    today   = datetime.datetime.now()   
    print(today ) 

    report=[]
    #print(week)      
    pycursor.execute("""select listbase.ListId, listbase.listName  ,ContactBase.LastName,ContactBase.ContactId
                    from ListMemberBase inner  join listbase on listbase.ListId = ListMemberBase.ListId
                    inner join ContactBase on ContactBase.ContactId= ListMemberBase.EntityId
                    where purpose='小組名單' and listbase.ListId=%s  and  ListMemberBase.disp_yn='Y' order by  ListMemberBase.disp_order """ ,[  listid  ])
    listName=""                
    ListMember_rows = pycursor.fetchall()
    
    for listmember in ListMember_rows:
        # report.append({ "LastName": listmember[3],"ContactId":listmember[2] })
        wks =[]
        i=0
        while i<len(week):
            
            present =  WeekPresent(week[i]["bdate"], week[i]["edate"],"□" )
            #print(worship_date )            
            pycursor.execute(""" select session from worship where  contactid=%s and  worship_date>=%s and worship_date<%s and del_flag='N' """,[   listmember[3],present.bdate,present.edate ] )
            row =pycursor.fetchone()
                        
            if row!=None:
                present.present= ("□" if row[ 0 ]==None else  str(row[ 0 ]))
            wks.append( present  )
            i+=1
        report.append(  GroupPresent( listmember[3] ,listmember[2],wks  ))
    #print(report)
    msgcontents["body"]["contents"].append(
        {   "type": "box",
            "layout": "horizontal",
            "margin":"xs",              
            "contents":[{
                "type": "box",
                "layout": "horizontal",                  
                "width":"22%",
                "contents": [
                            {
                            "type": "text",
                            "text":  "姓名",
                            "size":"md",                        
                            "margin":"xs",                            
                            "color":"#1a5276FF"
                        } , {
                            "type": "separator",
                            "color": "#ff0000"
                        }]
            }]
        }
    )
    today   = datetime.datetime.now()   
    print(today )     
    print(len(week) )     
    i=0
    while i<len(week):
        msgcontents["body"]["contents"][0]["contents"].append(
            {
                "type": "box",
                "layout": "horizontal",                
                "margin":"xs",      
                "width":"18%",
                "contents": [{
                    "type": "text",
                    "text":   week[i]["bdate"].strftime('%m-%d'),
                    "size":"sm",                     
                    "align":"center",
                    "color":"#1a5276FF"
                }, {
                    "type": "separator",
                    "color": "#ff0000"
                }
                ]
            })
        i+=1
    
    today   = datetime.datetime.now()   
    print(today )     
    for grouppresent in report:
        
        msg={"type": "box",
             "layout": "horizontal",             
             "margin":"xs",
             "contents":[{
                "type": "box",
                "layout": "horizontal",                                  
                "width":"22%",
                "contents": [{
                    "type": "text",
                    "text":  grouppresent.contactname,
                    "size":"md",                    
                    "color":"#1a5276FF"
                    } , {
                    "type": "separator",
                    "color": "#ff0000"
                     } ]
            } ]
        }
        for wk in grouppresent.groupworship:  
            msg["contents"].append(
                {"type": "box",
                "margin":"xs", 
                 "layout": "horizontal",                
                 "width":"18%",
                 "contents": [{
                    "type": "text",
                    "text":  wk.present,
                    "size":"sm",                                             
                    "align":"center",
                    "color":"#1a5276FF"
                  }, {
                    "type": "separator",
                    "color": "#ff0000"
                  }]
                })
        
        
        msgcontents["body"]["contents"].append(msg)
   
    
    msgcontents["footer"]["contents"].append(
            {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color": "#FF8000",
            "action": {
                "type": "postback",
                "label":"回上層",
                "data": goBackAction #"action=groupshipMenu&cid="+contactid
            }
        }    
    )
    return msgcontents


def getPersonalWorshipReport(contactid,listid,sender=None,psconn=None):
  goBackAction="action=groupshipMenu&cid="+contactid
  goBackAction="action=ninjia&page=3"

  app.logger.info(goBackAction)
    #psconn =  getConnection()
  with  psconn.cursor() as  pycursor:
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    today   = datetime.datetime.now()   
    pycursor.execute("""select distinct worship_date   from worshipdate where worship_date<=%s order by worship_date desc limit 8 """ ,[ today.strftime('%Y-%m-%d') ])
    worshipdate_rows = pycursor.fetchall()
    week=[]
    bdate=None
    edate=None
    page=0
    for  worshipdate in worshipdate_rows:       
        page+=1
        edate= worshipdate[0]
        if bdate==None:
            bdate=worshipdate[0] 
        if (page %4)==0:        
            week.append( { "bdate":bdate,"edate": edate  } )
            bdate=None
    if(bdate!=None):
        week.append( { "bdate":bdate,"edate": edate  } )

   # print(week)
    
    contents=  {
       "type": "carousel",  
        "contents": []
    }
    i=0
    while (i<len( week)):
        pageContent =getPersonalWorshipReportByDate(contactid,listid,week[i]["bdate"],goBackAction,psconn )
        contents["contents"].append(pageContent )
        i+=1

    return contents

def getPersonalWorshipReportByDate(contactid,listid,thedate,goBackAction=None,psconn=None):
  msgcontents={}
#    psconn =  getConnection()
  with   psconn.cursor() as pycursor:
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    
                
    week=[]
    # worshipdata   =  Worshipdata (None,None,None,None,None,None)
    the_sunday = current_weekday( datetime.date(thedate.year, thedate.month, thedate.day) , 6)
    
    pycursor.execute("""select distinct worship_date   from worshipdate where worship_date<=%s order by worship_date desc limit 4""" ,[ the_sunday.strftime('%Y-%m-%d') ])
    worshipdate_rows = pycursor.fetchall()
    for  worshipdate in worshipdate_rows:        
        nextsunday = next_weekday(  worshipdate[0] , 6)        
        week.append( { "bdate":worshipdate[0] ,"edate": nextsunday} )

    pycursor.execute("""select listbase.ListId,listbase.listName , group_place, group_time   from   listbase     where ListId=%s   """ ,[  listid ])
    listName=""                
    row = pycursor.fetchone()    
    if row:
        listName=row[1]

    msgcontents={
 
                "type": "bubble",
                "size":  "giga",
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text":  listName  +"靈修狀態"+week[len(week)-1]["bdate"].strftime('%m-%d')+"~"+week[0]["bdate"].strftime('%m-%d'),
                        "wrap": True,
                        "size":"md",
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
 
    }


    report=[]
    #print(week)      
    pycursor.execute("""select listbase.ListId, listbase.listName  ,ContactBase.LastName,ContactBase.ContactId
                    from ListMemberBase inner  join listbase on listbase.ListId = ListMemberBase.ListId
                    inner join ContactBase on ContactBase.ContactId= ListMemberBase.EntityId
                    where purpose='小組名單' and listbase.ListId=%s  and  ListMemberBase.disp_yn='Y' order by  ListMemberBase.disp_order """ ,[  listid  ])
    listName=""                
    ListMember_rows = pycursor.fetchall()
    
    for listmember in ListMember_rows:
        # report.append({ "LastName": listmember[3],"ContactId":listmember[2] })
        wks =[]
        i=0
        while i<len(week):
            
            present =  WeekPresent(week[i]["bdate"], week[i]["edate"]," " )
            #print(worship_date )            
            pycursor.execute("""select * from personalworship where  contactid=%s and  worship_date>=%s and worship_date<%s and del_flag='N' """,[   listmember[3],present.bdate,present.edate ] )
            row =pycursor.fetchone()
            columns = []

            for col in pycursor.description:
                columns.append(col[0])
            if row!=None:
                present.present= (" " if row[columns.index("worship_times")]==None else  str(row[columns.index("worship_times")]))
            wks.append( present  )
            i+=1
        report.append(  GroupPresent( listmember[3] ,listmember[2],wks  ))
    #print(report)
    msgcontents["body"]["contents"].append(
        {   "type": "box",
            "layout": "horizontal",
            "margin":"xs",              
            "contents":[{
                "type": "box",
                "layout": "horizontal",                  
                "width":"22%",
                "contents": [
                            {
                            "type": "text",
                            "text":  "姓名",
                            "size":"md",                        
                            "margin":"xs",                            
                            "color":"#1a5276FF"
                        } , {
                            "type": "separator",
                            "color": "#ff0000"
                        }]
            }]
        }
    )
    i=0
    while i<len(week):
        msgcontents["body"]["contents"][0]["contents"].append(
            {
                "type": "box",
                "layout": "horizontal",                
                "margin":"xs",      
                "width":"18%",
                "contents": [{
                    "type": "text",
                    "text":   week[i]["bdate"].strftime('%m-%d'),
                    "size":"sm",                     
                    "align":"center",
                    "color":"#1a5276FF"
                }, {
                    "type": "separator",
                    "color": "#ff0000"
                }
                ]
            })
        i+=1
    
    for grouppresent in report:
        
        msg={"type": "box",
             "layout": "horizontal",             
             "margin":"xs",
             "contents":[{
                "type": "box",
                "layout": "horizontal",                                  
                "width":"22%",
                "contents": [{
                    "type": "text",
                    "text":  grouppresent.contactname,
                    "size":"md",                    
                    "color":"#1a5276FF"
                    } , {
                    "type": "separator",
                    "color": "#ff0000"
                     } ]
            } ]
        }
        for wk in grouppresent.groupworship:  
            msg["contents"].append(
                {"type": "box",
                "margin":"xs", 
                 "layout": "horizontal",                
                 "width":"18%",
                 "contents": [{
                    "type": "text",
                    "text":  wk.present,
                    "size":"sm",                                             
                    "align":"center",
                    "color":"#1a5276FF"
                  }, {
                    "type": "separator",
                    "color": "#ff0000"
                  }]
                })
        
        
        msgcontents["body"]["contents"].append(msg)
   
    
    msgcontents["footer"]["contents"].append(
            {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color": "#FF8000",
            "action": {
                "type": "postback",
                "label":"回上層",
                "data": goBackAction #"action=groupshipMenu&cid="+contactid
            }
        }    
    )
    return msgcontents    

def getManageGroup(contactid,forwardAction=None,psconn=None):
    gotoaction="getGroupMemberList"
    if forwardAction!=None:
        gotoaction=forwardAction
    app.logger.info(gotoaction)
    msgcontents={
 
                "type": "bubble",
                "size":  "giga",
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text":  "選擇小組",                        
                        "size":"md",
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
 
    }
    groupdata = GroupOwner(contactid,psconn)    
    app.logger.info(len(groupdata)) 
    appendItems=[]
    for group in groupdata:
#        app.logger.info(group.listid+","+group.listname+","+group.role)
        #if (group.role!="member"):
        btnlabel=group.listname
        btndata ="action="+gotoaction+"&listid="+group.listid+"&cid="+ contactid 
        btnstyle="primary"
        btncolor="#4277bd"
        appendItems.append(
             {"type": "box",
              "layout": "vertical",
               "contents":[ 
                {
                    "type": "button",
                    "margin":"xs",
                    "style":btnstyle,
                    "color":btncolor,
                    "action": {
                        "type": "postback",
                        "label":btnlabel,
                        "data":btndata,
                    }
                }]
            })  
  #  if  len(appendItems)>0:
  #     
    for btns in appendItems:

        msgcontents[ "body"]["contents"].append(
              btns
         )

    #msgcontents["body"]["contents"].append(
    #         {"type": "box",
    #            "layout": "vertical",
    #            "contents":[ 
    #            ]
    #        })        
    # 
    msgcontents["footer"]["contents"].append(
            {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color": "#FF8000",
            "action": {
                "type": "postback",
                "label":"回上層",
                "data": "action=ninjia&page=3"
            }
        }    
    )    
    return msgcontents    

