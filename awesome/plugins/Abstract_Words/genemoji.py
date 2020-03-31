from ab import str2abs,init_data,get_emojiList
import os
import sys
import cv2
def deal_emoj(mode=1):
    emojiList=get_emojiList()
    if not os.path.exists('emoji'):
        raise Exception('no emoji in dir')
    if not os.path.exists('emoji/emoji.txt'):
        tmp=[i[1] for i in emojiList]
        with open('emoji/emoji.txt','w+') as f:
            f.write('\n'.join(tmp))
    with open('emoji/emoji.txt','r') as f:
        emojiBuffer=f.read().replace(' ','')
    dealList=[i.split(',') for i in emojiBuffer.split('\n')]
    i=0
    #mode
    #1 is input by order;0 is input the uncheck emoji;
    while True:
        if mode==0:
            while i < len(dealList) and (not len(dealList[i])==1):
                i+=1
            if i==len(dealList):
                print('done with 0 mode')
                break
            cv2.imshow('test',cv2.imread('emoji/'+dealList[i][0]))
            cv2.waitKey(100)
            print('input the %s'%dealList[i][0])
            inp=input().replace(' ','').replace('\n','').replace('\t','').lower()
            if inp=='':
                break
            if not inp in dealList[i]:
                dealList[i].append(inp)
            i+=1
        elif mode==1:
            if i==len(dealList):
                print('done with 1 mode')
                break
            cv2.imshow('test',cv2.imread('emoji/'+dealList[i][0]))
            cv2.waitKey(100)
            print('input the %s'%dealList[i][0])
            print(dealList[i])
            inp=input().replace(' ','').replace('\n','').replace('\t','').lower()
            if inp=='':
                i+=1
                continue
            elif inp[0]==':':
                #control cmd
                inp=inp[1:]
                isBreak=False
                for k in range(len(inp)):
                    if inp[k]=='q':
                        print('save and quit the program')
                        isBreak=True
                    elif inp[k]=='w':
                        print('write the file')
                        with open('emoji/emoji.txt','w+') as f:
                            f.write('\n'.join([','.join(i) for i in dealList]))
                    elif inp[k]=='p':
                        print('goto previous')
                        i-=1
                    elif inp[k]=='j':
                        print('jump 10')
                        i+=10
                if isBreak:
                    break
            else:
                if not inp in dealList[i]:
                    if dealList[i][-1]=='-':
                        dealList[i].pop()
                    dealList[i].append(inp)
        else:
            raise Exception('known mode')
    with open('emoji/emoji.txt','w+') as f:
        f.write('\n'.join([','.join(i) for i in dealList]))

if __name__=='__main__':
    init_data()
    deal_emoj()
