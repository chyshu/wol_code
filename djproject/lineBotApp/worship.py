from calendar import SUNDAY
import json
import logging
from time import strftime,time
#from .models import Greeting
from flask import Flask
import datetime
from .classes import Member,Family
from .utils import next_weekday, getConnection,current_weekday
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

def getMyGroupListMenu(psconn, contactid, displayname,next_action):
  #psconn =  getConnection()    
  with  psconn.cursor() as  pycursor:
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
                        "text":  "主日出席回報",
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
        btnlabel=listbase[1]
        # btndata ="action="+next_action+"&listid="+listbase[0]+"&cid="+ contactid 
        btndata ="listid="+listbase[0]+"&cid="+ contactid 
        btnstyle="primary"
        btncolor="#BABD42"
        msgcontents["body"]["contents"].append(
                {
                    "type": "button",
                    "margin":"xs",
                    "style":btnstyle,
                    "color":btncolor,
                    "action": {
                        #"type": "postback",
                        "label":btnlabel,
                        #"data":btndata,
                        "type": "uri",                        
                        "uri": "https://liff.line.me/1657309833-rY7845XQ"+"?"+btndata
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
                "data":"action=worshipMenu&cid="+contactid
            }
        }
    )
  return msgcontents    


def getGroupMemberWorshipDate(contactid, displayname,listid,next_action,psconn):
    #psconn =  getConnection()    
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
                        "text": "小組主日出席回報",
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
                                "text": "請選要回報的主日",
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
    next_sunday = current_weekday( datetime.date(today.year, today.month, today.day) , 6)

    pycursor.execute("""select distinct worship_date   from worshipdate where worship_date<=%s order by worship_date desc limit 4""" ,[ next_sunday.strftime('%Y-%m-%d') ])
    worshipdate_rows = pycursor.fetchall()
    for  worshipdate in worshipdate_rows:
        #print(worshipdate[0])
     
        btnstyle ="primary" 
        btncolor="#BABD42"
        btnlabel= worshipdate[0].strftime('%m%d')+"主日"
 

        msgcontents["contents"][0]["body"]["contents"].append(
        {
            "type": "button",
            "margin":"xs",
            "style": btnstyle,
            "color":btncolor,
            "action": {
                "type": "postback",
                "label":btnlabel,
                "data": "action="+next_action+"&worshipdate="+ worshipdate[0].strftime('%Y-%m-%d')+"&cid="+contactid+"&listid="+listid,
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
                "data":"action=worship_groupsmenu&cid="+contactid
            }
        }
    )
    return msgcontents    


def getGroupMemberWorshipList(contactid, displayname,listid,worship_date,psconn):
    #psconn =  getConnection()
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
                        "text":  datetime.datetime.strptime( worship_date , '%Y-%m-%d').strftime("%y%m%d")  +"小組成員主日回報",
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
                                "text": "請點選出席", 
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
    print( worship_date)  
    ListMember_rows = pycursor.fetchall()
    for listmember in ListMember_rows:
        box={
            "type": "box",
            "layout": "horizontal",
            "margin":"xs",    
            "contents": []
        }
        pycursor.execute(""" select worship_date,session from worshipdate where worship_date=%s """,[ worship_date  ] )
        worshipdateRows= pycursor.fetchall()
        for wdate in worshipdateRows:

            btndata="action=setGroupMember"
            btnstyle ="primary" 
            btncolor="#BABD42"
            btnlabel=  listmember[2]  
            pycursor.execute(""" select * from worship where worship_date=%s and session=%s and contactid=%s and del_flag='N' """,[ wdate[0], wdate[1] ,  listmember[3]  ] )
            row =pycursor.fetchone()       
            if row:
                btnstyle="secondary"
                btnlabel=btnlabel+ "\n1出席"
                btndata="action=cancelGroupMember"
                btncolor="#ECA6A6"
                box
            box["contents"].append(
                {
                    "type": "button",
                    "margin":"xs",
                    "size":"md",
                    "style":btnstyle,
                    "color":btncolor,
                    "action": {
                        "type": "postback",
                        "label":btnlabel,
                        "data":btndata+"&listid="+listmember[0] + "&cid="+listmember[3] + "&opid="+ contactid +"&worshipdate="+worship_date+"&session="+listmember[3]                        
                    }
                })
        msgcontents["body"]["contents"].append( box)
    print( msgcontents["body"]["contents"])
    msgcontents["footer"]["contents"].append( 
        {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color": "#f1c40f",
            "action": {
                "type": "postback",
                "label":"更新名冊",

                "data":"action=worship_groupsmenu_liste&listid="+listid+"&cid="+ contactid +"&worshipdate="+worship_date                
                
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
                "data":"action=worship_groupsmenu_selectdate&listid="+listid+"&cid="+contactid
            }
        }
    )

    return msgcontents
# 主日回報MENU

