import hashlib
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import asyncio
import httpx
from . import tencent_talk
import os
from aip import AipOcr
import urllib.parse
from PIL import Image, ImageFilter,ImageOps
from lxml import etree
import time
import base64
from nonebot import on_command, CommandSession, on_notice,NoticeSession,on_request, RequestSession
import nonebot
import requests
import re
import random
import json
import pymysql
import redis
from datetime import datetime,timedelta
from matplotlib import pyplot as plt
from awesome.plugins.zzkia.api.nokia import generate_image


rd = redis.Redis(host="127.0.0.1", port="6379",db=5,decode_responses=True)


class Translate:
    def md5_b(self, key):
        m = hashlib.md5()
        m.update(key.encode('utf-8'))
        return m.hexdigest()


    def sign_b(self, key, salt):
        sign = 'fanyideskweb' + key + str(salt) + 'n%A-rKaT5fb[Gy?;N5@Tj'
        return self.md5_b(sign)


    def translate(self, key, fro="AUTO", to="AUTO"):
        url = 'http://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule'
        salt = str(int(time.time()*1000) + random.randint(0, 10))
        data = {
            "i": key,
            "from": fro,
            "to": to,
            "smartresult": "dict",
            "client": "fanyideskweb",
            "ts": salt[:-1],
            "salt": salt,
            "sign": self.sign_b(key, salt),
            "bv": self.md5_b("5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"),
            "doctype": "json",
            "version": "2.1",
            'keyfrom': 'fanyi.web',
            'action': 'FY_BY_REALTIME',
            # 'typoResult': 'false'
        }

        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            "Content-Length": "272",
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie': 'OUTFOX_SEARCH_USER_ID=-995880639@10.168.8.64; JSESSIONID=aaa4S2JviOjAFe8LvizRw; '
                      'OUTFOX_SEARCH_USER_ID_NCOO=2146618943.795375; ___rl__test__cookies=1558425516486',
            'Host': 'fanyi.youdao.com',
            'Origin': 'http://fanyi.youdao.com',
            'Referer': 'http://fanyi.youdao.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                          ' (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }

        res = requests.post(url, data=data, headers=headers).json()
        if res['type'] == "zh-CHS2en" and random.choice([0,1]):
           return self.translate(key, fro="zh-CHS", to="ja")

        result = res['translateResult'][0]
        return ' '.join([i['tgt'] for i in result])

def getBKN(skey):
    length = len(skey)
    hash = 5381
    for i in range(length):
        hash += (hash << 5) + ord(skey[i])
    return hash & 0x7fffffff # 计算bkn

async def qiandao(location, text, pic,g,self_id):
    bot = nonebot.get_bot()
    g_list = await bot.get_group_list()
    cookie = await bot.get_cookies()
    cookie = str(cookie)
    skey = re.findall(r"skey=(.+?)'",cookie)[0]
    headers = {
    'Cookie': 'uin=o0%s; skey=%s;' % (self_id,skey.replace(';','')),
    }
    if not g_list:
        g_list = []
        glist = await bot.get_group_list()
        for g in glist:
            group_id=g.get('group_id')
            g_list.append(group_id)

    bkn = getBKN(skey)
    url = 'https://qun.qq.com/cgi-bin/qiandao/sign/publish'
    if pic:
        async with httpx.AsyncClient() as client:
            c = await client.get(pic,timeout=5)
            c = c.content
        #if arg:
        #    with open('/home/setu/qq.jpg','wb') as f:
        #        f.write(c)

        #    im = Image.open('/home/setu/qq.jpg')
        #    im2 = im.filter(ImageFilter.MyGaussianBlur(radius=10))
        #    im2.save('/home/qq_image_result.jpg')
        #    c = open('/home/qq_image_result.jpg','rb')
        #    c = c.read()
        data = {
            'bkn':str(getBKN(skey)),
            'pic_up':str(base64.b64encode(c).decode())
        }
        async with httpx.AsyncClient() as client:
            res = await client.post('https://qun.qq.com/cgi-bin/qiandao/upload/pic',data=data,headers=headers,timeout=5)
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
    async with httpx.AsyncClient() as client:
        await client.post(url, data=data, headers=headers)


def select_db(args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select title,score from animation where title not like '%僅限%' order by score limit "+str(args)+", 10"
        cur.execute(sql)
        ret = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)

def select_db_g(args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select title,score from animation where title not like '%僅限%' and score not like '%暂无%' order by score desc limit "+str(args)+", 10"
        cur.execute(sql)
        ret = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)

def select_db2(args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select title,score from animation where title like %s"
        cur.execute(sql,['%' + args + '%'])
        ret = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)

def select_db3(*args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select user_id,sum(count) from qq_active where group_id=%s and publish_date between %s and %s GROUP BY user_id order by sum(count) desc;"
        cur.execute(sql,args)
        ret = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)

def select_db4(*args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select count from qq_active where group_id=%s and user_id=%s and publish_date=%s"
        cur.execute(sql,args)
        ret = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)

def select_db_self7(*args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select publish_date,count from qq_active where group_id = %s and user_id = %s and publish_date between %s and %s"
        print(args)
        cur.execute(sql,args)
        ret = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)

def select_db33(*args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select user_id,sum(count) from qq_active where group_id=%s and publish_date between %s and %s GROUP BY user_id order by sum(count);"
        cur.execute(sql,args)
        ret = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)


@on_command('命令', aliases=('命令','功能','帮助','菜单','help'),only_to_me=False)
async def mingling(session: CommandSession):
    arg_text = session.ctx['raw_message'].strip()
    if len(arg_text)==2:
        if session.ctx['group_id'] == 233269216:
            order_list = [
                '排行1，可以查看b站番剧总播放量前10，2查看连载中的，3查看近期上线的',
                '活跃1，可查询群内活跃度排行，只输活跃查看自己',
                '低分1，查询b站低分番剧, 下架、隐藏、高分同理',
                'online，b站大家都在看什么',
                '头像，后可加：男、女、动漫',
                '查分 番名，可查看番剧评分',
                '改名，谁改的名',
                '搜番+番剧图片,搜索图片来源(仅限番剧截图)',
                '搜图+p站图片,搜索p站来源',
                '主人qq：736209298，b站：玩好吃好喝好，微博：p站前线姬。支持作者可发红包赞助一波，不定时添加新功能',
                ]
        else:

            order_list = [
                '———蕾姆食用方法———',
                '★蕾の简介★   ★蕾の人设★',
                '★蕾の功能★   ★蕾の娱乐★',
                '★蕾の群管★   ★蕾の卡牌★',
                '★蕾の主人★   ★蕾の教学★',
                '★蕾の活跃★   ★蕾のbili★',
                '★例如输入：蕾的功能',
                '————————————',
            ]
        await session.send('\n'.join(order_list))
        
@on_command('低分', aliases=('低分'),only_to_me=False)
async def difen(session: CommandSession):
    arg_text = session.ctx['raw_message'].replace('低分','').strip()
    if arg_text.isdigit():
        if 0 <= int(arg_text) - 1:
            if arg_text == '':
                arg_text = 1
            ret3s = select_db(int(arg_text)-1)
            msg = 'b站低分%s-%s名：' % (arg_text,int(arg_text)+9)
            for i in ret3s:
                msg += ('\n%s：%s' % (i[0],i[1]))
            await session.send('@%s\n' % session.ctx['sender']['card'] + msg)

@on_command('高分', aliases=('高分'),only_to_me=False)
async def gaofen(session: CommandSession):
    arg_text = session.ctx['raw_message'].replace('高分','').strip()
    if arg_text.isdigit():
        if 0 <= int(arg_text) - 1:
            if arg_text == '':
                arg_text = 1
            ret3s = select_db_g(int(arg_text)-1)
            msg = 'b站高分%s-%s名：' % (arg_text,int(arg_text)+9)
            for i in ret3s:
                msg += ('\n%s：%s' % (i[0],i[1]))
            await session.send('@%s\n' % session.ctx['sender']['card'] + msg)

@on_command('翻译', aliases=('翻译'),only_to_me=False)
async def fanyi(session: CommandSession):
    arg_text = session.ctx['raw_message'].replace('翻译','').strip()
    if 'CQ' in arg_text:
        return
    t = Translate()
    ret = t.translate(arg_text)
    await session.send(ret)

def select_total_active(*args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select sum(count) from qq_active where group_id = %s and user_id = %s"
        cur.execute(sql,args)
        ret = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)


def select_db_gtotal(*args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select publish_date,sum(count) from qq_active where group_id = %s and publish_date between %s and %s group by publish_date"
        print(args)
        cur.execute(sql,args)
        ret = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)



@on_command('活跃', aliases=('总活','群总','群活'),only_to_me=False)
async def huoyue(session: CommandSession):
    #bot = nonebot.get_bot()
    arg_text = session.ctx['raw_message'].replace('活跃','',1).strip().replace('－','-')
    if '[C' in session.ctx['raw_message']:
        user_id = re.findall(r'\[CQ:at,qq=(\d+)\]', session.ctx['raw_message'])[0]
        #bot = nonebot.get_bot()
        info = await session.bot.get_group_member_info(group_id=session.ctx['group_id'],user_id=user_id)
        nickname = info.get('card')
        nickname = nickname if nickname else info.get('nickname')
    else:
        user_id = session.ctx['user_id']

    if session.ctx['raw_message'].startswith('总活跃'):
        if '[C' in session.ctx['raw_message']:
            msg = '%s 在此群的总活跃数' % nickname
        else:
            msg = '您在此群的总活跃数'
        total_num = select_total_active(session.ctx['group_id'],user_id)[0]
        await session.send('%s：%s' % (msg,total_num))
        return
    elif '图' in session.ctx['raw_message']:
        d2 = datetime.now().strftime('%Y-%m-%d')
        d1 = (datetime.now()-timedelta(days=6)).strftime('%Y-%m-%d')
        if '群' in session.ctx['raw_message']:
            msg = '近7天群总活跃图'
            rets = select_db_gtotal(session.ctx['group_id'],d1,d2)
        else:
            if '[C' in session.ctx['raw_message']:
                msg = '%s 近7天活跃统计' % nickname
            else:
                msg = '您近7天活跃统计'
            rets = select_db_self7(session.ctx['group_id'],user_id,d1,d2)
        x = [(datetime.now()-timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6,-1,-1)]
        y = []
        rets = {i[0].strftime('%Y-%m-%d'):i[1] for i in rets}
        for i in x:
            y.append(rets.get(i,0))
        plt.figure(figsize=(18,12),dpi=60)
        plt.plot(x,y)
        plt.xticks(x,rotation=45)
        c = 0
        for i in y:
            plt.text(c,y[c],'%s' % y[c],fontdict={'size': 30, 'color':  'red'})
            c += 1
        if session.ctx['self_id'] == 302554188:
            plt.savefig('/home/pro_coolq/data/image/huoyue.jpg')
        else:
            plt.savefig('/home/2coolq/data/image/huoyue.jpg')
        await session.send(message='%s[CQ:image,file=huoyue.jpg]' % msg)
        return


    elif arg_text.replace('-','').replace('－','').isdigit():
        if int(arg_text) >= 1:
            rets = select_db3(session.ctx['group_id'],(datetime.now()-timedelta(days=(int(arg_text)-1))).strftime('%Y-%m-%d'),datetime.now().strftime('%Y-%m-%d'))
            msg = '近%s天活跃度排行,活跃人数%s' % (arg_text,len(rets))
    
        elif int(arg_text) <= -1:
            d = (datetime.now()-timedelta(days=abs(int(arg_text)))).strftime('%Y-%m-%d')
            rets = select_db3(session.ctx['group_id'],d,d)
            msg = '%s活跃度排行,活跃人数%s' % (d,len(rets))
        c = 0
        for i in rets:
            c += 1
            count = i[1]
            if c < 11:
                user_id = i[0]
                try:
                    info = await session.bot.get_group_member_info(group_id=session.ctx['group_id'],user_id=user_id)
                    nickname = info.get('card')
                    nickname = nickname if nickname else info.get('nickname')
                    nickname = nickname.replace('\n','')
                except:
                    nickname = user_id
                if c == 1:
                    msg += '\n%s、%s：%s' % ('[CQ:emoji,id=127942]',nickname,count)
                else:
                    msg += '\n%s、%s：%s' % (c,nickname,count)
        await session.send(msg)
        return
   
    elif arg_text == '' or 'CQ' in session.ctx['raw_message']:
        if '[C' in session.ctx['raw_message']:
            msg = '%s 今日活跃次数' % nickname
        else:
            msg = '您今日活跃次数'
        print(user_id)
        total_num = select_db4(session.ctx['group_id'],user_id,datetime.now().strftime('%Y-%m-%d'))[0]
        await session.send('%s：%s' % (msg,total_num))
        return


@on_command('天气', aliases=('天气'),only_to_me=False)
async def weather(session: CommandSession):
    bot = nonebot.get_bot()
    arg_text = session.ctx['raw_message'].replace('天气','').strip().replace('省','').replace('市','').replace('区','')
    async with httpx.AsyncClient() as client:
        ret = await client.get('https://www.tianqiapi.com/api/?version=v6&city=%s&appid=45434669&appsecret=mJLZcVd9' % arg_text)
        ret = ret.json()
    if arg_text not in ['北京','上海'] and ret['city'] in ['北京','上海']:
        return
    msg = '%s %s %s到%s摄氏度 %s%s，当前温度：%s摄氏度' % (ret['city'],ret['wea'],ret['tem2'],ret['tem1'],ret['win'],ret['win_speed'],ret['tem'])
    info = await bot.get_group_member_info(group_id=session.ctx['group_id'],user_id=session.ctx['user_id'])
    nickname = info.get('card') if info else None
    nickname = nickname if nickname else session.ctx['sender']['nickname']
    msg = '%s %s %s到%s摄氏度\n%s%s，当前温度：%s摄氏度' % (ret['city'],ret['wea'],ret['tem2'],ret['tem1'],ret['win'],ret['win_speed'],ret['tem'])
    await session.send(msg)
    #generate_image(msg)
    #await qiandao('主人qq736209298','@ '+nickname,'http://47.101.42.136:6/rbq/duanxin.jpg', session.ctx.get('group_id'))

@on_command('查分', aliases=('查分'),only_to_me=False)
async def chafen(session: CommandSession):
    arg_text = session.ctx['raw_message'].replace('查分','').strip()
    async with httpx.AsyncClient() as client:
        
        items1 = await client.get('https://api.bilibili.com/x/web-interface/search/type?search_type=media_bangumi&page=1&keyword=%s&__refresh__=true&single_column=0' % arg_text,timeout=3)
        items1 = items1.json()['data']
    if not items1.get('result'):
        items1 = []
    else:
        items1 = items1['result'][:5]
    async with httpx.AsyncClient() as client:
        items2 = requests.get('https://api.bilibili.com/x/web-interface/search/type?search_type=media_ft&page=1&keyword=%s&__refresh__=true&single_column=0' % arg_text,timeout=3)
        items2 = items2.json()['data']
    if not items2.get('result'):
        items2 = []
    else:
        items2 = items2['result']

    items = items1 + items2

    msg = '------- bilibili -------'
    if not items:
        for i in select_xiajia(arg_text):
            msg += '\n%s：%s(下架)' % (i[0],i[1])
    else:
        for i in items:
            if i.get('media_score'):
                score = str(i['media_score']['score']) + '分'
            else:
                continue
            msg += ('\n%s：%s' % (i['title'].replace('<em class="keyword">','').replace('</em>',''),score))


    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36'}
    async with httpx.AsyncClient() as client:
        html = await client.get('https://bangumi.tv/subject_search/%s?cat=2' % arg_text,headers=headers,timeout=3)
        html = html.content.decode()
    html = etree.HTML(html)
    lis = html.xpath("//ul[@id='browserItemList']/li")
    text = '\n------- bangumi -------'
    for li in lis[:10]:
        title = li.xpath('./div/h3/a/text()')[0]
        try:
            score = li.xpath('./div/p/small/text()')[0] + '分'
        except:
            continue
        text += '\n%s：%s' % (title,score)
    #async with httpx.AsyncClient() as client:
    #    html = await client.get('https://www.douban.com/search?cat=1002&q=%s' % arg_text,headers=headers,timeout=3)
    #    html = html.content.decode()
    #html = etree.HTML(html)
    #lis = html.xpath("//div[@class='result-list']/div")
    #res = '\n------- douban -------'
    #for li in lis[:10]:
    #    try:
    #        title = li.xpath(".//div[@class='title']//a/text()")[0]
    #        score = li.xpath(".//div[@class='title']//span[@class='rating_nums']/text()")[0] + '分'
    #    except:
    #        continue
    #    res += '\n%s：%s' % (title,score)
    await session.send(msg+text)

@on_command('搜番', aliases=('搜番'),only_to_me=False)
async def fan(session: CommandSession):
    #if session.ctx['group_id'] in [333269216]:
    #    return
    pic = ''
    for i in session.ctx['message']:
        if i['type'] == 'image':
            pic = i['data']['url']
    if pic:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get('https://trace.moe/api/search?url='+pic, timeout=10)  # 获取trace.moe的返回信息
            response.encoding = 'utf-8'  # 把trace.moe的返回信息转码成utf-8
            result = response.json()  # 转换成json格式
            if 'Error' in result:
                await session.send('暂时没有找到，图片必须是完整清晰的番剧截图，请注意')
                return
            animename = result["docs"][0]["title_chinese"]  # 切片番剧名称
            similarity = result["docs"][0]["similarity"]  # 切片相似度
            time = result["docs"][0]["at"]  # 切片时间
            episode = result["docs"][0]["episode"]  # 切片集数
            msg = "番剧名称：" + animename + " 第" + str(episode) + "集" + '\n' +"相似度：" + str(round(similarity,4)*100)[:5]+"%"+ '\n' + "时间：" + str(time / 60).split('.')[0] + '分' + str(time % 60).split('.')[0] + '秒'
            await session.send(msg+'\n图片必须是完整的动漫截图才可以哦，因为原理是记录每张完整动漫截图的特征，没记录同人图和不完整的')
 
            return
        except:
            await session.send('暂时没找到，必须是完整番剧截图，请重试')

