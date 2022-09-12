import datetime
from logging import exception
from operator import truediv
from pickle import NONE, TRUE

import psycopg2
from .classes import Member,Family,CloseFriend,MyGroup
from flask import Flask
from linebot import LineBotApi, WebhookParser,WebhookHandler
from django.conf import settings
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from logging.config  import dictConfig

app = Flask(__name__) 


#dictConfig({
#    'version': 1,
#    'formatters': {'default': {
#        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
#    }},
#    'handlers': {'wsgi': {
#        'class': 'logging.StreamHandler',
#        'stream': 'ext://flask.logging.wsgi_errors_stream',
#        'formatter': 'default'
#    }},
#    'root': {
#        'level': 'INFO',
#        'handlers': ['wsgi']
#    }
#})

#dictConfig( {
#    'version': 1,
#    'formatters': { 'default': {
#    'format': '[%(ascttime)s] %(levelname)s in %(module)s: %(message)s'
#    }},
#    'handlers': { 'wsgi': {
#            'class': 'logging.StreamHandler',
#            'formatter': 'default',
#            'stream':'ext://flask.logging.wsgi_info_stream',
#    }},
#    'root': {
#            'handlers': ['wsgi'],
#            'level': 'INFO',
#    }
#})


line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

#app.logger.info("utils");
 
def getLineProfile(userid):
 
    try:
        profile = line_bot_api.get_profile(userid)

        if profile:
            #ret.display_name=profile.display_name
            #ret.language=profile.language
            #ret.picture_url=profile.picture_url
            #ret.status_message=profile.status_message
            app.logger.info("profile:"+ profile.display_name )
            app.logger.info("profile:"+ profile.user_id )

    except LineBotApiError as e:
        app.logger.error("profile err " + e.message)

    return profile
#
#  0 Monday 1 Tuesday 2 Wednesday  3 Thursday 4 Friday 5 Saturday 6 Sunday
def next_weekday(d, weekday):
	days_ahead =  weekday-d.weekday()
	#print("days_ahead="+ str(days_ahead))
	if days_ahead <= 0:
		days_ahead += 7

	return d + datetime.timedelta(days_ahead)

def current_weekday(d, weekday):
	# days_ahead =  weekday-d.weekday()
	#print("days_ahead="+ str(days_ahead))
	#if days_ahead <= 0:
	#	days_ahead += 7
	days_ahead=d.weekday()

	if (days_ahead<6):
		return d - datetime.timedelta(days_ahead+1)
	else:
		return d	

#def getConnection():
#	conn = psycopg2.connect(database="d4hpotv59bt154", user="qhfvjzcqqgbykn", password="eaa367e02a61a4dac21029cc54684143e35380c47dd8f2f69486dfdc7d2f85cd", host="ec2-3-224-8-189.compute-1.amazonaws.com", port="5432")#
#	conn.autocommit = True

#	return conn



def getConnection():
	#conn = psycopg2.connect(database="d4hpotv59bt154", user="qhfvjzcqqgbykn", password="eaa367e02a61a4dac21029cc54684143e35380c47dd8f2f69486dfdc7d2f85cd", host="ec2-3-224-8-189.compute-1.amazonaws.com", port="5432")
	conn = psycopg2.connect(database="postgres", user="qhfvjzcqqgbykn", password="eaa367e02a61a4dac21029cc54684143e35380c47dd8f2f69486dfdc7d2f85cd", host="163.22.27.130", port="5432")
	conn.autocommit = True

	return conn	



def get_contactbase(userid,psconn):
	#if psconn==None:
	#	psconn =  getConnection()
#	app.logger.info("get_contact")
	pycursor = psconn.cursor()
	pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")

	ret = Member(None,None,None,None,None,None)
	app.logger.info("get_contactbase "+userid)

	pycursor.execute("""select contactid,user_id,displayname,sid from Id2contact where user_id=%s""" ,[ userid ])
	row = pycursor.fetchone()
	if row:
		ret.user_id  =str(row[1])
		ret.display_name=str(row[2])
		app.logger.info("profile:"+ret.user_id +" "+ret.display_name )
		if row[0]!="":
			# ret.display_name=str(row[0])
			pycursor.execute("""select contactid,LastName from contactbase where contactid=%s""" ,[ str(row[0])	 ])
			contactbase = pycursor.fetchone() 
			if contactbase!=None:
				ret.contactid=str(contactbase[0])
				ret.contactname=str(contactbase[1])
				#print("profile:"+ ret.contactid  )
				#print("profile:"+ret.contactname )
		#app.logger.info(ret)
	else:
		app.logger.info("profile: "+ userid+" not found"   )
	return ret

def get_contactbaseByContactId(contactid,psconn):
	#if psconn==None:
	#psconn =  getConnection()
	app.logger.info('contactbaseByContactid'+contactid)
	pycursor = psconn.cursor()
	pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")

	ret = Member(None,None,None,None,None,None)
	pycursor.execute("""select contactid,LastName from contactbase where contactid=%s""" ,[ contactid 	 ])
	contactbase = pycursor.fetchone() 
	
	if contactbase:
		ret.contactid=str(contactbase[0])
		ret.contactname=str(contactbase[1])
#	app.logger.info(ret)
	pycursor.execute("""select contactid,user_id,displayname,sid from Id2contact where contactid=%s""" ,[ contactid ])
	row = pycursor.fetchone()
	if row:
		ret.user_id  =str(row[1])
		ret.display_name=str(row[2])
	#psconn.close()
	app.logger.info(ret)	
	pycursor.close()
	return ret


