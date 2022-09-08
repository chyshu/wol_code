from django.db import models

class Member:
    def __init__(self,display_name=None, user_id=None, picture_url=None,status_message=None, language=None, contactid=None,contactname=None):        
        self.display_name = display_name
        self.user_id = user_id
        self.picture_url = picture_url
        self.status_message = status_message
        self.language = language
        self.contactid=contactid
        self.contactname=contactname


class Family:
    def __init__(self,display_name=None, user_id=None, picture_url=None,status_message=None, language=None, contactid=None,contactname=None,relation=None):        
        self.display_name = display_name
        self.user_id = user_id
        self.picture_url = picture_url
        self.status_message = status_message
        self.language = language
        self.contactid=contactid
        self.contactname=contactname
        self.relation=relation

class Friend:

    # NICK NAME should be unique
    #nick_name = models.CharField(max_length=100, unique =  True)
    #first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    #last_name = models.CharField(max_length=100)
    #likes = models.CharField(max_length = 250)
    # dob = models.DateField(auto_now=False, auto_now_add=False)
    #lives_in = models.CharField(max_length=150, null = True, blank = True)
    def __str__(self):
        return self.nick_name
class  CloseFriend:
      def __init__(self,display_name=None, user_id=None, picture_url=None,status_message=None, language=None, contactid=None,contactname=None,relation=None):        
        self.display_name = display_name
        self.user_id = user_id
        self.picture_url = picture_url
        self.status_message = status_message
        self.language = language
        self.contactid=contactid
        self.contactname=contactname
        self.relation=relation

class Worshipdata:
    def __init__(self, contactid=None,contactname=None,worshipdate=None,session=None,spirtualtimes=None,groupworship=None):         
        self.contactid=contactid
        self.contactname=contactname
        self.worshipdate=worshipdate
        self.session=session
        self.spirtualtimes = spirtualtimes
        self.groupworship=groupworship

class MyGroup:
    def __init__(self, listid=None,listname=None,isMember=None,isLeader=None,isAssistant=None,isFamilyLeader=None,isAreaChief=None,isPastor=None):
        self.listid=listid
        self.listname=listname        
        self.isMember=isMember
        self.isLeader=isLeader
        self.isAssistant=isAssistant
        self.isFamilyLeader=isFamilyLeader
        self.isAreaChief=isAreaChief
        self.isPastor=isPastor

class WeekPresent:
    def __init__(self, bdate=None,edate=None,present=None):
        self.bdate=bdate
        self.edate=edate
        self.present=present

class GroupPresent:
    def __init__(self, contactid=None,contactname=None,groupworship=None):
        self.contactid=contactid
        self.contactname=contactname
        self.groupworship=groupworship
