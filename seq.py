# coding=utf-8
import sys
import os
import re
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QApplication, QFileDialog, QTabWidget, QMessageBox
from PyQt5.QtGui import QIcon, QColor
import pandas as pd
import numpy as np
from pathlib import Path
import time, threading
from datetime import datetime,timedelta
from openpyxl import load_workbook
from rule_analyzing import RuleAnalyzing

class SeqStatistics(QWidget):
    def __init__(self):
        super().__init__()
        self.initui()

#******************************************   初始化函数   **************************************************#
    def initui(self):
        #*************************************   加载UI    ***************************************#
        self.ui = uic.loadUi(r'./ui/SEQ.ui')
        self.ui.setWindowTitle('SEQ话单统计 v1.2')
        self.ui.setWindowIcon(QIcon('./imag/中国电信 .png'))
        # self.ui.setStyleSheet("QWidget{background-color:lightcyan}")   # 背景颜色
        self.ui.progressBar.setRange(0, 5)            # 初始化进度条
        self.ui.progressBar.hide()

        # 初始化显示栏
        self.ui.lineEdit_MO.setReadOnly(True)
        self.ui.lineEdit_MO.setPlaceholderText('请选择主叫话单清单')
        self.ui.lineEdit_MT.setReadOnly(True)
        self.ui.lineEdit_MT.setPlaceholderText('请选择被叫话单清单')
        self.ui.lineEdit_rule.setReadOnly(True)
        self.ui.lineEdit_rule.setPlaceholderText('请选择筛选规则')
        self.ui.lineEdit_dict.setReadOnly(True)
        self.ui.lineEdit_dict.setPlaceholderText('请选择基站台账')

        # 初始化按钮及关联事件函数
        self.ui.pushButton_MO.clicked.connect(self.open_MO)
        self.ui.pushButton_MT.clicked.connect(self.open_MT)
        self.ui.pushButton_rule.clicked.connect(self.open_rule)
        self.ui.pushButton_dict.clicked.connect(self.open_dict)
        self.ui.pushButton_calculate.clicked.connect(self.calculate)
        self.ui.pushButton_analysis.clicked.connect(self.analysis)
        self.ui.pushButton_abandon.clicked.connect(self.abandon)
        self.ui.pushButton_save.clicked.connect(self.save_result)
        self.ui.textEdit.setText('<统计开始开始>')

        # 加载Qtabwidget界面
        str = "QTabBar::tab:selected{color:red;background-color:rbg(255,200,255);} "
        self.ui.tabWidget.setStyleSheet(str)
        # self.ui.tabWidget.setTabsClosable(True)
        self.ui.tabWidget.currentChanged.connect(self.tab_changed)

        # *************************************   初始化全局变量    ***************************************#
        self.filepath_MO = r'./data/CDR_IMS_MO_CALL_LEG_SIP_20210308151653.xlsx'
        self.ui.lineEdit_MO.setText(self.filepath_MO)
        self.filepath_MT = r'./data/CDR_IMS_MT_CALL_LEG_SIP_20210308152205.xlsx'
        self.ui.lineEdit_MT.setText(self.filepath_MT)
        self.filepath_rule = r'./data/rule.txt'
        self.ui.lineEdit_rule.setText(self.filepath_rule)
        self.filepath_dict = r'./data/dict.xlsx'
        self.ui.lineEdit_dict.setText(self.filepath_dict)

        # *******************************   全局变量用来保存结果   *************************************#
        self.df_result = pd.DataFrame()
        self.call_statistics = pd.DataFrame(
            columns=["VIP用户话单", "话单总数", "volte话单数", "EPSFB话单数", "问题话单数", "volte问题话单数", "EPSFB问题话单数"]
        )

