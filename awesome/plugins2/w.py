import os
import time
import base64
from nonebot import on_command, CommandSession, on_notice,NoticeSession,on_request, RequestSession
import nonebot
import requests
import re
import random
import json
from datetime import datetime,timedelta

@on_command('哔哩', aliases=('哔哩'), only_to_me=False)
async def tuling(session: CommandSession):
    if session.ctx['raw_message'] == '哔哩哔哩干杯':
        await session.send('正在连接b站客服。。。')
        with open("/home/bili_kefu_stop", "w") as f:
            f.write('1')


        sess = requests.session()
        web_url = sess.get('https://api.bilibili.com/x/web-goblin/customer/center').json()['data']['contact']['business_list'][0]['list'][0]['web_url']
        sysNum = re.findall(r'sysNum=(.+?)&', web_url)[0]
        groupId = re.findall(r'groupId=(.+?)&', web_url)[0]
        data = {
            'ack': '1',
            'sysNum': sysNum,
            'source': '0',
            'tranFlag': '0',
            'groupId': groupId,
            'isReComment': '1',
        }

        ret = sess.post('https://service.bilibili.com/v2/chat/user/init.action', data=data).json()
        uid = ret['uid']
        pid = ret['pid']
        cid = ret['cid']

        data2 = {
            'sysNum': sysNum,
            'uid': uid,
            'tranFlag': '0',
            'way': '1',
            'current': 'false',
            'groupId': groupId,

        }
        res = sess.post('https://service.bilibili.com/v2/chat/user/chatconnect.action', data=data2).json()
        puid = res['puid']
        the_cookies = {
            'puid': puid,
            'uid': uid,
            'cid': cid,
        }
        with open("/home/bili_kefu", "w") as f:
            json.dump(the_cookies, f)

        aid = res['aid']
        s = set()
        while True:
            time.sleep(2)
            with open("/home/bili_kefu_stop", "r") as f:
                t = f.read()
            if '停止' in t:
                await session.send('已经与b站断开连接。')
                break
            ret2 = sess.get('https://service.bilibili.com/v2/chat/user/msg.action?puid={}&uid={}&token={}'.format(puid, uid, int(time.time()*1000))).json()
            if ret2:
                if '202' in ret2[0]:
                    mid = re.findall(r'"msgId":"(.+?)"', ret2[0])[0]
                    if mid not in s:
                        s.add(mid)
                        content = re.findall(r'"content":"(.+?)"', ret2[0])[0]
                        print(content)
                        await session.send(content)

