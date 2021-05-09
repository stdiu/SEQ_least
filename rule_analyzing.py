import pandas as pd

class RuleAnalyzing():
    def __init__(self, file):
        self.file = file
        self.Analyzing()

    def Analyzing(self):
        self.rule_mo = pd.read_excel(f"./data/{self.file}", sheet_name=0)
        self.rule_mt = pd.read_excel(f"./data/{self.file}", sheet_name=1)