@on_command('搜图', aliases=('搜图'),only_to_me=False)
async def soutu(session: CommandSession):
    pic = ''
    for i in session.ctx['message']:
        if i['type'] == 'image':
            pic = i['data']['url']
    if pic:
        try: 
            async with httpx.AsyncClient() as client:
                response = await client.get('https://saucenao.com/search.php?api_key=8b7b2df2fb5bebb93b4023885889ef453fd3ee53&db=999&output_type=2&testmode=1&numres=1&url='+pic, timeout=20)  # 获取trace.moe的返回信息
            response.encoding = 'utf-8'  # 把trace.moe的返回信息转码成utf-8
            result = response.json()["results"][0]
        except:
            await session.send('要被玩坏了啦~')
            return
        if result: # 转换成json格式
            similarity = str(result["header"]["similarity"])
            url = result["data"]["ext_urls"][0]  
            try:
                title = result["data"]["title"] 
                pixiv_id = str(result["data"]["pixiv_id"])
                member_name = result["data"]["member_name"] 
                mid = result["data"]["member_id"] 

                #msg = '图片标题：'+title+'\n作者：'+member_name+'，ID：'+pixiv_id+'\n相似度：'+similarity+'%'
                msg = '图片标题：'+title+'\n作者：'+member_name+'\n作者id：'+ str(mid) +'\n作品id：'+pixiv_id+'\n相似度：'+similarity+'%\n'+url
                await session.send(msg)
                return
            except:
                try:
                    msg = '\n'.join([str(i) for i in result["data"].values() if isinstance(i,(str,int))])
                    await session.send(msg)
                    return
                except:
                    await session.send('要被玩坏了啦~')

@on_notice('group_increase')
async def _(session: NoticeSession):
    group_id = session.ctx.get('group_id')
    user_id = session.ctx.get('user_id')
    bot = nonebot.get_bot()
    info = await bot.get_group_member_info(group_id=group_id,user_id=user_id)
    name = info.get('nickname')
    #dir_list = os.listdir('/home/pro_coolq/data/record/dashu/welcome')
    #file = 'dashu/welcome/' + random.choice(dir_list)
    a = random.choice([1])
    if a == 1:
        l = ['萌新，快到碗里来~','欢迎欢迎，进群就是一家人了','欢迎欢迎，我们的大家庭又有新成员了','欢迎，进群就别想走了哦~','欢迎！举朵小花欢迎你！','我是蕾姆，今后还请多多指教~',]
        await session.send('@%s %s' % (name,random.choice(l)))
    elif a == 2:
        file = os.listdir('/home/pro_coolq/data/record/welcome')
        await session.send('[CQ:record,file=welcome/%s]' % random.choice(file))
    elif a == 3:
        async with httpx.AsyncClient() as client:
            items = await client.get('https://api.pixivic.com/illustrations?keyword=%s&page=%s' % ('蕾姆',random.randrange(1,3)), timeout=5)
        item = random.choice(items.json()['data'])
        pic = item['imageUrls'][0]['medium'].replace('i.pximg.net','img.cheerfun.dev:233')
        h = {
            'Referer': 'https://pixivic.com/popSearch',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
            }
        with open('/home/pro_coolq/data/image/cai.jpg','wb') as f:
            f.write(requests.get(pic,headers=h,timeout=3).content)
        await session.send(message='欢迎新人入侵~[CQ:image,file=cai.jpg]我是蕾姆，请多指教！')
    elif a == 4:
        location = 'Re:从零开始的异世界生活'
        text = '%s，欢迎新人入群喵~' % name
        await qiandao(location, text, '',group_id,arg=None)


@on_command('改名', aliases=('起名',),only_to_me=False)
async def qiming(session: CommandSession):
    arg_text = session.ctx['raw_message'].replace('起名','',1).replace('改名','',1).strip()
    if 'CQ' in arg_text and session.ctx['user_id'] != 736209298:
        return
    if not arg_text:
        return
    role = session.ctx['sender']['role']
    j = 0
    user_id = session.ctx['user_id']
    group_id = session.ctx['group_id']
    if session.ctx['user_id'] != 736209298 and session.ctx.get('group_id') not in [875164857,686950644,736742903]:
        p = select_db_score(user_id,group_id)
        if p:
            score = p[1]
            if score >= 10:
                tscore = score-10
                update_db_score(tscore, p[0])
                msg = '更改成功\n消耗10圣金币\n剩余：%s圣金币' % tscore
                j = 1
            else:
                msg = '更改失败\n圣金币不足\n剩余：%s圣金币' % score
        else:
            msg = '更改失败\n圣金币不足\n可以签到获得哦'
    else:
        msg = '更改成功，欧尼酱~'
        j = 1

    if j == 0:
        await session.send(msg)
        return
    if 'CQ' in arg_text:
        qq = re.findall(r'\[CQ:at,qq=(\d+?)\]',session.ctx['raw_message'])[0]
        arg_text = session.ctx['raw_message'].split(']')[-1].strip()
    else:
        qq = session.ctx.get('self_id')
    bot = nonebot.get_bot()
    await bot.set_group_card(group_id=session.ctx.get('group_id'),user_id=qq,card=arg_text)
    await session.send(msg)
    info = await bot.get_group_member_info(group_id=session.ctx['group_id'],user_id=session.ctx['user_id'])
    nickname = info.get('card')
    nickname = nickname if nickname else info.get('nickname')
    msg = '改名人：%s（%s）\n时间：%s' % (nickname,session.ctx['user_id'],datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    with open('/home/qiming_log','r') as f:
        qiming_data = json.load(f)
    qiming_data[session.ctx['group_id']] = msg
    with open('/home/qiming_log','w') as f:
        json.dump(qiming_data, f)
    
@on_command('排行', aliases=('排行'),only_to_me=False)
async def rank(session: CommandSession):
    if not session.ctx['raw_message'].startswith('排行'):
        return
    arg = session.ctx['raw_message'].replace('排行','').strip()
    if arg not in ['1','2','3']:
        return
    
    today = datetime.now()
    m = {1:1,2:1,3:1,4:4,5:4,6:4,7:7,8:7,9:7,10:10,11:10,12:10}
    if arg == '1':
        text = 'b站番剧总播放量前10：'
        l = requests.get('https://api.bilibili.com/pgc/season/index/result?season_version=-1&area=-1&is_finish=-1&copyright=-1&season_status=-1&season_month=-1&year=-1&style_id=-1&order=2&st=1&sort=0&page=1&season_type=1&pagesize=10&type=1',timeout=3).json()['data']['list']
    elif arg == '2':
        text = 'b站连载中番剧播放量前10：'
        l = requests.get('https://api.bilibili.com/pgc/season/index/result?season_version=1&area=2&is_finish=0&copyright=-1&season_status=-1&season_month=-1&year=-1&style_id=-1&order=2&st=1&sort=0&page=1&season_type=1&pagesize=10&type=1',timeout=3).json()['data']['list']
    else:
        text = 'b站近期上线番剧播放量前10：'
        l = requests.get('https://api.bilibili.com/pgc/season/index/result?season_version=1&area=2&is_finish=0&copyright=-1&season_status=-1&season_month='+str(m[today.month])+'&year=%5B'+str(today.year)+'%2C'+str(today.year+1)+')&style_id=-1&order=2&st=1&sort=0&page=1&season_type=1&pagesize=10&type=1',timeout=3).json()['data']['list']
        if not l:
            if today.month == 1:
                l = requests.get('https://api.bilibili.com/pgc/season/index/result?season_version=1&area=2&is_finish=0&copyright=-1&season_status=-1&season_month=10&year=%5B'+str(today.year-1)+'%2C'+str(today.year)+')&style_id=-1&order=2&st=1&sort=0&page=1&season_type=1&pagesize=10&type=1').json()['data']['list']
            else:
                l = requests.get('https://api.bilibili.com/pgc/season/index/result?season_version=1&area=2&is_finish=0&copyright=-1&season_status=-1&season_month='+str(m[today.month-1])+'&year=%5B'+str(today.year)+'%2C'+str(today.year+1)+')&style_id=-1&order=2&st=1&sort=0&page=1&season_type=1&pagesize=10&type=1',timeout=3).json()['data']['list']
    for i in range(len(l)):
        if '僅限' not in l[i]['title']:
            text += '\n%s：%s' % (l[i]['title'], l[i]['order'].replace('次播放',''))
    await session.send(text)

@on_command('点歌', aliases=('点歌'),only_to_me=False)
async def diange(session: CommandSession):
    if session.ctx['group_id'] in [333269216]:
        return
    role = session.ctx['sender']['role']
    if session.ctx['user_id'] != 736209298 and role == 'member':
        return
    arg_text = session.ctx['raw_message'].split('点歌')[1].strip()
    if '点歌' not in session.ctx['raw_message']:
        return
    #with open('/home/awesome-bot/pixiv','r') as f:
    #    t1 = f.read()
    #if int(time.time()) - int(t1) < 10:
    #    return
    #with open('/home/awesome-bot/pixiv','w') as f:
    #    f.write(str(int(time.time())))
    a = random.choice([1,2])
    if a == 1:
        header = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36'}
        url = 'http://music.163.com/api/search/get/web?csrf_token=hlpretag=&hlposttag=&s={}&type=1&offset=0&total=true&limit=1'
        respone = requests.get(url.format(arg_text), headers = header)
        songid = re.search('"id":.*?(.*?),', respone.text, re.IGNORECASE)
        await session.send('[CQ:music,type=163,id={}]'.format(songid.group().strip('"id": | ,')))
    else:
        url = 'https://c.y.qq.com/soso/fcgi-bin/client_search_cp?g_tk=5381&p=1&n=20&w={}&format=json&loginUin=0&hostUin=0&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0&remoteplace=txt.yqq.song&t=0&aggr=1&cr=1&catZhida=1&flag_qc=0'
        songid = requests.get(url.format(arg_text)).json()['data']['song']['list'][0]['songid']

        s1 = 'https://i.y.qq.com/v8/playsong.html?_wv=1&songid=%s&souce=qqaio&ADTAG=aiodiange' % songid
        h = {
            'User-Agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Mobile Safari/537.36'
        }
        ret = requests.get(s1,headers=h).text
        audio = re.findall(r'src="(http://aqqmusic\.tc\.qq\.com/amobile\.music\.tc\.qq\.com/.+?)"',ret)[0]
        title = re.findall(r'"songname":"(.+?)"',ret)[0]
        desc = re.findall(r'"title":".+?_(.+?)_在线试听',ret)[0]+'\n主人说不要点太快哦~'
        pic = 'http:' + re.findall(r'"pic":"(.+?)"',ret)[0]
        await session.send('[CQ:music,type=custom,url=%s,title=%s,content=%s,image=%s,audio=%s]' % (s1,title,desc,pic,audio))
        #with open('/home/pro_coolq/data/record/song.m4a','wb') as f:
        #    f.write(requests.get(audio).content)
        #await session.send('[CQ:record,file=song.m4a]')
        #comment = requests.get('https://c.y.qq.com/base/fcgi-bin/fcg_global_comment_h5.fcg?format=json&inCharset=utf8&outCharset=GB2312&notice=0&platform=yqq.json&needNewCode=0&reqtype=2&biztype=1&topid=%s&cmd=8&needmusiccrit=0&pagenum=0&pagesize=25' % songid).json()['comment']['commentlist'][0]['rootcommentcontent']
        #await session.send('歌曲评论：\n'+comment)
         

def turn_on(id):
    try:
        r = redis.Redis(host="127.0.0.1", port="6379",db=5)
        r.srem('g',id)
    except Exception as e:
        print(e)

def turn_off(id):
    try:
        r = redis.Redis(host="127.0.0.1", port="6379",db=5)
        r.sadd('g',id)
    except Exception as e:
        print(e)


@on_command('换头', aliases=('换头'),only_to_me=False)
async def huantou(session: CommandSession):
    arg = session.ctx['raw_message']
    if arg != '换头':
        return

    j = 0
    user_id = session.ctx['user_id']
    group_id = session.ctx['group_id']
    p = select_db_score(user_id,group_id)
    if p:
        score = p[1]
        if score >=10:
            tscore = score-10
            update_db_score(tscore, p[0])
            msg = '换头像成功\n消耗10圣金币\n剩余：%s圣金币' % tscore
            j = 1
        else:
            msg = '换头像失败\n圣金币不足\n剩余：%s圣金币' % score
    else:
        msg = '换头像失败\n圣金币不足\n可以签到获得哦'

    if j == 0:
        await session.send(msg)
        return

    bot = nonebot.get_bot()
    cookie = await bot.get_cookies()
    cookie = str(cookie)
    skey = re.findall(r"skey=(.+?)'",cookie)[0]
    headers = {
    'Cookie': 'uin=o0%s; skey=%s;' % (session.ctx['self_id'],skey.replace(';','')),
    }
    head_info_list = requests.get('https://ti.qq.com/mqqbase/cgi/history/face/list?timestamp=%s&num=50&need_cur=0&filter_type=0' % int(time.time()),headers=headers,timeout=3).json()['data']['head_info_list']
    fileid = random.choice(head_info_list)['fileid']
    code = requests.get('https://ti.qq.com/mqqbase/cgi/history/face/set?str_fileid=%s' % fileid,headers=headers,timeout=3).json()['code']
    if code == 0:
        await session.send(msg)

#    else:
#        pic = ''
#        for i in session.ctx['message']:
#            if i['type'] == 'image':
#                pic = 'https://gchat.qpic.cn/gchatpic_new/%s/%s--%s/0' % (session.ctx['user_id'],session.ctx['group_id'],i['data']['file'].split('.')[0])
#                break
#        if pic:
#            data = {
#                'clientuin': 302554188,
#                'clientkey': 'D8F749E579B057CFD27C45626CE4E95701E5191E550F73047E5E4B564E58BBAE',
#                'sign': 'F284F0A624201535D3CA0C97CD3626290DD85725A7960A663B3EDF1E4ADAC6A37D7F7B1CC33A47C5A80A05FF3C3FF535',
#                'usertype': 1,
#                'filetype': 5,
#                'imagetype': 1,
#                'Localeid': 2052,
#                'CldVer': 5665,
#                'sourceid': 0,
#            }
#            headers = {
#                'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)'
#            }
#            img_data = requests.get(pic).content
#            files = [('customfacefile', ('customfacefile', img_data, 'application/octet-stream'))]
#            res = requests.post('https://cface.qq.com/cgi-bin/cface/upload4',data=data,files=files,headers=headers).content
#            print(res.decode())
 ##           if '200' in res.decode():
  #              await session.send('换头成功')
 #           else:
#                await session.send('换头失败，此功能失效')
#
#def select_ciku(q):
#    try:
#        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
#        cur = conn.cursor()
#        sql = "select answer from ciku where question like '%"+q+"%'" 
#        cur.execute(sql)
#        ret = cur.fetchall()
#        cur.close()
#        conn.close()
#        return ret
#    except Exception as e:
#        print(e)
@on_command('tu', aliases=('tu'),only_to_me=True)
async def tuling(session: CommandSession):
    if session.ctx['group_id'] in [838343455]:
        return
    for i in session.ctx['message']:
        if i['type'] == 'text':
            arg = i['data']['text'].replace('tu','').strip()
    if not arg:
        await session.send('?')
        return
    rems = rd.hkeys('rem')
    ret = process.extract(arg, rems, limit=1, scorer=fuzz.token_set_ratio)[0]
    if ret[1] > 50:
        callback_msg = random.choice(rd.hget('rem',ret[0]).split('|'))
    else:
        bot = nonebot.get_bot()
        ai_obj = tencent_talk.AiPlat('2128554885', 'FMPEttRpwhngDj2K')
        rsp = ai_obj.getNlpTextChat(10000,arg)
        callback_msg = rsp['data']['answer'].replace('小豪豪','蕾姆').replace('?','喵？').replace('？','喵？')
        if '中东' in callback_msg:
            callback_msg = '喵？'
    #ciku_insert([arg,callback_msg])
    await session.send(callback_msg[:200])
#@on_command('pr', aliases=('pr'))
#async def tuling(session: CommandSession):
#    if session.ctx['user_id'] != 1538482349:
#        return
#    text = ''
#    image = 0
#    if 'image' in session.ctx['raw_message']:
#        image = 1
#        with open('/home/pro_coolq/data/image/pr.jpg','wb') as f:
#            f.write(requests.get(session.ctx['message'][0]['data']['url']).content)
#    else:
#        text = session.ctx['message'][0]['data']['text'][2:].strip().replace('早苗','蕾姆')
#        #text = session.ctx['message'][0]['data']['text'][2:].strip().replace('浅羽','蕾姆').replace('澪','拉姆')
#    bans = ['命令','领养','介绍']
#    for i in bans:
#        if i in text:
#            return
#    bot = nonebot.get_bot()
#    if image == 1:
#        await bot.send_group_msg(group_id=talk_group,message='%s[CQ:image,file=pr.jpg]' % text)
#    else:
#        await bot.send_group_msg(group_id=talk_group,message=text)

@on_command('换牌', aliases=('换牌'),only_to_me=False)
async def huanpai(session: CommandSession):
    arg = session.ctx['raw_message']
    if arg == '换牌':
        bot = nonebot.get_bot()
        g_list = await bot.get_group_list()
        cookie = await bot.get_cookies()
        cookie = str(cookie)
        skey = re.findall(r"skey=(.+?)'",cookie)[0]
        headers = {
        'Cookie': 'uin=o0%s; skey=%s;' % (session.ctx['self_id'],skey.replace(';','')),
        }
        gc = session.ctx['group_id']
        bkn = getBKN(skey)
        url = 'https://qun.qq.com/cgi-bin/qunwelcome/medal/set'
        res = requests.get('https://qun.qq.com/cgi-bin/qunwelcome/medal2/list?gc=%s&uin=%s&bkn=%s' % (gc,session.ctx['self_id'],bkn),headers=headers,timeout=3).json()['data']['list']
        item = random.choice([i for i in res if i.get('achieve_ts') != 0 and i.get('wear_ts') == 0])
        mask = item.get('mask')
        name = item.get('name')
        data = {
            'gc': gc,
            'bkn': bkn,
            'medal': mask,
        }
        res = requests.post(url, data=data, headers=headers,timeout=3)
        if res.json()["retcode"] == 0:
            await session.send('更换头衔成功：【%s】' % name)


@on_command('禁言', aliases=('禁言','牙卡','无路',),only_to_me=False)
async def jinyan(session: CommandSession):
    arg_text = session.ctx['raw_message'].replace('禁言','').strip()
    bot = nonebot.get_bot()
    qq = re.findall(r'\[CQ:at,qq=(\d+?)\]',arg_text)[0]
    if int(qq) in [736209298,302554188,1300294537]:
        return
    qqinfo = await bot.get_group_member_info(group_id=session.ctx['group_id'],user_id=int(qq))
    if session.ctx['sender']['role'] != 'member' and qqinfo['role'] != 'member': 
        return
    if '[CQ:at' in arg_text:
        if (session.ctx['sender']['role'] != 'member' or session.ctx['user_id'] == 736209298) or (session.ctx['user_id']==int(qq) and session.ctx['group_id'] in [950422325,949377627]):
            if session.ctx['user_id']==int(qq):
                await bot.set_group_ban(group_id=session.ctx['group_id'],user_id=qq,duration=60)
                return
            if arg_text.endswith(']'):
                jin_str = '1分钟'
            else:
                jin_str = arg_text.split(']')[-1].strip()
            if '分' in jin_str:
                jin_time = int(jin_str.replace('分','').replace('钟',''))*60
            elif '小时' in jin_str:
                jin_time = int(jin_str.replace('小时',''))*60*60
            elif '天' in jin_str:
                jin_time = int(jin_str.replace('天',''))*24*60*60
            elif '秒' in jin_str:
                jin_time = int(jin_str.replace('秒',''))
            elif jin_str == '0':
                jin_time = 0
            await bot.set_group_ban(group_id=session.ctx['group_id'],user_id=qq,duration=jin_time)


@on_command('去屎', aliases=('去屎','西内','洗内'),only_to_me=False)
async def jinyan(session: CommandSession):
    arg_text = session.ctx['raw_message'].replace('去屎','').strip()
    bot = nonebot.get_bot()
    qq = re.findall(r'\[CQ:at,qq=(\d+?)\]',arg_text)[0]
    qqinfo = await bot.get_group_member_info(group_id=session.ctx['group_id'],user_id=int(qq))
    if session.ctx['sender']['role'] != 'member' and qqinfo['role'] != 'member':
        return

    if '[CQ:at' in arg_text and (session.ctx['sender']['role'] != 'member' or session.ctx['user_id'] == 736209298):
        qq = re.findall(r'\[CQ:at,qq=(\d+?)\]',arg_text)[0]
        if int(qq) in [736209298,1300294537,302554188]:
            return
        await bot.set_group_kick(group_id=session.ctx['group_id'],user_id=qq)

@on_command('解禁', aliases=('解禁','然后','疯狂'),only_to_me=False)
async def jiejin(session: CommandSession):
    if session.ctx['sender']['role'] != 'member' or session.ctx['user_id'] == 736209298:
        arg_text = session.ctx['raw_message'].replace('解禁','').strip()
        bot = nonebot.get_bot()
        if '[CQ:at' in arg_text:
            qq = re.findall(r'\[CQ:at,qq=(\d+?)\]',arg_text)[0]
            await bot.set_group_ban(group_id=session.ctx['group_id'],user_id=qq,duration=0)
        else:
            await bot.set_group_whole_ban(group_id=session.ctx['group_id'],enable=False)


@on_command('全体', aliases=('全员','th','Th',),only_to_me=False)
async def jinyan(session: CommandSession):
    if session.ctx['sender']['role'] != 'member' or session.ctx['user_id'] == 736209298:
        arg_text = session.ctx['raw_message'][2:].strip()
        bot = nonebot.get_bot()
        if arg_text == '禁言':
            await bot.set_group_whole_ban(group_id=session.ctx['group_id'])
        elif 'orld' in session.ctx['raw_message']:
            await bot.set_group_whole_ban(group_id=session.ctx['group_id'])
            await session.send('[CQ:record,file=声音3.mp3]')
            #await session.send('[CQ:record,file=声音6.mp3]')
            #await session.send('[CQ:record,file=声音7.mp3]')
            #await session.send('[CQ:record,file=声音8.mp3]')
            #await session.send('[CQ:record,file=声音11.mp3]')
    elif 'orld' in session.ctx['raw_message']:
        dir_list = os.listdir('/home/pro_coolq/data/record/world')
        file = 'world/' + random.choice(dir_list)
        await session.send('[CQ:record,file=%s]' % file)

        

def select_db_yiyan(hid):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select id from yiyan where id=%s" % hid
        cur.execute(sql)
        ret = cur.fetchone()
       
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)

