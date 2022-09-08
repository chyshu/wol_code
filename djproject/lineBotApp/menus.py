from calendar import SUNDAY
import json
import logging
from time import strftime,time
#from .models import Greeting
from flask import Flask
import datetime
from .classes import Member,Family
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

def get_menu():
    contents={
        "type": "carousel",  
        "contents": [
            {
                "type": "bubble",    
                "size":  "kilo", 
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text": "主日回報",
                        "size":"xl",
                        "weight":"bold", 
                        "color":"#FFFFFF",
                    }],                                    
                    "backgroundColor": "#FF8000FF",
                },
                "hero": {
                    "type": "image",
                    "url": settings.SERVER_URL+"static/525452.png",  
                    "aspectMode":"cover",
                    "aspectRatio":"1:1",
                    "margin":"sm",
                    "spacing":"sm",
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "回報",
                                "data":"action=worshipMenu"
                            },
                            "style": "primary",
                            "color": "#A64B2A",
                        }
                    ]
                },
            },
            {
                "type": "bubble",    
                "size":  "kilo", 
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text": "小組回報",
                        "size":"xl",
                        "weight":"bold", 
                        "color":"#FFFFFF",

                    }],
                    "backgroundColor": "#FF8000FF",
                },
                "hero": {
                    "type": "image",
                    "url": settings.SERVER_URL+ "static/570638.png",     
                    "aspectMode":"cover",
                    "aspectRatio":"1:1",
                    "margin":"sm",
                    "spacing":"sm",
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "回報",
                                "data":"action=groupshipMenu"
                            },
                            "style": "primary",
                            "color": "#A64B2A",
                        }
                    ]
                },
            },
            {
                "type": "bubble",    
                "size":  "kilo", 
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text":"代禱",
                        "size":"xl",
                            "weight":"bold", 
                        "color":"#FFFFFF",

                    }],
                    "backgroundColor": "#FF8000FF",
                },
                "hero": {
                    "type": "image",
                    "url":settings.SERVER_URL+ "static/praying-child-285x300.jpg",
                    "aspectMode":"cover",
                    "aspectRatio":"1:1",
                    "margin":"sm",
                    "spacing":"sm",
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "代禱",
                                "data":"action=praymenu", 
                            },
                            "style": "primary",
                            "color": "#A64B2A",
                        }
                    ]
                },
            },
            {
                "type": "bubble",    
                "size":  "kilo", 
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text":"靈修",
                        "size":"xl",
                        "weight":"bold", 
                        "color":"#FFFFFF",
 
                    }],
                    "backgroundColor": "#FF8000FF",
                },
                "hero": {
                    "type": "image",
                    "url": settings.SERVER_URL+"static/3-0cover.jpg",  
                    "margin":"sm",
                    "spacing":"sm",
                    "aspectMode":"cover",
                    "aspectRatio":"1:1"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "靈修",
                                "data":"action=PersonalWorshipMenu"
                            },
                            "style": "primary",
                            "color": "#A64B2A",
                        }
                    ]
                },
            },
            {
                "type": "bubble",    
                "size":  "kilo", 
                "header" :{
                    "type": "box",
                    "layout": "vertical",
                    "contents":[{
                        "type": "text",
                        "text": "綁定資料",
                        "size":"xl",
                        "weight":"bold", 
                        "color":"#FFFFFF",
                    }],                                    
                    "backgroundColor": "#FF8000FF",
                },
                "hero": {
                    "type": "image",
                    "url": settings.SERVER_URL+"static/25737461.jpg",  
                    "aspectMode":"cover",
                    "aspectRatio":"1:1",
                    "margin":"sm",
                    "spacing":"sm",
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "綁定",
                                "data":"action=bindingMenu"
                            },
                            "style": "primary",
                            "color": "#A64B2A",
                        }
                    ]
                },
            },
        ]
    }
    return contents

