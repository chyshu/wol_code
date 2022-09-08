# Create your views here.
from flask import  Flask
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
import datetime
import psycopg2

from django.views.decorators.csrf import csrf_exempt
from linebot.models import FlexSendMessage, BubbleContainer, ImageComponent
from linebot import LineBotApi, WebhookParser,WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage,JoinEvent,UnfollowEvent,FollowEvent,LeaveEvent,PostbackEvent,BeaconEvent,MemberJoinedEvent,MemberLeftEvent,AccountLinkEvent,ThingsEvent,ThingsEvent,SourceUser,SourceGroup,SourceRoom
from linebot.models import TemplateSendMessage, ButtonsTemplate, DatetimePickerTemplateAction,QuickReply,QuickReplyButton, MessageAction
import json
from .utils import next_weekday,getConnection,get_contactbase,get_contactbaseByContactId,current_weekday,GroupOwner
from .classes import Member,Family
from logging.config import dictConfig
from .menus import get_menu,getMenuV2
from .binding import getBindingMenu,getBindingData,getFamily
from .worship import getWorshipMenu,getWorshipDate,getWorshipMenuWithClose,getMyGroupListMenu,getGroupMemberWorshipDate,getGroupMemberWorshipList
from .groupship import getGroupListMenu,getGroupDateDialog,getGroupDateList,getGroupDatePersonal,getGroupReport,getGroupMemberList,GroupMemberMoveDown
from .groupship import GroupMemberMoveUp,GroupMemberDisplay,getGroupMemberListforMove,getWorshipReport,getPersonalWorshipReport,getManageGroup
from .personalworship import selectPersonalWorshipDate,PersonalWorshipMenu
from .prayforme import getPrayforMeMenu,getPrayforMeListMenu,getPrayforMeByNo,getPrayListByOwner,getPrayItemByOwner,getPrayWeekByOwner

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '%(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

#import logging

app = Flask(__name__)

#LINE_CHANNEL_ACCESS_TOKEN='JsxDdLf5cuphuUVuoGvujchNKUIXJ8EtPC8t9A2ScfS9CgtMNxshsmelb/DE6SxTm5k5M7W4ZEkwEHM51pAyusK9r7FN1JQJJ83xBs0efkt2gZ9JygTkh4Zpwg4pc48tsSHQMKc3uXwwsNankROK4wdB04t89/1O/w1cDnyilFU='

#LINE_CHANNEL_SECRET='6c50569bec91e809674daf78228a4689'

#LINE_CHANNEL_ACCESS_TOKEN='JsxDdLf5cuphuUVuoGvujchNKUIXJ8EtPC8t9A2ScfS9CgtMNxshsmelb/DE6SxTm5k5M7W4ZEkwEHM51pAyusK9r7FN1JQJJ83xBs0efkt2gZ9JygTkh4Zpwg4pc48tsSHQMKc3uXwwsNankROK4wdB04t89/1O/w1cDnyilFU='

#LINE_CHANNEL_SECRET='6c50569bec91e809674daf78228a4689'

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

#logger = logging.getLogger('djproject')

app.logger.info(settings.LINE_CHANNEL_SECRET)

#@app.route("/webhook", methods=['POST'])
@csrf_exempt
def webhook(request):
	app.logger.info("webhook")
	#app.logger.info("234" if request.method=='POST' else "123")
	message=[]
	if request.method == 'POST':
		today   = datetime.datetime.now()
		app.logger.info("=webook=="+today.strftime('%m-%d %H%M%s'))
		signature = request.META['HTTP_X_LINE_SIGNATURE']
		#app.logger.info(signature )
		#app.logger.info( request.body.decode("utf-8")  )
		body = request.body.decode('utf-8')
		#body = request.get_data(as_text=True)
		app.logger.info(body)
		try:
			events = parser.parse(body, signature)