def select_xiajia(name):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select title,score from animate where title like '%"+name+"%'"
        cur.execute(sql)
        ret = cur.fetchall()

        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)


def insert_db_yiyan(*args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "insert into yiyan values(%s,%s,%s,%s)"
        cur.execute(sql,args)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(e)


def insert_kexue(*args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "insert into moukexue(ability,levels) values(%s,%s)"
        cur.execute(sql,args)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(e)


@on_command('一言', aliases=('一言'),only_to_me=False)
async def yiyan(session: CommandSession):
    if session.ctx['raw_message']=='一言':
        m = [['a','动漫'],['b','漫画'],['c','游戏'],['d','小说']]
        args = random.choice(m)
        ret = requests.get('https://v1.hitokoto.cn/?c=%s' % args[0]).json()
        hid = ret['id']
        text = ret['hitokoto']
        source = ret['from']
        if not select_db_yiyan(hid):
            insert_db_yiyan(hid,text,args[0],source)
        await session.send('%s\n——%s[%s]' % (text,source,args[1]))


#@on_command('死跃', aliases=('死跃'),only_to_me=False)
#async def huoyue(session: CommandSession):
#    arg_text = session.ctx['raw_message'].replace('死跃','').strip()
#    if arg_text == '':
#        arg_text = '1'
#    if arg_text.isdigit():
#        rets = select_db33(session.ctx['group_id'],(datetime.now()-timedelta(days=(int(arg_text)-1))).strftime('%Y-%m-%d'),datetime.now().strftime('%Y-%m-%d'))
#        bot = nonebot.get_bot()
#        msg = '近%s天死跃度排行,活跃人数%s' % (arg_text,len(rets))
##        c = 0
#        for i in rets:
#            c += 1
#            if c >= 21:
#                break
#            user_id = i[0]
#            count = i[1]
##            if int(user_id) == 1448444297 and random.choice([0,0]):
#                nickname = '[CQ:face,id=46]'
#            else:
#                try:
#                    info = await bot.get_group_member_info(group_id=session.ctx['group_id'],user_id=user_id)
#                    nickname = info.get('card')
#                    nickname = nickname if nickname else info.get('nickname')
#                except:
#                    nickname = user_id
#            if c == 1:
#                msg += '\n%s、%s：%s条' % ('[CQ:emoji,id=127942]',nickname,count)
#            else:
#                msg += '\n%s、%s：%s条' % (c,nickname,count)
#        await session.send(msg)

@on_command('短信', aliases=('短信'),only_to_me=False)
async def duanxin(session: CommandSession):
    msg = session.ctx['raw_message'].replace('短信','').strip()
    if '[' in msg:
        return
    if msg and '短信' in session.ctx['raw_message']:
    #if session.ctx['user_id'] == 736209298:
        generate_image(msg)
        await qiandao('Re：从零开始的异世界生活','您有一条新的短信消息','http://47.101.42.136:6/rbq/duanxin.jpg', session.ctx.get('group_id'),session.ctx.get('self_id'))
#@on_command('莲花', aliases=('莲花'),only_to_me=False)
#async def duanxin(session: CommandSession):
#    msg = session.ctx['raw_message'].replace('莲花','').strip()
#    if msg == '':
#        headers = {'referer': 'https://nmsl.shadiao.app/?from_chp',
#                    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36'}
#        text = requests.get('https://nmsl.shadiao.app/api.php?level=min&lang=zh_cn',headers=headers,timeout=5).text
#        #text = requests.get('https://nmsl.shadiao.app/api.php?lang=zh_cn').text
#        await session.send(text)

@on_command('抽象', aliases=('抽象'),only_to_me=False)
async def duanxin(session: CommandSession):
    msg = session.ctx['raw_message'].replace('抽象','',1).strip()
    if msg:
        import ab
        await session.send(ab.str2abs(msg))

@on_command('情话', aliases=('骚话'),only_to_me=False)
async def duanxin(session: CommandSession):
    msg = session.ctx['raw_message'].replace('情话','').strip()
    if msg == '':
        text = requests.get('http://chp.shadiao.app/api.php',timeout=5).text
        #text = requests.get('https://nmsl.shadiao.app/api.php?lang=zh_cn').text
        await session.send(text)

@on_command('鸡汤', only_to_me=False)
async def duanxin(session: CommandSession):
    msg = session.ctx['raw_message'].replace('鸡汤','').strip()
    if msg == '':
        text = requests.get('http://du.shadiao.app/api.php',timeout=5).text
        #text = requests.get('https://nmsl.shadiao.app/api.php?lang=zh_cn').text
        await session.send(text)

@on_command('on', aliases=('on'),only_to_me=False)
async def duanxin(session: CommandSession):
    if session.ctx['raw_message'].strip() == 'online':
        text = requests.get("https://www.bilibili.com/video/online.html",timeout=3).text
        html = etree.HTML(text)
        divs = html.xpath('//div[@class="online-list"]/div')
        c = 0
        msg = '【大家都在看】'
        for div in divs[:5]:
            c += 1
            title = div.xpath('./a/@title')[0]
            link = div.xpath('./a/@href')[0]
            author = div.xpath('./div/a/text()')[0]
            count = div.xpath('./p/b/text()')[0]
            msg += '\n%s、%s\nup：%s\n在线：%s\n%s' % (c, title, author, count, 'https://www.bilibili.com/video/av' + link.split('av')[-1]) 
        await session.send(msg)

@on_command('谁起', aliases=('谁改',),only_to_me=False)
async def duanxin(session: CommandSession):
    if '的名' in session.ctx['raw_message'].strip():
        with open('/home/qiming_log','r') as f:
            qiming_data = json.load(f)

        await session.send(qiming_data.get(str(session.ctx['group_id'])))

@on_command('状况', aliases=('状况'),only_to_me=False)
async def duanxin(session: CommandSession):
    if session.ctx['raw_message'].strip() == '状况':
        info = requests.get('https://api.64clouds.com/v1/getServiceInfo?veid=1125513&api_key=private_v5jTeMoAxtWoPVJJyqxPwGic').json()
        data_counter = info['data_counter'] / (1024**3)
        num = 29 - datetime.now().day
        if str(num).startswith('-'):
            count = abs(num) + 29
        else:
            count = num
        msg = '剩余流量：%sG\n剩余天数：%s天' % (round(550-data_counter,2),count)
        await session.send(msg)


#@on_command('fd', aliases=('fd'),only_to_me=False)
#async def tuling(session: CommandSession):
#    with open('/home/awesome-bot/fd','r') as f:
#        t1 = f.read()
#    if int(time.time()) - int(t1) > 60:
#        msg = session.ctx['raw_message'].replace('fd','')
#        await session.send(msg)
#        with open('/home/awesome-bot/fd','w') as f:
#            f.write(str(int(time.time())))
#


def ciku_insert(args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "insert into ciku values(%s,%s)"
        cur.execute(sql,args)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(e)


#@on_command('i问题', aliases=('问题'),only_to_me=False)
#async def tuling(session: CommandSession):
#    arg = session.ctx['raw_message']
#    if '问题' in arg and '答案' in arg and arg.startswith('问题'):
#        ciku_insert(arg[2:].replace('答案','asdf',1).split('asdf'))
#        await session.send('词库导入成功，快@机器人问一下吧~')

#@on_command('ai', aliases=('ai'),only_to_me=False)
#async def tuling(session: CommandSession):
#    if '器人' in session.ctx['raw_message'] and random.choice([0,0,0,1]):
#        face_list = [34,25,21,22,178,27,18,177,108,174,106,176,98,32,3,4,6,8,13,12,38,101,102,103,104,212,175,180,181,183,46,66,49,119,185,147,192]
#        await session.send('[CQ:face,id=%s]' % random.choice(face_list))

@on_command('ba', aliases=('ba'),only_to_me=False)
async def tuling(session: CommandSession):
    if session.ctx['raw_message'].replace('ba','').isdigit():
        bot = nonebot.get_bot()
        mid = int(session.ctx['raw_message'].replace('ba',''))
        await bot.delete_msg(message_id=mid)
        await bot.set_group_ban(group_id=session.ctx['group_id'],user_id=session.ctx['user_id'],duration=60)

#@on_command('i赞助', aliases=('i赞助'),only_to_me=False)
#async def tuling(session: CommandSession):
#    if '赞助' == session.ctx['raw_message']:
#        await session.send('多谢大家的支持~[CQ:image,file=zfb.jpg]')


def select_bans():
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select keyword from ban_words"
        cur.execute(sql)
        ret = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)

def insert_bans(keyword):
    conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
    cur = conn.cursor()
    sql = "insert into ban_words values(%s)"
    cur.execute(sql,[keyword])
    conn.commit()
    cur.close()
    conn.close()
    return ret


@on_request('group')
async def _(session: RequestSession):
    bot = nonebot.get_bot()
    if session.ctx['group_id'] in [373486526, 949377627]:
        await bot.set_group_add_request(flag=session.ctx['flag'],sub_type='add')
        return
    
    if session.ctx['group_id'] == 949377627:
        info = await session.bot._get_vip_info(user_id=session.ctx['user_id'])
        level = info['level']
        if level > 1:
            await bot.set_group_add_request(flag=session.ctx['flag'],sub_type='add')
            return
        else:
            await bot.set_group_add_request(flag=session.ctx['flag'],sub_type='add',approve='false',reason='等级不足')

@on_command('纸片', aliases=('纸片'),only_to_me=False)
async def tuling(session: CommandSession):
    #await session.send('存货已用完')
    #if session.ctx['group_id'] not in [482261061]:
    #return
    role = session.ctx['sender']['role']
    if role == 'member'and session.ctx['user_id'] != 736209298:
        await session.send('暂时只能管理员使用，请见谅！')
        return

    with open('/home/awesome-bot/pixiv','r') as f:
        t1 = f.read()
    if int(time.time()) - int(t1) < 7:
        return
    with open('/home/awesome-bot/pixiv','w') as f:
        f.write(str(int(time.time())))


    if session.ctx['raw_message'] == '纸片人':

        pic = random.choice(os.listdir('/home/pro_coolq/data/image/pixiv'))
        #mid=await session.send(message="[CQ:share,url=https://pixiv.cat/%s,title=%s,content='测试中',image=https://pixiv.cat/%s]" % (pic,pic.split('.')[0],pic))
        mid=await session.send(message='id：%s[CQ:image,file=pixiv/%s]有频率限制' % (pic.split('.')[0].split('-')[0],pic))
        #os.remove('/home/pro_coolq/data/image/pixiv/%s' % pic)
        #bot = nonebot.get_bot()
        #time.sleep(3)
        #await bot.delete_msg(message_id=mid.get('message_id'))
    else:
        #await session.send('搜索纸片人功能暂时关闭，请谅解')
        return
        role = session.ctx['sender']['role']
        #if session.ctx['user_id'] != 736209298 and role == 'member':
        #    return
        async with httpx.AsyncClient() as client:
            items = await client.get('https://api.pixivic.com/illustrations?keyword=%s&page=%s' % (session.ctx['raw_message'].replace('纸片人','').strip(),1), timeout=5)
        items = items.json()['data'] 
        #items = requests.get('https://api.pixivic.com/illustrations?keyword=%s&page=%s' % (session.ctx['raw_message'].replace('纸片人','').strip(),random.randrange(1,3)), timeout=5).json()['data']
        if not items:
            await session.send('@%s\n' % session.ctx['sender']['card'] + '哎呀，肿么搜不到，残念')
            return
        item = random.choice(items)

        #pic = item['imageUrls'][0]['large'].replace('i.pximg.net','img.cheerfun.dev:233')
        pic = item['imageUrls'][0]['medium'].replace('i.pximg.net','img.cheerfun.dev:233')
        #pic = item['imageUrls'][0]['original'].replace('i.pximg.net','original.img.cheerfun.dev')
        h = {
            'Referer': 'https://pixivic.com/popSearch',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
            }
        with open('/home/pro_coolq/data/image/cai.jpg','wb') as f:
            f.write(requests.get(pic,headers=h,timeout=3).content)
        await session.send('[CQ:image,file=cai.jpg]')


#@on_command('历史', aliases=('历史'),only_to_me=False)
#async def tuling(session: CommandSession):
#    if session.ctx['raw_message'] == '历史上的今天':
#        items = requests.get('https://api.66mz8.com/api/today.php?format=json',timeout=5).json()['data']
#        msg = '\n'.join([i['date'] + '\n' + i['message'] for i in items[:10]])
#        await session.send(message=msg)

@on_command('历史', aliases=('历史'),only_to_me=False)
async def tuling(session: CommandSession):
    if session.ctx['raw_message'] == '历史上的今天':
        items = requests.get('https://v1.alapi.cn/api/eventHitory',timeout=5).json()['data']
        msg = '\n'.join(['%s-%s-%s\n%s' % (i['year'],i['monthday'][:2],i['monthday'][2:],i['title']) for i in list(reversed(items))[:10]])
        await session.send(message=msg)


def get_ocr_str_from_bytes(img_url, origin_format=True):
    """
    图片转文字
    :param file_bytes: 图片的字节
    :return:
    """
    APP_ID = '18273595'
    API_KEY = 'mVAl04EodIz5rGcbaSfPquv1'
    SECRET_KEY = 'TuoGpvYAgbgTgoUsMv1GSpteG5QfgFmq'
    options = {
        'detect_direction': 'false',
        'language_type': 'CHN_ENG',
    }
    ocr = AipOcr(APP_ID, API_KEY, SECRET_KEY)
    result_dict = ocr.basicGeneral(requests.get(img_url,timeout=3).content, options)
    result_str = '\n'.join([entity['words'] for entity in result_dict['words_result']])
    return result_str


def select_kexue_count():
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select count(id) from moukexue"
        cur.execute(sql)
        ret = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)

def select_kexue(sid):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select ability,levels from moukexue where id=%s" % sid
        cur.execute(sql)
        ret = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)