# ******************************************   按钮函数   **************************************************#
    def open_MO(self):      # 打开主叫清单
        self.filepath_MO, _ = QFileDialog.getOpenFileName(
            self.ui,
            '选择主叫话单文件',
            r'./'
            '*.xlsx'
        )
        self.ui.lineEdit_MO.setText(self.filepath_MO)

    def open_MT(self):      # 打开被叫清单
        self.filepath_MT, _ = QFileDialog.getOpenFileName(
            self.ui,
            "选择被叫清单",
            r"./",
            '*.xlsx'
        )
        self.ui.lineEdit_MT.setText(self.filepath_MT)

    def open_rule(self):        # 打开规则表
        self.filepath_rule, _ = QFileDialog.getOpenFileName(
            self.ui,
            '选择筛选规则',
            r'./',
            '*.txt'
        )
        self.ui.lineEdit_rule.setText(self.filepath_rule)

    def open_dict(self):      # 打开台账
        self.filepath_dict, _ = QFileDialog.getOpenFileName(
            self.ui,
            '选择台账',
            r'./',
            '*.xlsx'
        )
        self.ui.lineEdit_dict.setText(self.filepath_dict)

    def calculate(self):        # 统计函数
        # self.progressBardisp()      # 调用进度条显示函数
        self.ui.progressBar.show()
        self.ui.progressBar.setValue(1)
        # 读取字典
        self.dict_NR = pd.read_excel(self.filepath_dict, sheet_name='NR小区', usecols=['ENBID_CELLID', 'Cell Name'])
        self.dict_LTE = pd.read_excel(self.filepath_dict, sheet_name='FDD小区', usecols=['eNodeBID_CELL_ID', 'CELL_NAME'])
        #************  判断话单原始数据  **********#
        if self.filepath_MO != '':
            # 读取主叫话单dataframe
            try:
                df_MO = pd.read_excel(
                self.filepath_MO,
                sheet_name = 'CDR_IMS_MO_CALL_LEG_SIP',
                usecols = ['MSISDN', 'IMSI','用户类型', '业务状态', '异常释放标识', '综合失败原因', '接入位置名称', '结束4G小区名称']
                )
            except:
                QMessageBox.critical(self.ui, '错误', '请选择正确的话单文件！')
            self.calculate_MO(df_MO, 0, 2)
            self.ui.progressBar.setValue(3)
        if self.filepath_MT != '':
            # 读取被叫话单dataframe
            try:
                df_MT = pd.read_excel(
                    self.filepath_MT,
                    sheet_name = 'CDR_IMS_MT_CALL_LEG_SIP',
                    usecols=['MSISDN', 'IMSI', '用户类型', '业务状态','异常释放标识', '综合失败原因', '接入位置名称', '结束4G小区名称']
                )
            except:
                QMessageBox.critical(self.ui, '错误', '请选择正确的话单文件！')
            self.calculate_MT(df_MT, 1, 3)
            self.ui.progressBar.setValue(5)
        if self.filepath_MO == '' and self.filepath_MT == '':
            QMessageBox.critical(self.ui, '错误', '请选择话单文件！')

        time.sleep(3)
        self.ui.progressBar.hide()

    def tab_changed(self):          # tabwidget切换事件函数
        if self.ui.tabWidget.currentIndex() == 0:
            print('这是第一个子表')
        elif self.ui.tabWidget.currentIndex() == 1:
            print('这是第二个子表')
        else:
            print('子表切换错误')

    def calculate_MO(self, df, callfail_index, offline_index):         # 主叫统计函数
        # 话单数统计
        sum_calling = df.shape[0]                   # 行
        sum_epsfb = df['用户类型'].value_counts()    # 统计各话单类型数量
        sum_epsfb = sum_epsfb['Vo5G']               # Vo5G话单数量
        sum_volte = sum_calling - sum_epsfb         # Volte话单数量

        # 返回筛选规则
        callfail_status, callfail_reasons, offline_flag, offline_reasons = self.resoved_rule(callfail_index, offline_index)
        # ****************************************  主叫统计  *********************************************** #
        # 主叫失败统计
        df_calling_fail = df[(df['业务状态']==callfail_status) & (df['综合失败原因'].isin(callfail_reasons))]
        self.df_calling_fail = df_calling_fail   # 将主叫失败统计为全局变量
        # 统计主叫失败次数
        num_calling_fail = len(df_calling_fail)
        # 统计主叫失败类型次数
        num_use_type = df_calling_fail['用户类型'].value_counts()
        try:
            num_epsfb = num_use_type['Vo5G']
        except:
            num_epsfb = 0
        num_Volte = num_calling_fail - num_epsfb
        # 主叫失败原因统计
        reason_calling_fail = df_calling_fail['综合失败原因'].value_counts().reset_index()
        reason_calling_fail.columns = ['综合失败原因', '统计次数']
        reason_calling_fail['初步归属类型'] = '主叫打不通'
        # print(self.reason_calling_fail)
        # 问题小区统计
        fail_cell_equal = df_calling_fail[df_calling_fail['接入位置名称'] == df_calling_fail['结束4G小区名称']]
        fail_cell_unequal = df_calling_fail[df_calling_fail['接入位置名称'] != df_calling_fail['结束4G小区名称']]
        # 调用问题小区统计函数
        self.cell_equal(fail_cell_equal, '主叫打不通')
        self.cell_equal(fail_cell_unequal, '主叫打不通') # 不相同小区需要分开统计
        self.cell_unqual(fail_cell_unequal, '主叫打不通')

        # 主叫掉线统计
        df_calling_offline = df[(df['异常释放标识'] == offline_flag) & (df['综合失败原因'].isin(offline_reasons))]
        self.df_calling_offline = df_calling_fail  # 将主叫掉线统计全局化
        num_calling_offline = len(df_calling_offline)
        num_use_type_1 = df_calling_offline['用户类型'].value_counts()
        try:
            num_epsfb_1 = num_use_type_1['Vo5G']
        except:
            num_epsfb_1 = 0
        num_Volte_1 = num_calling_offline - num_epsfb_1
        # 主叫掉线原因统计
        reason_calling_offline = df_calling_offline['综合失败原因'].value_counts().reset_index()
        reason_calling_offline.columns = ['综合失败原因', '统计次数']
        reason_calling_offline['初步归属类型'] = '主叫掉线'
        # 问题小区统计
        offline_cell_equal = df_calling_offline[df_calling_offline['接入位置名称'] == df_calling_offline['结束4G小区名称']]
        offline_cell_unequal = df_calling_offline[df_calling_offline['接入位置名称'] != df_calling_offline['结束4G小区名称']]
        # 调用问题小区统计函数
        self.cell_equal(offline_cell_equal, '主叫掉线')
        self.cell_equal(offline_cell_unequal, '主叫掉线')  # 不相同小区需要分开统计
        self.cell_unqual(offline_cell_unequal, '主叫掉线')

        # 统计结果
        self.reason_statistics_calling = pd.concat([reason_calling_fail, reason_calling_offline])
        print('主叫原因统计为：')
        print(self.reason_statistics_calling)
        calling = {
            "VIP用户话单": '主叫',
            "话单总数": sum_calling,
            "volte话单数": sum_volte,
            "EPSFB话单数": sum_epsfb,
            "问题话单数": (num_calling_fail + num_calling_offline),
            "volte问题话单数": (num_Volte + num_Volte_1),
            "EPSFB问题话单数": (num_epsfb + num_epsfb_1)
        }
        self.call_statistics = self.call_statistics.append(calling, ignore_index = True)
        print('主叫统计完毕')

    def calculate_MT(self, df, callfail_index, offline_index):         # 被叫统计函数
        # 话单数统计
        sum_called = df.shape[0]
        sum_epsfb = df['用户类型'].value_counts()
        sum_epsfb = sum_epsfb['Vo5G']
        sum_volte = sum_called - sum_epsfb

        # 返回筛选规则
        callfail_status, callfail_reasons, offline_flag, offline_reasons = self.resoved_rule(callfail_index, offline_index)
        # ****************************************  主叫统计  *********************************************** #
        # 被叫失败统计
        df_called_fail = df[(df['业务状态']==callfail_status) & (df['综合失败原因'].isin(callfail_reasons))]
        self.df_called_fail = df_called_fail
        # 统计被叫失败次数
        num_called_fail = len(df_called_fail)
        # 统计主叫失败类型次数
        num_use_type = df_called_fail['用户类型'].value_counts()
        try:
            num_epsfb = num_use_type['Vo5G']
        except:
            num_epsfb = 0
        num_Volte = num_called_fail - num_epsfb
        # 被叫失败原因统计
        reason_called_fail = df_called_fail['综合失败原因'].value_counts().reset_index()
        reason_called_fail.columns = ['综合失败原因', '统计次数']
        reason_called_fail['初步归属类型'] = '被叫打不通'
        # 问题小区统计
        fail_cell_equal = df_called_fail[df_called_fail['接入位置名称'] == df_called_fail['结束4G小区名称']]
        fail_cell_unequal = df_called_fail[df_called_fail['接入位置名称'] != df_called_fail['结束4G小区名称']]
        # 调用问题小区统计函数
        self.cell_equal(fail_cell_equal, '被叫打不通')
        self.cell_equal(fail_cell_unequal, '被叫打不通') # 不相同小区需要分开统计
        self.cell_unqual(fail_cell_unequal, '被叫打不通')

        # 被叫掉线统计
        df_called_offline = df[(df['异常释放标识'] == offline_flag) & (df['综合失败原因'].isin(offline_reasons))]
        self.df_called_offline = df_called_offline
        num_called_offline = len(df_called_offline)
        num_use_type_1 = df_called_offline['用户类型'].value_counts()
        try:
            num_epsfb_1 = num_use_type_1['Vo5G']
        except:
            num_epsfb_1 = 0
        num_Volte_1 = num_called_offline - num_epsfb_1
        # 被叫掉线原因统计
        reason_called_offline = df_called_offline['综合失败原因'].value_counts().reset_index()
        reason_called_offline.columns = ['综合失败原因', '统计次数']
        reason_called_offline['初步归属类型'] = '被叫掉线'
        # 问题小区统计
        offline_cell_equal = df_called_offline[df_called_offline['接入位置名称'] == df_called_offline['结束4G小区名称']]
        offline_cell_unequal = df_called_offline[df_called_offline['接入位置名称'] != df_called_offline['结束4G小区名称']]
        # 调用问题小区统计函数
        self.cell_equal(offline_cell_equal, '被叫掉线')
        self.cell_equal(offline_cell_unequal, '被叫掉线')  # 不相同小区需要分开统计
        self.cell_unqual(offline_cell_unequal, '被叫掉线')

        # 统计结果
        self.reason_statistics_called = pd.concat([reason_called_fail, reason_called_offline])
        print('被叫统计为：')
        print(self.reason_statistics_called)
        called = {
            "VIP用户话单": '被叫',
            "话单总数": sum_called,
            "volte话单数": sum_volte,
            "EPSFB话单数": sum_epsfb,
            "问题话单数": (num_called_fail + num_called_offline),
            "volte问题话单数": (num_Volte + num_Volte_1),
            "EPSFB问题话单数": (num_epsfb + num_epsfb_1)
        }
        self.call_statistics = self.call_statistics.append(called, ignore_index = True)
        print('被叫统计完毕')

    # ****************************************  掉话回拨  *********************************************** #
    def analysis(self):
        # self.progressBardisp()      # 调用进度条显示函数
        self.ui.progressBar.show()
        self.ui.progressBar.setValue(1)

        # 实例化规则表
        self.rule = RuleAnalyzing('筛选原则v3.xlsx')

        # ************  判断话单原始数据  **********#
        write = pd.ExcelWriter(rf'./data/{datetime.now().strftime("%Y-%m-%d")}筛选表.xlsx')  # 建立筛选规则表

        if self.filepath_MO != '':
            # 读取主叫话单dataframe
            try:
                df_MO = pd.read_excel(
                    self.filepath_MO,
                    sheet_name='CDR_IMS_MO_CALL_LEG_SIP',
                    usecols=['开始时间', '结束时间', '序号','MSISDN', 'IMSI', '用户类型', '业务状态',
                               '异常释放标识', '综合失败原因', '接入位置名称', '结束4G小区名称']
                )
                mo_rule = self.analysis_timestamp(df_MO, self.rule.rule_mo)  # 调用时间戳函数计算时间
                mo_rule= self.analysis_userhabits(df_MO, mo_rule)  # 调用用户分析函数分析回拨行为
                mo_rule.to_excel(write, '主叫筛选规则', index=False)
            except:
                QMessageBox.critical(self.ui, '错误', '请选择正确的主叫话单文件！')

        if self.filepath_MT != '':
            # 读取被叫话单dataframe
            try:
                df_MT = pd.read_excel(
                    self.filepath_MT,
                    sheet_name='CDR_IMS_MT_CALL_LEG_SIP',
                    usecols=['开始时间', '结束时间', '序号', 'MSISDN', 'IMSI', '用户类型', '业务状态', '异常释放标识', '综合失败原因', '接入位置名称', '结束4G小区名称']
                )
                mt_rule = self.analysis_timestamp(df_MT, self.rule.rule_mt)  # 调用时间戳函数计算时间
                mt_rule = self.analysis_userhabits(df_MT, mt_rule)  # 调用用户分析函数分析回拨行为
                mt_rule.to_excel(write, '被叫筛选规则', index=False)
            except:
                QMessageBox.critical(self.ui, '错误', '请选择正确的被叫话单文件！')
        if self.filepath_MO == '' and self.filepath_MT == '':
            QMessageBox.critical(self.ui, '错误', '请选择话单文件！')

        write.save()
        self.analysis_statistics(df_MO, mo_rule, "主叫")

        # 调用分析函数   # 原因值为 mo_rule、mt_rule  主叫表为 df_MO 、df_MT

    # 分析原因函数
    def analysis_statistics(self, df, rule, identifi):
        # identifi = 主被叫

        # 总话单数统计
        sum_call = df.shape[0]          # 行数
        sum_call_tpye = df['用户类型'].value_counts()   # 统计话单类型及数量
        sum_call_epsfb = sum_call_tpye['Vo5G']   # Vo5G话单数量
        sum_call_volte = sum_call - sum_call_epsfb  # volte话单数量

        # 主被叫问题话单统计
        rule_check = rule[rule['是否保留'] == '是']
        print(rule_check)
        df_fail = df[df['业务状态'] == '失败' & df['综合失败原因'].isin(rule_check)]  # *叫失败
        df_offline = df[df['异常释放标识'] == '是' & df['综合失败原因'].isin(rule_check)]  # *叫掉线

        print(identifi)
        print('主叫失败名单')
        print(df_fail0)
        print('主叫掉线名单')
        print(df_offline)













    # 用户回拨行为分析
    def analysis_userhabits(self, df, rule):
        print('进入用户行为分析函数')
        for i in range(len(df)-1):
            TD_flag = False
            TU_flag = False
            if df.iloc[i]['业务状态'] == '失败' or df.iloc[i]['异常释放标识'] == '是':
                if df.iloc[i]['IMSI'] == df.iloc[i-1]['IMSI']:
                    TD = datetime.strptime(df.iloc[i]['开始时间'], "%Y-%m-%d %H:%M:%S.%f") - datetime.strptime(
                        df.iloc[i-1]['结束时间'], "%Y-%m-%d %H:%M:%S.%f")
                    if TD.total_seconds() <= 120 :
                        if df.iloc[i-1]['业务状态'] == '成功' and df.iloc[i-1]['异常释放标识'] == '否':
                            TD_flag = True
                        else:
                            TD_flag = False
                    else:
                        TD_flag = False
                if df.iloc[i]['IMSI'] == df.iloc[i + 1]['IMSI']:
                    TU = datetime.strptime(df.iloc[i+1]['开始时间'], "%Y-%m-%d %H:%M:%S.%f") - datetime.strptime(
                        df.iloc[i]['结束时间'], "%Y-%m-%d %H:%M:%S.%f")
                    if TU.total_seconds() <= 120:
                        if df.iloc[i - 1]['业务状态'] == '成功' and df.iloc[i - 1]['异常释放标识'] == '否':
                            TU_flag = True
                        else:
                            TU_flag = False
                    else:
                        TU_flag = False

            if TD_flag == True and TU_flag == True:
                if df.iloc[i]['综合失败原因'] in rule['综合失败原因']:
                    pass
                else:
                    rule = rule.append([{'综合失败原因': df.iloc[i]["综合失败原因"], '是否保留': '是',
                                         '原因': datetime.now().strftime("%Y-%m-%d") + '新增' + ",用户通话前后2分钟内正常"}],
                                       ignore_index=True)
        return rule

    # 时间戳函数
    def analysis_timestamp(self, df, rule):
        print('进入时间戳计算')
        for i in range(len(df)):
            d = datetime.strptime(df.iloc[i]['结束时间'], "%Y-%m-%d %H:%M:%S.%f") - datetime.strptime(
                df.iloc[i]['开始时间'], "%Y-%m-%d %H:%M:%S.%f")
            if d.total_seconds() <= 2:
                print(df.iloc[i]['序号'])
                if str(df.iloc[i]["综合失败原因"]) in str(rule['综合失败原因']):       # 如果在筛选表，判断是否保留
                    pass  # 只要在表里，都不需要保留直接跳过该原因值
                    # b=rule[rule['综合失败原因']==df.iloc[i]["综合失败原因"]]['是否保留']
                    # # print(b.iloc[-1])
                    # if str(b.iloc[-1]) != '否':
                    #     print('在表里')
                    #     rule = rule.append([{'综合失败原因': df.iloc[i]["综合失败原因"], '是否保留': '是', '原因': datetime.now().strftime("%Y-%M-%d ")+'新增'+",2秒内断开"}],
                    #                        ignore_index=True)
                    # else:
                    #     pass
                else:       # 如果不在筛选表，直接保留
                    print('不在表里')
                    rule = rule.append([{'综合失败原因':df.iloc[i]["综合失败原因"], '是否保留':'是', '原因':datetime.now().strftime("%Y-%m-%d")+'新增'+",通话2秒内断开"}], ignore_index=True)

        # 更新筛选表
        return rule

    def abandon(self):          # 进程中止函数
        app = QApplication.instance()
        app.quit()

    def save_result(self):      # 数据保存函数
        filepath_save,_ = QFileDialog.getSaveFileName(
            self.ui,
            '保存结果为',
            r'./data',
            '*.xlsx'
        )
        try:
            reason_statistics = pd.concat([self.reason_statistics_calling, self.reason_statistics_called])
        except:
            pass
        write = pd.ExcelWriter(f'{filepath_save}')
        self.call_statistics.to_excel(write, index=False, sheet_name='话单统计')
        reason_statistics.to_excel(write, index=False, sheet_name='失败原因')
        self.df_result.to_excel(write, index=False, sheet_name='问题小区统计')
        self.df_calling_fail.to_excel(write, index=False, sheet_name='主叫失败清单')
        self.df_calling_offline.to_excel(write, index=False, sheet_name ='主叫掉线清单')
        self.df_called_fail.to_excel(write, index=False, sheet_name='被叫失败清单')
        self.df_called_offline.to_excel(write, index=False, sheet_name='被叫掉线清单')
        write.close()
        print('数据已经保存')

