import sys
from random import random
import os

isDebug=False
hasInit=False
useMan=True

def hex2chr(s):
    ret=0
    for i in s:
        ret=(ret<<4)+int(i,16)
    return chr(ret)

def hex2utf8(s):
    s=s[1:].split('%')
    ret=b''
    for i in s:
        ret+=chr(16*(int(i[0],16))+int(i[1],16)).encode('latin1')
    return ret.decode('utf-8')

def init_data():
    #load the hanzi list
    global dataDict
    global isDebug
    global emojiUtf8
    global emojiStr
    global asaPinYin
    dataList=[]
    if not useMan:
        dataBuffer=asaPinYin
        dataListTmp=dataBuffer.replace('\r','').split('\n')
        while True:
            try:
                dataListTmp.remove('')
            except ValueError:
                break
        for i in dataListTmp:
        #i=i.decode('utf-8')
            l=len(i)-1
            while ord('a')<=ord(i[l]) and ord(i[l])<=ord('z'):
                l=l-1
            if l < 0:
                if isDebug:
                    print(i)
                raise Exception('str are all alpha')
            elif l == len(i)-1:
                if isDebug:
                    print(i)
                raise Exception('str has no alpha')
            dataList.append([i[l+1:],i[:l+1]])
    else:
        dataBuffer=manDic
        dataBuffer=[i.split('\t') for i in dataBuffer.split('\n')]
        while True:
            try:
                dataBuffer.remove([''])
            except ValueError:
                break
        dataList=[[i[1].split(' ')[0][:-1].lower(),hex2chr(i[0])] for i in dataBuffer]
    dataDict={}
    for i in dataList:
        if not i[1] in dataDict:
            dataDict[i[1]]=i[0]
        else:
            if len(dataDict[i[1]])<len(i[0]):
                dataDict[i[1]]=i[0]
    #load the emoji list
    global emojiDict
    global emojiList
    dataBuffer=emojiUtf8
    emojiList=[[hex2utf8(i.split(',')[0]),i.split(',')[1]] for i in dataBuffer.split('\n')]
    emojiDict={i[1]:i[0] for i in emojiList}
    
    #loadd the absinfo
    global absDict
    absBuffer=emojiStr
    absBuffer=[i.split(',') for i in absBuffer.split('\n')]
    absDict={}
    for i in absBuffer:
        for j in i[1:]:
            if j=='-':
                continue
            repNum=1
            if '^' in j:
                repNum=int(j[j.find('^')+1:])
                j=j[:j.find('^')]
            if j in absDict:
                absDict[j].append({i[0]:repNum})
            else:
                absDict[j]=[{i[0]:repNum}]
                
def is_space(s):
    if s==' ' or s=='\t' or s=='\r' or s=='\f' or s=='\n':
        return True
    else:
        return False
def is_alpha(s):
    if (s>='a' and s<='z') or (s>='A' and s<='Z'):
        return True
    else:
        return False
    
def str2abs(s):
    global dataDict
    global emojiDict
    global absDict
    global hasInit

    if not hasInit:
        hasInit=True
        init_data()
    
    #split s to word
    wordList=[]
    i=0
    while True:
        if i == len(s):
            break
        if isDebug:
            print(s[i])
        if ord(s[i])>255:
            #not ascii
            if s[i] in dataDict:
                tmp=[]
                tmp.append(s[i])
                tmp.append(dataDict[s[i]])
                wordList.append(tmp)
            else:
                #other language
                wordList.append(s[i])
            
        elif is_alpha(s[i]):
            #english word
            j=i
            while j<len(s) and is_alpha(s[j]):
                j+=1
            wordList.append(s[i:j])
            i=j-1
        else:
            wordList.append(s[i])
        i+=1
    i=0
    absList=[]
    if isDebug:
        print('wordList: ')
        print(wordList)
    while True:
        if i==len(wordList):
            break
        if type(wordList[i])==list:
            #chiness
            conNum=1
            j=i+1
            conPyList=[wordList[i][1]]
            while j<len(wordList) and type(wordList[j])==list:
                conPyList.append(wordList[j][1])
                j+=1
                conNum+=1
            if isDebug:
                print('conPyList:')
                print(conPyList)
            while True:
                if conNum<=0:
                    break
                tmp=''.join(conPyList[:conNum])
                if tmp in absDict:
                    break
                else:
                    conNum-=1
            if not conNum == 0:
                absList.append(absDict[tmp])
                i+=conNum-1
            else:
                absList.append(wordList[i][0])
        else:
            #else
            if wordList[i] in absDict:
                absList.append(absDict[wordList[i]])
            else:
                absList.append(wordList[i])
        i+=1
    #get the final result with a random way
    ret=''
    for i in absList:
        if type(i)==list:
            repDict=i[int(random()*10000)%len(i)].copy().popitem()
            ret+=emojiDict[repDict[0]]*repDict[1]
        else:
            ret+=i
    return ret

def get_emojiList():
    global emojiList
    return emojiList
def get_emojiDict():
    global emojiDict
    return emojiDict

def main():
    global dataDict
    global emojiDict
    global emojiDict
    #deal_emoj()
    print(str2abs('那你是真滴牛皮，弟弟'))

if __name__ == '__main__':
    isDebug=True
    main()
    print(temp)
