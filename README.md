# pyForescout

## Description
For whatever reason, Forescout has four different APIs to query. This library attempts to simplify things and provide functions for common use cases.

## Setup
#### For WebAPI GET operations, you will need:
- a Web API Account (Forescout Console > Options > Web API > User Settings)
- an IP ACL (Forescout Console > Options > Web API > Client IPs)
#### For WebAPI POST operations, you will need:
- a CounterACT Web Service Account (Forescout Console > Options > Data Exchange (DEX) > CounterACT Web Service > Accounts)
- an IP ACL (Forescout Console > Options > Data Exchange (DEX) > CounterACT Web Service > Security Settings)
#### For SwitchAPI and AdminAPI functions, you will need:
- a standard CounterACT User Profile with relevant privledges (Forescout Console > Options > CounterACT User Profiles)
- an IP ACL for REST API (Forescout Console > Options > Access > Web)

## Use
```python
from pyForescout import *
host = getHost("192.168.1.1")
pprint(host)
```

## To Do
Error Handling
