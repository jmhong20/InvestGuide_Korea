import urllib
import bs4
import requests
from datetime import datetime

class StockInfo():
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
        try: return (float(self.find_total_stocks(code)) - float(self.find_comp_stocks(code)))
        except: return 1

    def get_book_info(self, code, name):
        """
        Returns: 
        Cur_Asset, Bef_Asset, Cur_Debt, Bef_Debt, Profit, Oth_Profit, Oth_Loss, Tax
        = (당기 총자산, 전기 총자산, 당기 총부채, 전기 총부채, 영업이익, 영업외수익, 영업외비용, 법인세비용)
        """
        ###재무제표 요청 url 생성
        endpoint = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json?"
        # API 키
        crtfc_key = ""
        # 기업 이름
        corp_code = str(self.find_corp_num(code))
        # 사업 연도
        bsns_year = "2020"
        # 보고서 코드:
        # 1분기보고서: 11013
        # 반기보고서: 11012
        # 3분기보고서: 11014
        reprt_code = "11014"
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
