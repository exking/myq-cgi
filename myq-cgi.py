#!/usr/bin/env python2.7

import time
import datetime
import sys
import os
import cgi
import cgitb
import requests

try:
	import json
except ImportError:
	try:
		import simplejson as json
	except ImportError:
		print "No json library available. I recommend installing either python-json"
		print "or simplejson. Python 2.6+ contains json library already."
		sys.exit(-1)

class MyQ:
	def __init__(self, username, password, serial=None):
		self.s = requests.Session()
		self.username = username
		self.password = password
		self.serial = serial
		self.appid = "NWknvuBd7LoFHfXmKNMBcgajXtZEgKUh4V7WNzMidrpUUluDpVYVZx+xT4PCM5Kx"
                self.headers = { 
                                 "MyQApplicationId": self.appid,
                                 "BrandId": "2",
                                 "ApiVersion": "4.1",
                                 "User-Agent": "Chamberlain/3.73",
                                 "Culture": "en",
                               }
		self.baseurl = "https://myqexternal.myqdevice.com"
		self.authurl = self.baseurl+"/api/v4/User/Validate"
		self.enumurl = self.baseurl+"/api/v4/userdevicedetails/get"
		self.seturl  = self.baseurl+"/api/v4/DeviceAttribute/PutDeviceAttribute"
		self.geturl  = self.baseurl+"/api/v4/deviceattribute/getdeviceattribute"
		self.tokenfname="/tmp/myqdata.json"
		self.tokentimeout=60
		self.read_token()
		
	def loads(self, res):
		if hasattr(json, "loads"):
			res = json.loads(res)
		else:
			res = json.read(res)
		return res
	
	def save_token(self):
		ts=time.time()
		token_file={}
		token_file["SecurityToken"]=self.securitytoken
		token_file["TimeStamp"]=datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
		json_data=json.dumps(token_file)
		f = open(self.tokenfname,"w")
		f.write(json_data)
		f.close()
		os.chmod(self.tokenfname, 0o600)		
	
	def read_token(self):
		try:
			f = open(self.tokenfname,"r")
			data = f.read()
		except IOError:
			print "savefile not found"
			self.login()
			return True
		else:
			res = self.loads(data)
			f.close()
			s = res["TimeStamp"]
			tsfile = time.mktime(datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").timetuple())
			ts = time.time()
			if ((ts - tsfile) < 60*self.tokentimeout):
				print "saved token is good"
				self.securitytoken=res["SecurityToken"]
				return True
			else:
				print "saved token is too old"
				self.login()
				return True

	def login(self):
		payload = { "username": self.username, "password": self.password }
		req=self.s.post(self.authurl, headers=self.headers, json=payload)

		if (req.status_code != requests.codes.ok):
			print "Login err code: " + req.status_code
			sys.exit(-1)

		res = req.json()
        
		if (res["ReturnCode"] == "0"):	
			self.securitytoken = res["SecurityToken"]
			self.save_token()
			print "login OK"
		else:	
			print "Auth failed"
			print res
			sys.exit(-1)
			
	def enum_get_status(self):
		# 1 = open
		# 2 = closed
		# 4 = opening
		# 5 = closing
		payload = { "appId": self.appid, "SecurityToken": self.securitytoken, "filterOn": "true", "format": "json", "nojsoncallback": "1" }
		self.s.headers.update({ "SecurityToken": self.securitytoken })

		req = self.s.get(self.enumurl, headers=self.headers, params=payload)

		if (req.status_code != requests.codes.ok):
			print "Enum err code: " + req.status_code
			return -1

		res = req.json()
		if (res["ReturnCode"] == "0"):			
			for d in res["Devices"]:
				if (d["MyQDeviceTypeId"] == 2):
					self.serial=d["SerialNumber"]
					self.deviceid=d["MyQDeviceId"]
					print "Using: "+self.serial
					for attr in d["Attributes"]:
						if (attr["AttributeDisplayName"] == "doorstate"):
							self.cur_state=int(attr["Value"])
							return self.cur_state
							break
					break
			return -1
		else:	
			print "Can't enumerate devices, bad token?"
			return -1

	def set_state(self, newstate):
		# 0 = close
		# 1 = open
		post_data = {}
		post_data["AttributeName"]  = "desireddoorstate"
		post_data["MyQDeviceId"]       = self.deviceid
		post_data["ApplicationId"]  = self.appid
		post_data["AttributeValue"] = newstate
		post_data["SecurityToken"]  = self.securitytoken
		post_data["format"]  = "json"
		post_data["nojsoncallback"]  = "1"

		self.s.headers.update({ "SecurityToken": self.securitytoken })
		payload = { "appId": self.appid, "SecurityToken": self.securitytoken }

		req = self.s.put(self.seturl, headers=self.headers, params=payload, data=post_data)

		if (req.status_code != requests.codes.ok):
			print "Enum err code: " + req.status_code
			return -1

		res = req.json()
		
		if (res["ReturnCode"] == "0"):
			print "status changed"
			return True
		else:	
			print "Can't set state, bad token?"
			return False
              
def main():
	cgitb.enable()

	form = cgi.FieldStorage()

	print "Content-Type: text/html"     # HTML is following
	print                               # blank line, end of headers
	print "<html>"
	print "<body>"

	if ("user" not in form) or ("pass" not in form) or ("cmd" not in form):
		print "how about specifying a user and pass arguments next time?<br/>"
		sys.exit(-1)
	else:
		user=form["user"].value
		password=form["pass"].value

	if ("serial" in form):
		serial=form["serial"].value
	else:
		serial=None
	#user="user@example.com"
	#password="secret"

	m = MyQ(user,password)
	
	r = m.enum_get_status()
	if (r == -1):
		print "first status request failed, re-trying<br/>"
		m.login()
		r = m.enum_get_status()

	if "cmd" not in form:
                cmd = "status"
        else:
	        cmd = form["cmd"].value

	if (cmd == "open"):
		if ((r == 1) or (r == 4)):
			print "already open!<br/>"
		else:	
			r = m.set_state(1)
	elif (cmd == "close"):
		if ((r == 2) or (r == 5)):
			print "already closed!<br/>"
		else:	
			r = m.set_state(0)
	elif (cmd == "status"):
		print "Status is: "+str(r)
		print "<br/>"
	else:
		print "misunderstood command:", cmd

	print "OK"
	print "</body>"
	print "</html>"

if __name__=="__main__":
   main()
