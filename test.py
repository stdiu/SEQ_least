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
                usecols=["开始时间", "结束时间", "序号", 'MSISDN', 'IMSI', '用户类型', '业务状态', '异常释放标识', '综合失败原因', '接入位置名称', '结束4G小区名称'])

a = df_MO[df_MO['序号']==10]['综合失败原因'].iloc[-1]
print(a)

# for i in range(len(df_MO)):
#     d = datetime.strptime(df_MO.iloc[i]['结束时间'], "%Y-%m-%d %H:%M:%S.%f") - datetime.strptime(df_MO.iloc[i]['开始时间'], "%Y-%m-%d %H:%M:%S.%f")
#     # print(d.total_seconds())
#     if d.total_seconds() <= 2:
#         # print(i)
#         # print(df_MO.iloc[i]["序号"])
#         print(df_MO.iloc['Q850(16 Normal Call Clearing)(--)']["综合失败原因"])
