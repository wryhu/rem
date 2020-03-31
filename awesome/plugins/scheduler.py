import random
import os
import base64
import pymysql
import time
from datetime import datetime
import requests
import re
import nonebot
from lxml import etree
from aiocqhttp.exceptions import Error as CQHttpError


def getBKN(skey):
    length = len(skey)
    hash = 5381
    for i in range(length):
        hash += (hash << 5) + ord(skey[i])
    return hash & 0x7fffffff # 计算bkn

async def qiandao(location, text, pic,g,arg=None):
    bot = nonebot.get_bot()
    g_list = await bot.get_group_list()
    cookie = await bot.get_cookies()
    cookie = str(cookie)
    skey = re.findall(r"skey=(.+?)'",cookie)[0]
    headers = {
    'Cookie': 'uin=o0302554188; skey=%s;' % skey.replace(';',''),
    }

    bkn = getBKN(skey)
    url = 'https://qun.qq.com/cgi-bin/qiandao/sign/publish'
    if pic:
        with open(pic,'rb') as f:
            c = f.read()
        data = {
            'bkn':str(getBKN(skey)),
            'pic_up':str(base64.b64encode(c).decode())
        }
        res = requests.post('https://qun.qq.com/cgi-bin/qiandao/upload/pic',data=data,headers=headers,timeout=5)
        pic_id = res.json()['data']['pic_id']
    else:
        pic_id = 'sign_50f255507406be808d8dd701bc7c9ffbk2h6z7xe'
    data = {
        'client': '2',
        'gallery_info': {
            'category_id': '21',
            'page': '0',
            'pic_id': '173'
        },
        'gc': str(g),
        'lgt': '0',
        'poi': location,
        'pic_id': pic_id,
        'template_id': '6',
        'bkn': bkn,
        'text': text, #### 签到内容 ####
        'lat': '0',
        'template_data': ''
    }
    res = requests.post(url, data=data, headers=headers)
    print(res.text)

    
def select_db():
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "SELECT * from animate where DATE_FORMAT(create_time,'%Y-%m-%d') = DATE_FORMAT(NOW(),'%Y-%m-%d')"
        cur.execute(sql)
        ret = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)

def select_db2():
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "SELECT * from animation where badge like '%限时%'"
        cur.execute(sql)
        ret = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)

def select_db3():
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select title,pub_date from animation where index_show like '%即将开播%'"
        cur.execute(sql)
        ret = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)

async def send_msg(msg,pic=None):
    bili_list = [333269216,630484590,1065415447,949377627,1035554908]
    bot = nonebot.get_bot()
    # await bot.send_group_msg(group_id=949377627, message=msg)
    glist = await bot.get_group_list()
    if pic:
        con = requests.get(pic).content
        with open('/home/pro_coolq/data/image/cv.jpg','wb') as f:
            f.write(con)
        desc,title,url = msg.split('\n')
        for g in glist:
            group_id=g.get('group_id')
            if group_id in bili_list:
                try:
                    #await bot.send_group_msg(group_id=group_id, message='[CQ:share,url=%s,title=%s,content=%s,image=%s]' % (url,title,desc,pic))
                    await bot.send_group_msg(group_id=group_id, message='[CQ:image,file=cv.jpg]%s' % msg)
                    time.sleep(0.5)
                except:
                    pass

@nonebot.scheduler.scheduled_job('interval', seconds=60)
async def _():
    items = requests.get('https://space.bilibili.com/ajax/member/getSubmitVideos?mid=928123&pagesize=3&tid=0&page=1&keyword=&order=pubdate').json()['data']['vlist']

    with open(r'/home/awesome-bot/bgm', 'r') as f:
        old_aid = f.read()
    if str(items[0]['aid']) not in old_aid:

        with open(r'/home/awesome-bot/bgm', 'w') as f:
            f.write(str(items[0]['aid']) + str(items[1]['aid']) + str(items[2]['aid']))
        
        htitle = items[0]['title']
        pic = 'https:'+items[0]['pic']
        #await qiandao(htitle,items[0]['author']+' 投稿了一个新视频',pic)
        msg = '%s 投稿了一个新视频\n%s\nhttps://www.bilibili.com/video/av%s' % (items[0]['author'], htitle, items[0]['aid'])
        await send_msg(msg,pic) 

    items = requests.get('https://space.bilibili.com/ajax/member/getSubmitVideos?mid=408002864&pagesize=3&tid=0&page=1&keyword=&order=pubdate').json()['data']['vlist']

    with open(r'/home/awesome-bot/bgm2', 'r') as f:
        old_aid = f.read()
    if str(items[0]['aid']) not in old_aid:

        with open(r'/home/awesome-bot/bgm2', 'w') as f:
            f.write(str(items[0]['aid']) + str(items[1]['aid']) + str(items[2]['aid']))
        
        htitle = items[0]['title']
        pic = 'https:'+items[0]['pic']
        #await qiandao(htitle,items[0]['author']+' 投稿了一个新视频',pic)
        msg = '%s 投稿了一个新视频\n%s\nhttps://www.bilibili.com/video/av%s' % (items[0]['author'], htitle, items[0]['aid'])
        await send_msg(msg,pic) 
    items = requests.get('https://space.bilibili.com/ajax/member/getSubmitVideos?mid=21453565&pagesize=3&tid=0&page=1&keyword=&order=pubdate').json()['data']['vlist']

    with open(r'/home/awesome-bot/bgm3', 'r') as f:
        old_aid = f.read()
    if str(items[0]['aid']) not in old_aid:

        with open(r'/home/awesome-bot/bgm3', 'w') as f:
            f.write(str(items[0]['aid']) + str(items[1]['aid']) + str(items[2]['aid']))
        
        htitle = items[0]['title']
        pic = 'https:'+items[0]['pic']
        #await qiandao(htitle,items[0]['author']+' 投稿了一个新视频',pic)
        msg = '%s 投稿了一个新视频\n%s\nhttps://www.bilibili.com/video/av%s' % (items[0]['author'], htitle, items[0]['aid'])
        await send_msg(msg,pic) 
    items = requests.get('https://space.bilibili.com/ajax/member/getSubmitVideos?mid=15773384&pagesize=3&tid=0&page=1&keyword=&order=pubdate').json()['data']['vlist']

    #with open(r'/home/awesome-bot/bgm4', 'r') as f:
    #    old_aid = f.read()
    #if str(items[0]['aid']) not in old_aid:
#
#        with open(r'/home/awesome-bot/bgm4', 'w') as f:
#            f.write(str(items[0]['aid']) + str(items[1]['aid']) + str(items[2]['aid']))
#
#        htitle = items[0]['title']
 #       pic = 'https:'+items[0]['pic']
        #await qiandao(htitle,items[0]['author']+' 投稿了一个新视频',pic)
#        msg = '%s 投稿了一个新电影\n%s\nhttps://www.bilibili.com/video/av%s' % (items[0]['author'], htitle, items[0]['aid'])
#        await send_msg(msg,pic)


#@nonebot.scheduler.scheduled_job('cron', hour='18', minute='23')
#async def xiajia():
#    msg = 'msg'
#    rets = select_db()
#    ret2s = select_db2()
#    ret3s = select_db3()
#    if rets:
#        msg += '\nb站今日下架番剧：'
#        for ret in rets:
#            if requests.get("https://www.bilibili.com/bangumi/play/ss%s" % ret[1]).status_code == 200:
#                continue
#            msg += ('\n' + ret[2])
#            #msg += ('\n' + ret[2] + '\n' + ret[-2])
#    
#    if ret2s:
#        msg += '\nb站限免番剧：'
#        for i in ret2s:
#            msg += ('\n' + i[2])
#            #msg += ('\n' + i[2] + '\n' + ret[-2])
#    if ret3s:
#        msg += ('\n%s 即将开播\n开播日期：%s' % (random.choice(ret3s)))
#    if msg != 'msg':
#        msg = msg.replace('msg\n', '')
#        await send_msg(msg)

#@nonebot.scheduler.scheduled_job('cron', hour='18', minute='26')
#async def jiangfen():
#    conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
#    cur = conn.cursor()
#    sql = "select title,score_status from animation where score_status like '%降%'"
#    cur.execute(sql)
#    ret = cur.fetchall()
#    conn.commit()
#    cur.close()
#    conn.close()
#    msg = []
#    for i in ret:
#        text = '%s：%s' % (i[0],i[1])
#        msg.append(text)
#    m = '\n'.join(msg)
#    await send_msg(m)


#@nonebot.scheduler.scheduled_job('cron', hour='18', minute='27')
#async def jiangfen():
#    conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
#    cur = conn.cursor()
#    sql = "select title,score_status from animation where score_status like '%升%'"
#    cur.execute(sql)
#    ret = cur.fetchall()
#    conn.commit()
#    cur.close()
#    conn.close()
#    msg = []
#    for i in ret:
#        text = '%s：%s' % (i[0],i[1])
#        msg.append(text)
#    m = '\n'.join(msg)
#    await send_msg(m)


#@nonebot.scheduler.scheduled_job('cron', hour='0', minute='5')
#async def qian():
#    bot = nonebot.get_bot()
#    g_list = await bot.get_group_list()
#    gid = random.choice(g_list).get('group_id')
#    pic = random.choice(os.listdir('/home/pro_coolq/data/image/pixiv'))
#    pici = '/home/pro_coolq/data/image/pixiv/%s' % pic
#    msg = '蕾姆明白，昴是不会放弃未来的人'
#    await qiandao('Re:从零开始的异世界生活',msg,pici,gid)
#    os.remove(pici)
#@nonebot.scheduler.scheduled_job('interval', seconds=5)
#async def qian():
#    bot = nonebot.get_bot()
#    await bot.send_group_msg(group_id=949377627,message='测试')

#@nonebot.scheduler.scheduled_job('interval', seconds=6666)
#async def qia():
#    bot = nonebot.get_bot()
#    g_list = await bot.get_group_list()
#    gid = random.choice(g_list).get('group_id')
#    headers = {
#        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
#    }
#    ret = requests.get('http://www.xiachufang.com/activity/site/?order=hot',headers=headers).text
#    html = etree.HTML(ret)
#    lis = html.xpath('//div[@class="ias-container"]/div/ul/li')[0]
#    img = lis.xpath('./div/div[1]/img/@data-src')[0].split('@')[0]
#    title = lis.xpath('./div/div[1]/img/@alt')[0]
#    desc = lis.xpath('./div/p[@class="desc"]/text()')[0].strip()
#    msg = title + '\n' + desc
#    with open('/home/pro_coolq/data/image/cai.jpg','wb') as f:
#        f.write(requests.get(img).content)
#    await bot.send_group_msg(group_id=gid, message='[CQ:image,file=cai.jpg]%s' % msg)
@nonebot.scheduler.scheduled_job('interval', seconds=9999)
async def shuo():
    bot = nonebot.get_bot()
    cookie = await bot.get_cookies()
    cookie = str(cookie)
    with open('/home/bot_cookie','w') as f:
        f.write(cookie)