# ******************************************   功能函数   **************************************************#
    def progressBardisp(self):          # 进度条显示函数
        self.ui.progressBar.show()
        self.ui.progressBar.setValue(1)
        time.sleep(3)
        self.ui.progressBar.setValue(3)
        time.sleep(3)
        self.ui.progressBar.setValue(5)

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

    def cell_equal(self, df, type_reason):       # 小区相同统计函数
        for i in range(0 , len(df)):
            if re.match(r'46011.+', df.iloc[i]['接入位置名称']):  # 正则表达判断是否为enodBID
                ID = str(df.iloc[i]['接入位置名称'])[:11] # 得到ID = plmn+gnodeBID+cellID
                gnodBID = ID[-7:-2]
                cellID = ID[-2:]
                # 十六进制转换为十进制
                gnodBID = int(gnodBID, 16)
                cellID = int(cellID, 16)
                gnodB_cell_ID = str(gnodBID) + '_' + str(cellID)
                # 根据用户类型查找基站
                if df.iloc[i]['用户类型'] == 'V05G':
                    if gnodB_cell_ID in list(self.dict_NR['ENBID_CELLID']):
                        print('查找5G台账')
                        find_data = self.dict_NR.loc[self.dict_NR['ENBID_CELLID']==gnodB_cell_ID, 'Cell Name']
                        self.df_result = self.df_result.append([{'cell小区': find_data.values[0],
                                                                 '原cell小区': df.iloc[i]['接入位置名称'],
                                                                 '用户类型': df.iloc[i]['用户类型'],
                                                                 '综合失败原因': df.iloc[i]['综合失败原因'],
                                                                 '初步原因分类': type_reason,
                                                                 }], ignore_index=False)
                else:
                    if gnodB_cell_ID in list(self.dict_LTE['eNodeBID_CELL_ID']):
                        print('查找4G台账')
                        find_data = self.dict_LTE.loc[self.dict_LTE['eNodeBID_CELL_ID']==gnodB_cell_ID, 'CELL_NAME']
                        self.df_result = self.df_result.append([{'cell小区': find_data.values[0],
                                                                 '原cell小区': df.iloc[i]['接入位置名称'],
                                                                 '用户类型': df.iloc[i]['用户类型'],
                                                                 '综合失败原因': df.iloc[i]['综合失败原因'],
                                                                 '初步原因分类': type_reason,
                                                                 }], ignore_index=False)
            elif df.iloc[i]['接入位置名称'] == '--':  # 平台没跟踪到位置
                pass
            else:
                self.df_result = self.df_result.append([{'cell小区': df.iloc[i]['接入位置名称'],
                                                         '原cell小区': df.iloc[i]['接入位置名称'],
                                                                 '用户类型': df.iloc[i]['用户类型'],
                                                                 '综合失败原因': df.iloc[i]['综合失败原因'],
                                                                 '初步原因分类': type_reason,
                                                                 }], ignore_index=False)

    def cell_unqual(self, df, type_reason):  # 小区不相同统计函数
        for i in range(0, len(df)):
            if re.match(r'46011.+', df.iloc[i]['结束4G小区名称']):  # 正则表达判断是否为enodBID
                ID = str(df.iloc[i]['结束4G小区名称'])[:11]  # 得到ID = plmn+gnodeBID+cellID
                gnodBID = ID[-7:-2]
                cellID = ID[-2:]
                # 十六进制转换为十进制
                gnodBID = int(gnodBID, 16)
                cellID = int(cellID, 16)
                gnodB_cell_ID = str(gnodBID) + '_' + str(cellID)
                # 根据用户类型查找基站
                if df.iloc[i]['用户类型'] == 'V05G':
                    if gnodB_cell_ID in list(self.dict_NR['ENBID_CELLID']):
                        print('查找5G台账')
                        find_data = self.dict_NR.loc[self.dict_NR['ENBID_CELLID'] == gnodB_cell_ID, 'Cell Name']
                        self.df_result = self.df_result.append([{'综合失败原因': df.iloc[i]['综合失败原因'],
                                                                 '初步原因分类': type_reason,
                                                                 '原cell小区': df.iloc[i]['结束4G小区名称'],
                                                                 'cell小区': find_data.values[0],
                                                                 '用户类型': df.iloc[i]['用户类型']}], ignore_index=False)
                else:
                    if gnodB_cell_ID in list(self.dict_LTE['eNodeBID_CELL_ID']):
                        print('查找4G台账')
                        find_data = self.dict_LTE.loc[self.dict_LTE['eNodeBID_CELL_ID'] == gnodB_cell_ID, 'CELL_NAME']
                        self.df_result = self.df_result.append([{'综合失败原因': df.iloc[i]['综合失败原因'],
                                                                 '初步原因分类': type_reason,
                                                                 '原cell小区': df.iloc[i]['结束4G小区名称'],
                                                                 'cell小区': find_data.values[0],
                                                                 '用户类型': df.iloc[i]['用户类型']}], ignore_index=False)
            elif df.iloc[i]['结束4G小区名称'] == '--':  # 平台没跟踪到位置
                pass
            else:
                self.df_result = self.df_result.append([{'综合失败原因': df.iloc[i]['综合失败原因'],
                                                         '初步原因分类': type_reason,
                                                         '原cell小区': df.iloc[i]['结束4G小区名称'],
                                                         'cell小区': df.iloc[i]['结束4G小区名称'],
                                                         '用户类型': df.iloc[i]['用户类型']}], ignore_index=False)

# ******************************************   主函数   **************************************************#
if __name__ == '__main__':
    app = QApplication(sys.argv)
    SeqStatistics = SeqStatistics()
    SeqStatistics.ui.show()
    sys.exit(app.exec_())