from calendar import SUNDAY
import json
import logging
from time import strftime,time

from flask import Flask
import datetime
from .classes import Member,Family
from .utils import next_weekday,getConnection,current_weekday
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

#個人靈修
def PersonalWorshipMenu(contactid,displayname,psconn):
#    psconn =  getConnection()

    pycursor = psconn.cursor()
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
                        "text": "靈修天數回報",
                        "size":"lg",
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
                                "text":("" if (displayname==None) else displayname)+",請選回報的週次",
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
    today   = datetime.datetime.now()
    next_sunday = current_weekday( datetime.date(today.year, today.month, today.day) , 6)
    pycursor.execute("""select distinct worship_date   from worshipdate where worship_date<=%s order by worship_date desc limit 4""" ,[ next_sunday.strftime('%Y-%m-%d') ])
    worshipdate_rows = pycursor.fetchall()
    for  worshipdate in worshipdate_rows:
        print(worshipdate[0])
        pycursor.execute("""select contactid,user_id,worship_date,worship_times from personalworship where contactid=%s and worship_date=%s   and del_flag='N' """ ,
                    [ contactid , worshipdate[0].strftime('%Y-%m-%d') ])
        row = pycursor.fetchone()                                          

        btnstyle ="primary" 
        btncolor="#BABD42"
        btnlabel= worshipdate[0].strftime('%m%d')+"週靈修"
        btndata = "action=selectPersonalWorshipDate&worshipdate="+ worshipdate[0].strftime('%Y-%m-%d')+"&cid="+contactid
        if row!=None:
            if( row[3]>0):
                btnstyle="secondary"                                            
                btnlabel=btnlabel+ "-"+ str(row[3])+"天"
                btncolor="#ECA6A6"
                btndata = "action=CancelPersonalWorshipDateTimes&worshipdate="+ worshipdate[0].strftime('%Y-%m-%d')+"&cid="+contactid
            app.logger.info(btndata)
        msgcontents["contents"][0]["body"]["contents"].append(
        {
            "type": "button",
            "margin":"xs",
            "style": btnstyle,
            "color":btncolor,
            "action": {
                "type": "postback",                
                "label": btnlabel,
                "data":  btndata
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
    pycursor.close()
    return msgcontents

def selectPersonalWorshipDate(contactid, worshipdate,displayname,psconn):
#    psconn = getConnection()
    pycursor = psconn.cursor()
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
                        "text": worshipdate+"靈修天數回報",
                        "size":"lg",
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
                                "text":("" if (displayname==None) else displayname)+",請選本週靈修的天數", 
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

    pycursor.execute("""select contactid,user_id,worship_date,worship_times from personalworship where contactid=%s and worship_date=%s and del_flag='N' """ ,
                                       [ contactid ,  worshipdate  ])
    worship =pycursor.fetchone()                                                                                                     
    btndata="action=setPersonalWorshipDateTimes&cid="+contactid+"&worshipdate="+worshipdate
    btnstyle ="primary" 
    wtimes=0
    if worship!=None:
        btnstyle="secondary"
        if worship[3]>0:
            btndata="action=CancelPersonalWorshipDateTimes&cid="+contactid +"&worshipdate="+worshipdate
        wtimes=worship[3]
                    
    msgcontents["contents"][0]["body"]["contents"].append(
        {
            "type": "box",
            "margin":"xs",
            "layout": "horizontal",
            "contents":[                                    
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin":"xs",
                    "contents": [
                        {
                            "type" :"button",
                            "margin":"xs",
                            "style": "secondary" if wtimes==1 else "primary" ,
                            "color":"#BABD42",
                            "action": {
                                "type": "postback",
                                "label": "0",
                                "data":  btndata+"&times=0"
                            }
                        }
                    ],
                    "width": "72px",
                    "height": "72px",
                    "background":  "#FFFF00",                                   
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin":"xs",
                    "contents": [
                        {
                            "type" :"button",
                            "margin":"xs",
                            "style": "secondary" if wtimes==2 else "primary" ,
                            "color":"#BABD42",
                            "action": {
                                "type": "postback",
                                "label": "1",
                                "data":   btndata+"&times=1"
                            }
                        }
                    ],
                    "width": "72px",
                    "height": "72px",
                    "background":  "#FFFF00",                                   
                    },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin":"xs",
                    "contents": [
                        {
                            "type" :"button",
                            "margin":"xs",
                            "style": "secondary" if wtimes==3 else "primary" ,
                            "color":"#BABD42",
                            "action": {
                                "type": "postback",
                                "label": "2",
                                "data":   btndata+"&times=2"
                            }
                        }
                    ],
                    "width": "72px",
                    "height": "72px",
                    "background":  "#FFFF00", 
                }
                                
            ]
        })
    msgcontents["contents"][0]["body"]["contents"].append(            
                {
                    "type": "box",
                    "margin":"xs",
                    "layout": "horizontal",
                    "contents":[                                    
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin":"xs",
                            "contents": [
                                {
                                    "type" :"button",
                                    "margin":"xs",
                                    "style":"secondary" if wtimes==4 else "primary" ,
                                    "color":"#BABD42",
                                    "action": {
                                        "type": "postback",
                                        "label": "3",
                                        "data":   btndata+"&times=3"
                                    }
                                }
                            ],
                            "width": "72px",
                            "height": "72px",
                            "background":  "#FFFF00",
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin":"xs",
                            "contents": [
                                {
                                    "type" :"button",
                                    "margin":"xs",
                                    "style": "secondary" if wtimes==5 else "primary" ,
                                    "color":"#BABD42",
                                    "action": {
                                        "type": "postback",
                                        "label": "4",
                                        "data":  btndata+"&times=4"
                                    }
                                }
                            ],
                            "width": "72px",
                            "height": "72px",
                            "background":  "#FFFF00",                                   
                            },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin":"xs",
                            "contents": [
                                {
                                    "type" :"button",
                                    "margin":"xs",
                                    "style": "secondary" if wtimes==6 else "primary" ,
                                    "color":"#BABD42",
                                    "action": {
                                        "type": "postback",
                                        "label": "5",
                                        "data":  btndata+"&times=5"
                                    }
                                }
                            ],
                            "width": "72px",
                            "height": "72px",
                            "background":  "#FFFF00",                                   
                        }
                                        
                    ]
                }
        )
    msgcontents["contents"][0]["body"]["contents"].append(
                    {
                    "type": "box",
                    "margin":"xs",
                    "layout": "horizontal",
                    "contents":[                                    
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin":"xs",
                            "contents": [
                                {
                                    "type" :"button",
                                    "margin":"xs",
                                    "style": "secondary" if wtimes==7 else "primary" ,
                                    "color":"#BABD42",
                                    "action": {
                                        "type": "postback",
                                        "label": "6",
                                        "data":  btndata+"&times=6"
                                    }
                                }
                            ],
                            "width": "72px",
                            "height": "72px",
                            "background":  "#FFFF00",
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin":"xs",
                            "contents": [
                                {
                                    "type" :"button",
                                    "margin":"xs",
                                    "style": "secondary" if wtimes==8 else "primary" ,
                                    "color":"#BABD42",
                                    "action": {
                                        "type": "postback",
                                        "label": "7",
                                        "data": btndata+"&times=7"
                                    }
                                }
                            ],
                            "width": "72px",
                            "height": "72px",
                            "background":  "#FFFF00",                                   
                            },
                             

                    ]
                }
        )   
    msgcontents["contents"][0]["footer"]["contents"].append(
            { "type": "box",
              "margin":"xs",
              "layout": "horizontal",
              "contents":[                                    
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin":"xs",
                            "contents": [
                                {
                                    "type": "button",
                                    "margin":"xs",
                                    "style":"primary",
                                    "color": "#FF8000",
                                    "action": {
                                        "type": "postback",
                                        "label":"回上層",
                                        "data": "action=personalWorship&cid="+contactid
                                    }
                                }
                            ],
                             "width": "216px",
                            "height": "80px",
                        }]
            }
        )
    pycursor.close()
    return msgcontents