def select_kexue_single(*args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select id from moukexue where ability=%s"
        cur.execute(sql,args)
        ret = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(2)
        print(e)

ab = {}
@on_command('能力', aliases=('能力'),only_to_me=False)
async def tuling(session: CommandSession):
    user_id = session.ctx['user_id']
    group_id = session.ctx['group_id']
    c = ab.get(user_id,'')
    current_date = datetime.now().strftime('%Y-%m-%d')
    if c:
        if c == current_date:
            await session.send('您今天已经判定过了哦')
            return
    ab[user_id] = current_date
    if not session.ctx['raw_message'].startswith('能力判定') or len(session.ctx['raw_message']) > 14:
        return
    if len(session.ctx['raw_message']) == 4:
        card = session.ctx['sender'].get('card','')
        name = card if card else session.ctx['sender'].get('nickname','')
    else:
        name = session.ctx['raw_message'].replace('能力判定','').strip()

    count = int(select_kexue_count()[0])
    abilitys,level = select_kexue(random.randrange(1,count+1))
    print(abilitys)
    ability,ability_name = abilitys.split('|')
    ability_map = {0:'无',1:'低',2:'异',3:'强',4:'大',5:'超',6:'觉醒',7:'觉醒'}
    msg = '某科学的能力判定\nname：%s\nLevel：%s\n等级：%s\nABILITY：%s\n能力：%s' % (name,ability_map.get(level)+'能力者',level,ability,ability_name)
    await session.send(message=msg)


@on_command('识别', aliases=('识别'),only_to_me=False)
async def fan(session: CommandSession):
    pic = ''
    for i in session.ctx['message']:
        if i['type'] == 'image':
            pic = i['data']['url']
    if pic:
        await session.send(get_ocr_str_from_bytes(pic))

#@on_command('dz', aliases=('dz'),only_to_me=False)
#async def fan(session: CommandSession):
#    bot = nonebot.get_bot()
#    await bot.send_like(user_id=session.ctx['user_id'],times=1)

@on_command('摇骰', aliases=('摇骰'),only_to_me=False)
async def fan(session: CommandSession):
    await session.send('[CQ:dice]')

#@on_command('我回', aliases=('摇骰'),only_to_me=False)
#async def fan(session: CommandSession):
#    await session.send('[CQ:record,file=dashu/welcome/1.silk]')
#@on_command('提问', aliases=('提问'),only_to_me=False)
#async def tuling(session: CommandSession):
#    arg = session.ctx['raw_message'].replace('提问','').strip()
#    if not arg:
#        return
#    with open("/home/bili_kefu", "r") as f:
#        the_cookies = json.load(f)
#
#    data3 = {
#        'puid': the_cookies['puid'],
#        'cid': the_cookies['cid'],
#        'uid': the_cookies['uid'],
#        'content': arg
#    }
#    r = requests.post('https://service.bilibili.com/v2/chat/user/chatsend.action', data=data3).text
#    print(r)


#@on_command('红包', aliases=('红包'),only_to_me=False)
#async def fan(session: CommandSession):
#    await session.send('[CQ:record,file=dashu/hongbao1.silk]')
#    await session.send('[CQ:record,file=dashu/hongbao2.silk]')
#@on_command('晚安', aliases=('晚安'),only_to_me=False)
#async def fan(session: CommandSession):
#    if random.choice([0,1,1]):
#        return
#    dir_list = os.listdir('/home/pro_coolq/data/record/dashu/night')
#    file = 'dashu/night/' + random.choice(dir_list)
#    await session.send('[CQ:record,file=%s]' % file)
#@on_command('早上', aliases=('早上'),only_to_me=False)
#async def fan(session: CommandSession):
#    if random.choice([1,1,1,0]):
#        return
#    dir_list = os.listdir('/home/pro_coolq/data/record/dashu/morning')
#    file = 'dashu/morning/' + random.choice(dir_list)
#    await session.send('[CQ:record,file=%s]' % file)

#@on_command('早呀', aliases=('早呀'),only_to_me=False)
#async def fan(session: CommandSession):
#   if '早呀' in session.ctx['raw_message']: 
#        dir_list = os.listdir('/home/pro_coolq/data/record/dashu/morning')
#        file = 'dashu/morning/' + random.choice(dir_list)
#        file = '38C24E96DBC43F65F96403EE73860050.silk'
#        await session.send('[CQ:record,file=%s]' % file)

def insert_banqq(qq):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "insert into ban_qq values(%s)" % qq
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(e)

def delete_banqq(qq):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "delete from ban_qq where qq=%s" % qq
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(e)


@on_command('添加', aliases=('添加'),only_to_me=False)
async def fan(session: CommandSession):
    qq = re.findall(r'\[CQ:at,qq=(\d+?)\]',session.ctx['raw_message'])[0]
    if '添加管理员' in session.ctx['raw_message'] and session.ctx['user_id'] == 736209298:
        bot = nonebot.get_bot()
        await bot.set_group_admin(group_id=session.ctx['group_id'],user_id=qq,enable=True)

@on_command('删除', aliases=('取消',),only_to_me=False)
async def fan(session: CommandSession):
    qq = re.findall(r'\[CQ:at,qq=(\d+?)\]',session.ctx['raw_message'])[0]
    if '取消管理员' in session.ctx['raw_message'] and session.ctx['user_id'] == 736209298:
        bot = nonebot.get_bot()
        await bot.set_group_admin(group_id=session.ctx['group_id'],user_id=qq,enable=False)

#@on_command('捞纸', aliases=('删除'),only_to_me=False)
#async def fan(session: CommandSession):
#    await session.send('由于个别网友经常发些作死言论，此功能暂停')

def select_av(av):
    url = 'https://api.bilibili.com/x/web-interface/view?aid=%s' % av
    r = requests.get(url,timeout=3).json()
    tname = r['data']['tname']
    title = r['data']['title']
    img = r['data']['pic'] + '@412w_232h_1c_100q.jpg'
    with open('/home/pro_coolq/data/image/cai.jpg','wb') as f:
        f.write(requests.get(img).content)

    pubdate = r['data']['pubdate']
    desc = r['data']['desc']
    timeArray = time.localtime(pubdate)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    owner = r['data']['owner']['name']
    mid = 'https://space.bilibili.com/%s' % r['data']['owner']['mid']
    dynamic = r['data']['dynamic']
    view = r['data']['stat']['view']
    danmaku = r['data']['stat']['danmaku']
    reply = r['data']['stat']['reply']
    favorite = r['data']['stat']['favorite']
    coin = r['data']['stat']['coin']
    share = r['data']['stat']['share']
    like = r['data']['stat']['like']
    text = '标题：%s\nUP：%s\n%s\n投稿时间：%s\n投区：%s\n标签：%s\n简介：%s\n播放量：%s 弹幕：%s\n评论：%s 投币：%s\n点赞：%s 收藏：%s 分享：%s' % (title, owner, mid, otherStyleTime, tname, dynamic, desc[:70], view, danmaku, reply, coin, like, favorite, share)
    return text

#@on_command('[C', aliases=('[C'),only_to_me=False)
#async def fan(session: CommandSession):
#    jurl = re.findall(r'"jumpUrl":"(.+?)"',session.ctx['raw_message'])
#    if jurl and '哔哩哔哩' in session.ctx['raw_message']:
#        headers = {
#            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
#        }
#        ret = requests.get(jurl[0],headers=headers, allow_redirects=False)
#        loc = ret.headers['Location']
#        av = re.findall(r'av(\d+)', loc)[0]
#        await session.send(select_av(av))
    #if '哔哩哔哩' in session.ctx['raw_message'] and '小程序' in session.ctx['raw_message']:
    #    await session.send('下次一定')

def select_bv(av):
    url = 'https://api.bilibili.com/x/web-interface/view?bvid=%s' % av
    r = requests.get(url,timeout=3).json()
    tname = r['data']['tname']
    title = r['data']['title']
    img = r['data']['pic']
    #img = r['data']['pic'] + '@412w_232h_1c_100q.jpg'
    with open('/home/pro_coolq/data/image/cai.jpg','wb') as f:
        f.write(requests.get(img).content)

    pubdate = r['data']['pubdate']
    desc = r['data']['desc']
    timeArray = time.localtime(pubdate)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    owner = r['data']['owner']['name']
    mid = 'https://space.bilibili.com/%s' % r['data']['owner']['mid']
    dynamic = r['data']['dynamic']
    view = r['data']['stat']['view']
    danmaku = r['data']['stat']['danmaku']
    reply = r['data']['stat']['reply']
    favorite = r['data']['stat']['favorite']
    coin = r['data']['stat']['coin']
    share = r['data']['stat']['share']
    like = r['data']['stat']['like']
    text = '标题：%s\nUP：%s\n%s\n投稿时间：%s\n投区：%s\n标签：%s\n简介：%s\n播放量：%s 弹幕：%s\n评论：%s 投币：%s\n点赞：%s 收藏：%s 分享：%s' % (title, owner, mid, otherStyleTime, tname, dynamic, desc[:70], view, danmaku, reply, coin, like, favorite, share)
    return text


@on_command('av', aliases=('BV',),only_to_me=False)
async def fan(session: CommandSession):
    if session.ctx['group_id'] in [600219391,333269216]:
       return
    av = re.findall(r'av(\d+)',session.ctx['raw_message'])
    if av:
        await session.send('[CQ:image,file=cai.jpg]'+select_av(av[0]))
    else:
        bv = re.findall(r'BV(.+)',session.ctx['raw_message'])[0]
        await session.send('[CQ:image,file=cai.jpg]'+select_bv(bv))
   


def select_db_xiajia(args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "SELECT * from animate where hide = 0 order by create_time desc limit "+str(args)+", 10"
        cur.execute(sql)
        ret = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)


@on_command('下架', aliases=('下架'),only_to_me=False)
async def fan(session: CommandSession):
    arg_text = session.ctx['raw_message'].replace('下架','').strip()
    if arg_text.isdigit():
        if 0 <= int(arg_text) - 1:
            if arg_text == '':
                arg_text = 1
            ret3s = select_db_xiajia(int(arg_text)-1)
            msg = 'b站近期下架%s-%s名：' % (arg_text,int(arg_text)+9)
            for ret in ret3s:
                msg += ('\n' + ret[2])
            await session.send(msg)
def select_db_yincang(args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "SELECT * from animate where hide = 1 order by create_time desc limit "+str(args)+", 5"
        cur.execute(sql)
        ret = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)


@on_command('隐藏', aliases=('隐藏'),only_to_me=False)
async def fan(session: CommandSession):
    arg_text = session.ctx['raw_message'].replace('隐藏','').strip()
    if arg_text.isdigit():
        if 0 <= int(arg_text) - 1:
            if arg_text == '':
                arg_text = 1
            ret3s = select_db_yincang(int(arg_text)-1)
            msg = 'b站隐藏%s-%s名：' % (arg_text,int(arg_text)+4)
            for ret in ret3s:
                msg += ('\n' + ret[2] + '\nhttps://www.bilibili.com/bangumi/media/md%s' % ret[0])
            await session.send(msg)

#@on_command('头像', aliases=('头像'),only_to_me=False)
#async def fan(session: CommandSession):
#    arg_text = session.ctx['raw_message'].replace('头像','').strip()
#    if arg_text in ['男','女','动漫'] or arg_text == '':
#        if arg_text == '':
#            arg_text = random.choice(['男','女','动漫'])
#        async with httpx.AsyncClient() as client:
#            imgurl = await client.get('https://api.66mz8.com/api/rand.pic.php?type=%s&return=json' % arg_text,timeout=3)
#            imgurl = imgurl.json()['imgurl']
#        await session.send(message='[CQ:image,file=%s]' % imgurl)

@on_command('头像', aliases=('头像'),only_to_me=False)
async def fan(session: CommandSession):
    arg_text = session.ctx['raw_message'].replace('头像','').strip()
    if arg_text in ['男','女','动漫'] or arg_text == '':
        if arg_text == '':
            arg_text = random.choice(['nan','nv','katong'] )
        else:
            m = {'男':'nan','女':'nv','动漫':'katong',}
            arg_text = m.get(arg_text)
            
        async with httpx.AsyncClient() as client:
            ret = await client.get('https://www.woyaogexing.com/touxiang/%s/' % arg_text,timeout=3)
        imgs = re.findall(r'//img2\.woyaogexing\.com/.+?\.jpeg',ret.content.decode())
        
        imgurl = 'https:'+random.choice(imgs)
        
        await session.send(message='[CQ:image,file=%s]' % imgurl)

@on_command('点菜', aliases=('点菜'),only_to_me=False)
async def fan(session: CommandSession):
    if '点菜' not in session.ctx['raw_message']:
        return
    with open('/home/awesome-bot/pixiv','r') as f:
        t1 = f.read()
    if int(time.time()) - int(t1) < 5:
        return
    with open('/home/awesome-bot/pixiv','w') as f:
        f.write(str(int(time.time())))

    arg_text = session.ctx['raw_message'].replace('点菜','').strip()
    url = 'http://www.xiachufang.com/search/?keyword=%s' % arg_text
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    }
    ret = requests.get(url,headers=headers,timeout=3).text
    html = etree.HTML(ret)
    lis = html.xpath('//div[@class="page-outer"]//ul[@class="list"]/li')
    li = random.choice(lis[:15])
    t = li.xpath('.//div[contains(@class,"info")]')[0]
    img = li.xpath('.//div[contains(@class,"cover")]/img/@data-src')[0]
    name = t.xpath('./p[1]/a/text()')[0].strip()
    tag = ''.join(t.xpath('./p[2]//text()')).replace(' ','').strip()
    if session.ctx['self_id'] == 302554188: 
        with open('/home/pro_coolq/data/image/cai.jpg','wb') as f:
            f.write(requests.get(img,timeout=3).content)
    else:
        with open('/home/2coolq/data/image/cai.jpg','wb') as f:
            f.write(requests.get(img,timeout=3).content)
    msg = '%s\n用料：%s' % (name,tag)
    #await session.send('[CQ:image,file=cai.jpg,destruct=true]%s' % msg)
    await session.send('[CQ:image,file=cai.jpg]%s' % msg)


@on_command('康娜', aliases=('康娜'),only_to_me=False)
async def fan(session: CommandSession):

    dir_list = os.listdir('/home/pro_coolq/data/record/kangna')
    file = 'kangna/' + random.choice(dir_list)
    await session.send('[CQ:record,file=%s]' % file)

@on_command('雷姆', aliases=('蕾姆','蕾蕾',),only_to_me=False)
async def fan(session: CommandSession):
    role = session.ctx['sender']['role']
    #if role == 'member' and session.ctx['user_id'] != 736209298:
    #    return
    dir_list = os.listdir('/home/pro_coolq/data/record/leimu')
    file = 'leimu/' + random.choice(dir_list)
    await session.send('[CQ:record,file=%s]' % file)

