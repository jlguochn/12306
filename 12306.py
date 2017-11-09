# encoding:utf-8
import requests
import json
import time
import datetime
import pickle
import sys
import re
from sms import send

requests.packages.urllib3.disable_warnings()

#读入车站字典
with open('dict_s.txt','rb') as file2:
    dict_s = pickle.load(file2)

#座位字典
dict_seat = {'特等座':'32','一等座':'31','二等座':'30','硬座':'29','硬卧':'28','无座':'26','软卧':'23'}

#正则表达式
date_re = '((((19|20)\d{2})-(0?(1|[3-9])|1[012])-(0?[1-9]|[12]\d|30))|(((19|20)\d{2})-(0?[13578]|1[02])-31)|(((19|20)\d{2})-0?2-(0?[1-9]|1\d|2[0-8]))|((((19|20)([13579][26]|[2468][048]|0[48]))|(2000))-0?2-29))$'
phone_re = '0?(13|14|15|18)[0-9]{9}'
refresh_re = '^[1-9]\d*|0$'

#检查输入日期是否大于当前日期
def check_date(date_input,date_now_):
    if date_input<date_now_:
        return False
    return True

#get车次信息列表
def getlist():
    url = 'https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date=%s&leftTicketDTO.from_station=%s&leftTicketDTO.to_station=%s&purpose_codes=ADULT' % (
    date_s, from_s, to_s)#请求URL
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}#http请求头
    html = requests.get(url, verify=False, headers=headers)#发起请求
    dict_html = json.loads(html.text)#将非结构化数据结构化
    return dict_html['data']['result']

#当前日期
date_now = datetime.date.today()
#输入车次信息
from_c = input("请输入出发站:(如:桂林) ")
while not from_c in dict_s:
    from_c = input("出发站不正确，请校验后输入:(如:桂林) ")

to = input("请输入到达站:(如:南宁) ")
while not to in dict_s:
    to = input("到达站不正确，请校验后输入:(如:南宁) ")

date_s = input("请输入乘车日期:(如:%s) "%(date_now.strftime("%Y-%m-%d")))
while True:
    if re.match(date_re, date_s):
        date_s_t = datetime.datetime.strptime(date_s, '%Y-%m-%d').date()  # 将输入日期的str转为datetime类型
        if check_date(date_s_t,date_now):
            break
    date_s = input("日期不正确，请校验后输入:(如:%s) " % (date_now.strftime("%Y-%m-%d")))


print('%s %s-%s'%(date_s,from_c,to))
from_s = dict_s[from_c]#出发站
to_s = dict_s[to]#到达站
list_c = getlist()#车次列表
list_n = []
if not list_c:
    print('已没有车次')
    sys.exit(0)
for n in list_c:
    tr = n.split('|')
    list_n.append(tr[3])#将车次号加入列表
    print(tr[3],tr[8],'-',tr[9])#输出车次号，出发时间，到达时间

train_num = input("请输入您要监测的列车号，若不输入，监测全天列车(注意大小写):")
while not train_num in list_n:
    if train_num == '':
        break
    train_num = input("列车号不正确，请校验后输入，若不输入，监测全天列车(注意大小写):")


phone_num = input("请输入手机号码(有票时短信提醒您:) ")
while not re.match(phone_re,phone_num):
    phone_num = input("手机号码不正确，请校验后输入: ")

seat = input("请输入座位类型:(如:一等座/二等座/硬卧/软卧/硬座) ")
while not seat in dict_seat:
    seat = input("座位类型不正确，请校验后输入:(如:一等座/二等座/硬卧/软卧/硬座) ")

refresh_time = input("请输入刷新间隔(建议10，若暂时无票，每10秒刷新一次)")
while not re.match(refresh_re,refresh_time):
    refresh_time = input("刷新间隔不正确，请输入非负整数(如:30)")







# 车次=3
# 出发时间=8
# 到达时间=9
# 历时=10
# 出发日期=13
# 软卧=23
# 无座=26
# 硬卧=28
# 硬座=29
# 二等座=30
# 一等座=31
# 特等座=32


#输出list确定各类座位在列表当中的序号
# number = 0
# for i in getlist():
#     for n in i.split('|'):
#         print('[%d] %s' %(number,n))
#         number+=1
#     break

t = 0#计数，用来跳出循环
while True:
    date_now = datetime.date.today()
    list_c2 = getlist()
    if not list_c2:
        print('已没有车次!')
        break
    for i in list_c2:
        train = i.split('|')
        train_number = train[3]#车次号
        date = train[13]#日期
        time_t = train[8]#发车时间
        if train_num != '' and train_num != train_number:#判断是否为监测的列车号
            continue
        if train[int(dict_seat[seat])] and train[int(dict_seat[seat])] != '无':#判断是否有座位
            print(train_number, '有票,短信通知中....')
            t = 1
            a = send(from_c,to,train_number,date_s+' '+time_t,phone_num)#发送短信，send返回值为bytes型
            if eval(a.decode())['Message'] == 'OK':#先将返回值转为str 在由str转为dict 判断是否发送成功
                print('短信已发出')
            else:
                print('短信发送失败，请稍后重试，或联系开发人员处理')
            break
        print(train_number, '无票')
    if t or not check_date(date_s_t,date_now):#若发送短信成功或当前日期超过监测日期则退出
        break
    print('暂时无票,%s秒后刷新'%(refresh_time))
    time.sleep(int(refresh_time))#刷新间隔
input("程序结束，请按回车退出")