import pandas as pd

class CompInfo:
    # Class Constructor
    def __init__(self):
        self.stocks = self.read_krx_code()
    
    # Read company information from KRX
    def read_krx_code(self):
        """
        KRX로부터 상장기업 목록 파일을 읽어와서 데이터프레임으로 반환
        Read all listed companies "name" and their corresponding "stock_code" from KRX,
        and transform them into a dataframe.
        """
        url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=' \
                'download&searchType=13'
        krx = pd.read_html(url, header=0)[0]
        krx = krx[['종목코드', '회사명']]
        krx = krx.rename(columns={'종목코드': 'code', '회사명': 'company'})
        krx.code = krx.code.map('{:06d}'.format)
        return krx
    
    # Convert company's stock_code into its name
    def get_name_from_code(self, stock_code):
        ### 회사 이름으로 회사 고유번호 찾기
        """
        Finding [comp_name] by stock_code:
        ex.)
            se = code.loc[code['code'] == "005930"].values.tolist()[0][1]
        """
        return self.stocks.loc[self.stocks['code'] == stock_code].values.tolist()[0][1]

    # Convert company's name into its stock_code
    def get_code_from_name(self, name):
        ###주식종목코드 찾기
        """
        Finding [stock_code] by company name:
        ex.)
            se = code.loc[code['company'] == "삼성전자"].values.tolist()[0][1]
        """
        return self.stocks.loc[self.stocks['company'] == name].values.tolist()[0][0]
