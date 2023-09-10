import pandas as pd
import requests
import xml.etree.ElementTree as et
from io import BytesIO
from zipfile import ZipFile

from bs4 import BeautifulSoup
from urllib.request import urlopen

import urllib
import bs4

from datetime import date

class StockInfo():
    def __init__(self) -> None:
        """
        # DataFrame 검색
        df[(df['corp_name'] == '삼성전자')].iloc[0].corp_code
        """
        crtfc_key = ""
        # OpenDART에서 Zipfile 받아와 객체에 저장하기
        u = requests.get('https://opendart.fss.or.kr/api/corpCode.xml', params={'crtfc_key':crtfc_key})
        zipfile_bytes = u.content
        zipfile_obj = ZipFile(BytesIO(zipfile_bytes))

        # 압축을 풀어서 XML File을 string으로 담기
        xmlfile_objs = {name: zipfile_obj.read(name) for name in zipfile_obj.namelist()}
        xml_str = xmlfile_objs['CORPCODE.xml'].decode('utf-8')

        # XML String을 가져와서 DataFrame에 담기
        xroot = et.fromstring(xml_str)

        df_cols = ["corp_code", "corp_name", "stock_code", "modify_date"]
        rows = []

        for node in xroot: 
            res = []
            for el in df_cols[0:]: 
                if node is not None and node.find(el) is not None:
                    res.append(node.find(el).text)
                else: 
                    res.append(None)
            rows.append({df_cols[i]: res[i] 
                        for i, _ in enumerate(df_cols)})

        self.df = pd.DataFrame(rows, columns=df_cols)

    def get_corp_num(self, code):
        return self.df[(self.df['stock_code'] == code)].iloc[0].corp_code
    
    def get_price(self, code, pages_to_fetch = 1):
        """네이버에서 주식 시세를 읽어서 데이터프레임으로 반환"""
        try:
            baseURL = "https://fchart.stock.naver.com/sise.nhn?"
            symbol = str(code)
            timeframe = "day"
            count = str(pages_to_fetch)
            requestType = "0"
            url = baseURL + "symbol=" + symbol + "&" + "timeframe=" + timeframe + "&" + "count=" + count + "&" + "requestType=" + requestType
            bf_price = 0

            df = []
            with urlopen(url) as doc:
                if doc is None:
                    return None
                html = BeautifulSoup(doc, "lxml")
                items = html.findAll('item')
                for item in items:
                    data = item.get('data').split('|')
                    data.insert(5, 0)
                    if bf_price == 0:
                        bf_price = int(data[4])
                        data[5] = 0
                    else:
                        diff = int(data[4]) - bf_price
                        bf_price = int(data[4])
                        data[5] = str(diff)
                    date = data[0][:4] + "-" + data[0][4:6] + "-" + data[0][6:8]
                    data[0] = date
                    df.append(data)
        except Exception as e:
            print('Exception occured :', str(e))
            return None
        return df[0][4]

    def get_outstanding(self, code):
        ###발행주식수 찾기
        endpoint = "https://finance.naver.com/item/coinfo.nhn?"
        # 종목코드
        code = str(code)
        url = endpoint + "code=" + code
        html = urllib.request.urlopen(url)
        bs_obj = bs4.BeautifulSoup(html, "html.parser")
        trs = bs_obj.find_all('tr')
        for tr in trs:
            if tr:
                th = tr.find('th')
                if th:
                    if th.text == '상장주식수':
                        td = tr.find('td')
                        temp = td.text
                        temp2 = temp.split(",")
                        total_stocks = ""
                        for c in temp2:
                            total_stocks += c
                        return total_stocks

    def get_treasury(self, code):
        ###자기주식수 찾기
        endpoint = "https://comp.fnguide.com/SVO2/ASP/SVD_shareanalysis.asp?"
        pGB = "1"
        # 종목코드
        gicode = "A"+str(code)
        cID = ""
        MenuYn = "Y"
        ReportGB = ""
        NewMenuID = "109"
        stkGb = "701"

        url = endpoint + "pGB=" + pGB + "&" + "gicode=" + gicode + "&" + "cID=" + cID + "&" + "MenuYn=" + MenuYn + "&" \
              + "ReportGB=" + ReportGB + "&" + "NewMenuID=" + NewMenuID + "&" + "stkGB=" + stkGb

        html = urllib.request.urlopen(url)
        bs_obj = bs4.BeautifulSoup(html, "html.parser")
        table = bs_obj.find("table", {"class": "us_table_ty1 h_fix zigbg_no th_topbdno"})
        trs = table.findAll("tr")
        for tr in trs:
            th = tr.find("th")
            if ("자기주식" in th.text):
                tds = tr.findAll("td")
                #print(len(tds[1].text))
                if len(tds[1].text) > 2:
                    temp = tds[1].text
                    temp2 = temp.split(",")
                    string = ""
                    for c in temp2:
                        string += c
                    return string
                return "0"

    def get_ready_to_trade_shares(self, code):
        ###유통주식수 찾기
        try: return (float(self.get_outstanding(code)) - float(self.get_treasury(code)))
        except: return 1
    

    def get_book_info(self, code, name):
        """
        Returns: 
        Cur_Asset, Bef_Asset, Cur_Debt, Bef_Debt, Profit, Oth_Profit, Oth_Loss, Tax
        = (당기 총자산, 전기 총자산, 당기 총부채, 전기 총부채, 영업이익, 영업외수익, 영업외비용, 법인세비용)
        """
        endpoint = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json?"
        crtfc_key = ""
        corp_code = self.get_corp_num(code)

        today = str(date.today())
        dates = today.split("-")
        # 사업 연도
        bsns_year = dates[0]
        """
        5월 15일 ~ 8월 13일: 11013
        8월 14일 ~ 11월 13일: 11012
        11월 14일 ~ 5월 14일: 11014
        """
        reprt_code = "11012"
        
        # OFS: 재무제표
        fs_div = "OFS"
        paramset = "crtfc_key=" + crtfc_key + "&" + "corp_code=" + corp_code + "&" + "bsns_year=" + bsns_year + "&" + "reprt_code=" + reprt_code + "&" + "fs_div=" + fs_div
        url = endpoint + paramset
        ###재무제표 요청
        result = requests.get(url)

        ###파싱가능한 리스트형태로 변환
        try:
            list = result.json()["list"]
        except:
            return

        ###저장할 변수
        Cur_Asset = 0  # 당기 총자산
        Bef_Asset = 0  # 전기 총자산
        Cur_Debt = 0  # 당기 총부채
        Bef_Debt = 0  # 전기 총부채
        Profit = 0  # 영업이익
        Oth_Profit = 0  # 영업외수익
        Oth_Loss = 0  # 영업외비용
        Tax = 0  # 법인세비용

        for i in range(len(list)):
            account_name = list[i]["account_nm"].replace(" ", "")
            amount = list[i]["thstrm_amount"]
            if "," in list[i]["thstrm_amount"]:
                amount = list[i]["thstrm_amount"].replace(",", "")

            if (list[i]["sj_div"] == "BS" and account_name == "자산총계"):
                try:
                    Cur_Asset = int(amount)
                    Bef_Asset = int(amount)
                except:
                    return name
            if (list[i]["sj_div"] == "BS" and account_name == "부채총계"):
                try:
                    Cur_Debt = int(amount)
                    Bef_Debt = int(amount)
                except:
                    return name

            elif (list[i]["sj_div"] == "IS" and ("영업이익" == account_name or "영업이익(손실)" == account_name
                                                 or "영업이익(수익)" == account_name or "영업손익" == account_name
                                                 or "영업손실" == account_name or "V.영업손익" == account_name
                                                 or "Ⅴ.영업이익" == account_name or "Ⅴ.영업이익(손실)" == account_name
                                                 or "Ⅲ.영업이익(손실)" == account_name or "Ⅳ.영업이익" == account_name)):
                if len(str(amount)) >= 1:
                    Profit = int(amount)
                else:
                    Profit = 0

            elif (list[i]["sj_div"] == "IS" and ("기타수익" == account_name or "기타영업외수익" == account_name
                                                 or "1.기타수익" == account_name or "기타이익" == account_name
                                                 or "순기타수익(비용)" == account_name or "Ⅵ.기타수익" == account_name
                                                 or "Ⅳ.기타수익" == account_name or "1.기타수익(주석22.24)" == account_name
                                                 or "기타이익(주26)" == account_name)):
                try:
                    if len(str(amount)) >= 1:
                        if int(amount) < 0:
                            Oth_Profit += int(amount) * -1
                        else:
                            Oth_Profit += int(amount)
                    else:
                        Oth_Profit += 0
                except:
                    return name
            elif (list[i]["sj_div"] == "IS" and ("금융수익" == account_name or "3.금융수익" == account_name
                                                 or "금융수익-기타" == account_name or "순금융수익(원가)" == account_name
                                                 or "1.금융수익" == account_name or "Ⅵ.금융수익" == account_name
                                                 or "3.금융수익(주석3.23.24)" == account_name or "금융수익(주10,27)" == account_name)):
                try:
                    if len(str(amount)) >= 1:
                        if int(amount) < 0:
                            Oth_Profit += int(amount) * -1
                        else:
                            Oth_Profit += int(amount)
                    else:
                        Oth_Profit += 0
                except:
                    return name

            elif (list[i]["sj_div"] == "IS" and ("기타비용" == account_name or "기타영업외비용" == account_name
                                                 or "기타손실" == account_name or "2.기타비용" == account_name
                                                 or "Ⅶ.기타비용" == account_name or "Ⅴ.기타비용" == account_name
                                                 or "2.기타비용(주석22.24)" == account_name or "기타손실(주26)" == account_name)):
                try:
                    if len(str(amount)) >= 1:
                        if int(amount) < 0:
                            Oth_Loss += int(amount) * -1
                        else:
                            Oth_Loss += int(amount)
                    else:
                        Oth_Loss += 0
                except:
                    return name
            elif (list[i]["sj_div"] == "IS" and ("금융비용" == account_name or "금융원가" == account_name
                                                 or "4.금융비용" == account_name or "2.금융비용" == account_name
                                                 or "Ⅶ.금융비용" == account_name or "4.금융원가(주석3.23.24)" == account_name
                                                 or "금융원가(주10,27)" == account_name)):
                try:
                    if len(str(amount)) >= 1:
                        if int(amount) < 0:
                            Oth_Loss += int(amount) * -1
                        else:
                            Oth_Loss += int(amount)
                    else:
                        Oth_Loss += 0
                except:
                    return name
            elif (list[i]["sj_div"] == "IS" and ("법인세비용" == account_name or "법인세비용(수익)" == account_name
                                                 or "법인세비용(손실)" == account_name or "법인세비용 (손실)" == account_name
                                                 or "법인세비용(효익)" == account_name or "법인세비용(효익익" == account_name
                                                 or "Ⅶ.법인세비용" == account_name or "계속영업법인세비용" == account_name
                                                 or "법인세비용(주19)" == account_name or "법인세수익(비용)" == account_name
                                                 or "법인세비용(이익)" == account_name or "계속영업법인세비용(효익)" == account_name
                                                 or "계속영업법인세비용(수익)" == account_name or "Ⅹ.법인세비용(수익)" == account_name
                                                 or "Ⅸ.법인세비용" == account_name or "Ⅵ.법인세비용(주석3.25)" == account_name
                                                 or "법인세비용(주29)" == account_name)):
                if len(str(amount)) >= 1:
                    if int(amount) < 0:
                        Tax = int(amount) * -1
                    else:
                        Tax = int(amount)
                else:
                    Tax = 0
        if Profit == 0:
            for i in range(len(list)):
                account_name = list[i]["account_nm"].replace(" ", "")
                amount = list[i]["thstrm_amount"]
                if "," in list[i]["thstrm_amount"]:
                    amount = list[i]["thstrm_amount"].replace(",", "")

                if (list[i]["sj_div"] == "CIS" and ("영업이익" == account_name or "영업이익(손실)" == account_name
                                                    or "영업이익(수익)" == account_name or "영업손익" == account_name
                                                    or "영업손실" == account_name or "V.영업손익" == account_name
                                                    or "Ⅴ.영업이익" == account_name or "Ⅴ.영업이익(손실)" == account_name
                                                    or "Ⅲ.영업이익(손실)" == account_name or "Ⅳ.영업이익" == account_name)):
                    if len(str(amount)) >= 1:
                        Profit = int(amount)
                    else:
                        Profit = 0

                elif (list[i]["sj_div"] == "CIS" and ("기타수익" == account_name or "기타영업외수익" == account_name
                                                      or "1.기타수익" == account_name or "기타이익" == account_name
                                                      or "순기타수익(비용)" == account_name or "Ⅵ.기타수익" == account_name
                                                      or "Ⅳ.기타수익" == account_name or "1.기타수익(주석22.24)" == account_name
                                                      or "기타이익(주26)" == account_name)):
                    try:
                        if len(str(amount)) >= 1:
                            if int(amount) < 0:
                                Oth_Profit += int(amount) * -1
                            else:
                                Oth_Profit += int(amount)
                        else:
                            Oth_Profit += 0
                    except:
                        return name
                elif (list[i]["sj_div"] == "CIS" and ("금융수익" == account_name or "3.금융수익" == account_name
                                                      or "금융수익-기타" == account_name or "순금융수익(원가)" == account_name
                                                      or "1.금융수익" == account_name or "Ⅵ.금융수익" == account_name
                                                      or "3.금융수익(주석3.23.24)" == account_name or "금융수익(주10,27)" == account_name)):
                    try:
                        if len(str(amount)) >= 1:
                            if int(amount) < 0:
                                Oth_Profit += int(amount) * -1
                            else:
                                Oth_Profit += int(amount)
                        else:
                            Oth_Profit += 0
                    except:
                        return name

                elif (list[i]["sj_div"] == "CIS" and ("기타비용" == account_name or "기타영업외비용" == account_name
                                                      or "기타손실" == account_name or "2.기타비용" == account_name
                                                      or "Ⅶ.기타비용" == account_name or "Ⅴ.기타비용" == account_name
                                                      or "2.기타비용(주석22.24)" == account_name or "기타손실(주26)" == account_name)):
                    try:
                        if len(str(amount)) >= 1:
                            if int(amount) < 0:
                                Oth_Loss += int(amount) * -1
                            else:
                                Oth_Loss += int(amount)
                        else:
                            Oth_Loss += 0
                    except:
                        return name
                elif (list[i]["sj_div"] == "CIS" and ("금융비용" == account_name or "금융원가" == account_name
                                                      or "4.금융비용" == account_name or "2.금융비용" == account_name
                                                      or "Ⅶ.금융비용" == account_name or "4.금융원가(주석3.23.24)" == account_name
                                                      or "금융원가(주10,27)" == account_name)):
                    try:
                        if len(str(amount)) >= 1:
                            if int(amount) < 0:
                                Oth_Loss += int(amount) * -1
                            else:
                                Oth_Loss += int(amount)
                        else:
                            Oth_Loss += 0
                    except:
                        return name
                elif (list[i]["sj_div"] == "CIS" and ("법인세비용" == account_name or "법인세비용(수익)" == account_name
                                                      or "법인세비용(손실)" == account_name or "법인세비용 (손실)" == account_name
                                                      or "법인세비용(효익)" == account_name or "법인세비용(효익익" == account_name
                                                      or "Ⅶ.법인세비용" == account_name or "계속영업법인세비용" == account_name
                                                      or "법인세비용(주19)" == account_name or "법인세수익(비용)" == account_name
                                                      or "법인세비용(이익)" == account_name or "계속영업법인세비용(효익)" == account_name
                                                      or "계속영업법인세비용(수익)" == account_name or "Ⅹ.법인세비용(수익)" == account_name
                                                      or "Ⅸ.법인세비용" == account_name or "Ⅵ.법인세비용(주석3.25)" == account_name
                                                      or "법인세비용(주29)" == account_name)):
                    if len(str(amount)) >= 1:
                        if int(amount) < 0:
                            Tax = int(amount) * -1
                        else:
                            Tax = int(amount)
                    else:
                        Tax = 0

        return Cur_Asset, Bef_Asset, Cur_Debt, Bef_Debt, Profit, Oth_Profit, Oth_Loss, Tax
    