#			app.logger.info("11111111111")
		except InvalidSignatureError as e1:
			app.logger.info("e1 " )
			return HttpResponseForbidden()
		except  LineBotApiError :
			app.logger.info("e2 ")
			return HttpResponseBadRequest()
		#today   = datetime.datetime.now()
		#app.logger.info(len(events))

		try:
			conn = psycopg2.connect(database="postgres", user="qhfvjzcqqgbykn", password="eaa367e02a61a4dac21029cc54684143e35380c47dd8f2f69486dfdc7d2f85cd", host="163.22.27.130", port="5432")
			conn.autocommit = True

			for event in events:
				if isinstance(event, MessageEvent):
					#app.logger.info(event)
					if  event.message.type=="text":
						mtext=event.message.text
						message=[]
						app.logger.info(event)
						member = get_contactbase(event.source.user_id,conn)
						app.logger.info(event.source.user_id)
						if(member.contactname==None):
							message.append( TextSendMessage( text="請先綁定LINE帳號資料"))
							line_bot_api.reply_message(  event.reply_token, message)
						else:
							app.logger.info(member.display_name)
							displayname=member.contactname if  member.contactname!=None else member.display_name
							if(displayname==None):
								displayname=""
							if mtext.replace(" ","")=="忍者" or mtext.replace(" ","").lower() =="ninjia" :
								message.append( FlexSendMessage("選單",contents=  getMenuV2(member.contactid, "1" ,conn )))
								line_bot_api.reply_message(   event.reply_token, message)
							elif mtext.lower()=="wol" or mtext=="回報" or mtext=="小天使" or mtext=="Cherub"  or mtext=="東東"   or mtext=="咚咚"  :
								message.append( FlexSendMessage("系統選單",      contents= getMenuV2(member.contactid,"1" ,conn )  ))
								line_bot_api.reply_message(event.reply_token,message)

							elif mtext=="主日回報":
								message.append( FlexSendMessage("主日回報",contents= getWorshipMenu( member.contactid ,displayname,conn) ))
								line_bot_api.reply_message(   event.reply_token,   message)							#else:
							elif  mtext=="小組回報":
								message.append( FlexSendMessage("小組回報",contents= getGroupListMenu( member.contactid ,displayname,conn) ))                  
								line_bot_api.reply_message( event.reply_token,   message) 
							elif  mtext=="靈修" or mtext=="靈修回報" :
								message.append( FlexSendMessage("靈修回報",contents= PersonalWorshipMenu(  member.contactid,displayname ,conn )))
								line_bot_api.reply_message(   event.reply_token,   message)
							elif  mtext.startswith("綁定") or   mtext.startswith("綁 定") :
								message.append(  FlexSendMessage("綁定資料",contents= getBindingData( event.source.user_id ,conn  ) ))
								line_bot_api.reply_message(     event.reply_token, message)
							# no a command do not response app.logger.info("non command")
				elif isinstance(event, JoinEvent):
					app.logger.info( "Join user "+event.source.user_id  )
					member = get_contactbase(event.source.user_id,conn)
					if member.contactid==None:
						with conn.cursor() as curs:
							curs.execute("""select contactid,user_id,displayname,sid from Id2contact where user_id=%s""" ,[ event.source.user_id  ])
							row = curs.fetchone()
							if row==None:
					                        #  第一次加入ID2CONTACT 找不到資料
								pycursor.execute("""insert into id2contact (groupId, user_id,displayname,contactid) values (%s,%s,%s,%s) """ ,[ "", event.source.user_id, "" , ""]) 
							profile= getLineProfile(event.source.user_id )
							if profile:
								curs.execute("""update id2contact set displayname=%s where user_id =%s """ ,[  profile.display_name , event.source.user_id   ])
								curs.execute("""select contactid,LastName from contactbase where new_line_displayname=%s""" ,[ profile.display_name ])
								row = curs.fetchone()
								if  row :
									contactid=str(row[0])
									curs.execute("""update id2contact set contactid=%s  where user_id=%s""" , [ contactid, event.source.user_id ] )
									member = get_contactbase(event.source.user_id,conn)
								else:
									message.append(TextSendMessage(  text="請先綁定LINE帳號資料"))
									message.append(  FlexSendMessage("綁定資料",contents= 
                                                                        	       getBindingData( event.source.user_id ,conn  ) ))
								line_bot_api.reply_message(     event.reply_token, message)
							else:
								message.append(  TextSendMessage(  text="請先綁定LINE帳號資料")     )
								message.append(  FlexSendMessage("綁定資料",contents= getBindingData( event.source.user_id ,conn  ) ))
								line_bot_api.reply_message(     event.reply_token, message)


				elif isinstance(event, LeaveEvent):
					if isinstance( event.source,SourceUser ):
						app.logger.info( "Leave  user "+event.source.user_id  )
					elif  isinstance(event.source, SourceGroup):
						app.logger.info( "Leave Group "+event.source.group_id)
					else:
						app.logger.info( "Leave room "+event.source.room_id  )
				elif isinstance(event, PostbackEvent):
					app.logger.info("posback")
					member = get_contactbase(event.source.user_id,conn)
					# app.logger.info( '=====================================' )
					displayname=member.contactname if  member.contactname!=None else member.display_name
					my_dict = {"action":[],"cid":[],"worshipdate":[],"session":[],"listid":[],"type":{} ,"listmemberid":{} ,"opid":[]   ,"times":[]  ,"prayid":[] ,"friendid":[] ,"sender":[] ,
							"newRichMenuAliasId":[],"disp_order":[] ,"disp_yn":[], "page":[],"subject":[],"goback":[],"ownerid":[]
					}
					#app.logger.info(event.postback.data)
					for item in event.postback.data.split('&'):
						value =item.split("=")
						if value:
							#print(value[0]+","+ value[1] )
							my_dict[value[0]].append(value[1])
					if event.postback.params:
						p = event.postback.params  
						for p in  event.postback.params:
							if p=="date":
								my_dict["worshipdate"].append( event.postback.params[p])
							elif p=="newRichMenuAliasId":
								my_dict["newRichMenuAliasId"].append( event.postback.params[p])
					if  my_dict['worshipdate']:
						worship_date = datetime.datetime.strptime(my_dict['worshipdate'] [0] , '%Y-%m-%d')
					app.logger.info(my_dict["action"][0])
					if(my_dict["action"][0].lower() =="cherub"):
						page =  ( "1" if len(my_dict["page"])==0 else  my_dict["page"][0])
						contents= getMenuV2(member.contactid, page ,conn )
						message.append( FlexSendMessage("系統選單",   contents     ) )
						line_bot_api.reply_message(event.reply_token,message)
					elif(my_dict["action"][0]=="ninjia"):
						page =  ( "1" if len(my_dict["page"])==0 else  my_dict["page"][0])
						contents= getMenuV2(member.contactid, page ,conn )
						message.append( FlexSendMessage("系統選單",   contents     ) )
						line_bot_api.reply_message(event.reply_token,message)
					elif(my_dict["action"][0]=="Praylist"):
						message.append( FlexSendMessage("代禱事項",contents= getPrayforMeListMenu( member.contactid ,displayname,conn) ))   
						line_bot_api.reply_message(     event.reply_token, message)	
					elif (my_dict["action"][0]=="bindingMenu"): 
						app.logger.info(member.contactid )
						member =get_contactbaseByContactId( member.contactid,conn )
						displayname=member.contactname if  member.contactname!=None else member.display_name
						message.append( FlexSendMessage("綁定資料",contents= getBindingMenu(member.contactid,displayname, event.source.user_id ,conn  ) )) 
						line_bot_api.reply_message(     event.reply_token, message)
					elif (my_dict["action"][0]=="bindingme"): 
						message.append(  FlexSendMessage("綁定資料",contents= getBindingData( event.source.user_id,conn   ) ))
						line_bot_api.reply_message(     event.reply_token, message)
					elif (my_dict["action"][0]=="bindingName"): 
						with  conn.cursor as curs:
							curs.execute("""update  Id2contact set isediting='N' where user_id=%s """ , [   event.source.user_id    ])
							curs.execute("""select  sid,user_id,input_name,isediting from Id2contact where user_id=%s """ , [   event.source.user_id    ])
							row = curs.fetchone()
							if row:
								curs.execute("""update  Id2contact set isediting='Y' where sid=%s """ , [  row[0]   ])
						message.append(   TextSendMessage(   text="輸入綁定:(你要重新綁定的姓名)" )  )
						line_bot_api.reply_message(     event.reply_token, message)

					elif (my_dict["action"][0]=="myfamily"): 
						message.append(  FlexSendMessage("綁定資料",contents= getFamily( event.source.user_id ,conn  ) ))
						line_bot_api.reply_message(     event.reply_token, message)  
					elif (my_dict["action"][0]=="removeFriend"): 
