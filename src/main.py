import sqlite3
import pandas as pd
import csv
import os

from CompInfo import CompInfo
from StockInfo import StockInfo
from Calculate import InvestKorea

class main:
    growthRate = 3

    def __init__(self) -> None:
        dbpath = "book_info.db"
        self.conn = sqlite3.connect(dbpath)
        self.cur = self.conn.cursor()
        sql = """
        CREATE TABLE IF NOT EXISTS book_info (
            code VARCHAR(20),
            name VARCHAR(40),
            cur_asset BIGINT(20),
            bef_asset BIGINT(20),
            cur_debt BIGINT(20),
            bef_debt BIGINT(20),
            profit BIGINT(20),
            oth_profit BIGINT(20),
            oth_loss BIGINT(20),
            tax BIGINT(20),
            stock_count BIGINT(20),
            PRIMARY KEY (code, name))
        """
        self.cur.executescript(sql)
        self.conn.commit()

    def refresh_table(self, names):
        for name in names:
            code = compinfo.get_code_from_name(name)
            StockCounts = stockinfo.get_ready_to_trade_shares(code)
            data = stockinfo.get_book_info(code, name)
            if data == None:
                continue
            Cur_Asset, Bef_Asset, Cur_Debt, Bef_Debt, Profit, Oth_Profit, Oth_Loss, Tax = data
            print(name + ":")
            
            sql = f"REPLACE INTO book_info VALUES ('{code}', " \
                f"'{name}', {Cur_Asset}, {Bef_Asset}, {Cur_Debt}, {Bef_Debt}, " \
                f"{Profit}, {Oth_Profit}, {Oth_Loss}, {Tax}, {StockCounts})"
            self.cur.executescript(sql)
            self.conn.commit()
            print("done")

    def get_company_list(self):
        sql = f"SELECT * FROM book_info"
        df = pd.read_sql(sql, self.conn)
        return df
    
    """
    ==================================================
    Export the calculated results into an Excel file.
    ==================================================
    """
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
        

    """
    ==================================================
    main() function.
    ==================================================
    """
if __name__ == "__main__":
    analyzer = main()
    compinfo = CompInfo()
    stockinfo = StockInfo()
    calculator = InvestKorea()

    #names = list(compinfo.stocks['company'])
    #analyzer.refresh_table(names)

    analyzer.create_Excel()
    
    db_info = analyzer.get_company_list()

    for i in range(len(db_info)):
        print(i)
        code = db_info.iloc[i]['code']
        name = db_info.iloc[i]['name']
        price = stockinfo.get_price(code)
        data = calculator.calculate(code, name, price, db_info, analyzer.growthRate)
        if data != None:
            with open('ANALYSIS.csv', 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(data)
        print()
    

    
    
    
