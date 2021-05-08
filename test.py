# -*- coding: UTF-8 -*-    
# Author:yansh  
# FileName:test  
# DateTime:2021/5/7 17:16  
# SoftWare: PyCharm
import time
from datetime import datetime,timedelta
import pandas as pd


a = datetime.now()
time.sleep(1)
b = str(a)
print(type(b))

c = datetime.strptime(b, "%Y-%m-%d %H:%M:%S.%f")
print(type(c))
print(c)

df_MO = pd.read_excel(r'./data/CDR_IMS_MO_CALL_LEG_SIP_20210308151653.xlsx', sheet_name=1,
                usecols=["开始时间", "结束时间", "序号", 'MSISDN', 'IMSI','用户类型', '业务状态', '异常释放标识', '综合失败原因', '接入位置名称', '结束4G小区名称'])

# print(df_MO['开始时间'])

for i in range(len(df_MO)):
    d = datetime.strptime(df_MO.iloc[i]['结束时间'], "%Y-%m-%d %H:%M:%S.%f") - datetime.strptime(df_MO.iloc[i]['开始时间'], "%Y-%m-%d %H:%M:%S.%f")
    # print(d.total_seconds())
    if d.total_seconds() <= 2:
        # print(i)
        print(df_MO.iloc[i]["序号"])

def resoved_rule(self, index_callfail, index_offline):  # 规则表解析函数
    rule = pd.read_csv(self.filepath_rule, sep='#', header=None)
    callfail = rule.iloc[0, index_callfail]                 # 主被叫失败规则表
    callfail = callfail.split('&')                          # 主被叫失败列表
    callfail_status = callfail[0]                           # 主被叫业务状态
    callfail_reasons = callfail[1:]                         # 失败综合失败原因
    offline = rule.iloc[0, index_offline]                   # 主被叫掉线规则表
    offline = offline.split('&')                            # 主被叫掉线列表
    offline_flag = offline[0]                               # 主被叫释放标识
    offline_reasons = offline[1:]                           # 掉线综合失败原因
    # 返回业务状态、失败原因、释放标识、掉线原因筛选值
    return callfail_status, callfail_reasons, offline_flag, offline_reasons