#						app.logger.info(event.source.user_id  )
						with  conn.cursor() as  curs:
							curs.execute("""select *  from id2contact where user_id=%s """ , [   event.source.user_id    ])                    
							Id2contact = curs.fetchone()    
#							app.logger.info( event.source.user_id )
							if Id2contact:
								curs.execute("""delete  from closegroup  where contactid=%s and familyid=%s   """ ,[  member.contactid,   my_dict["friendid"][0] ])
								message.append(   TextSendMessage(   text="移除成功" )  )
								message.append(  FlexSendMessage("綁定資料",contents= getFamily( event.source.user_id,conn   ) ))
							else:
								message.append(   TextSendMessage(   text="請先綁定帳號" )  )
						line_bot_api.reply_message(     event.reply_token, message)  

					elif (my_dict["action"][0]=="PersonalWorshipMenu"):
						message.append( FlexSendMessage("靈修回報",contents= PersonalWorshipMenu(  member.contactid,displayname,conn  )))
						line_bot_api.reply_message(   event.reply_token,   message)
					elif (my_dict["action"][0]=="selectPersonalWorshipDate"):
						member =get_contactbaseByContactId(my_dict["cid"][0] ,conn )
						displayname=member.contactname if  member.contactname!=None else member.display_name
						message.append( FlexSendMessage("靈修回報",contents= selectPersonalWorshipDate( member.contactid, my_dict["worshipdate"][0] , displayname,conn ) ) )
						line_bot_api.reply_message(     event.reply_token,    message) 

					elif (my_dict["action"][0]=="setPersonalWorshipDateTimes"):
						member =get_contactbaseByContactId(my_dict["cid"][0] ,conn)
