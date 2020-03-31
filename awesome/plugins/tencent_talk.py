#-*- coding: UTF-8 -*-
import hashlib
import urllib.request
import urllib.parse
import base64
import requests
import json
import time


def setParams(array, key, value):
    array[key] = value

def genSignString(parser):
    uri_str = ''
    for key in sorted(parser.keys()):
        if key == 'app_key':
            continue
        uri_str += "%s=%s&" % (key, urllib.parse.quote(str(parser[key]), safe = ''))
    sign_str = uri_str + 'app_key=' + parser['app_key']

    hash_md5 = hashlib.md5(sign_str.encode())
    return hash_md5.hexdigest().upper()


class AiPlat(object):
    def __init__(self, app_id, app_key):
        self.app_id = app_id
        self.app_key = app_key
        self.data = {}

    def invoke(self, params,arg=0):
        try:
            if arg == 1:
                dict_rsp = requests.get(self.url, data=params).json()
            else:
                dict_rsp = requests.post(self.url, data=params).json()
            return dict_rsp
        except urllib.error.URLError as e:
            dict_error = {}
            if hasattr(e, "code"):
                dict_error = {}
                dict_error['ret'] = -1
                dict_error['httpcode'] = e.code
                dict_error['msg'] = "sdk http post err"
                return dict_error
            if hasattr(e,"reason"):
                dict_error['msg'] = 'sdk http post err'
                dict_error['httpcode'] = -1
                dict_error['ret'] = -1
                return dict_error
        else:
            dict_error = {}
            dict_error['ret'] = -1
            dict_error['httpcode'] = -1
            dict_error['msg'] = "system error"
            return dict_error


    # def getOcrGeneralocr(self, image):
    #     self.url = url_preffix + 'ocr/ocr_generalocr'
    #     setParams(self.data, 'app_id', self.app_id)
    #     setParams(self.data, 'app_key', self.app_key)
    #     setParams(self.data, 'time_stamp', int(time.time()))
    #     setParams(self.data, 'nonce_str', int(time.time()))
    #     image_data = base64.b64encode(image)
    #     setParams(self.data, 'image', image_data)
    #     sign_str = genSignString(self.data)
    #     setParams(self.data, 'sign', sign_str)
    #     return self.invoke(self.data)

    # def getNlpTextTrans(self, text, type):
    #     self.url = url_preffix + 'nlp/nlp_texttrans'
    #     setParams(self.data, 'app_id', self.app_id)
    #     setParams(self.data, 'app_key', self.app_key)
    #     setParams(self.data, 'time_stamp', int(time.time()))
    #     setParams(self.data, 'nonce_str', int(time.time()))
    #     setParams(self.data, 'text', text)
    #     setParams(self.data, 'type', type)
    #     sign_str = genSignString(self.data)
    #     setParams(self.data, 'sign', sign_str)
    #     return self.invoke(self.data)

    # def getAaiWxAsrs(self, chunk, speech_id, end_flag, format_id, rate, bits, seq, chunk_len, cont_res):
    #     self.url = url_preffix + 'aai/aai_wxasrs'
    #     setParams(self.data, 'app_id', self.app_id)
    #     setParams(self.data, 'app_key', self.app_key)
    #     setParams(self.data, 'time_stamp', int(time.time()))
    #     setParams(self.data, 'nonce_str', int(time.time()))
    #     speech_chunk = base64.b64encode(chunk)
    #     setParams(self.data, 'speech_chunk', speech_chunk)
    #     setParams(self.data, 'speech_id', speech_id)
    #     setParams(self.data, 'end', end_flag)
    #     setParams(self.data, 'format', format_id)
    #     setParams(self.data, 'rate', rate)
    #     setParams(self.data, 'bits', bits)
    #     setParams(self.data, 'seq', seq)
    #     setParams(self.data, 'len', chunk_len)
    #     setParams(self.data, 'cont_res', cont_res)
    #     sign_str = genSignString(self.data)
    #     setParams(self.data, 'sign', sign_str)
    #     return self.invoke(self.data)

    def getNlpTextChat(self, session, question):
        self.url = 'https://api.ai.qq.com/fcgi-bin/nlp/nlp_textchat'
        setParams(self.data, 'app_id', self.app_id)
        setParams(self.data, 'app_key', self.app_key)
        setParams(self.data, 'time_stamp', int(time.time()))
        setParams(self.data, 'nonce_str', int(time.time()))
        setParams(self.data, 'session', session)
        setParams(self.data, 'question', question)
        sign_str = genSignString(self.data)
        setParams(self.data, 'sign', sign_str)
        return self.invoke(self.data)

    def getNlpImgPorn(self, image_url):
        self.url = 'https://api.ai.qq.com/fcgi-bin/vision/vision_porn'
        setParams(self.data, 'app_id', self.app_id)
        setParams(self.data, 'app_key', self.app_key)
        setParams(self.data, 'time_stamp', int(time.time()))
        setParams(self.data, 'nonce_str', int(time.time()))
        ret = requests.get(image_url).content
        setParams(self.data, 'image', base64.b64encode(ret).decode("utf-8"))
        sign_str = genSignString(self.data)
        setParams(self.data, 'sign', sign_str)
        return self.invoke(self.data)
 
    def getNlpRecord(self, image_url):
        self.url = 'https://api.ai.qq.com/fcgi-bin/vision/vision_porn'
        setParams(self.data, 'app_id', self.app_id)
        setParams(self.data, 'app_key', self.app_key)
        setParams(self.data, 'time_stamp', int(time.time()))
        setParams(self.data, 'nonce_str', int(time.time()))
        setParams(self.data, 'speaker', 5)
        setParams(self.data, 'format', 3)
        setParams(self.data, 'volume', 0)
        setParams(self.data, 'speed', 100)
        setParams(self.data, 'text', image_url)
        setParams(self.data, 'aht', 0)
        setParams(self.data, 'apc', 58)
        sign_str = genSignString(self.data)
        setParams(self.data, 'sign', sign_str)
        return self.invoke(self.data,1)