def get_contactbaseByContactName(lastname,psconn):
	#psconn =  getConnection()
	pycursor=  psconn.cursor() 
	app.logger.info(" get contactname "+ ("" if lastname==None else lastname))
	pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
	thename = "" if lastname==None else lastname
	ret = Member(None,None,None,None,None,None)
	app.logger.info("getcontactname "+thename)
	if thename!="":
		# pycursor.execute("""select   contactid,lastname, birthdate,mobilephone  from contactbase  where lastname like '%"""+thename+"""%'""" )
		pycursor.execute("""select   contactid,lastname, birthdate,mobilephone  from contactbase  where lastname =%s  and statuscode='1' """,[ thename] )
		contactbase = pycursor.fetchone()   
		if contactbase: 
			ret.contactid=str(contactbase[0])
			ret.contactname=str(contactbase[1])
			pycursor.execute("""select contactid,user_id,displayname,sid from Id2contact where contactid=%s   """ ,[ ret.contactid ])
			row = pycursor.fetchone()
			if row:
				ret.user_id  =str(row[1])
				ret.display_name=str(row[2])
	pycursor.close()

	return ret

def GroupOwner(contactid,psconn):
	#psconn =  getConnection()
	pycursor = psconn.cursor()
	ret = []

	pycursor.execute(""" select distinct listid from listmemberbase where listmemberbase.entityid =%s """,[contactid])
	list_rows = pycursor.fetchall()
	app.logger.info( "contactid "+contactid )
	for list in list_rows:
		pycursor.execute(""" select listbase.listid, listbase.listname,listbase.list_leader,listbase.assistant,listbase.chief,listbase.family_leader 
		                     from listbase  where  listbase.purpose ='小組名單' and listbase.inuse='1' and listbase.listid =%s """,[list[0]])
		
		columns = []
		for col in pycursor.description:
			columns.append(col[0].lower())

		listbase=pycursor.fetchone()
		if listbase!=None:
		#	print( str(listbase[columns.index("listname")]) )
			listid=("" if listbase[columns.index("listid")]==None else  str(listbase[columns.index("listid")]) ) 
			listname=("" if listbase[columns.index("listname")]==None else  str(listbase[columns.index("listname")]) ) 
			list_leader=("" if listbase[columns.index("list_leader")]==None else  str(listbase[columns.index("list_leader")]) ) 
			
			chief=("" if listbase[columns.index("chief")]==None else  str(listbase[columns.index("chief")]) ) 
			assistant=("" if listbase[columns.index("assistant")]==None else  str(listbase[columns.index("assistant")]) ) 
			family_leader=("" if listbase[columns.index("family_leader")]==None else  str(listbase[columns.index("family_leader")]) ) 
			
			#if chief==contactid:
		#	role="chief"
	#		elif  list_leader==contactid:
	#			role="list_leader"
	#		elif  family_leader==contactid:
	#			role="family_leader"
	#		elif  assistant==contactid:
	#			role="assistant"
			f=False
			for i in range(0, len(ret)):
				if(ret[i].listid==listid  ):
					f=True
					break
			if f==False:
				ret.append( MyGroup(listid,listname, True,list_leader==contactid, assistant==contactid,family_leader==contactid,   chief==contactid, False   ) )

	pycursor.execute(""" select listbase.listid, listbase.listname,listbase.list_leader,listbase.assistant,listbase.chief,listbase.family_leader 
	                 from listbase 	
					 where  ( listbase.list_leader =%s or  listbase.family_leader =%s  or chief=%s or assistant=%s )
					 and listbase.purpose ='小組名單' and listbase.inuse='1' """, [ contactid ,contactid ,contactid,contactid   ])

	columns = []
	for col in pycursor.description:
		columns.append(col[0].lower())

	for listbase in pycursor.fetchall():
		listid=("" if listbase[columns.index("listid")]==None else  str(listbase[columns.index("listid")]) ) 
		listname=("" if listbase[columns.index("listname")]==None else  str(listbase[columns.index("listname")]) ) 
		list_leader=("" if listbase[columns.index("list_leader")]==None else  str(listbase[columns.index("list_leader")]) ) 
		
		chief=("" if listbase[columns.index("chief")]==None else  str(listbase[columns.index("chief")]) ) 
		assistant=("" if listbase[columns.index("assistant")]==None else  str(listbase[columns.index("assistant")]) ) 
		family_leader=("" if listbase[columns.index("family_leader")]==None else  str(listbase[columns.index("family_leader")]) ) 
		
 
		f=False
		for i in range(0, len(ret)):
			if(ret[i].listid==listid  ):
				f=True
				break
		if f==False:
			ret.append( MyGroup(listid,listname, True,list_leader==contactid, assistant==contactid,family_leader==contactid,   chief==contactid, False   ) )
	pycursor.close()
	app.logger.info(ret)
	return ret 

def addCloseGroup(member,family,psconn):
	ret="新增成功"
	#psconn =  getConnection()
	pycursor = psconn.cursor()
	pycursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
	ret = Member(None,None,None,None,None,None)
	try:
		pycursor.execute("""select  sid,contactid, familyid  from closegroup  where contactid=%s and familyid=%s   """ ,[  member.contactid,   family.contactid     ])
		closegroup = pycursor.fetchone()   
		if closegroup==None:
			pycursor.execute("""insert into closegroup(contactid, familyid ,relation ,input_name,isediting) values (%s,%s,%s,%s,%s)   """ ,[    member.contactid,  family.contactid ,"" ,family.contactname,"N"   ])
		else:
			ret="成員已經存在"
	except exception as err:
		ret="發生錯誤"
		#print("addCloseGroup err " + err.message)
	pycursor.close()
	return ret

