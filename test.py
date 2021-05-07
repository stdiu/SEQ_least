# -*- coding: UTF-8 -*-    
# Author:yansh  
# FileName:test  
# DateTime:2021/5/7 17:16  
# SoftWare: PyCharm
import time
from datetime import datetime

a = datetime.now()
time.sleep(1)
b = datetime.now()
c = a - b

print(c)