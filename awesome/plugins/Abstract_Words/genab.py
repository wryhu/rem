import os
import sys

with open('ab_raw.py','r') as f:
    ab_raw=f.read()
pos=ab_raw.find('__main__')
while ab_raw[pos]!='\n':
    pos-=1
qian=ab_raw[:pos]
hou=ab_raw[pos:]
ins='\nemojiUtf8='
with open('EmojiUtf8','r') as f:
    ins+=repr(f.read())
ins+='\nasaPinYin='
with open('Asa_PinYin','r') as f:
    ins+=repr(f.read())
ins+='\n'
ins+='emojiStr='
with open('emoji/emoji.txt','r') as f:
    ins+=repr(f.read())
ins+='\n'
ins+='manDic='
with open('Mandarin.dat','r') as f:
    ins+=repr(f.read())
ins+='\n'
with open('ab.py','w+') as f:
    f.write(qian+ins+hou)

    
