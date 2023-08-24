import csv
import os

class InvestKorea:
    def calculate(self, code, name, price, growth_rate, df):
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

            Constant = growth_rate  # 적정화계분수, 무위험채권의 PER, 무성장기업의 PER
            Price = int(price)  # 주가
            StockCounts = int(self.find_avail_stocks(code))

            Cur_Profit = Profit + Oth_Profit - Oth_Loss  # 경상이익
            Cur_ROA = (Cur_Profit - Tax) / ((Cur_Asset + Bef_Asset) / 2)  # 경상ROA
            APS = ((Cur_Asset + Bef_Asset) / 2) / StockCounts
            Nor_EPS = APS * Cur_ROA  # 정상EPS
            Nor_PER = Price / Nor_EPS  # 정상PER
            Debt_Ratio = Cur_Debt / Cur_Asset
            Debt_Ratio *= 100

            ValidPrice = Nor_EPS * (Nor_PER + Constant * 2)  # 적정주가
            Difference = round((ValidPrice - Price) / Price * 100, 2)  # 괴리율

            data = code, name, Price, ValidPrice, Difference, Debt_Ratio, Cur_ROA, APS, Nor_EPS, Nor_PER, Cur_Profit, Cur_Asset, Cur_Debt, Bef_Asset, Bef_Debt, Profit, Oth_Profit, Oth_Loss, Tax, StockCounts

            return data

        except:
            return None
        
    def create_Excel(self):
        ###csv파일 생성
        if os.path.exists('ANALYSIS.csv'):
            os.remove('ANALYSIS.csv')
        else:
            print("Sorry, I can't remove {} file.".format('ANALYSIS.csv'))

        title = "주식코드", "회사명", "현재주가", "적정주가", "괴리율", "부채비율", "경상ROA", "APS", "정상EPS", "정상PER", "경상이익", "당기 총자산", "당기 총부채",  "전기 총자산", "전기 총부채", "영업이익", "영업외수익", "영업외비용", "법인세비용", "유통주식수"
        with open('ANALYSIS.csv', 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(title)
    
    def Refresh_Excel(self, growth_rate):
        self.create_Excel()

        for i in range(len(mk.get_company_list())):
            print(i)
            # code = 
            # name =
            # price =
            data = self.calculate(code, name, price, growth_rate)
            if data != None:
                with open('ANALYSIS.csv', 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(data)
            print()

    def run(self):
        ...

if __name__ == "__main__":
    ...
