'''
@author: M.D.W
'''
from urllib.request import *

def post(url, data=None):
    req = Request(url, data)
    rsp = urlopen(req)
    return rsp.read()

def unpack(d):
    return d
