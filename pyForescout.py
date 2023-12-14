#!/usr/bin/env python
__author__		= "Nick Muse"

# Standard Library Modules
from configparser import ConfigParser
from requests import get, post

# Load Config
config							= ConfigParser()
config.read("config.ini")
server							= config["main"]["server"]
user_webapi    					= config["webapi"]["username"]
pass_webapi    					= config["webapi"]["password"]
user_dex						= config["dex"]["name"] + "@" + config["dex"]["username"]
pass_dex						= config["dex"]["password"]
user_counteract					= config["counteractuser"]["username"]
pass_counteract					= config["counteractuser"]["password"]

# Global Variables
url_webapi      				= "https://%s/api" % server
url_switch      				= "https://%s/switch/api/v1" % server
url_admin       				= "https://%s/adminapi" % server
url_nicore						= "https://%s/fsapi/niCore" % server
headers_base    				= {'Content-Type': "application/x-www-form-urlencoded"}
headers_xml						= {'Content-Type': 'application/xml', 'Accept': 'application/xml'}

# Make Header Basic - used by WebAPI functions
def makeHeaderWebApi():
	# Authenticate
	_login_url					= url_webapi + "/login"
	_login_payload				= "username=%s&password=%s" % (user_webapi, pass_webapi)
	_response       			= post(_login_url, headers=headers_base, data=_login_payload)
	_token						= _response.content.decode("utf-8")
	# Build Header
	_retval						= headers_base
	_retval["Authorization"]	= _token
	return _retval

# Make Header oAuth2 - used by SwitchAPI and AdminAPI functions
def makeHeaderOA2():
	# Authenticate
	_login_url					= "https://" + server + "/fsum/oauth2.0/token"
	_login_payload				= "username=%s&password=%s&grant_type=password&client_id=fs-oauth-client" % (user_counteract, pass_counteract)
	_response					= post(_login_url, headers=headers_base, data=_login_payload)
	_token						= _response.json()["access_token"]
	# Build Header
	_retval						= headers_base
	_retval["Authorization"]	= "Bearer " + _token
	return _retval

# Helper to converts a "String" to ["String"] so that a value can just be assumed as a List
def normalize_to_list(value):
	if type(value) == type([]):
		_value_list = value
	else: 
		_value_list = [value]
	return _value_list

######################################################################################
###
### WebAPI Functions
###

# Get All Hosts
def getHosts():
	_header 					= makeHeaderWebApi()
	_url						= url_webapi + "/hosts"
	return get(_url,headers=_header).json()
	
# Get All Policies
def getPolicies():
	_header 					= makeHeaderWebApi()
	_url						= url_webapi + "/policies"
	return get(_url,headers=_header).json()

# Get Single Policy
def getPolicy(_policy_name: str):
	_all_policies				= getPolicies()
	for _rule in _all_policies["policies"]:
		for _rule_id in _rule["rules"]:
			if _policy_name in _rule_id["name"]:
				return _rule_id["ruleId"]

# Get All Host Fields
def getHostFields():
	_header						= makeHeaderWebApi()
	_url						= url_webapi + "/hostfields"
	return get(_url,headers=_header).json()

# Get Single Host
def getHost(ip: str):
	_header						= makeHeaderWebApi()
	_url						= url_webapi + "/hosts/ip/" + ip
	return get(_url,headers=_header).json()["host"]["fields"]

# Get Host's Switch
def getHostSwitch(ip: str) -> str:
	return getHost(ip)["sw_ip"]["value"]

######################################################################################
###
### SwitchAPI Functions
###

# Get Single Managed Switch
def getSwitch(ip: str):
	_header						= makeHeaderOA2()
	_url						= url_switch + "/switches?managementAddress=" + ip
	return get(_url,headers=_header).json()

# Get All Managed Switches
def getSwitches():
	_header						= makeHeaderOA2()
	_url						= url_switch + "/switches/summary"
	return get(_url,headers=_header).json()["switches"]

######################################################################################
###
### AdminAPI Functions
###

# Get All Segments - Subject to Change / Work in Progress
def getSegments():
	import ipaddress
	_header						= makeHeaderOA2()
	_url						= url_admin + "/segments"
	_tree						= get(_url,headers=_header).json()["node"]["nodes"]
	_retlist					= []
	class segment:
		def __init__(self,name,networks,vlan):
			self.name       		= name
			self.networks			= networks
			self.vlan       		= vlan
		def __str__(self):
			_output = "\nName: %s\nVLAN: %s\nNetworks: %s" % (self.name,self.vlan,self.networks)
			return _output
	def cidr(_range):
		if "-" in _range:
			_range	    			= _range.split("-")
			_start	    			= ipaddress.IPv4Address(_range[0])
			_end	    			= ipaddress.IPv4Address(_range[0])
			_range	    			= str([_ipaddr for _ipaddr in ipaddress.summarize_address_range(_start, _end)][0])
		return _range
	def process(_tree):
		for _node in _tree:
			if "ranges" in _node:
				_name = _node["name"]
				_vlan = None
				_name_split = _name.split(" - ")
				if len(_name_split) >= 2:
					_name = _name_split[1]
					_vlan = _name_split[0]
				_ranges = []
				for _net in _node["ranges"]:
					_net = cidr(_net)
					_ranges.append(_net)
				_segment = segment(_name,_ranges,_vlan)
				_retlist.append(_segment)
			if "nodes" in _node:
				process(_node["nodes"])
	process(_tree)
	return _retlist

######################################################################################
###
### DEXAPI Functions
###

# Clear a List
def listClearAll(list_name: str):
	_header					= headers_xml
	_url					= url_nicore + "/Lists"
	_data_xml				= """<?xml version='1.0' encoding='utf-8'?><FSAPI API_VERSION="2.0" TYPE="request"><TRANSACTION TYPE="delete_all_list_values"><LISTS><LIST NAME="%s"></LIST></LISTS></TRANSACTION></FSAPI>""" % list_name
	return post(_url, headers=_header, auth=(user_dex,pass_dex), data=_data_xml).status_code == 200
	
# Add to a List
def listAddValue(list_name: str, value):
	_value_list				= normalize_to_list(value)
	_values_xml				= ""
	for _value in _value_list: 
		_values_xml += """<VALUE>%s</VALUE>""" % _value
	_header					= headers_xml
	_url					= url_nicore + "/Lists"
	_data_xml				= """<?xml version='1.0' encoding='utf-8'?><FSAPI API_VERSION="2.0" TYPE="request"><TRANSACTION TYPE="add_list_values"><LISTS><LIST NAME="%s">%s</LIST></LISTS></TRANSACTION></FSAPI>""" % (list_name,_values_xml)
	return post(_url, headers=_header, auth=(user_dex,pass_dex), data=_data_xml).status_code == 200

def listDeleteValue(list_name: str, value):
	_value_list				= normalize_to_list(value)
	_values_xml				= ""
	for _value in _value_list: 
		_values_xml += "<VALUE>%s</VALUE>" % _value
	_header					= headers_xml
	_url					= url_nicore + "/Lists"
	_data_xml				= """<?xml version='1.0' encoding='utf-8'?><FSAPI API_VERSION="2.0" TYPE="request"><TRANSACTION TYPE="delete_list_values"><LISTS><LIST NAME="%s">%s</LIST></LISTS></TRANSACTION></FSAPI>""" % (list_name,_values_xml)
	return post(_url, headers=_header, auth=(user_dex,pass_dex), data=_data_xml).status_code == 200