#						app.logger.info(member)
						displayname=member.contactname if  member.contactname!=None else member.display_name
						if len(my_dict["times"])>0:
							#app.logger.info( len(my_dict['times']) )
							with conn.cursor() as curs:
							#	app.logger.info(curs)
								curs.execute("""select sid,contactid,worship_date,worship_times from personalworship where contactid=%s and worship_date=%s and del_flag='N' """ ,   [ my_dict["cid"][0] ,  datetime.datetime.strptime(my_dict['worshipdate'] [0] , '%Y-%m-%d')  ])
								personalworship = curs.fetchone()
							#	app.logger.info(my_dict)
								if personalworship:
									curs.execute("""update personalworship set  worship_times=%s , del_flag='N' ,upd_date=%s,upd_no=%s  where sid=%s """ , [ my_dict["times"][0] ,    datetime.datetime.now(),  my_dict["cid"][0]  ,personalworship[0]  ])
								else:
									curs.execute("""insert into  personalworship (worship_date,contactid,user_id,worship_times,del_flag, crt_no,crt_date ) values (%s,%s,%s,%s,'N',%s,%s) """ ,
                                				       [     datetime.datetime.strptime(my_dict['worshipdate'] [0] , '%Y-%m-%d')  , my_dict["cid"][0] , member.user_id   , my_dict["times"][0] ,  my_dict["cid"][0] , datetime.datetime.now()  ])
							message.append( FlexSendMessage("靈修回報",contents= PersonalWorshipMenu( member.contactid,   displayname,conn ) ) )
							line_bot_api.reply_message( event.reply_token,   message) 
					elif (my_dict["action"][0]=="CancelPersonalWorshipDateTimes"):
						member =get_contactbaseByContactId(my_dict["cid"][0] ,conn  )
						displayname=member.contactname if  member.contactname!=None else member.display_name
						if len(my_dict["worshipdate"])>0:
							with conn.cursor() as curs:
								curs.execute("""select sid,contactid,worship_date,worship_times from personalworship where contactid=%s and worship_date=%s and del_flag='N' """ ,
				                                       [ my_dict["cid"][0] ,  my_dict["worshipdate"][0]  ])
								personalworship_row =curs.fetchone()
								if personalworship_row:
									curs.execute("""update personalworship set  worship_times=0 , del_flag='N' ,upd_date=%s,upd_no=%s  where sid=%s """ ,
				                                       		[  datetime.datetime.now(),  my_dict["cid"][0]  ,personalworship_row[0]  ])
									message.append( FlexSendMessage("靈修回報",contents= PersonalWorshipMenu( member.contactid,   displayname ,conn ) ) )
								else:
									message.append(   TextSendMessage(  text="取消靈修日期參數錯誤"  )   )
							line_bot_api.reply_message( event.reply_token,   message) 
					elif(my_dict["action"][0]=="praymenu"):
						message.append(
			                           FlexSendMessage("代禱",contents= getPrayforMeMenu( member.contactid , displayname,conn ))
				                )
						line_bot_api.reply_message(     event.reply_token, message)
					elif(my_dict["action"][0]=="prayitem"):

						message.append(
			                           FlexSendMessage("代禱",contents= getPrayforMeByNo( member.contactid , displayname,my_dict["prayid"][0] ,conn ))
				                )
						line_bot_api.reply_message(     event.reply_token, message)

					elif(my_dict["action"][0]=="Praylist"):
						message.append( FlexSendMessage("代禱事項",contents= getPrayforMeListMenu( member.contactid ,displayname ,conn ) ))   
						line_bot_api.reply_message(     event.reply_token, message)
					elif(my_dict["action"][0]=="createPray"):

						# prayid=today.strftime("%y%m%d%H%M%S%f") 
						n=1
						with conn.cursor() as curs:
						   curs.execute(""" select max(prayid) as sid from prayforme where contactid=%s """, [ member.contactid  ])
						   row = curs.fetchone() 
						   if row:                    
						      if row[0]!=None:
						         strnum=row[0]
						         n=int(strnum)+1
						   prayid=f'{n:04}'
						   curs.execute("""select prayid,tdate,contactid,description  from prayforme where contactid=%s  and del_flag='N' and isediting is null """ ,   [ member.contactid] )
						   row = curs.fetchone()
						   if row:
						      prayid=str(row[0])
						   else:
						      curs.execute("""insert into prayforme( prayid,tdate,contactid,description,isediting,isclose,del_flag,crt_no) values (%s,%s,%s,%s,'N','','N',%s )""" ,
						                     [ prayid , today.strftime("%Y-%m-%d") , member.contactid,None , member.contactid   ])
						   message.append(
					                    TextSendMessage(text=displayname+"建立代禱編號:"+prayid+"\n"+"請進入代禱事項查詢" )
					                )
						   message.append( FlexSendMessage("代禱事項",contents= getPrayforMeListMenu( member.contactid ,displayname,conn ) ))   
						   line_bot_api.reply_message(     event.reply_token, message)

					elif(my_dict["action"][0]=="PrayEOD"):
						with conn.cursor() as curs:
						   curs.execute("""select prayid,tdate,contactid,description  from prayforme where contactid=%s  and del_flag='N' and sid=%s """ ,
                                                   [ member.contactid, int( my_dict["prayid"][0])  ])
						   row = curs.fetchone() 
						   strMessage=""
						   if row: 
						      curs.execute("""update prayforme set isclose='Y',upd_date=%s where contactid=%s  and sid=%s   """ ,[datetime.datetime.now(),  member.contactid ,  my_dict["prayid"][0]   ])
						      message.append( TextSendMessage(text="代禱事項編號"+ row[0]+ "已經結案"  ))
						   message.append( FlexSendMessage("代禱事項",contents= getPrayforMeListMenu( member.contactid ,displayname,conn) )   )
						   line_bot_api.reply_message(     event.reply_token, message)

					elif(my_dict["action"][0]=="worshipMenu"): 
					# 顯示主日回報MENU
						 message.append( FlexSendMessage("主日回報",contents= getWorshipMenu( member.contactid , displayname,conn) ))
						 line_bot_api.reply_message(     event.reply_token, message)
					elif(my_dict["action"][0]=="groupshipMenu"):
					# 顯示小組回報MENU
						message.append( FlexSendMessage("小組回報",contents= getGroupListMenu( member.contactid ,displayname,conn) ))
						line_bot_api.reply_message( event.reply_token,   message) 

					elif (my_dict["action"][0]=="selectWorshipDate"):
					    member =get_contactbaseByContactId(my_dict["cid"][0] ,conn )
					    displayname=member.contactname if  member.contactname!=None else member.display_name
					    with conn.cursor() as curs:
					        if my_dict["sender"][0]=="close":
					            curs.execute(""" select closegroup.contactid,closegroup.familyid,contactbase.lastname,id2contact.user_id from closegroup  left outer join contactbase on contactbase.contactid=closegroup.familyid   
                                                                     left outer join id2contact on id2contact.contactid=closegroup.familyid  where closegroup.contactid=%s  """ , [my_dict["cid"][0] ] )
					            for closegroup in  curs.fetchall():
					                LastName="" 
					                if closegroup[2]!=None:
					                   LastName=str(closegroup[2])
					                   displayname=displayname+","+ LastName
					    message.append( FlexSendMessage("主日回報",contents=  getWorshipDate( member.contactid,displayname ,  my_dict["worshipdate"][0]  ,  my_dict["sender"][0] ,conn   ) ))
					    line_bot_api.reply_message(     event.reply_token, message)

					elif (my_dict["action"][0]=="setWorshipDate"):    
					# 登記主日 
					    member =get_contactbaseByContactId(my_dict["cid"][0],conn )
					    displayname=member.contactname if  member.contactname!=None else member.display_name
					    with conn.cursor() as curs:
					       curs.execute("""select contactid,user_id,worship_date,session  from worship where contactid=%s and worship_date = %s and session=%s  and del_flag='N' """ ,
                                                       [ my_dict["cid"][0],   my_dict["worshipdate"][0]  ,   my_dict["session"][0]    ])
					       row = curs.fetchone()
					       if  row:
					     	    # message.append( TextSendMessage(  text=displayname+"出席"+worship_date.strftime('%Y-%m-%d')+"," + str(row[3])+ "主日" )  )                        
					            displayname=displayname
					       else:
					            curs.execute("""insert into worship ( contactid,user_id,worship_date,session,crt_no,crt_date,del_flag) values (%s ,%s,%s,%s,%s,%s,'N') """ ,
                                                          [ member.contactid ,  member.user_id , worship_date ,   my_dict["session"][0]  , member.contactid , datetime.datetime.now() ])
					            displayname=displayname

					         # message.append( TextSendMessage( text=displayname+"出席"+worship_date.strftime('%Y-%m-%d')  +","+ my_dict["session"][0] + "主日" )  )

					       if my_dict["sender"][0]=="close":
					          curs.execute(""" select closegroup.contactid,closegroup.familyid,contactbase.lastname,id2contact.user_id from closegroup  left outer join contactbase on contactbase.contactid=closegroup.familyid   
                                                              left outer join id2contact on id2contact.contactid=closegroup.familyid  where closegroup.contactid=%s  """ , [my_dict["cid"][0] ] )
					          for closegroup in  curs.fetchall():
					            LastName="" 
					            if closegroup[2]!=None:
					               LastName=str(closegroup[2])
					            curs.execute("""select contactid,user_id,worship_date,session  from worship where contactid=%s and worship_date = %s and session=%s  and del_flag='N' """ ,
					                  [ closegroup[1],   my_dict["worshipdate"][0]  ,   my_dict["session"][0]    ])
					            row = pycursor.fetchone()
					            if  row:
					              #message.append( TextSendMessage(  text=LastName+"出席"+worship_date.strftime('%Y-%m-%d')+"," + str(row[3])+ "主日" )  )
					              displayname=displayname+","+ LastName
					            else:                            
					              curs.execute("""insert into worship ( contactid,user_id,worship_date,session,crt_no,crt_date,del_flag) values (%s ,%s,%s,%s,%s,%s,'N') """ ,
                                                          [  closegroup[1] ,  closegroup[3], worship_date ,   my_dict["session"][0]  , member.contactid , datetime.datetime.now() ])
					              displayname=displayname+","+ LastName

					       message.append( TextSendMessage( text=displayname+"登記"+worship_date.strftime('%Y-%m-%d')  +","+ my_dict["session"][0] + "主日" )  ) 
					       message.append( FlexSendMessage("主日回報",contents=  getWorshipDate( member.contactid,displayname ,  my_dict["worshipdate"][0]  ,  my_dict["sender"][0] ,conn  ) ))
					       line_bot_api.reply_message(     event.reply_token, message)

					elif (my_dict["action"][0]=="CacnelWorshipDate"): 
					# 取消主日
					     member =get_contactbaseByContactId(my_dict["cid"][0],conn )
					     displayname=member.contactname if  member.contactname!=None else member.display_name
					     with conn.cursor() as curs:
					         curs.execute("""select sid,contactid,worship_date,session  from worship where contactid=%s and worship_date = %s and session=%s and del_flag='N'  """ ,
			                            [ my_dict["cid"][0],   my_dict["worshipdate"][0]  ,   my_dict["session"][0]    ])
					         worshipdata = curs.fetchone()
					         if worshipdata:
					            curs.execute("""update worship set del_flag='Y' ,upd_no=%s,upd_date=%s where sid=%s and contactid=%s and worship_date=%s and session =%s """ ,
					             [  member.contactid , datetime.datetime.now() ,worshipdata[0], worshipdata[1], worshipdata[2].strftime('%Y-%m-%d'), worshipdata[3]  ])
					         if my_dict["sender"][0]=="close":
					            curs.execute(""" select closegroup.contactid,closegroup.familyid,contactbase.lastname,id2contact.user_id from closegroup  left outer join contactbase on contactbase.contactid=closegroup.familyid   
					                left outer join id2contact on id2contact.contactid=closegroup.familyid  where closegroup.contactid=%s  """ , [my_dict["cid"][0] ] )
					            closegroup_rows= curs.fetchall()
					            for closegroup in  closegroup_rows:
					               LastName="" 
					               if closegroup[2]!=None:
					                  LastName=str(closegroup[2])
					               curs.execute("""select sid,contactid,worship_date,session  from worship where contactid=%s and worship_date = %s and session=%s and del_flag='N'  """ ,
					                            [ closegroup[1],   my_dict["worshipdate"][0]  ,   my_dict["session"][0]    ])
					               worshipdata = curs.fetchone()
					               if  worshipdata:
					                   curs.execute("""update worship set del_flag='Y' ,upd_no=%s,upd_date=%s where sid=%s and contactid=%s and worship_date=%s and session =%s """ ,
					                          [  member.contactid , datetime.datetime.now() ,worshipdata[0], worshipdata[1], worshipdata[2].strftime('%Y-%m-%d'), worshipdata[3]  ])
					                   displayname=displayname+","+ LastName
					     message.append( TextSendMessage( text=displayname+"取消"+my_dict["worshipdate"][0]   +","+ my_dict["session"][0] + "出席登記" )     )
					     message.append( FlexSendMessage("主日回報",contents=  getWorshipDate( member.contactid,displayname ,  my_dict["worshipdate"][0]   ,  my_dict["sender"][0] ,conn  ) ))
					     line_bot_api.reply_message(     event.reply_token, message)

					elif(my_dict["action"][0]=="worship_groupsmenu"):
			 		# 顯示主日回報-小組MENU 
					    message.append( FlexSendMessage("小組主日回報",
                                                  contents= getMyGroupListMenu(conn, member.contactid , displayname,next_action="worship_groupsmenu_selectdate"  ) ))
					    line_bot_api.reply_message(     event.reply_token, message)

					elif(my_dict["action"][0]=="closeworship"):
					    member =get_contactbaseByContactId(my_dict["cid"][0] ,conn )
					    displayname=member.contactname if  member.contactname!=None else member.display_name
					    with conn.cursor() as  curs:
					       curs.execute(""" select closegroup.contactid,closegroup.familyid,contactbase.lastname,id2contact.user_id from closegroup  left outer join contactbase on contactbase.contactid=closegroup.familyid   
                                                  left outer join id2contact on id2contact.contactid=closegroup.familyid  where closegroup.contactid=%s  """ , [my_dict["cid"][0] ] )
					       for closegroup in  curs.fetchall(): 
					         LastName="" 
					         if closegroup[2]!=None:   
					             LastName=str(closegroup[2])
					             displayname=displayname+","+ LastName  
					       message.append( FlexSendMessage("主日回報",contents= getWorshipMenuWithClose( member.contactid ,displayname ,conn ) ))                  
					       line_bot_api.reply_message(     event.reply_token, message)

					elif (my_dict["action"][0]=="selectgroup"):
					   member =get_contactbaseByContactId(my_dict["cid"][0] ,conn )
					   displayname=member.contactname if  member.contactname!=None else member.display_name
					   message.append( FlexSendMessage("小組回報",contents= getGroupDateDialog(member.contactid, displayname, my_dict["listid"][0] ,my_dict["sender"][0] ,conn   )  ) )
					   line_bot_api.reply_message(  event.reply_token,   message)  
					elif (my_dict["action"][0]=="selectgroupdate"):
					   member =get_contactbaseByContactId(my_dict["cid"][0],conn )
					   if my_dict["sender"][0]=="personal":
					       message.append( FlexSendMessage("小組回報",contents= getGroupDatePersonal(member.contactid,displayname ,my_dict["listid"][0] , my_dict['worshipdate'] [0] ,my_dict["sender"][0],conn  ) )) 
					   else:
					       message.append( FlexSendMessage("小組回報",contents= getGroupDateList(member.contactid,displayname ,my_dict["listid"][0] , my_dict['worshipdate'] [0] ,my_dict["sender"][0],conn  ) ))
					   line_bot_api.reply_message(  event.reply_token,   message)  

					elif (my_dict["action"][0]=="setGroupDate"):
					# 登記小組出席
					   teamMember =get_contactbaseByContactId(my_dict["cid"][0] ,conn )
					   displayname=teamMember.contactname if  teamMember.contactname!=None else teamMember.display_name
					   with conn.cursor() as curs:
					        curs.execute("""select listbase.ListId,listbase.listName , group_place, group_time
					                       from   listbase     where ListId=%s   """ ,[ my_dict["listid"][0]  ])
					        listName=""
					        row = curs.fetchone()
					        if row:
					          listName=row[1]
					        curs.execute("""select contactid,listid,worship_date  from groupship where contactid=%s and worship_date = %s and listid=%s and del_flag='N' """ ,
					                   [ my_dict["cid"][0],   my_dict["worshipdate"][0]  ,   my_dict["listid"][0]    ])
					        row = curs.fetchone()
					        if  row:
					            message.append(  TextSendMessage(
					                         text=displayname+"出席"+worship_date.strftime('%y%m%d')+"," +  listName + "聚會" )   )
					        else:
					            curs.execute("""insert into groupship (  contactid, listid, worship_date, crt_no, crt_date, del_flag) values (%s ,%s,%s,%s,%s,'N') """ ,
                                                              [ my_dict["cid"][0],  my_dict["listid"][0]  , worship_date ,   my_dict["opid"][0]  , datetime.datetime.now() ])
					            message.append(  TextSendMessage(
					                         text=displayname+"出席"+worship_date.strftime('%Y%m%d')  +","+ listName + "聚會" )     )
					        if my_dict["sender"][0]=="personal":
					            message.append( FlexSendMessage("小組回報",contents= getGroupDatePersonal(member.contactid,displayname ,my_dict["listid"][0] , my_dict['worshipdate'] [0] ,my_dict["sender"][0],conn  ) ))
					        else:
					            message.append( FlexSendMessage("小組回報",contents= getGroupDateList(member.contactid,displayname ,my_dict["listid"][0] , my_dict['worshipdate'] [0] ,my_dict["sender"][0],conn ) ))
					   line_bot_api.reply_message(     event.reply_token, message)

					elif (my_dict["action"][0]=="CancelGroupDate"): 
					   # 取消小組出席                    
					   teamMember =get_contactbaseByContactId(my_dict["cid"][0],conn )
					   displayname=teamMember.contactname if  teamMember.contactname!=None else teamMember.display_name
					   with conn.cursor() as curs:
					      curs.execute("""select listbase.ListId,listbase.listName , group_place, group_time
					          from   listbase     where ListId=%s   """ ,[ my_dict["listid"][0]  ])
					      listName=""
					      row = curs.fetchone()
					      if row:
					         listName=row[1]
					      curs.execute("""select sid,contactid,worship_date,listid  from groupship where contactid=%s and worship_date = %s and listid=%s and del_flag='N'  """ ,
					         [ my_dict["cid"][0],   my_dict["worshipdate"][0]   ,   my_dict["listid"][0]    ])
					      rows = curs.fetchall()
					      for worshipdata in rows:
					          curs.execute("""update groupship set del_flag='Y' ,upd_no=%s,upd_date=%s where sid=%s  and listid =%s """ ,
                                        		 [  my_dict["cid"][0], datetime.datetime.now() ,worshipdata[0],   worshipdata[3]  ])
					      message.append(
					             TextSendMessage( text=displayname+"取消"+my_dict["worshipdate"][0]   +","+  listName +"聚會出席" )  )
					      if my_dict["sender"][0]=="personal":
					         message.append( FlexSendMessage("小組回報",contents= getGroupDatePersonal(member.contactid,displayname ,my_dict["listid"][0] , my_dict['worshipdate'] [0] ,my_dict["sender"][0],conn  ) )) 
					      else:
					         message.append( FlexSendMessage("小組回報",contents= getGroupDateList(member.contactid,displayname ,my_dict["listid"][0] , my_dict['worshipdate'] [0] ,my_dict["sender"][0],conn ) ))
					      line_bot_api.reply_message(     event.reply_token, message)

					elif(my_dict["action"][0]=="getManageGroup"):
					     groupdata = GroupOwner(member.contactid,conn)
					     app.logger.info(len(groupdata))
					     if(my_dict["subject"][0]=="getGroupMemberList"):
					         if len(groupdata)==1 :
					            message.append( FlexSendMessage("小組",contents= getGroupMemberList(  member.contactid , groupdata[0].listid ,"menu3" ,conn  ) ))    
					         else:
					            message.append( FlexSendMessage("小組",contents= getManageGroup( member.contactid,my_dict["subject"][0],conn ) ))
					     elif (my_dict["subject"][0]=="getGroupMemberListforMove"):
					         if len(groupdata)==1 :
					            message.append( FlexSendMessage("小組",contents= getGroupMemberListforMove(  member.contactid , groupdata[0].listid ,"menu3" ,conn  ) ))    
					         else:
					            message.append( FlexSendMessage("小組",contents= getManageGroup( member.contactid,my_dict["subject"][0],conn  ) ))
					     elif (my_dict["subject"][0]=="getWorshipReport"):
					         if len(groupdata)==1 :
					            message.append( FlexSendMessage("小組",contents= getWorshipReport(  member.contactid , groupdata[0].listid ,"menu3",conn  ) ))    
					         else:
					            message.append( FlexSendMessage("小組",contents= getManageGroup( member.contactid,my_dict["subject"][0],conn ) ))
					     elif (my_dict["subject"][0]=="getGroupReport"):
					         if len(groupdata)==1 :
					            message.append( FlexSendMessage("小組",contents= getGroupReport(  member.contactid , groupdata[0].listid ,"menu3",conn  ) ))    
					         else:
					            message.append( FlexSendMessage("小組",contents= getManageGroup( member.contactid,my_dict["subject"][0],conn ) ))
					     elif (my_dict["subject"][0]=="getPersonalWorshipReport"):
					        if len(groupdata)==1 :
				                   message.append( FlexSendMessage("小組",contents= getPersonalWorshipReport(  member.contactid , groupdata[0].listid ,"menu3",conn  ) ))    
					        else:
					           message.append( FlexSendMessage("小組",contents= getManageGroup( member.contactid,my_dict["subject"][0],conn ) ))
					     line_bot_api.reply_message( event.reply_token,   message) 
					elif(my_dict["action"][0]=="getGroupMemberList"):
					     message.append( FlexSendMessage("小組名單",contents= getGroupMemberList( member.contactid,my_dict["listid"][0],None,conn ) ))
					     line_bot_api.reply_message( event.reply_token,   message) 
					elif(my_dict["action"][0]=="getGroupMemberListforMove"):
					     message.append( FlexSendMessage("小組名單順序",contents= getGroupMemberListforMove(member.contactid ,my_dict["listid"][0] , ( None if len( my_dict["sender"])==0 else  my_dict["sender"][0] ), conn  ) ))
					     line_bot_api.reply_message( event.reply_token,   message) 
					elif(my_dict["action"][0]=="movedown"):
					     GroupMemberMoveDown(my_dict,conn)
					     message.append( FlexSendMessage("小組名單順序",contents= getGroupMemberListforMove( my_dict["cid"][0],my_dict["listid"][0] , ( None if len( my_dict["sender"])==0 else  my_dict["sender"][0]  ),conn    ) ))
					     line_bot_api.reply_message( event.reply_token,   message) 
					elif(my_dict["action"][0]=="moveup"):
					     GroupMemberMoveUp(my_dict,conn)
					     message.append( FlexSendMessage("小組名單順序",contents= getGroupMemberListforMove( my_dict["cid"][0],my_dict["listid"][0] ,  ( None if len( my_dict["sender"])==0 else  my_dict["sender"][0] ), conn   ) ))
					     line_bot_api.reply_message( event.reply_token,   message) 
					elif(my_dict["action"][0]=="disp_no"):
					     GroupMemberDisplay(my_dict,member.contactid ,conn )
					     message.append( FlexSendMessage("小組回報",contents= getGroupMemberList( my_dict["cid"][0],my_dict["listid"][0],None,conn ) ))
					     line_bot_api.reply_message( event.reply_token,   message) 
					elif(my_dict["action"][0]=="disp_yes"):
					     GroupMemberDisplay(my_dict,member.contactid ,conn )
					     message.append( FlexSendMessage("小組回報",contents= getGroupMemberList( my_dict["cid"][0],my_dict["listid"][0],None,conn ) ))
					     line_bot_api.reply_message( event.reply_token,   message) 

					elif (my_dict["action"][0]=="getGroupReport"):
					     member =get_contactbaseByContactId(my_dict["cid"][0] ,conn )
					     message.append( FlexSendMessage("小組出席",contents= getGroupReport(member.contactid ,my_dict["listid"][0],None,conn   ) ))
					     line_bot_api.reply_message(  event.reply_token,   message)  
					elif (my_dict["action"][0]=="getWorshipReport"):
					     member =get_contactbaseByContactId(my_dict["cid"][0] ,conn )
					     message.append( FlexSendMessage("小組主日出席",contents= getWorshipReport(member.contactid ,my_dict["listid"][0] ,None,conn  ) ))
					     line_bot_api.reply_message(  event.reply_token,   message)  
					elif (my_dict["action"][0]=="getPersonalWorshipReport"):
					     member =get_contactbaseByContactId(my_dict["cid"][0] ,conn )
					     message.append( FlexSendMessage("小組靈修天數",contents= getPersonalWorshipReport(member.contactid ,my_dict["listid"][0] ,None ,conn  ) ))                        
					     line_bot_api.reply_message(  event.reply_token,   message)
					elif(my_dict["action"][0]=="getPrayListByOwner"):
					     if( len(my_dict["subject"])==0 ):
					        message.append( FlexSendMessage("代禱清單",contents= getPrayWeekByOwner(member.contactid,None,conn ) ))
					     else:
					        message.append( FlexSendMessage("代禱清單",contents= getPrayListByOwner(my_dict['ownerid'] [0]  ,None, my_dict['worshipdate'] [0]  ,conn  ) ))
					     line_bot_api.reply_message( event.reply_token,   message) 
					elif(my_dict["action"][0]=="getPrayItemByOwner"): 
					     message.append( FlexSendMessage("代禱清單",contents= getPrayItemByOwner(member.contactid,my_dict["prayid"][0] ,conn  ) ))
					     line_bot_api.reply_message( event.reply_token,   message) 

		# end marked of process
		finally:
			conn.close()
		app.logger.info("post 200")
		return HttpResponse(status=200 )

	app.logger.info("not post request return bad request.")
	return HttpResponse(status=200)