@on_command('蕾の',aliases=('蕾的',), only_to_me=False)
async def fan(session: CommandSession):
    arg = session.ctx['raw_message'].replace('蕾の','',1).strip()
    if '简介' in arg:
        b = [
            '————蕾姆简介————',
            '★蕾姆是人工智能（Artificial Intelligence），英文缩写为AI，也可以称为智能姬。',
            '★由三好哥设计开发，三好运营，三好巡查，三好调试和维护。蕾姆是在2019年11月1日诞生的，在群友的培养下茁壮成长，到现在可以说是女大十八变了。',
            '★蕾姆除了红包群、点赞群、羊毛群等不加以外，其他类型的群都可以接受。',
            '★虽然可以叫蕾姆为机器人，但是蕾姆不是一个完完全全的机器！虽然可以调戏，但是也要有度！虽然没有实体，但是我们可以把它当成无形的伙伴！虽然没有情感，但是它有爱，有欢乐，有陪伴，背后还有我的汗水和艰辛，和大家的支持陪伴才创造的它！',
            '★所以，可以不爱，请别伤害！',
            '★蕾姆の群：949377627',
            '————————————',
        ]

    elif '人设' in arg:
        b = [
            '————蕾の人设————',
            '★蕾姆：《Re：从零开始的异世界生活》的主要角色，在罗兹沃尔的宅邸中一手担当全部杂务的双胞胎女仆中的妹妹，看似毒舌冷漠，其实内心很坚强，很温柔。',
            '★声优：水濑祈',
            '★生日：2月2日',
            '★年龄：17',
            '★喜欢的人：三好 拉姆',
            '★讨厌的东西：与魔女有关的一切东西',
            '★形象：身高大概150厘米左右，大大的蓝色眼睛和桃红色嘴唇，轮廓不太分明的面容显得可爱。发型是齐颈蓝色短发，然而头发分界线却有所不同，前留海盖住她的右眼（姐姐是左眼）。一身以黑色为基调的围裙，头上是白色帽饰，除刘海方向、发色和瞳色外和姐姐长得几乎一样，胸部比起姐姐拉姆要更加丰满。',
            '————————————',
        ]
    elif '功能' in arg:
        b = [
            '————蕾の功能————',
            '★天气 城市名：可以查天气信息',
            '★翻译 内容：支持多种语言哦',
            '★情话：随机推送一句情话',
            '★鸡汤：随机推送鸡汤？',
            '★一言：随机推送acg相关名言',
            '★历史上的今天：字面意思',
            '★改名 名字：可以给蕾姆改名哦',
            '★换牌：随机更换蕾姆现有头衔',
            '★换头：随机更换蕾姆现有头像',
            '★头衔 名字：自动设置自己的专属头衔（需要蕾姆当群主，可在主人的群体验）',
            '★搜番+番剧图片,搜索番剧名称',
            '★搜图+p站图片,搜索p站信息',
            '★鉴黄+图片(有频率限制)',
            '★识别+图片,识别文字',
            '★解析b站视频链接的具体信息',
            '★及时推送b站番剧更新信息',
            '————————————',
        ]

    elif '活跃' in arg:
        b = [
            '————蕾の活跃————',
            '★活跃：查看自己今日活跃',
            '★活跃1：查看群近1天活跃',
            '★活跃-1：查看群前1天活跃',
            '★总活跃：查看自己活跃总数',
            '★活跃图：查看自己近七天统计',
            '★群活跃图：查看近七天群统计',
            '★活跃 总活跃 活跃图：这三个命令后面@某人，可以查看别人活跃',
            '————————————',
        ]

    elif '群管' in arg:
        b = [
            '————蕾の群管————',
            '★管理专用★',
            '★禁言@某人10分钟，禁言@某人默认禁言1分钟，可以用天、小时、分钟、秒',
            '★解禁@某人：解除禁言',
            '★去屎@某人：踢出此人',
            '★全体禁言、解禁',
            '★改名@某人后加名字',
            '★开机、关机',
            '★违禁词添加 awsl',
            '★违禁词删除 awsl',
            '★违禁词查看',
            '★点歌 歌名：有时候被屏蔽',
            '★发说说：让蕾姆发说说',
            '★开启抽卡、关闭抽卡',
            '————————————',
        ]

    elif '娱乐' in arg:
        b = [
            '————蕾の娱乐————',
            '★能力判定：你是几级能力者?',
            '★替身判定：stand power！',
            '★营销号生成：有例子',
            '★纸片人：推送p站图片',
            '★头像男、女、动漫：推送头像',
            '★抽象 内容：转换抽象文字',
            '★短信 内容：手机短信图片',
            '★签到：可以获得圣金币',
            '★签到排行：群内签到天数排行',
            '★点菜 菜名：饿的时候望梅止渴',
            '————————————',
        ]
    elif 'bili' in arg:
        b = [
            '————蕾のbili————',
            '★查分 番名：查番剧评分',
            '★低分1：查b站番剧排名，下架、隐藏、高分同理',
            '★online：b站大家都在看',
            '★2233：会推送2233小剧场',
            '★排行1：查b站全部番剧播放量前10',
            '★排行2：查b站连载中播放量前10',
            '★排行3：查b站近期上线播放量前10',
            '————————————',
        ]
    elif '卡牌' in arg:
        b = [
            '————蕾の卡牌————',
            '★商店：查看道具说明',
            '★抽卡：就是单抽啦',
            '★十连抽：考验欧气的时刻到了',
            '★打劫@某人：失败会进监狱',
            '★转账@某人：py交易',
            '★富豪榜、负豪榜：圣金币排行',
            '★关押时长：自己的出狱时间',
            '★背包：查看自己拥有的道具',
            '★小本本：查看谁打劫了你',
            '★赠送保释卡@张三1，可以赠送道具',
            '★讨伐白鲸：每次10人组团讨伐，可获得奖励',
            '★讨伐名单：查看成员',
            '★拍卖行：购买大家上架道具',
            '★上架保释卡300：只能上架单品',
            '★下架1：其中1是拍卖编号',
            '★购买1：其中1是拍卖编号',
            '————————————',
        ]
    elif '主人' in arg:
        b = [
            '————蕾の主人————',
            '★QQ：736209298',
            '★B站：玩好吃好喝好',
            '★微博：p站前线姬',
            '★蕾姆の群：949377627',
            '————————————',
        ]
    elif '教学' in arg:
        b = [
            '————蕾の教学————',
            'qq具体问题aa具体答案',
            '使用这种格式可以教蕾姆说话，比如：',
            'qq你叫什么？aa我叫蕾姆呀',
            '其中aa后面输入的答案要加入表情图片，颜文字，qq表情，看着比较可爱！但必须一起发送才有效',
            '教学过后不会立即生效，需要主人审核，回答越萌越可爱越好，不符合人设的，出现自己名字的都不会通过，谢谢大家支持',
            '————————————',
        ]
    await session.send('\n'.join(b))

@on_command('表情', only_to_me=False)
async def fan(session: CommandSession):
    if session.ctx['user_id'] != 736209298:
        return
    pic = ''
    for i in session.ctx['message']:
        if i['type'] == 'image':
            pic = i['data']['url']
    if pic:
        with open('/home/pro_coolq/data/image/biaoqing/%s.jpg' % pic.split('-')[-1].split('/')[0],'wb') as f:
            f.write(requests.get(pic,timeout=3).content)

@on_command('鉴黄', only_to_me=False)
async def soutu(session: CommandSession):
    pic = ''
    for i in session.ctx['message']:
        if i['type'] == 'image':
            pic = i['data']['url']
    if pic:
        with open('/home/awesome-bot/jianhuang','r') as f:
            t1 = f.read()
        if int(time.time()) - int(t1) < 20:
            return
        with open('/home/awesome-bot/jianhuang','w') as f:
            f.write(str(int(time.time())))
        ai_obj = tencent_talk.AiPlat('2128554885', 'FMPEttRpwhngDj2K')
        rsp = ai_obj.getNlpImgPorn(pic)
        if rsp['ret'] == 0:
            l = rsp['data']['tag_list']
            msg = []
            for i in l:
                if 'brea' in i['tag_name']:
                    continue
                msg.append('%s：%s' % (i['tag_name'],i['tag_confidence']))
            await session.send('@'+session.ctx['sender']['card']+'\n'+'\n'.join(msg))

@on_command('发说', only_to_me=False)
async def soutu(session: CommandSession):
    if session.ctx['raw_message'].startswith('发说说'):
        if '[CQ' in session.ctx['raw_message']:
            await session.send('残念，目前只开放纯文字说说哦')
            return
        role = session.ctx['sender']['role']
        if session.ctx['user_id'] != 736209298 and role == 'member':
            await session.send('残念，人数较多，目前只允许管理员发说说')
            return
        message = session.ctx['raw_message'][3:].strip()
        if not message:
            await session.send('发表失败，不能为空消息')
            return
        user_info = '%s（%s）' % (session.ctx['sender']['card'], session.ctx['user_id']) 
        msg = '%s\n\n发表人：%s\n来源群：%s\n群里输入“发说说”即可使用' % (message,user_info,session.ctx['group_id'])
        d2 = {
            'syn_tweet_verson': '1',
            'paramstr': '1',
            'who': '1',
            'subrichtype': '1',
            'con': msg,
            'feedversion': '1',
            'ver': '1',
            'ugc_right': '1',
            'to_sign': '0',
            'hostuin': str(session.ctx['self_id']),
            'code_version': '1',
            'format': 'fs',
        }
        #with open('/home/bot_cookie','r') as f:
        #    cookie = f.read()
        cookie = await session.bot.get_cookies()
        skey = re.findall(r"skey=(.+?)'",str(cookie))[0]
        bkn = getBKN(skey)
        h = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
            'cookie': 'uin=o0%s; skey=%s; p_uin=o0%s; Loading=Yes;' % (session.ctx['self_id'],skey,session.ctx['self_id'])
        }
        url = 'https://user.qzone.qq.com/proxy/domain/taotao.qzone.qq.com/cgi-bin/emotion_cgi_publish_v6?g_tk=%s' % bkn
        ret = requests.post(url,headers=h,data=d2,timeout=3).text
        with open('/home/tes.txt','w') as f:
            f.write(ret)
        if 'repub' in ret:
            await session.send('发表成功，可以到我的空间查看说说哦~')
        else:
            await session.send('发表失败，请通知主人尽快修复')

#@on_command('词云', only_to_me=False)
#async def soutu(session: CommandSession):
#    if session.ctx['raw_message'].startswith('词云'):
#        await session.send(message='今日群词云[CQ:image,file=fenci/%s.jpg]' % session.ctx['group_id'])


#@on_command('jo', only_to_me=False)
#async def jinyan(session: CommandSession):
#    dir_list = os.listdir('/home/pro_coolq/data/record/jojo')
##    file = 'jojo/' + random.choice(dir_list)
#    await session.send('[CQ:record,file=%s]' % file)


@on_command('头衔',aliases=('头街',), only_to_me=False)
async def jinyan(session: CommandSession):
    if session.ctx['group_id'] not in [1035554908,949377627]:
        return
    if 'CQ' in session.ctx['raw_message'] and session.ctx['user_id'] != 736209298:
        return
    msg1 = session.ctx['raw_message'].replace('头街','').replace('头衔','').strip()
    
    if not msg1:
        await session.send('头衔后加你想要的名字')
        return

    if session.ctx['raw_message'].startswith('头衔') or session.ctx['raw_message'].startswith('头街'):
        j = 0
        user_id = session.ctx['user_id']
        group_id = session.ctx['group_id']
        if session.ctx['user_id'] != 736209298:
            p = select_db_score(user_id,group_id)
            if p:
                score = p[1]
                if score >=100:
                    tscore = score-100
                    update_db_score(tscore, p[0])
                    msg = '领取成功\n消耗100圣金币\n剩余：%s圣金币' % tscore
                    j = 1
                else:
                    msg = '领取失败\n圣金币不足100\n剩余：%s圣金币' % score
            else:
                msg = '领取失败\n圣金币为不足100\n可以签到获得哦'
        else:
            msg = '领取成功，欧尼酱~'
            j = 1
        if j == 0:
            await session.send(msg)
            return
        msg1 = session.ctx['raw_message'].replace('头衔','').replace('头街','').strip()
        if 'CQ' in session.ctx['raw_message']:
            qq = re.findall(r'\[CQ:at,qq=(\d+?)\]',session.ctx['raw_message'])[0]
            msg1 = session.ctx['raw_message'].split(']')[-1].strip()
        else:
            qq = session.ctx['user_id']
        bot = nonebot.get_bot()
        await bot.set_group_special_title(group_id=session.ctx['group_id'],user_id=qq,special_title=msg1)
        await session.send(msg)


ts = {}
@on_command('替身', aliases=('替身'),only_to_me=False)
async def tuling(session: CommandSession):
    if not session.ctx['raw_message'].startswith('替身判定') or len(session.ctx['raw_message']) > 14:
        return
    user_id = session.ctx['user_id']
    group_id = session.ctx['group_id']
    c = ts.get(user_id,'')
    if c:
        await session.send('认命吧，你只有这一个替身')
        return
    ts[user_id] = 1
    card = session.ctx['sender'].get('card','')
    name = card if card else session.ctx['sender'].get('nickname','')


    url = 'https://shindanmaker.com/905484'

    data = {
        'u': session.ctx['user_id']
    }
    res = requests.post(url,data=data,timeout=3).text
    a = re.findall(r'data: \[(\d), (\d), (\d), (\d), (\d), (\d)\],',res)[0]
    stand = re.findall(r'替身名称：(.+)<b',res)[0]
    stand_type, stand_face = re.findall(r"能力类型：(.+?) 外形：(.+?)'",res)[0]
    tags = ['破壊力', 'スピード', '射程距離', '持久力', '精密操作性', '成長性']
    msg = 'jojo的奇妙替身\n姓名：%s\n替身名称：%s\n能力类型：%s\n外形：%s' % (name, stand, stand_type, stand_face)
    for i in range(6):
        msg += '\n%s：%s' % (tags[i],a[i])
    await session.send(message=msg)

@on_command('22', aliases=('哔哩'),only_to_me=False)
async def tuling(session: CommandSession):
    res = requests.get('https://www.bilibili.com/activity/web/view/data/31',timeout=3).json()['data']['list']
    ret = 'http:' + random.choice(res)['data']['img']
    if session.ctx['self_id'] == 302554188:
        with open('/home/pro_coolq/data/image/2233.jpg','wb') as f:
            f.write(requests.get(ret,timeout=3).content)
    else:
        with open('/home/2coolq/data/image/2233.jpg','wb') as f:
            f.write(requests.get(ret,timeout=3).content)
    await session.send('[CQ:image,file=2233.jpg]')

def select_db_sign(*args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select id,sign_state from qq_active where user_id=%s and group_id=%s and publish_date=%s"
        cur.execute(sql,args)
        ret = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)

def select_db_score(*args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select id,score from qq_sign where user_id=%s and group_id=%s"
        cur.execute(sql,args)
        ret = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)