def getWorshipMenu(contactid, displayname,psconn):
    #psconn =  getConnection()    
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
                        "text": "主日出席回報",
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
                                "text": ("" if (displayname==None) else displayname) +",請選要回報的主日",
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
    next_sunday = current_weekday( datetime.date(today.year, today.month, today.day) , 6)
                        

    pycursor.execute("""select distinct worship_date   from worshipdate where worship_date<=%s order by worship_date desc limit 4""" ,[ next_sunday.strftime('%Y-%m-%d') ])
    worshipdate_rows = pycursor.fetchall()
    for  worshipdate in worshipdate_rows:
        #print(worshipdate[0])
        print(worshipdate[0].strftime('%Y-%m-%d'))
        pycursor.execute("""select contactid,user_id,worship_date,session from worship where contactid=%s and worship_date=%s """ ,[ contactid , worshipdate[0].strftime('%Y-%m-%d') ])
        worshipdate_row = pycursor.fetchone()
        # pycursor.execute("""select worship_date,session,caption   from worshipdate where worship_date=%s order by session""" ,[  worshipdate[0].strftime('%Y-%m-%d') ])                           
        # worshipdate_rows = pycursor.fetchall()
        # for  worshipdate_row in worshipdate_rows:   
        btnstyle ="primary" 
        btncolor="#BABD42"
        btnlabel= worshipdate[0].strftime('%m%d')+"主日"
        if worshipdate_row!=None:
            btnstyle="secondary"                                            
            btnlabel=btnlabel+ "-已回報"
            btncolor="#ECA6A6"

        msgcontents["contents"][0]["body"]["contents"].append(
        {
            "type": "button",
            "margin":"xs",
            "style": btnstyle,
            "color":btncolor,
            "action": {
                "type": "postback",
                "label":btnlabel,
                "data": "action=selectWorshipDate&worshipdate="+ worshipdate[0].strftime('%Y-%m-%d')+"&cid="+contactid+"&sender=personal",
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
                "label":"幫小組成員回報",
                "data":"action=worship_groupsmenu&cid="+contactid,
            }
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
                "label":"幫家人同行回報",
                "data":"action=closeworship&cid="+contactid,
            }
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
                "data":"action=cherub"
            }
        }
    )

    return msgcontents

def getWorshipDate(contactid, displayname,worshipdate,sender,psconn ): 
    #psconn =  getConnection()

    pycursor = psconn.cursor()
    print(contactid +" " +worshipdate)
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
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
                        "text":  worshipdate+"主日出席回報",
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
                                "text":("" if (displayname==None) else displayname)+",請回報"+("" if sender=="personal" else "家人")+"出席的場次", 
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
                    
    pycursor.execute("""select  worship_date,session,caption,description  from worshipdate where worship_date=%s  order by  session """ ,[ worshipdate  ])
    worshipdate_rows = pycursor.fetchall()
    for  worshipdateData in worshipdate_rows:             

        pycursor.execute("""select contactid,user_id,worship_date,session from worship where contactid=%s and worship_date=%s and session=%s  and del_flag<>'Y' """ ,
                        [ contactid , worshipdateData[0].strftime('%Y-%m-%d'), worshipdateData[1]   ])
        worship =pycursor.fetchone()              
        btndata="action=setWorshipDate"
        btnstyle ="primary" 
        btncolor="#BABD42"
        btnlabel= worshipdateData[1]
        if worship!=None:
            btnstyle="secondary"                                            
            btnlabel=btnlabel+ "-已回報"
            btndata="action=CacnelWorshipDate"
            btncolor="#ECA6A6"
        
        msgcontents["contents"][0]["body"]["contents"].append(
            {
                "type": "button",
                "margin":"xs",
                "style":btnstyle,
                "color":btncolor,
                "action": {
                    "type": "postback",
                    "label":btnlabel,
                    "data":btndata+"&worshipdate="+ worshipdateData[0].strftime('%Y-%m-%d')+"&session="+ worshipdateData[1]+"&cid="+contactid+"&sender="+sender
                }
            }
        )   
    msgcontents["contents"][0]["body"]["contents"].append(
            {
            "type": "button",
            "margin":"xs",
            "style":"primary",
            "color":"#BABD42",
            "action": {
                "type": "postback",
                "label":"更新本週狀態",
                "data":"action=selectWorshipDate&worshipdate="+  worshipdate  +"&cid="+ contactid+"&sender="+sender
            }
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
                "data":"action=worshipMenu"
            }
        }
    )


    return msgcontents

def getWorshipMenuWithClose(contactid, displayname,psconn):
#    psconn =  getConnection()    
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
                        "text": "家人同行主日回報",
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
                                "text":("" if (displayname==None) else displayname)+",請選要回報的主日",
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
    next_sunday = current_weekday( datetime.date(today.year, today.month, today.day) , 6)
    pycursor.execute("""select distinct worship_date   from worshipdate where worship_date<=%s order by worship_date desc limit 4""" ,[ next_sunday.strftime('%Y-%m-%d') ])
    worshipdate_rows = pycursor.fetchall()
    for  worshipdate in worshipdate_rows:
        #print(worshipdate[0])
        print(worshipdate[0].strftime('%Y-%m-%d'))
        pycursor.execute("""select contactid,user_id,worship_date,session from worship where contactid=%s and worship_date=%s """ ,[ contactid , worshipdate[0].strftime('%Y-%m-%d') ])
        worshipdate_row = pycursor.fetchone()                                          
        # pycursor.execute("""select worship_date,session,caption   from worshipdate where worship_date=%s order by session""" ,[  worshipdate[0].strftime('%Y-%m-%d') ])                           
        # worshipdate_rows = pycursor.fetchall()
        # for  worshipdate_row in worshipdate_rows:   
        btnstyle ="primary" 
        btncolor="#BABD42"
        btnlabel= worshipdate[0].strftime('%m%d')+"主日"
        if worshipdate_row!=None:
            btnstyle="secondary"                                            
            btnlabel=btnlabel+ "-已回報"
            btncolor="#ECA6A6"

        msgcontents["contents"][0]["body"]["contents"].append(
        {
            "type": "button",
            "margin":"xs",
            "style": btnstyle,
            "color":btncolor,
            "action": {
                "type": "postback",
                "label":btnlabel,
                "data": "action=selectWorshipDate&worshipdate="+ worshipdate[0].strftime('%Y-%m-%d')+"&cid="+contactid+"&sender=close",
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
                "data":"action=cherub"
            }
        }
    )

    return msgcontents

