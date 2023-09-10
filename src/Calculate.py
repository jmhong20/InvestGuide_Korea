import csv
import os

import CompInfo

class InvestKorea:
    def calculate(self, code, name, price, df, growth_rate = 3):
        """
        적정주가 = 정상EPS * (정상PER + 적정화계분수 * 2)
        
        정상EPS = (경상이익 - 법인세비용) / 유통주식수
        정상PER = 현재가격 / 정상EPS
        """
        try:
            ###계산에 필요한 변수
            Cur_Asset = df.loc[df['code'] == code]["cur_asset"].iloc[0] # 당기 총자산
            Bef_Asset = df.loc[df['code'] == code]["bef_asset"].iloc[0]  # 전기 총자산
            Cur_Debt = df.loc[df['code'] == code]["cur_debt"].iloc[0]  # 당기 총부채
            Bef_Debt = df.loc[df['code'] == code]["bef_debt"].iloc[0]  # 전기 총부채
            Profit = df.loc[df['code'] == code]["profit"].iloc[0]  # 영업이익
            Oth_Profit = df.loc[df['code'] == code]["oth_profit"].iloc[0]  # 영업외수익
            Oth_Loss = df.loc[df['code'] == code]["oth_loss"].iloc[0]  # 영업외비용
            Tax = df.loc[df['code'] == code]["tax"].iloc[0]  # 법인세비용

            Price = int(price)  # 주가
            StockCounts = df.loc[df['code'] == code]["stock_count"].iloc[0]  # 유통주식수

            Cur_Profit = Profit + Oth_Profit - Oth_Loss  # 경상이익
            Cur_ROA = (Cur_Profit - Tax) / ((Cur_Asset + Bef_Asset) / 2)  # 경상ROA
            APS = ((Cur_Asset + Bef_Asset) / 2) / StockCounts
            Nor_EPS = APS * Cur_ROA  # 정상EPS
            Nor_PER = Price / Nor_EPS  # 정상PER
            Debt_Ratio = Cur_Debt / Cur_Asset
            Debt_Ratio *= 100

            ValidPrice = Nor_EPS * (Nor_PER + growth_rate * 2)  # 적정주가
            Difference = round((ValidPrice - Price) / Price * 100, 2)  # 괴리율

            data = code, name, Price, ValidPrice, Difference, Debt_Ratio, Cur_ROA, APS, Nor_EPS, Nor_PER, Cur_Profit, Cur_Asset, Cur_Debt, Bef_Asset, Bef_Debt, Profit, Oth_Profit, Oth_Loss, Tax, StockCounts

            return data

        except:
            return None