def getMenuV2(contactid=None, page=None,psconn=None):
  app.logger.info("getMenuV2:"+"contactid-"+contactid+" page-"+ ("" if page==None else page))
  #app.logger.info(settings.SERVER_URL)
  # global  psconn #=  getConnection()
  with psconn.cursor() as pycursor:
    pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    contents={}
    if(page==None) or (page=="1"):
        contents={
            "type": "bubble",     
            "size":  "giga",
            "header" :{
                "type": "box",
                "layout": "horizontal",
                "width":"100%",
                "backgroundColor": "#f1c40fF0",
                "contents":[
                    {
                        "type": "box",
                        "width":"33%", 
                        "layout": "horizontal",
                        "contents":[
                            {
                                "align": "start",
                                "type": "text",
                                "text":" ",
                                "size":"xxs"
                            }
                        ]
                    },
                    {
                        "type": "text",
                        "text": "個人回報",
                        "gravity": "center",
                        "align": "center",
                        "width":"33%",
                        "size":"lg",
                        "weight":"bold", 
                        "color":"#FFFFFF",
                    },
                    {
                        "type": "box",
                        "width":"33%", 
                        "layout": "horizontal",
                        "contents":[
                            {
                                "type": "image",
                                "url": settings.SERVER_URL+"static/next.png",  
                                "aspectMode":"cover",
                                "aspectRatio":"1:1",
                                "margin":"none",
                                "spacing":"none",
                                "align": "end",
                                "size":"50px",
                                "action": {
                                    "type": "postback",
                                    "label": "下頁",
                                    "data":"action=ninjia&page=2"
                                },
                            }
                        ]
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "width":"100%",
                "margin":"sm",
                "spacing":"sm",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "width":"33%",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "contents":[{
                                        "type": "image",
                                            "url":settings.SERVER_URL+"static/menua_3.jpg",  
                                            "aspectMode":"cover",
                                            "aspectRatio":"1:1",
                                            "margin":"sm",
                                            "spacing":"sm",
                                            "action": {
                                                "type": "postback",
                                                "label": "主日出席回報",
                                                "data":"action=worshipMenu"
                                            },
                                        }]
                                    }
                                ]
                            },
                            {   "type": "box",
                                "layout": "horizontal",
                                "width":"33%",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "contents":[{
                                        "type": "image",
                                            "url": settings.SERVER_URL+"static/menua_5.jpg",  
                                            "aspectMode":"cover",
                                            "aspectRatio":"1:1",
                                            "margin":"sm",
                                            "spacing":"sm",
                                            "action": {
                                                "type": "postback",
                                                "label": "小組出席回報",
                                                "data":"action=groupshipMenu"
                                            },
                                        }]
                                    }
                                ]
                            },
                            {   "type": "box",
                                "layout": "horizontal",
                                "width":"33%",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "contents":[{
                                        "type": "image",
                                            "url": settings.SERVER_URL+"static/menua_7.jpg",  
                                            "aspectMode":"cover",
                                            "aspectRatio":"1:1",
                                            "margin":"sm",
                                            "spacing":"sm",
                                            "action": {
                                                "type": "postback",
                                                "label": "代禱",
                                                "data":"action=praymenu"
                                            },
                                        }]
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "width":"33%",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "contents":[{
                                        "type": "image",
                                            "url": settings.SERVER_URL+"static/menua_12.jpg",  
                                            "aspectMode":"cover",
                                            "aspectRatio":"1:1",
                                            "margin":"sm",
                                            "spacing":"sm",
                                            "action": {
                                                "type": "postback",
                                                "label": "靈修回報",
                                                "data":"action=PersonalWorshipMenu"
                                            },
                                        }]
                                    }
                                ]
                            },
                            {   "type": "box",
                                "layout": "horizontal",
                                "width":"33%",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "contents":[{
                                        "type": "image",
                                            "url": settings.SERVER_URL+"static/menua_13.jpg",  
                                            "aspectMode":"cover",
                                            "aspectRatio":"1:1",
                                            "margin":"sm",
                                            "spacing":"sm",
                                            "action": {
                                                "type": "postback",
                                                "label": "資料綁定",
                                                "data":"action=bindingMenu"
                                            },
                                        }]
                                    }
                                ]
                            },
                            {   "type": "box",
                                "layout": "horizontal",
                                "width":"33%",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "contents":[{
                                        "type": "image",
                                            "url": settings.SERVER_URL+"static/menua_14.jpg",  
                                            "aspectMode":"cover",
                                            "aspectRatio":"1:1",
                                            "margin":"sm",
                                            "spacing":"sm",
                                            "action": {
                                                "type": "uri",
                                                "label": "一頁回報",
                                                "uri": "https://liff.line.me/1657309833-P82YBEM5"
                                            },
                                        }]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    elif  (page=="2"):
        contents={
            "type": "bubble",    
            "size":  "giga",
            "header" :{
                "type": "box",
                "layout": "horizontal",
                "width":"100%",
                "backgroundColor": "#f1c40fF0",
                "contents":[
                    {
                        "type": "box",
                        "width":"33%", 
                        "layout": "horizontal",
                        "contents":[
                            {
                                "type": "image",
                                "align": "start",
                                "url": settings.SERVER_URL+"static/previous.png",  
                                "aspectMode":"cover",
                                "aspectRatio":"1:1",
                                "margin":"none",
                                "spacing":"none",
                                "size":"50px",
                                "action": {
                                    "type": "postback",
                                    "label": "上頁",
                                    "data":"action=ninjia&page=1"
                                },
                            }
                        ]
                    },
                    {
                        "type": "text",
                        "text": "教會連結",
                        "gravity": "center",
                        "align": "center",
                        "width":"33%", 
                        "size":"lg",
                        "weight":"bold", 
                        "color":"#FFFFFF",
                    },
                    {
                            "type": "box",
                            "width":"33%", 
                            "layout": "horizontal",
                            "contents":[
                                {
                                    "type": "image",
                                    "url": settings.SERVER_URL+"static/next.png",  
                                    "aspectMode":"cover",
                                    "aspectRatio":"1:1",
                                    "margin":"none",
                                    "spacing":"none",
                                    "align": "end",
                                    "size":"50px",
                                    "action": {
                                        "type": "postback",
                                        "label": "下頁",
                                        "data":"action=ninjia&page=3"
                                    },
                                }
                            ]
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "width":"100%",
                "margin":"sm",
                "spacing":"sm",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "width":"33%",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "contents":[{
                                        "type": "image",
                                            "url": settings.SERVER_URL+"static/menub_03.jpg",  
                                            "aspectMode":"cover",
                                            "aspectRatio":"1:1",
                                            "margin":"sm",
                                            "spacing":"sm",
                                            "action": {
                                                "type": "uri",
                                                "label": "禱告靈修",
                                                "uri": "https://m.youtube.com/playlist?list=PLW3vVgu_AOyrotwEYs9BORHfRjTY6rr0j"
                                                }
                                        }]
                                    }
                                ]
                            },
                            {   "type": "box",
                                "layout": "horizontal",
                                "width":"33%",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "contents":[{
                                        "type": "image",
                                            "url": settings.SERVER_URL+"static/menub_05.jpg",  
                                            "aspectMode":"cover",
                                            "aspectRatio":"1:1",
                                            "margin":"sm",
                                            "spacing":"sm",
                                            "action": {
                                                "type": "uri",
                                                "label": "線上主日",
                                                "uri": "https://m.youtube.com/playlist?list=PLW3vVgu_AOyrW3-uDNlGrjiH1VLUC1wAT"
                                            }
                                        }]
                                    }
                                ]
                            },
                            {   "type": "box",
                                "layout": "horizontal",
                                "width":"33%",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "contents":[{
                                        "type": "image",
                                            "url": settings.SERVER_URL+"static/menub_07.jpg",  
                                            "aspectMode":"cover",
                                            "aspectRatio":"1:1",
                                            "margin":"sm",
                                            "spacing":"sm",
                                            "action": {
                                                    "type": "uri",
                                                    "label": "奉獻資訊",
                                                    "uri": "https://docs.google.com/forms/d/e/1FAIpQLScg5B6rc2PJ72a6g6RYKvpcyEFQ6ak5-ygHl0xuO62y0tTjiQ/viewform?usp=send_form"
                                            },
                                        }]
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "width":"33%",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "contents":[{
                                        "type": "image",
                                            "url": settings.SERVER_URL+"static/menub_12.jpg",  
                                            "aspectMode":"cover",
                                            "aspectRatio":"1:1",
                                            "margin":"sm",
                                            "spacing":"sm",
                                            "action": {
                                                "type": "uri",
                                                "label": "我挺你",
                                                "uri": "https://wol.org.tw/wol/support/"
                                            },
                                        }]
                                    }
                                ]
                            },
                            {   "type": "box",
                                "layout": "horizontal",
                                "width":"33%",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "contents":[{
                                        "type": "image",
                                            "url": settings.SERVER_URL+"static/menub_13.jpg",  
                                            "aspectMode":"cover",
                                            "aspectRatio":"1:1",
                                            "margin":"sm",
                                            "spacing":"sm",
                                            "action": {
                                                "type": "postback",
                                                "label": "課程報名",
                                                "data":"action=register"
                                            },
                                        }]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    elif  (page=="3"):
      #  app.logger.info(contactid)
        groupdata = GroupOwner(contactid,psconn)    
        app.logger.info(groupdata)
        #for group in groupdata:
        #print(group.listid+","+group.listname+","+group.role)
        #if (group.role!="member"):
        #btnlabel=group.listname
        #    btndata ="action=getGroupMemberList&listid="+group.listid+"&cid="+ contactid 
        #    btnstyle="primary"
        #    btncolor="#4277bd"
        contents={
            "type": "bubble",
            "size":  "giga",
            "header" :{
                "type": "box",
                "layout": "horizontal",
                "width":"100%",
                "backgroundColor": "#f1c40fF0",
                "contents":[
                    {
                        "type": "box",
                        "width":"33%", 
                        "layout": "horizontal",
                        "contents":[
                            {
                                "type": "image",
                                "align": "start",
                                "url": settings.SERVER_URL+"static/previous.png",  
                                "aspectMode":"cover",
                                "aspectRatio":"1:1",
                                "margin":"none",
                                "spacing":"none",
                                "size":"50px",
                                "action": {
                                    "type": "postback",
                                    "label": "上頁",
                                    "data":"action=ninjia&page=2"
                                },
                            }
                        ]
                    },
                    {
                        "type": "text",
                        "text": "牧養",
                        "gravity": "center",
                        "align": "center",
                        "width":"33%", 
                        "size":"lg",
                        "weight":"bold", 
                        "color":"#FFFFFF",
                    },
                    {
                            "type": "box",
                            "width":"33%", 
                            "layout": "horizontal",
                            "contents":[
                                {
                                    "type": "text",
                                    "text": " ",
                                }
                            ]
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "width":"100%",
                "margin":"sm",
                "spacing":"sm",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "width":"33%",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "contents":[{
                                        "type": "image",
                                            "url":  settings.SERVER_URL+"static/menuc_03.jpg",  
                                            "aspectMode":"cover",
                                            "aspectRatio":"1:1",
                                            "margin":"sm",
                                            "spacing":"sm",
                                            "action": {
                                                "type":"postback",
                                                "label": "小組名冊",
                                                "data":"action=getManageGroup&cid="+contactid+"&subject=getGroupMemberList"
                                                }
                                        }]
                                    }
                                ]
                            },
                            {   "type": "box",
                                "layout": "horizontal",
                                "width":"33%",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "contents":[{
                                        "type": "image",
                                            "url":  settings.SERVER_URL+"static/menuc_05.jpg",  
                                            "aspectMode":"cover",
                                            "aspectRatio":"1:1",
                                            "margin":"sm",
                                            "spacing":"sm",
                                            "action": {
                                                "type": "postback",
                                                "label": "名冊順序",
                                                "data":"action=getManageGroup&cid="+contactid+"&subject=getGroupMemberListforMove"
                                            }
                                        }]
                                    }
                                ]
                            },
                            {   "type": "box",
                                "layout": "horizontal",
                                "width":"33%",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "contents":[{
                                        "type": "image",
                                            "url":  settings.SERVER_URL+"static/menuc_07.jpg",  
                                            "aspectMode":"cover",
                                            "aspectRatio":"1:1",
                                            "margin":"sm",
                                            "spacing":"sm",
                                            "action": {
                                                "type": "postback",
                                                "label": "主日出席",
                                                "data":"action=getManageGroup&cid="+contactid+"&subject=getWorshipReport"
                                            },
                                        }]
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "width":"33%",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "contents":[{
                                        "type": "image",
                                            "url":  settings.SERVER_URL+"static/menuc_12.jpg",  
                                            "aspectMode":"cover",
                                            "aspectRatio":"1:1",
                                            "margin":"sm",
                                            "spacing":"sm",
                                            "action": {
                                                "type": "postback",
                                                "label": "小組出席",
                                                "data":"action=getManageGroup&cid="+contactid+"&subject=getGroupReport"
                                            },
                                        }]
                                    }
                                ]
                            },
                            {   "type": "box",
                                "layout": "horizontal",
                                "width":"33%",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "contents":[{
                                        "type": "image",
                                            "url":  settings.SERVER_URL+"static/menuc_13.jpg",  
                                            "aspectMode":"cover",
                                            "aspectRatio":"1:1",
                                            "margin":"sm",
                                            "spacing":"sm",
                                            "action": {
                                                 "type": "postback",
                                                "label": "靈修天數",
                                                "data":"action=getManageGroup&cid="+contactid+"&subject=getPersonalWorshipReport"
                                            },
                                        }]
                                    }
                                ]
                            },
                             {   "type": "box",
                                "layout": "horizontal",
                                "width":"33%",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "contents":[{
                                        "type": "image",
                                            "url":  settings.SERVER_URL+"static/menuc_14.jpg",  
                                            "aspectMode":"cover",
                                            "aspectRatio":"1:1",
                                            "margin":"sm",
                                            "spacing":"sm",
                                            "action": {
                                                "type": "postback",
                                                "label": "代禱事項",
                                                "data":"action=getPrayListByOwner&cid="+contactid
                                            },
                                        }]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
 

    return contents