def update_db_sign(*args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "update qq_active set sign_state=1 where id=%s"
        cur.execute(sql,args)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(e)

def update_db_score(*args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "update qq_sign set score=%s where id=%s"
        cur.execute(sql,args)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(e)

def insert_db_active(*args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "insert into qq_active(user_id,group_id,count,publish_date) values(%s,%s,%s,%s)"
        cur.execute(sql,args)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(e)

def insert_db_score(*args):
    conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
    cur = conn.cursor()
    sql = "insert into qq_sign(user_id,group_id,score) values(%s,%s,%s)"
    cur.execute(sql,args)
    conn.commit()
    cur.close()
    conn.close()


def select_sign_count(*args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select count(id) from qq_active where user_id=%s and group_id=%s and sign_state=1"
        cur.execute(sql,args)
        ret = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)

def select_sign_counts(*args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select user_id,sum(sign_state) from qq_active where group_id=%s GROUP  by user_id order by sum(sign_state) desc limit 0,10;"
        cur.execute(sql,args)
        ret = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)

@on_command('签到', only_to_me=False)
async def tuling(session: CommandSession):
    if session.ctx['raw_message'] == '签到':
        user_id = session.ctx['user_id']
        group_id = session.ctx['group_id']
        if group_id in [875164857,686950644,736742903]:
            return
        current_date = datetime.now().strftime('%Y-%m-%d')
        uuid,sign_state = select_db_sign(user_id,group_id,current_date)
        p = select_db_score(user_id,group_id)
        if sign_state == 0:
            r = random.choice([0,0,0,0,0,1])
            if r:
                score = 100
            else:
                score = 30
            update_db_sign(uuid)
            if p:
                if p[1] < 30:
                    score = 30
                tscore = score+p[1]
                update_db_score(tscore, p[0])
            else:
                tscore = score
                insert_db_score(user_id,group_id,score)
            jinbi = [
                    '可以公开的情报：',
                    '看命令输入[功能]',
                    ]
            count = select_sign_count(user_id,group_id)[0]
            if score != 10:
                await session.send('签到成功\n获得%s圣金币\n总计：%s圣金币\n签到天数：%s天\n%s' % (score, tscore,count,'\n'.join(jinbi)))
            else:
                await session.send('签到成功\n获得%s圣金币\n总计：%s圣金币\n签到天数：%s天\n%s' % (score, tscore,count,'\n'.join(jinbi)))
        else:
            if not p:
                p = [0,0]
            await session.send('您今日已经签过到了\n总计：%s圣金币' % p[1])
    elif session.ctx['raw_message'] == '签到排行':
        rets = select_sign_counts(session.ctx['group_id'])
        msg = '★本群签到天数排行榜★'
        c = 0
        for i in rets:
            c += 1
            count = i[1]
            if c < 11:
                user_id = i[0]
                try:
                    info = await session.bot.get_group_member_info(group_id=session.ctx['group_id'],user_id=user_id)
                    nickname = info.get('card')
                    nickname = nickname if nickname else info.get('nickname')
                    nickname = nickname.replace('\n','') 
                except:
                    nickname = user_id
                if c == 1:
                    msg += '\n%s、%s：%s天' % ('[CQ:emoji,id=127942]',nickname,count)
                else:
                    msg += '\n%s、%s：%s天' % (c,nickname,count)
        await session.send(msg)

#@on_command('i点赞', only_to_me=False)
#async def jinyan(session: CommandSession):
#    await session.send('此功能暂时停止使用，请见谅')
#    return
#    if session.ctx.get('group_id') in [875164857,686950644,736742903]: 
#        return
#    if session.ctx['raw_message'] == '点赞':
#        j = 0
#        user_id = session.ctx['user_id']
#        group_id = session.ctx['group_id']
#        if session.ctx['user_id'] != 736209298:
#            p = select_db_score(user_id,group_id)
#            if p:
#                score = p[1]
#                if score >=10:
#                    tscore = score-10
#                    update_db_score(tscore, p[0])
#                    msg = '点赞成功，已点满10个\n消耗10圣金币\n剩余：%s圣金币' % tscore
#                    j = 1
#                else:
#                    msg = '点赞失败\n圣金币不足\n剩余：%s圣金币' % score
#            else:
#                msg = '点赞失败\n圣金币为不足\n可以签到获得哦'
#        else:
#            msg = '点赞成功，欧尼酱~'
#            j = 1
#        if j == 0:
#            await session.send(msg)
#            return
#        msg1 = session.ctx['raw_message'].replace('头衔','').strip()
#        bot = nonebot.get_bot()
#        await bot.send_like(user_id=session.ctx['user_id'],times=10)
#        await session.send(msg)

@on_command('充值', aliases=('充值'),only_to_me=False)
async def fan(session: CommandSession):
    if session.ctx['user_id'] == 736209298:
        qq = re.findall(r'\[CQ:at,qq=(\d+?)\]',session.ctx['raw_message'])
        if qq:
            qq = qq[0]
        else:
            qq, gid, score= session.ctx['raw_message'].replace('充值','').strip().split(' ')
            p = select_db_score(qq,gid)
            tscore = int(score)+p[1]
            update_db_score(tscore, p[0])
            await session.send('充值成功')
            return
        score = session.ctx['raw_message'].split(']')[-1].strip()
        p = select_db_score(qq,session.ctx['group_id'])
        tscore = int(score)+p[1]
        update_db_score(tscore, p[0])
        bot = nonebot.get_bot()
        info = await bot.get_group_member_info(group_id=session.ctx['group_id'],user_id=qq)
        nickname = info.get('card')
        nickname = nickname if nickname else info.get('nickname')
        await session.send('成功帮%s充值%s圣金币！' % (nickname, score))


@on_command('转账',only_to_me=False)
async def fan(session: CommandSession):

    qq = re.findall(r'\[CQ:at,qq=(\d+?)\]',session.ctx['raw_message'])[0]
    score = session.ctx['raw_message'].split(']')[-1].strip()

    if int(qq) == session.ctx['user_id']:
        return
    if int(score) > 0:
        p2 = select_db_score(session.ctx['user_id'],session.ctx['group_id'])
        pcount = p2[1]
        if pcount < int(score):
            await session.send('您的余额为%s圣金币\n超过转账金额' % (p2[1]))
            return
        p = select_db_score(qq,session.ctx['group_id'])
        tscore = int(score)+p[1]
        update_db_score(tscore, p[0])
        tscore2 = p2[1] - int(score)
        update_db_score(tscore2, p2[0])
        bot = nonebot.get_bot()
        info = await bot.get_group_member_info(group_id=session.ctx['group_id'],user_id=qq)
        nickname = info.get('card')
        nickname = nickname if nickname else info.get('nickname')
        await session.send('转账成功！\n您的余额为%s圣金币\n%s 余额%s圣金币' % (tscore2,nickname, tscore))


@on_command('jy', aliases=('jy'),only_to_me=False)
async def tuling(session: CommandSession):
    if session.ctx['message'][0]['data']['text'] != 'jy':
        return
    bot = nonebot.get_bot()
    await bot.set_group_ban(group_id=session.ctx['group_id'],user_id=session.ctx['user_id'],duration=60)

qian = {}
@on_command('抽签',only_to_me=False)
async def tuling(session: CommandSession):
    group_id = session.ctx['group_id']
    if group_id in [875164857,686950644,736742903]:
        return
    user_id = session.ctx['user_id']
    group_id = session.ctx['group_id']
    current_date = datetime.now().strftime('%Y-%m-%d')

    c = qian.get(user_id,'')
    if c:
        if c == current_date:
            await session.send('一天一次，不然就不灵了哦')
            return
    qian[user_id] = current_date
    # if not qian.get(session.ctx['user_id'],''):
    async with httpx.AsyncClient() as client:
        ret = await client.get('http://www.itpk.cn/jsonp/api.php?question=观音灵签',timeout=3)
    ret = json.loads(ret.content.decode('unicode_escape')[3:]) 
    msg = [
        '签位: ' + ret['haohua'],
        '签语: ' + ret['qianyu'],
        '诗意: ' + ret['shiyi'],
        '解签: ' + ret['jieqian'],
    ]
    await session.send('\n'.join(msg))


@on_command('开机', aliases=('关机',),only_to_me=False)
async def tuling(session: CommandSession):
    role = session.ctx['sender']['role']
    if session.ctx['user_id'] == 736209298 or (role != 'member' and session.ctx['group_id'] not in [333269216]):
        if session.ctx['raw_message'] == '开机':
            turn_on(session.ctx['group_id'])
            await session.send('开机是什么？能吃吗？')
        if session.ctx['raw_message'] == '关机':
            turn_off(session.ctx['group_id'])
            await session.send('太好了，终于可以下班啦')

@on_command('违禁',only_to_me=False)
async def tuling(session: CommandSession):

    role = session.ctx['sender']['role']
    if session.ctx['user_id'] == 736209298 or role == 'owner':
        if session.ctx['raw_message'].startswith('违禁词添加'):
            if session.ctx['raw_message'][5:].strip():
                rd.sadd(session.ctx['group_id'],session.ctx['raw_message'][5:].strip())
                await session.send('违禁词添加成功')
        if session.ctx['raw_message'].startswith('违禁词删除'):
            if session.ctx['raw_message'].startswith('违禁词删除'):
                rd.srem(session.ctx['group_id'],session.ctx['raw_message'][5:].strip())
                await session.send('违禁词删除成功')
        if session.ctx['raw_message'].startswith('违禁词查看'):
            if session.ctx['raw_message'].startswith('违禁词查看'):
                bans = rd.sinter(session.ctx['group_id'])
                msg = '本群违禁词：\n'
                for i in bans:
                    msg += '%s, ' % i
                await session.send(msg)


@on_command('取码', only_to_me=False)
async def huantou(session: CommandSession):
    arg = session.ctx['raw_message'].replace('取码','')
    await session.send(arg,auto_escape=True)

def select_sign_rank2(*args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select user_id,score from qq_sign where group_id=%s ORDER BY score limit 0,100"
        cur.execute(sql,args)
        ret = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)


def select_sign_rank(*args):
    try:
        conn = pymysql.connect(host='127.0.0.1',user='root',passwd='qwe123',db='bilibili',charset='utf8')
        cur = conn.cursor()
        sql = "select user_id,score from qq_sign where group_id=%s ORDER BY score desc limit 0,15"
        cur.execute(sql,args)
        ret = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print(e)

@on_command('富豪', aliases=('穷人','富人','负豪'),only_to_me=False)
async def tuling(session: CommandSession):
    if '富' in session.ctx['raw_message']:
        rets = select_sign_rank(session.ctx['group_id'])
        msg = '★本群圣金币富豪排行榜★'
    elif '穷人榜' in session.ctx['raw_message'] or '负豪榜' in session.ctx['raw_message']:
        rets = select_sign_rank2(session.ctx['group_id'])
        msg = '★本群圣金币负豪排行榜★'
    c = 0
    for i in rets:
        count = i[1]
        if c < 10:
            user_id = i[0]
            try:
                info = await session.bot.get_group_member_info(group_id=session.ctx['group_id'],user_id=user_id)
                nickname = info.get('card')
                nickname = nickname if nickname else info.get('nickname')
                nickname = nickname.replace('\n','')
                nickname = nickname if len(nickname) > 1 else nickname + '(' +str(user_id) + ')'
            except:
                #nickname = user_id
                continue
            c += 1
            if c == 1:
                msg += '\n%s、%s：%s' % ('[CQ:emoji,id=127942]',nickname,count)
            else:
                msg += '\n%s、%s：%s' % (c,nickname,count)
    await session.send(msg)

@on_command('qq', only_to_me=False)
async def huantou(session: CommandSession):
    rm = session.ctx['raw_message']
    if 'qq' in rm and 'aa' in rm:
        msg = ''
        if 'image' not in rm:
            msg = '教学失败，需要加表情包图片哦，让蕾姆可爱起来吧！'
            await session.send(msg)
            return
        for i in session.ctx['message']:
            if i['type'] == 'image':
                pic = i['data']['url']
                break
        img = re.findall(r'\[CQ:image,file=(.+?)\]', rm)[0]
        img_data = requests.get(pic).content
        with open('/home/pro_coolq/data/image/biaoqing/%s' % img,'wb') as f:
            f.write(img_data)
        with open('/home/2coolq/data/image/biaoqing/%s' % img,'wb') as f:
            f.write(img_data)
        k = rm.split('aa')[0].replace('qq','').strip()
        v = rm.split('aa')[-1].strip().replace(img,'biaoqing/' + img)
        ret = rd.hget('rem2',k)
        if ret:
            v = ret + '|' + v
        rd.hset('rem2',k,v)
        await session.send('教学成功，主人会尽快审核。' + msg)

@on_command('审核', only_to_me=False)
async def huantou(session: CommandSession):
    if session.ctx['user_id'] != 736209298:
        return
    k = rd.hkeys('rem2')[0]
    v = rd.hget('rem2',k)
    if '|' in v:
        v1,v2 = v.split('|',1)
        rd.hset('rem2',k,v2)
    else:
        v1 = v
        rd.hdel('rem2',k)
    with open('/home/rem','w') as f:
        f.write(k+'|'+v1)
    await session.send(k+'|'+v1)

@on_command('通过', only_to_me=False)
async def huantou(session: CommandSession):
    if session.ctx['user_id'] != 736209298:
        return
    with open('/home/rem','r') as f:
        ret = f.read()
    k,v = ret.split('|')
    ret = rd.hget('rem',k)
    if ret:
        v = ret + '|' + v
    rd.hset('rem',k,v)

@on_command('十连', only_to_me=False)
async def huantou(session: CommandSession):
    group_id = session.ctx['group_id']
    arg = session.ctx['raw_message']
    if arg != '十连抽':
        return

    j = 0
    user_id = session.ctx['user_id']
    p = select_db_score(user_id,group_id)
    if p:
        score = p[1]
        if score >=500:
            j = 1
        else:
            msg = '十连失败\n不足500圣金币\n剩余：%s圣金币\n可输入“商店”查看现有道具' % score
    else:
        msg = '十连失败\n不足500圣金币\n可以签到获得哦'
    #s = jiahu.get(user_id,0)
    s = rd.hget('jh',user_id)
    

    if j == 0 and (not s):
        await session.send(msg)
        return

    #c = ck.get(user_id,'')
    #cc = datetime.now().strftime('%Y-%m-%d')
    #if not c:
    #    c = [cc,1]
    #    ck[user_id] = c
    #else:
    #    if c[0] == cc:
    #        if c[1] >= 10000:
    #            return
           # else:
            #    ck[user_id] = [cc,c[1]+10]
            #await session.send('今日抽卡次数已满，请明天再来吧')
        #else:
         #   c = [cc,10]
          #  ck[user_id] = c
    paths = []
    tscore = 0
    for i in range(10):
        s = rd.hget('jh',user_id)
        if s:
            s = int(s)
            if s > 1:
                rd.hset('jh',user_id,s-1)
            else:
                rd.hdel('jh',user_id)
            ds = [10,50,50,5,5,5,5]
            if tscore <= 800 and i==9:
                ds = [399]
        else:
            ds = ['a30','a30','a30','a30','a30','a30','a50','a50','a30','a30','a50','a10','a10','a10','a10','a10','a30','a50','a50','a50','a50','a50',10,10,10,10,10,10,10,50,50,50,50,100]
        
        if tscore >= 1200:
            ds = ['a10','a10','a10','a30','a30','a30','a30','a30','a30','a30','a30','a50','a50','a50','a50','a50','a30','a30','a30','a30','a30','a30',10,10,10,10,10,10,10,10,50,50,50,100]
             
        d = random.choice(ds)
        if d == 5:
            d = random.choice([100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,188,188,188,188,188,266,266,288,288,299,299,399])
        pic = random.choice(os.listdir('/home/pro_coolq/data/image/re0/%s' % d))
        path = '/home/pro_coolq/data/image/re0/%s/%s' % (d,pic)
        paths.append(path)
        if 'a' in str(d):
            d = int(d.replace('a','-'))
        tscore += d

    #合成十连图
    os.chdir('/home/pro_coolq/data/image/re0')
    im_list = [Image.open(fn) for fn in paths]
    ims = []
    for i in im_list:
        new_img = i.resize((70, 120), Image.BILINEAR)
        ims.append(new_img)
    width, height = ims[0].size
    result = Image.new(ims[0].mode, (width * 5, height * 2))
    for i in range(5):
        result.paste(ims[i], box=(i * width, 0))
    for i in range(5):
        result.paste(ims[i+5], box=(i * width, height))
    shilian_name = str(tscore).replace('-','a')
    result.save('/home/pro_coolq/data/image/re0/shilian/%s.png' % shilian_name)
    result.save('/home/2coolq/data/image/re0/shilian/%s.png' % shilian_name)
    if tscore > 0:
        msg = '恭喜[CQ:face,id=99]本次十连\n奖励%s圣金币\n总计：%s圣金币' % (tscore, score + tscore)
    else:
        msg = '残念[CQ:face,id=173]本次十连\n扣除%s圣金币\n剩余：%s圣金币' % (str(abs(tscore)), score + tscore)
    update_db_score(score + tscore, p[0])
    await session.send('[CQ:image,file=re0/shilian/%s.png]%s' % (shilian_name, msg))

dajie={}
@on_command('打劫',only_to_me=False)
async def fan(session: CommandSession):
    user_id = session.ctx['user_id']
    gid = session.ctx['group_id']
    qq = re.findall(r'\[CQ:at,qq=(\d+?)\]',session.ctx['raw_message'])[0]
    if qq.strip() == '736209298':
        zl = [
            '@三好市民，主人，有人要打劫你，快来制裁他',
            '打劫我主人干嘛啦！',
            '看来你还不知道什么是真正的痛楚，@三好市民',
            '锤你哦',
            '呸呸呸',
            '这个人疯了，隔离吧',
            '呀嘞呀嘞',
            '洗洗睡吧',
            '？',
            '哦豁',
            '害',
            '在危险的边缘疯狂试探',
            '闷声发大财不懂吗',
            '你电动车没了',
            '哦',
        ]
        await session.send(random.choice(zl))
        return
    res = rd.hget('dajie',user_id)
    dj_time = datetime.now().strftime('%Y-%m-%d %H:%M')

    #c = dajie.get(user_id,'')
    #cc = datetime.now().strftime('%Y-%m-%d')
    #if not c:
    #    c = [cc,1]
    #    dajie[user_id] = c
    #else:
    #    if c[0] == cc:
    #        if c[1] >= 2 and (not res) and user_id != 736209298:
    #            return
    #        else:
    #            dajie[user_id] = [cc,c[1]+1]
    #    else:
    #        c = [cc,1]
    #        dajie[user_id] = c

    score = random.randrange(50,100)

    if int(qq) == session.ctx['user_id']:
        return
    count = rd.hget('fantan',qq)
    p = select_db_score(qq,session.ctx['group_id'])
    pcount1 = p[1]
    pat = [0,1,1,0]
    
    if count and res:
        await session.send('你有打劫卡，他有反弹卡\n蕾姆很为难的说，换其他人吧')
        code = '%s%s' % (gid,qq)
        dj = rd.hget('dj',code)
        card = session.ctx['sender'].get('card','')
        nickname = card if card else session.ctx['sender'].get('nickname','')
        sing = '冲突'
        msg = '%s\n%s（%s）:%s' % (dj_time, nickname, user_id, sing)
        if dj:
            dj_list = json.loads(dj)
            dj_list.insert(0, msg)
            rd.hset('dj', code, json.dumps(dj_list[:20]))
        else:
            rd.hset('dj', code, json.dumps([msg]))
        return
    if count:
        pat = [1]
    if res:
        score = random.randrange(100,200)
        pat = [1]
    if random.choice(pat):
        p2 = select_db_score(session.ctx['user_id'],session.ctx['group_id'])
        pcount = p2[1]
        #if pcount < 100:
        #    await session.send('您的余额为%s圣金币\n不足100无法使用打劫' % (p2[1]))
        #    return
        bot = nonebot.get_bot()
        info = await bot.get_group_member_info(group_id=session.ctx['group_id'],user_id=qq)
        nickname = info.get('card')
        nickname = nickname if nickname else info.get('nickname')
        if pcount1 < 100:
            await session.send('%s 余额为%s圣金币\n打劫穷人天理难容，换个人吧' % (nickname, pcount1))
            code = '%s%s' % (gid,qq)
            dj = rd.hget('dj',code)
            card = session.ctx['sender'].get('card','')
            nickname = card if card else session.ctx['sender'].get('nickname','')
            sing = '失败'
            msg = '%s\n%s（%s）:%s' % (dj_time, nickname, user_id, sing)
            if dj:
                dj_list = json.loads(dj)
                dj_list.insert(0, msg)
                rd.hset('dj', code, json.dumps(dj_list[:20]))
            else:
                rd.hset('dj', code, json.dumps([msg]))
            return
        if res:
            if int(res) > 1:
                res_count = int(res) - 1
                rd.hset('dajie',user_id,res_count)
            else:
                rd.hdel('dajie',user_id)
        if count:
            cc = int(count) - 1
            if cc == 0:
                rd.hdel('fantan',qq)
            else:
                rd.hset('fantan',qq,cc)

            tscore = pcount1 + int(score)
            update_db_score(tscore, p[0])
            tscore2 = pcount - int(score)
            update_db_score(tscore2, p2[0])
            if str(qq) == '2960419612i':
            #if str(qq) == '2960419612':
                rd.setex(user_id,24*60*60,1)
                await session.send('打劫失败！对方持有反弹卡\n你被反打劫%s圣金币！并且被关监狱1天！\n您的余额为%s圣金币\n%s 余额%s圣金币' % (score,tscore2,nickname, tscore))
            else:
                rd.setex(user_id,12*60*60,1)
                await session.send('打劫失败！对方持有反弹卡\n你被反打劫%s圣金币！并且被关监狱12小时！\n您的余额为%s圣金币\n%s 余额%s圣金币' % (score,tscore2,nickname, tscore))
            code = '%s%s' % (gid,qq)
            dj = rd.hget('dj',code)
            card = session.ctx['sender'].get('card','')
            nickname = card if card else session.ctx['sender'].get('nickname','')
            sing = '反弹'
            msg = '%s\n%s（%s）:%s' % (dj_time, nickname, user_id, sing)
            if dj:
                dj_list = json.loads(dj)
                dj_list.insert(0, msg)
                rd.hset('dj', code, json.dumps(dj_list[:20]))
            else:
                rd.hset('dj', code, json.dumps([msg]))

            return

        tscore = pcount1 - int(score)
        update_db_score(tscore, p[0])
        tscore2 = pcount + int(score)
        update_db_score(tscore2, p2[0])

        await session.send('打劫成功%s圣金币！\n您的余额为%s圣金币\n%s 余额%s圣金币' % (score,tscore2,nickname, tscore))
        code = '%s%s' % (gid,qq)
        dj = rd.hget('dj',code)
        card = session.ctx['sender'].get('card','')
        nickname = card if card else session.ctx['sender'].get('nickname','')
        sing = '成功'
        msg = '%s\n%s（%s）:%s' % (dj_time, nickname, user_id, sing)
        if dj:
            dj_list = json.loads(dj)
            dj_list.insert(0, msg)
            rd.hset('dj', code, json.dumps(dj_list[:20]))
        else:
            rd.hset('dj', code, json.dumps([msg]))

    else:
        rd.setex(user_id,12*60*60,1)
        await session.send('打劫失败，你被关入监狱，接下来12小时无法使用命令。')
        code = '%s%s' % (gid,qq)
        dj = rd.hget('dj',code)
        card = session.ctx['sender'].get('card','')
        nickname = card if card else session.ctx['sender'].get('nickname','')
        sing = '失败'
        msg = '%s\n%s（%s）:%s' % (dj_time, nickname, user_id, sing)
        if dj:
            dj_list = json.loads(dj)
            dj_list.insert(0, msg)
            rd.hset('dj', code, json.dumps(dj_list[:20]))
        else:
            rd.hset('dj', code, json.dumps([msg]))


ck = {} 
jiahu = {}
@on_command('抽卡', aliases=('抽卡'),only_to_me=False)
async def huantou(session: CommandSession):
    user_id = session.ctx['user_id']
    group_id = session.ctx['group_id']
    if str(group_id) in rd.sinter('ck_button'):
        return
    arg = session.ctx['raw_message']
    if arg != '抽卡':
        return

    j = 0
    user_id = session.ctx['user_id']
    p = select_db_score(user_id,group_id)
    if p:
        score = p[1]
        if score >=10:
            j = 1
        else:
            msg = '抽卡失败\n圣金币不足\n剩余：%s圣金币\n可输入“商店”查看现有道具' % score
    else:
        msg = '抽卡失败\n圣金币不足\n可以签到获得哦'
    #s = jiahu.get(user_id,0)
    s = rd.hget('jh',user_id)

    if j == 0 and (not s):
        await session.send(msg)
        return
    ds = [1,1,1,1,1,1,1,1,1,1,2,2,3,3,4,4,5]
    #if score < 500:
    #    ds = [1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,3,3,3,3,3,3,3,4,4,4,4,5]
    c = ck.get(user_id,'')
    cc = datetime.now().strftime('%Y-%m-%d')
    if not c:
        c = [cc,1]
        ck[user_id] = c
    else:
        if c[0] == cc:
            if c[1] == 10 and (not s):
                ck[user_id] = [cc,c[1]+1]
                await session.send('真的要继续吗？下面可能是万丈深渊哦！')
                return
            if c[1] == 31 and (not s):
                await session.send('今日单抽已满30次！')
                ck[user_id] = [cc,c[1]+1]
                return
            if c[1] > 31 and (not s):
                return
            else:
                ck[user_id] = [cc,c[1]+1]

            #await session.send('今日抽卡次数已满，请明天再来吧')
        else:
            c = [cc,1]
            ck[user_id] = c
    if c[1] > 10:
        ds = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,3,3,4,4]
    #if ck[user_id][1] == 10:
    #    await session.send('真的要继续吗？下面可能是万丈深渊哦')
    #    return
    # 测试
    #if score > 100:
    #    ds = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,3,3,3,4,4,4,4,5]
    if s:
        s = int(s)
        if s > 1:
            rd.hset('jh',user_id,s-1)
        else:
            rd.hdel('jh',user_id)
        ds = [3,4,5,5,5]
    d = random.choice(ds)
    if d == 1:
        pic = random.choice(os.listdir('/home/pro_coolq/data/image/re0/%s' % d))
        if '你很' in pic:
            c = 50
        else:
            c = 30
        tscore = score - c
        update_db_score(tscore, p[0])
        msg = '糟糕[CQ:face,id=177]本次抽卡\n扣除%s圣金币\n剩余：%s圣金币' % (c,tscore)
        name = pic.split('.')[0]
        await session.send('%s[CQ:image,file=re0/%s/%s]%s' % (name,d, pic, msg))
        return
    elif d == 2:
        tscore = score-10
        update_db_score(tscore, p[0])
        msg = '残念[CQ:face,id=173]本次抽卡\n消耗10圣金币\n剩余：%s圣金币' % tscore
    elif d == 3:
        tscore = score+10
        update_db_score(tscore, p[0])
        msg = '加油[CQ:face,id=21]本次抽卡\n奖励10圣金币\n剩余：%s圣金币' % tscore
    elif d == 4:
        tscore = score+50
        update_db_score(tscore, p[0])
        msg = '恭喜[CQ:face,id=99]本次抽卡\n奖励50圣金币\n总计：%s圣金币' % tscore
    elif d == 5:
        pic = random.choice(os.listdir('/home/pro_coolq/data/image/re0/%s' % d))
        if '剑圣的名义' in pic:
            c=399
        elif '莱因哈鲁特·工作闲暇' in pic:
            c=299
        elif '特蕾希雅·漫天黄花' in pic:
            c=288
        elif '雷姆·失控的鬼' in pic or '鬼族' in pic:
            c=299
        elif '青年威尔海姆·挥剑练习' in pic:
            c=266
        elif '由里乌斯·王国之剑' in pic:
            c=188
        elif '爱蜜莉雅·朦胧的睡意' in pic:
            c=266
        elif '沙' in pic:
            c=399
        elif '信任的约定' in pic:
            c=299
        else:
            c=100
        tscore = score + c
        update_db_score(tscore, p[0])
        msg = '撒花[CQ:face,id=144]本次抽卡\n奖励%s圣金币!\n总计：%s圣金币' % (c,tscore)
        name = pic.split('.')[0]
        await session.send('%s[CQ:image,file=re0/%s/%s]%s' % (name,d, pic, msg))
        return
    pic = random.choice(os.listdir('/home/pro_coolq/data/image/re0/%s' % d))
    name = pic.split('.')[0]
    #if d == 2 or d==3:
    #    await session.send('%s\n%s' % (name,msg))
    #    return

    await session.send('%s[CQ:image,file=re0/%s/%s]%s' % (name,d, pic, msg))

@on_command('商店',only_to_me=False)
async def fan(session: CommandSession):
    if session.ctx['raw_message'].strip() == '商店':
        msg = [
            '★加护(5块/1个)：\n输入"使用加护"，接下来的十次抽卡强运加持，总共可获得一千左右圣金币。',
            #'★死亡回溯(5块/1个)：\n先输入"存档"，记录现有圣金币数a，想回档的时候输入"使用死亡回溯"，即可回档至a圣金币。',
            '★反弹卡(1块/1个)：\n当有人打劫你时消耗一张，会反打劫对方，并将对方关入监狱',
            '★保释卡(5毛/1个)：\n保释@某人，或输入：保释自己，就可以出狱啦',
            '★打劫卡(1块/1个)：\n打劫@某人,打劫金额翻倍成功率100%。',
            '★禁闭卡(1块/1个)：\n关禁闭@某人，可将对方关禁闭12小时。'
        ]
        t = '\n' + '可找三好736209298购买，支持一下，就当赞助服务器了。'
        await session.send('\n'.join(msg) + t)

@on_command('赠送',only_to_me=False)
async def fan(session: CommandSession):
    qq = re.findall(r'\[CQ:at,qq=(\d+?)\]',session.ctx['raw_message'])
    if qq:
        qq = qq[0]
    uid = session.ctx['user_id']
    if uid == 736209298:

        if session.ctx['raw_message'].startswith('赠送加护'):
            qq, count = session.ctx['raw_message'].replace('赠送加护','').strip().split(' ')
            ret = rd.hget('jiahu',qq)
            if ret:
                ccount = int(ret) + int(count)
            else:
                ccount = int(count)
            rd.hset('jiahu',qq,ccount)
            await session.send('恭喜%s获得莱茵哈鲁特的加护%s个，可输入背包查看' % (qq,count))

        elif session.ctx['raw_message'].startswith('赠送死亡回溯'):
            qq, count = session.ctx['raw_message'].replace('赠送死亡回溯','').strip().split(' ')
            ret = rd.hget('siwang',qq)
            if ret:
                ccount = int(ret) + int(count)
            else:
                ccount = int(count)
            rd.hset('siwang',qq,ccount)
            await session.send('恭喜%s获得死亡回溯，可输入背包查看' % qq)

        elif session.ctx['raw_message'].startswith('赠送反弹卡'):
            qq, count = session.ctx['raw_message'].replace('赠送反弹卡','').strip().split(' ')
            ret = rd.hget('fantan',qq)
            if ret:
                ccount = int(ret) + int(count)
            else:
                ccount = int(count)
            rd.hset('fantan',qq,ccount)
            await session.send('恭喜%s获得反弹卡%s张，可输入背包查看' % (qq,count))

        elif session.ctx['raw_message'].startswith('赠送打劫卡'):
            qq, count = session.ctx['raw_message'].replace('赠送打劫卡','').strip().split(' ')
            ret = rd.hget('dajie',qq)
            if ret:
                ccount = int(ret) + int(count)
            else:
                ccount = int(count)
            rd.hset('dajie',qq,ccount)
            await session.send('恭喜%s获得打劫卡%s张，可输入背包查看' % (qq,count))

        elif session.ctx['raw_message'].startswith('赠送保释卡'):
            qq, count = session.ctx['raw_message'].replace('赠送保释卡','').strip().split(' ')
            ret = rd.hget('baoshi',qq)
            if ret:
                ccount = int(ret) + int(count)
            else:
                ccount = int(count)
            rd.hset('baoshi',qq,ccount)
            await session.send('恭喜%s获得保释卡%s张，可输入背包查看' % (qq,count))
        elif session.ctx['raw_message'].startswith('赠送禁闭卡'):
            qq, count = session.ctx['raw_message'].replace('赠送禁闭卡','').strip().split(' ')
            ret = rd.hget('jinbi',qq)
            if ret:
                ccount = int(ret) + int(count)
            else:
                ccount = int(count)
            rd.hset('jinbi',qq,ccount)
            await session.send('恭喜%s获得禁闭卡%s张，可输入背包查看' % (qq,count))

    elif qq:
        count = int(session.ctx['raw_message'].split(']')[-1].strip())

        if session.ctx['raw_message'].startswith('赠送加护'):
            ret = rd.hget('jiahu',uid)
            if ret:
                ccount = int(ret) - count
                if ccount >= 0:
                    if ccount == 0:
                        rd.hdel('jiahu',uid)
                    else:
                        rd.hset('jiahu',uid,ccount)
                    ret2 = rd.hget('jiahu',qq)
                    if ret2:
                        ccc = int(ret2) + int(count)
                    else:
                        ccc = int(count)
                    rd.hset('jiahu',qq,ccc)
                    await session.send('恭喜%s获得莱茵哈鲁特的加护%s个，可输入背包查看' % (qq,count))

        elif session.ctx['raw_message'].startswith('赠送死亡回溯'):
            ret = rd.hget('siwang',uid)
            if ret:
                ccount = int(ret) - count
                if ccount >= 0:
                    if ccount == 0:
                        rd.hdel('siwang',uid)
                    else:
                        rd.hset('siwang',uid,ccount)
                    ret2 = rd.hget('siwang',qq)
                    if ret2:
                        ccc = int(ret2) + int(count)
                    else:
                        ccc = int(count)
                    rd.hset('siwang',qq,ccc)
                    await session.send('恭喜%s获得死亡回溯，可输入背包查看' % qq)

        elif session.ctx['raw_message'].startswith('赠送反弹卡'):
            ret = rd.hget('fantan',uid)
            if ret:
                ccount = int(ret) - count
                if ccount >= 0:
                    if ccount == 0:
                        rd.hdel('fantan',uid)
                    else:
                        rd.hset('fantan',uid,ccount)
                    ret2 = rd.hget('fantan',qq)
                    if ret2:
                        ccc = int(ret2) + int(count)
                    else:
                        ccc = int(count)
                    rd.hset('fantan',qq,ccc)
                    await session.send('恭喜%s获得反弹卡%s张，可输入背包查看' % (qq,count))

        elif session.ctx['raw_message'].startswith('赠送打劫卡'):
            ret = rd.hget('dajie',uid)
            if ret:
                ccount = int(ret) - count
                if ccount >= 0:
                    if ccount == 0:
                        rd.hdel('dajie',uid)
                    else:
                        rd.hset('dajie',uid,ccount)
                    ret2 = rd.hget('dajie',qq)
                    if ret2:
                        ccc = int(ret2) + int(count)
                    else:
                        ccc = int(count)
                    rd.hset('dajie',qq,ccc)
                    await session.send('恭喜%s获得打劫卡%s张，可输入背包查看' % (qq,count))

        elif session.ctx['raw_message'].startswith('赠送保释卡'):
            ret = rd.hget('baoshi',uid)
            if ret:
                ccount = int(ret) - count
                if ccount >= 0:
                    if ccount == 0:
                        rd.hdel('baoshi',uid)
                    else:
                        rd.hset('baoshi',uid,ccount)
                    ret2 = rd.hget('baoshi',qq)
                    if ret2:
                        ccc = int(ret2) + int(count)
                    else:
                        ccc = int(count)
                    rd.hset('baoshi',qq,ccc)
                    await session.send('恭喜%s获得保释卡%s张，可输入背包查看' % (qq,count))
        elif session.ctx['raw_message'].startswith('赠送禁闭卡'):
            ret = rd.hget('jinbi',uid)
            if ret:
                ccount = int(ret) - count
                if ccount >= 0:
                    if ccount == 0:
                        rd.hdel('jinbi',uid)
                    else:
                        rd.hset('jinbi',uid,ccount)
                    ret2 = rd.hget('jinbi',qq)
                    if ret2:
                        ccc = int(ret2) + int(count)
                    else:
                        ccc = int(count)
                    rd.hset('jinbi',qq,ccc)
                    await session.send('恭喜%s获得禁闭卡%s张，可输入背包查看' % (qq,count))



@on_command('背包',only_to_me=False)
async def fan(session: CommandSession):
    if '背包' in session.ctx['raw_message']:
        qq = session.ctx['user_id']
        msg = '您现有的道具如下：'
        if str(qq) in rd.hkeys('jiahu'):
            c = rd.hget('jiahu',qq)
            msg += '\n' + '★加护（%s个）' % c
        if str(qq) in rd.hkeys('siwang'):
            c = rd.hget('siwang',qq)
            msg += '\n' + '★死亡回溯（%s个）' % c
        if str(qq) in rd.hkeys('fantan'):
            c = rd.hget('fantan',qq)
            msg += '\n' + '★反弹卡（%s个）' % c
        if str(qq) in rd.hkeys('dajie'):
            c = rd.hget('dajie',qq)
            msg += '\n' + '★打劫卡（%s个）' % c
        if str(qq) in rd.hkeys('baoshi'):
            c = rd.hget('baoshi',qq)
            msg += '\n' + '★保释卡（%s个）' % c
        if str(qq) in rd.hkeys('jinbi'):
            c = rd.hget('jinbi',qq)
            msg += '\n' + '★禁闭卡（%s个）' % c

        if msg == '您现有的道具如下：':
            return
        await session.send(msg)

@on_command('存档',only_to_me=False)
async def fan(session: CommandSession):
    qq = session.ctx['user_id']
    group_id = session.ctx['group_id']
    if session.ctx['raw_message'] == '存档':
        c = rd.hget('siwang',qq)
        if c:
            p = select_db_score(qq,group_id)
            ret = rd.hget('cundang',qq)
            if ret:
                zz = ret.split('|')[-1]
            else:
                zz = 0
            rd.hset('cundang',qq,'%s|%s|%s' % (p[0],p[1],zz))
            await session.send('存档成功！\n当"使用死亡回溯"时，将会回档至现在的%s圣金币' % p[1])
            return

@on_command('使用',only_to_me=False)
async def fan(session: CommandSession):
    qq = session.ctx['user_id']
    if session.ctx['raw_message'] == '使用加护':
        c = rd.hget('jiahu',qq)
        if c:
            if int(c) <= 1:
                rd.hdel('jiahu',qq)
            else:
                rd.hset('jiahu',qq,int(c)-1)
            rd.hset('jh',qq,10)
            #jiahu[int(qq)] = 10
            await session.send('加护成功！\n接下来的十次抽卡欧皇附身，祝你好运哦~')
            return
    elif session.ctx['raw_message'] == '使用死亡回溯':
        ret = rd.hget('cundang',qq)
        c = rd.hget('siwang',qq)
        if c and ret:
            if int(c) <= 1:
                rd.hdel('siwang',qq)
            else:
                rd.hset('siwang',qq,int(c)-1)
            cid,score,zz = ret.split('|')
            update_db_score(score,cid)
            rd.hdel('cundang',qq)
            await session.send('触发死亡回溯成功！\n已成功回档至%s圣金币！' % score)
            return
    elif session.ctx['raw_message'].startswith('使用大赦天下卡'):
        c = rd.hget('dashe',qq)
        if c:
            if int(c) <= 1:
                rd.hdel('dashe',qq)
            else:
                rd.hset('dashe',qq,int(c)-1)
            rd.hdel('jianyu',session.ctx['group_id'])
            await session.send('触发大赦天下成功！\n本群所有因打劫入狱的群员全部释放！')
            return

#@on_command('i监狱',only_to_me=False)
#async def fan(session: CommandSession):
#    qq = session.ctx['user_id']
#    msg = '离释放小于12小时的犯人：'
#    if session.ctx['raw_message'] == '监狱名单':
#        for i in rd.keys():
#            ttl = rd.ttl(i)
#            if ttl > 0 and ttl < 43200:
#                try:
#                    info = await session.bot.get_group_member_info(group_id=session.ctx['group_id'],user_id=i)
#                    nickname = info.get('card')
#                    nickname = nickname if nickname else info.get('nickname')
#                except:
#                    continue
#                msg += '\n%s：%.1f小时' % (nickname,ttl/3600) 
#        await session.send(msg)

@on_command('保释',aliases=('开门',),only_to_me=False)
async def fan(session: CommandSession):
    if session.ctx['raw_message'].startswith('保释') or session.ctx['raw_message'].startswith('开门'):
        uid = session.ctx['user_id']
        group_id = session.ctx['group_id']
        if 'CQ' in session.ctx['raw_message']:
            qq = re.findall(r'\[CQ:at,qq=(\d+?)\]',session.ctx['raw_message'])[0]
        elif session.ctx['raw_message'] == '保释自己':
            qq = uid     
        else:
            return     
        c = rd.hget('baoshi',uid)
        if c:
            if not rd.get(qq):
                await session.send('对方不在监狱内。')
                return
            if int(c) <= 1:
                rd.hdel('baoshi',uid)
            else:
                rd.hset('baoshi',uid,int(c)-1)
            rd.delete(qq)
            info = await session.bot.get_group_member_info(group_id=session.ctx['group_id'],user_id=qq)
            nickname = info.get('card')
            nickname = nickname if nickname else info.get('nickname')
            await session.send('保释成功！恭喜%s成功出狱！' % nickname)

@on_command('关押',only_to_me=False)
async def fan(session: CommandSession):
    if session.ctx['raw_message'].startswith('关押时长'):
        uid = session.ctx['user_id']
        c = rd.get(uid)
        if c:
            ttl = rd.ttl(uid)
            msg = '您离出狱还有%.2f小时\n输入商店可购买保释卡' % (ttl/3600)
            await session.send(msg)

@on_command('一起',only_to_me=False)
async def huantou(session: CommandSession):
    role = session.ctx['sender']['role']
    if role == 'member':
        return
    if '一起听歌' not in session.ctx['raw_message']:
        return
    bot = nonebot.get_bot()
    cookie = await bot.get_cookies()
    cookie = str(cookie)
    skey = re.findall(r"skey=(.+?)'",cookie)[0]
    headers = {
    'Cookie': 'uin=o0%s; skey=%s;' % (session.ctx['self_id'],skey.replace(';','')),
    }
    bkn = getBKN(skey)
    ret = requests.get('https://web.qun.qq.com/cgi-bin/media/set_media_state?t=0.469486734896817&g_tk=%s&state=1&gcode=%s&qua=V1_AND_SQ_8.2.6_1320_YYB_D&uin=o0%s&format=json&inCharset=utf-8&outCharset=utf-8' % (bkn,session.ctx['group_id'],session.ctx['self_id']),headers=headers,timeout=3)

#@on_command('关闭',only_to_me=False)
#async def huantou(session: CommandSession):
#    role = session.ctx['sender']['role']
#    if role == 'member':
#        return
#    if '关闭听歌' not in session.ctx['raw_message']:
#        return
#    bot = nonebot.get_bot()
#    cookie = await bot.get_cookies()
#    skey = re.findall(r"skey=(.+?)'",str(cookie))[0]
#    headers = {
#    'Cookie': 'uin=o0%s; skey=%s;' % (session.ctx['self_id'],skey.replace(';','')),
#    }
#    bkn = getBKN(skey)
#    requests.get('https://web.qun.qq.com/cgi-bin/media/set_media_state?t=0.469486734896817&g_tk=%s&state=0&gcode=%s&qua=V1_AND_SQ_8.2.6_1320_YYB_D&uin=o0%s&format=json&inCharset=utf-8&outCharset=utf-8' % (bkn,session.ctx['group_id'],session.ctx['self_id']),headers=headers,timeout=3)

@on_command('主体',only_to_me=False)
async def huantou(session: CommandSession):
    zt,sjyy = session.ctx['raw_message'].split('事件')
    t1 = zt.replace('主体','').replace('\n','').strip()
    sj,yy = sjyy.split('原因')
    t2 = sj.replace('\n','').strip()
    t3 = yy.replace('\n','').strip()
    text = f"""　　{t1}{t2}是怎么回事呢？{t1}相信大家都很熟悉，但是{t1}{t2}是怎么回事呢，下面就让小编带大家一起了解吧。\n　　{t1}{t2}，其实就是{t3}，大家可能会很惊讶{t1}怎么会{t2}呢？但事实就是这样，小编也感到非常惊讶。\n　　这就是关于{t1}{t2}的事情了，大家有什么想法呢，欢迎在评论区告诉小编一起讨论哦！"""
    await session.send(text)

@on_command('营销',only_to_me=False)
async def huantou(session: CommandSession):
    if '营销号生成' in session.ctx['raw_message']:
        text = "营销号生成例子：\n主体 群主\n事件 太帅了\n原因 群主天生丽质"
    await session.send(text)

@on_command('开启', aliases=('关闭',),only_to_me=False)
async def tuling(session: CommandSession):
    gid = session.ctx['group_id']
    role = session.ctx['sender']['role']
    if session.ctx['user_id'] == 736209298 or (role != 'member'):
        if session.ctx['raw_message'] == '开启抽卡':
            rd.srem('ck_button',gid)
            await session.send('Link Start!')
        if session.ctx['raw_message'] == '关闭抽卡':
            rd.sadd('ck_button',gid)
            await session.send('Link Disconnected!')

@on_command('关监',only_to_me=False)
async def huantou(session: CommandSession):
    if session.ctx['user_id'] == 736209298:
        qq = re.findall(r'\[CQ:at,qq=(\d+?)\]',session.ctx['raw_message'])[0]
        c = session.ctx['raw_message'].split(']')[-1].strip()
        arg_text = session.ctx['raw_message']
        if not c:
            jin_str = '1分钟'
        else:
            jin_str = arg_text.split(']')[-1].strip()
        if '分' in jin_str:
            jin_time = int(jin_str.replace('分','').replace('钟',''))*60
        elif '小时' in jin_str:
            jin_time = int(jin_str.replace('小时',''))*60*60
        elif '天' in jin_str:
            jin_time = int(jin_str.replace('天',''))*24*60*60
        elif '秒' in jin_str:
            jin_time = int(jin_str.replace('秒',''))
        elif jin_str == '0':
            jin_time = 0
        rd.setex(qq,jin_time,1)
        await session.send('恭喜[CQ:at,qq=%s]成功入狱！' % qq)

@on_command('小本',only_to_me=False)
async def huantou(session: CommandSession):
    user_id = session.ctx['user_id']
    gid = session.ctx['group_id']
    code = '%s%s' % (gid,user_id)
    dj = rd.hget('dj',code)
    if dj:
        msg = '您近期被人打劫名单：\n'
        dj_list = '\n'.join(json.loads(dj)[:5])
        await session.send(msg+dj_list)

@on_command('关禁',only_to_me=False)
async def huantou(session: CommandSession):
    if session.ctx['raw_message'].startswith('关禁闭'):
        uid = session.ctx['user_id']
        # group_id = session.ctx['group_id']
        if 'CQ' in session.ctx['raw_message']:
            qq = re.findall(r'\[CQ:at,qq=(\d+?)\]',session.ctx['raw_message'])[0]
        else:
            return
        c = rd.hget('jinbi',uid)
        if c:
            if int(c) <= 1:
                rd.hdel('jinbi',uid)
            else:
                rd.hset('jinbi',uid,int(c)-1)
            rd.setex(qq,12*3600,1)
            await session.send('恭喜[CQ:at,qq=%s]成功入狱！' % qq)
def jiangli(qq, gid, name):
    p = select_db_score(qq,gid)
    tscore = p[1] + name
    update_db_score(tscore, p[0])

def zengsong(qq, name):
    count = 1
    if name == '加护':
        ret = rd.hget('jiahu',qq)
        if ret:
            ccount = int(ret) + int(count)
        else:
            ccount = int(count)
        rd.hset('jiahu',qq,ccount)

    elif name == '反弹卡':
        ret = rd.hget('fantan',qq)
        if ret:
            ccount = int(ret) + int(count)
        else:
            ccount = int(count)
        rd.hset('fantan',qq,ccount)

    elif name == '打劫卡':
        ret = rd.hget('dajie',qq)
        if ret:
            ccount = int(ret) + int(count)
        else:
            ccount = int(count)
        rd.hset('dajie',qq,ccount)

    elif name == '保释卡':
        ret = rd.hget('baoshi',qq)
        if ret:
            ccount = int(ret) + int(count)
        else:
            ccount = int(count)
        rd.hset('baoshi',qq,ccount)
    elif name == '禁闭卡':
        ret = rd.hget('jinbi',qq)
        if ret:
            ccount = int(ret) + int(count)
        else:
            ccount = int(count)
        rd.hset('jinbi',qq,ccount)

@on_command('讨伐',only_to_me=False)
async def huantou(session: CommandSession):
    if session.ctx['raw_message'].startswith('讨伐名单'):
        gid = session.ctx['group_id']
        bid = 'baijing%s' % gid
        ret = rd.sinter(bid)
        if ret:
            tst = [x for x in ret]
            msg = '本次白鲸讨伐队成员名单：'
            for qq in tst:
                try:
                    info = await session.bot.get_group_member_info(group_id=gid,user_id=qq)
                    nickname = info.get('card')
                    nickname = nickname if nickname else info.get('nickname')
                    nickname = nickname.replace('\n','')
                except:
                    nickname = qq
                msg += '\n%s' % nickname
            await session.send(msg)
    if not session.ctx['raw_message'].startswith('讨伐白鲸'):
        return
    uid = session.ctx['user_id']
    gid = session.ctx['group_id']
    bid = 'baijing%s' % gid
    if session.ctx['raw_message'].startswith('讨伐白鲸') and rd.sismember(bid, uid):
        ret = rd.sinter(bid)
        if ret:
            count = int(rd.scard(bid))
            if count >= 10:
                tst = [x for x in ret]
                #bst1 = ['打劫卡','禁闭卡','保释卡','打劫卡','加护','加护','加护','保释卡','打劫卡','反弹卡',]
                #bst3 = ['打劫卡','禁闭卡','保释卡','打劫卡','加护','保释卡','保释卡','保释卡','打劫卡','反弹卡',]
                #bst2 = ['打劫卡','禁闭卡','加护','加护','反弹卡','加护','加护','保释卡','打劫卡','反弹卡',]
                #bst5 = ['反弹卡','禁闭卡','保释卡','打劫卡','打劫卡','加护','加护','保释卡','打劫卡','反弹卡',]
                #bst4 = ['禁闭卡','打劫卡','打劫卡','打劫卡','反弹卡','保释卡','保释卡','保释卡','打劫卡','反弹卡',]
                #bst = random.choice([bst1,bst4,bst5, bst2,bst3,bst1]) 
                #bst = ['禁闭卡','打劫卡','打劫卡','加护','打劫卡','保释卡','保释卡','保释卡','保释卡','反弹卡',]
                bst = [100, 200, 300, 400, 500, 50, 200, 50, 200, 1000]
                random.shuffle(bst)
                if '1662572451' in tst:
                    num1 = random.choice([50,300,400,500,1000])
                    rindex = tst.index('1662572451')
                    num2 = bst[rindex]
                    if num2 != num1:
                        bst[bst.index(num1)] = num2
                        bst[rindex] = num1
                msg = '[CQ:image,file=re0/bj/success.jpg]讨伐白鲸成功！奖励如下：'
                #msg = '[CQ:image,file=re0/bj/success.jpg]讨伐白鲸成功！战利品如下：'
                for i in range(10):
                    qq = tst[i]
                    name = bst[i]
                    #zengsong(qq, name)
                    jiangli(qq, gid, name)
                    msg += '\n[CQ:at,qq=%s]：%s' % (qq, name)
                rd.delete(bid)
            else:
                msg = '[CQ:image,file=re0/bj/bj1.jpg]人数不足10人，无法开启讨伐白鲸任务：\n目前讨伐队成员：%s人\n"加入讨伐战"消耗300圣金币。' % count
        else:
            msg = '[CQ:image,file=re0/bj/bj1.jpg]人数不足10人，无法开启讨伐白鲸任务：\n目前讨伐队成员：0人\n"加入讨伐战"消耗300圣金币。'
    else:
        msg = '参加讨伐白鲸任务消耗300金币，随机获得奖励。您不是白鲸讨伐队成员，请输入"加入讨伐战"加入。'
    await session.send(msg)
        
@on_command('加入',only_to_me=False)
async def huantou(session: CommandSession):
    if session.ctx['raw_message'].startswith('加入讨伐'):
        uid = session.ctx['user_id']
        gid = session.ctx['group_id']
        bid = 'baijing%s' % gid
        count = int(rd.scard(bid))
        if rd.sismember(bid, uid):
            msg = '您已加入过讨伐白鲸战了，无法重复加入。目前讨伐队人数：%s。' % count
        else:
            p = select_db_score(uid,gid)
            if count < 10:
                if p:
                    score = p[1]
                    if score >=300:
                        tscore = score-300
                        update_db_score(tscore, p[0])
                        rd.sadd(bid, uid)
                        msg = '[CQ:image,file=re0/bj/jiaru.jpg]您已成功加入白鲸讨伐战，消耗300圣金币\n目前讨伐队人数：%s' % (count+1)
                    else:
                        msg = '不足300圣金币，无法加入白鲸讨伐战。'
                else:
                    msg = '不足300圣金币，无法加入白鲸讨伐战。'
            else:
                msg = '[CQ:image,file=re0/bj/bj2.jpg]白鲸讨伐对人数已满10人，请战队成员输入"讨伐白鲸"。'
        await session.send(msg)

@on_command('拍卖',only_to_me=False)
async def huantou(session: CommandSession):
    if session.ctx['raw_message'].startswith('拍卖行'):
        msg = '[CQ:face,id=158]性感蕾姆在线拍卖[CQ:face,id=158]'
        gid = session.ctx['group_id']
        bid = 'paimai%s' % gid

        pm = rd.hgetall(bid)
        for k,v in pm.items():
            print(v)
            print(k)
            qq, daoju, jb = v.split('|')
            msg += '\n[%s][%s][%s圣金币]' % (k, daoju, jb)
        await session.send(msg)
        
@on_command('上架',only_to_me=False)
async def huantou(session: CommandSession):
    if session.ctx['raw_message'].startswith('上架'):
        uid = session.ctx['user_id']
        if session.ctx['raw_message'][2:].startswith('保释卡'):
            ret = rd.hget('baoshi',uid)
            gid = session.ctx['group_id']
            bid = 'paimai%s' % gid
            if ret:
                jb = int(session.ctx['raw_message'][5:])
                if jb < 1 or jb > 1000:
                    return
                ccount = int(ret) - 1
                if ccount >= 0:
                    res = rd.hgetall(bid)
                    if res:
                        if str(uid) in [x.split('|')[0] for x in res.values()]:
                            await session.send('主人说每个人只能上架一个道具哦')
                            return
                        resl = [1,2,3,4,5,6,7,8,9,10]
                        for i in res.keys():
                            resl.remove(int(i))
                        if resl:
                            if ccount == 0:
                                rd.hdel('baoshi',uid)
                            else:
                                rd.hset('baoshi',uid,ccount)
                            rd.hset(bid, resl[0], '%s|%s|%s' % (uid, '保释卡', jb))
                            await session.send('上架拍卖行成功')
                        else:
                            await session.send('目前拍卖行只能上架10个单品')
                            return
                    else:
                        if ccount == 0:
                            rd.hdel('baoshi',uid)
                        else:
                            rd.hset('baoshi',uid,ccount)
                        rd.hset(bid, 1, '%s|%s|%s' % (uid, '保释卡', jb))
                        await session.send('上架拍卖行成功')
                    
@on_command('购买',only_to_me=False)
async def huantou(session: CommandSession):
    if session.ctx['raw_message'].startswith('购买'):
        code = int(session.ctx['raw_message'].replace('购买','').strip())

        uid = session.ctx['user_id']
        gid = session.ctx['group_id']
        bid = 'paimai%s' % gid
        res = rd.hget(bid, code)
        if res:
            qq, daoju, jb = res.split('|')
            p2 = select_db_score(uid,gid)
            pcount = p2[1]
            if pcount < int(jb):
                await session.send('您的余额为%s圣金币\n低于商品价格' % (pcount))
                return
            else:

                pcount2 = pcount - int(jb)
                update_db_score(pcount2, p2[0])
                p1 = select_db_score(qq,gid)
                score1 = p1[1] + int(jb)
                update_db_score(score1, p1[0])
                ret = rd.hget('baoshi',uid)
                if ret:
                    ccount = int(ret) + 1
                else:
                    ccount = 1
                rd.hset('baoshi',uid,ccount)
                rd.hdel(bid,code)
                await session.send('购买成功，可输入背包查看')

@on_command('下架',only_to_me=False)
async def huantou(session: CommandSession):
    if session.ctx['raw_message'].startswith('下架'):
        code = int(session.ctx['raw_message'].replace('下架','').strip())

        uid = session.ctx['user_id']
        gid = session.ctx['group_id']
        bid = 'paimai%s' % gid
        res = rd.hget(bid, code)
        if res:
            qq, daoju, jb = res.split('|')
            if int(qq) != uid:
                return
            ret = rd.hget('baoshi',qq)
            if ret:
                ccount = int(ret) + 1
            else:
                ccount = 1
            rd.hset('baoshi',qq,ccount)
            rd.hdel(bid,code)
            await session.send('下架成功')

