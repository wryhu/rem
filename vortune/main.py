# -*- coding: utf-8 -*-

from . import utils
from .constant import *
import random
import os
from PIL import Image, ImageSequence, ImageDraw, ImageFont


async def handlingMessages(msg, bot, userGroup, userQQ):
    msg = await utils.cleanAt(msg)
    commandList = ['今日人品', '今日运势', '人品', '运势', '小狐狸签', '吹雪签']
    #commandList = ['今日人品', '今日运势', '抽签', '人品', '运势', '小狐狸签', '吹雪签']
    match = await utils.commandMatching(msg, commandList, model = ALL)
    if match['mark']:
        # Determine if it has been used today
        if await testUse(userQQ) == SUCCESS:
            model = DEFAULT
            # Detect whether it is a small fox lottery
            if msg.find('小狐狸') != -1 or msg.find('吹雪') != -1:
                model = LITTLE_FOX
            # Plot
            outPath = await drawing(model)
            # Send a message
            sendMsg = await utils.atQQ(userQQ)
            sendMsg += await utils.pictureCqCode(outPath)
            await bot.send_group_msg(group_id = userGroup, message = sendMsg)

async def testUse(userQQ):
    p = './vortune/data/user/' + str(userQQ) + '.json'
    await utils.checkFolder(p)
    content = await utils.readJson(p)
    if content == FAILURE:
        userStructure = {
            'time': await utils.getTheCurrentTime()
        }
        await utils.writeJson(p, userStructure)
        return SUCCESS
    interval = await utils.getTimeDifference(content['time'], DAY)
    if interval >= 1:
        content['time'] = await utils.getTheCurrentTime()
        await utils.writeJson(p, content)
        return SUCCESS
    return FAILURE
    
async def drawing(model):
    fontPath = {
        'title': './vortune/data/font/Mamelon.otf',
        'text': './vortune/data/font/sakura.ttf'
    }
    imgPath = await randomBasemap()
    if model == LITTLE_FOX:
        imgPath = './vortune/data/img/frame_17.png'
    img = Image.open(imgPath)
    # Draw title
    draw = ImageDraw.Draw(img)
    text = await copywriting()
    title = await getTitle(text)
    text = text['content']
    font_size = 45
    color = '#F5F5F5'
    image_font_center = (140, 99)
    ttfront = ImageFont.truetype(fontPath['title'], font_size)
    font_length = ttfront.getsize(title)
    draw.text((image_font_center[0]-font_length[0]/2, image_font_center[1]-font_length[1]/2),
                title, fill=color,font=ttfront)
    # Text rendering
    font_size = 25
    color = '#323232'
    image_font_center = [140, 297]
    ttfront = ImageFont.truetype(fontPath['text'], font_size)
    result = await decrement(text)
    if not result[0]:
        return 
    textVertical = []
    for i in range(0, result[0]):
        font_height = len(result[i + 1]) * (font_size + 4)
        textVertical = await vertical(result[i + 1])
        x = int(image_font_center[0] + (result[0] - 2) * font_size / 2 + 
                (result[0] - 1) * 4 - i * (font_size + 4))
        y = int(image_font_center[1] - font_height / 2)
        draw.text((x, y), textVertical, fill = color, font = ttfront)
    # Save
    outPath = await exportFilePath(imgPath)
    img.save(outPath)
    return outPath

async def exportFilePath(originalFilePath):
    outPath = originalFilePath.replace('/img/', '/out/')
    await utils.checkFolder(outPath)
    return outPath

async def randomBasemap():
    p = './vortune/data/img'
    return p + '/' + random.choice(os.listdir(p))

async def copywriting():
    p = './vortune/data/fortune/copywriting.json'
    content = await utils.readJson(p)
    return random.choice(content['copywriting'])

async def getTitle(structure):
    p = './vortune/data/fortune/goodLuck.json'
    content = await utils.readJson(p)
    for i in content['types_of']:
        if i['good-luck'] == structure['good-luck']:
            return i['name']
    raise Exception('Configuration file error')

async def decrement(text):
    length = len(text)
    result = []
    cardinality = 9
    if length > 4 * cardinality:
        return [False]
    numberOfSlices = 1
    while length > cardinality:
        numberOfSlices += 1
        length -= cardinality
    result.append(numberOfSlices)
    # Optimize for two columns
    space = ' '
    length = len(text)
    if numberOfSlices == 2:
        if length % 2 == 0:
            # even
            fillIn = space * int(9 - length / 2)
            return [numberOfSlices, text[:int(length / 2)] + fillIn, fillIn + text[int(length / 2):]]
        else:
            # odd number
            fillIn = space * int(9 - (length + 1) / 2)
            return [numberOfSlices, text[:int((length + 1) / 2)] + fillIn,
                                    fillIn + space + text[int((length + 1) / 2):]]
    for i in range(0, numberOfSlices):
        if i == numberOfSlices - 1 or numberOfSlices == 1:
            result.append(text[i * cardinality:])
        else:
            result.append(text[i * cardinality:(i + 1) * cardinality])
    return result

async def vertical(str):
    list = []
    for s in str:
        list.append(s)
    return '\n'.join(list)
