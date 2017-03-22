# -*- coding: utf8 -*-
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import os
import time,re,random
import traceback
import json
import re

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from bs4 import BeautifulSoup

from userlist import JohnCarrolSchool

class PowerSchool(object):
    def __init__(self):
        #driver = webdriver.Chrome(executable_path=r"C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe")
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        dcap["phantomjs.page.settings.userAgent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:25.0) Gecko/20100101 Firefox/25.0"
        )

        #self.driver = webdriver.PhantomJS(executable_path=r"./phantomjs.exe",
        self.driver = webdriver.PhantomJS(executable_path=r"phantomjs",
                                          port=9989, desired_capabilities=dcap,
                                          service_args=['--load-images=no'])
        self.driver.set_window_size(1024, 768)
        self.website = "capitalchristian"
        #John Carrol School
    def _genFileName(self, paths, files, suffix="json", timeflag=True):
        rpath = ["data"]
        if timeflag:
            t = time.localtime()
            strt = '%d-%d-%d' % (t.tm_year, t.tm_mon, t.tm_mday)
            rpath[1:1] = paths
            rpath.append(strt)
            dr = os.path.join(*rpath)
        else:
            rpath[1:1] = paths
            dr = os.path.join(*rpath)
        if not os.path.exists(dr):
            os.makedirs(dr)
        nm = "_".join([str(i) for i in files]) + "." + suffix
        fn = os.path.join(dr, nm)
        return fn


    def crawl(self):
        driver = self.driver
        #url = "https://capitalchristian.powerschool.com"
        url = "https://portals.veracross.com/jcs/student";
        driver.get(url)
        #print driver.page_source
        print driver.current_url
        print driver.save_screenshot("1.png")

        #print driver.add_cookie()
        #print driver.delete_all_cookies()
        print driver.get_cookies()

    def procAttance(self, name, data):
        fn = self._genFileName((self.website,), (name, "attance"), suffix="html")
        with open(fn, "a+") as f:
            f.write(data)
            f.write("<!-- === -->\n")
        soup = BeautifulSoup(data, "html.parser")
        #trs = soup.select('div[class="box-round"] table[class="tableToGrid"] tr')
        trs = soup.select('div[class="ui-jqgrid-bdiv"] table[class="ui-jqgrid-btable"] tr')
        items = []
        fields = ["course", "dueDate", "category", "AssignmentName", "score", "percent", "letterGrade", "codes"]
        for tr in trs[1:]:
            tds = tr.select("td")
            item = {}
            for i,f in  enumerate(fields):
                item[f] = tds[i].text.strip()
                items.append(item)
        fn = self._genFileName((self.website,), (name, "attance", "result"))
        with open(fn, "a+") as f:
            json.dump(items, f)
            f.write("\n")
        return items


    def procHistory(self, name, data):
        fn = self._genFileName((self.website,), (name, "history"), suffix="html")
        with open(fn, "a+") as f:
            f.write(data)
            f.write("<!-- === -->\n")
        soup = BeautifulSoup(data, "html.parser")
        sel = soup.select('#gradesHistory table tr')
        lis = soup.select('#gradesHistory li[class="selected"]')
        strtime = lis[0].text
        if len(lis) >= 2:
            strtime = lis[1].text
        strtime = strtime.strip()
        if not strtime:
            strtime = "default"
        items = []

        cats = ["Q1", "Q2", "F1", "S1"]
        for tr in sel[2:]:
            item = {}
            marks = []
            tds = tr.select('td')
            item["courseName"] = tds[0].text

            item["mark"] = marks
            for i, c in enumerate(cats):
                j = i*4 + 1
                gs = {}
                gs["category"] = c
                gs["grade"] = tds[j].text.strip()
                try:
                    gs["score"] = tds[j+1].select('a')[0].text.strip()
                except:
                    gs["score"] = ""
                gs["git"] = tds[j+2].text.strip()
                gs["hrs"] = tds[j+3].text.strip()
                marks.append(gs)
            items.append(item)
        ret = {"time":strtime, "data": items}
        fn = self._genFileName((self.website,), (name, "history", "result"))
        with open(fn, "a+") as f:
            json.dump(ret, f)
            f.write("\n")
        return ret


    def procAttanceHome(self, name, data):
        fn = self._genFileName((self.website,), (name, "attancehome"), suffix="html")
        with open(fn, "a+") as f:
            f.write(data)
            f.write("<!-- === -->\n")
        soup = BeautifulSoup(data, "html.parser")

        showname = soup.select("#userName span")[0].text
        printschool = ""
        sdiv = soup.select("#print-school")
        ret = re.search('<div.*?.*?<br>(.*?)<br><span>(.*?)</span>', str(sdiv))
        if ret:
            printschool = ret.group(1) + "||" + ret.group(2)

        sel  = soup.select('#quickLookup table[class~="linkDescList"] tr')
        term = ""
        try:
            term = sel[1].select("th")[4].text
        except:
            pass
        scoresums = []
        for tr in sel[3:-1]:
            scoresum = {}
            scoresum["courseId"] = tr["id"]
            #print tr["id"]
            tds = tr.select("td")
            #print len(tds), tds
            #scoresum['exp'] = tds[0].text
            tm = tds[11]
            ret = re.search('<td.*?>(.*?)\xa0<br>.*?<a.*?href="(.*?)".*?>.*?<a href="mailto:(.*?)">Email (.*?)</a>', str(tm), re.S)
            if ret:
                scoresum["course"] = ret.group(1).replace("\xc2", "")
                #scoresum["teacherUrl"] = ret.group(2)
                scoresum["teacherMail"] = ret.group(3)
                scoresum["teacherName"] = ret.group(4)
                #print ret.groups()
            else:
                print "re not found", tm
            tm = tds[12]
            ret = re.search('<td><a.*?href="(.*?)".*?>(.*?)<br>(.*?)<', str(tm), re.S)
            if ret:
                #scoresum["gradeUrl"] = ret.group(1)
                scoresum["grade"] = ret.group(2)
                scoresum["score"] = ret.group(3)
            else:
                try:
                    scoresum["gradeUrl"] = tm.select(a)[0]["href"]
                except:
                    pass
                scoresum["grade"] = tm.text
                print "score re not found", tm
            scoresum["absences"] = tds[13].text
            scoresum["tardies"] = tds[14].text
            #print tm.split(u"\xa0")
            scoresums.append(scoresum)

        ret = {}
        baseinfo = {}
        baseinfo["studentName"] = showname.strip()
        baseinfo["schoolName"] = printschool
        baseinfo["loginName"] = name
        baseinfo["term"] = term
        ret["baseinfo"] = baseinfo

        absenceinfo = {}
        attancesum = sel[-1]
        ths = attancesum.select("th")
        absenceinfo["absencesSum"] = ths[1].text
        absa = ths[1].select("a")
        baseurl = "https://capitalchristian.powerschool.com/guardian/"
        if absa:
            try:
                absenceinfo["absencesSumUrl"] = baseurl + absa[0]["href"]
            except Exception as e:
                print "absences url fail", name, absa
        absenceinfo["tardiesSum"] = ths[2].text
        absa = ths[2].select("a")
        if absa:
            try:
                absenceinfo["tardiesSumUrl"] = baseurl + absa[0]["href"]
            except Exception as e:
                print "tardies url fail", name, absa
        ret["scoreOutline"] = scoresums
        ret["absencesInfo"] = absenceinfo
        fn = self._genFileName((self.website,), (name, "attancehome", "result"))
        with open(fn, "a+") as f:
            json.dump(ret, f)
            f.write("\n")
        return ret


    def procScoreDetail(self, name, courseid, coursename, data):
        fn = self._genFileName((self.website,), (name, "scoredetail", courseid), suffix="html")
        with open(fn, "a+") as f:
            f.write(data)
            f.write("<!-- === -->\n")
        soup = BeautifulSoup(str(data), "lxml")
        #print soup
        boxround = soup.select(".box-round")
        #print boxround
        tbs = boxround[0].select("table")
        ret = {}
        ret["courseId"] = courseid
        ret["courseName"] = coursename
        try:
            tb = tbs[0]
            trs = tb.select("tr")
            tds = trs[1].select("td")
            ret["courseName"] = tds[0].text
            ret["teacherName"] = tds[1].text
            #ret["exp"] = tds[2].text
        except Exception as e:
            print "score detail sourse:", courseid, coursename, tbs, e

        try:
            ttb  = tbs[1]
            trs = ttb.select("tr")
            ret["lastupdated"] = trs[0].select("td")[0].text
        except Exception as e:
            print "score detail updatetime:", courseid, coursename, e, tbs

        tbs = boxround[1].select("table")
        trs  = tbs[0].select("tr")
        drs = []
        keys = ["dueDate", "category", "assignment", "standard", "score", "percent", "grd", "flag"]
        for tr in trs[1:-1]:
            tds = tr.select("td")
            rs = {}
            for i, td in enumerate(tds[:len(keys)]):
                rs[keys[i]] = td.text
            drs.append(rs)
        ret["scoreDetail"] = drs
        fn = self._genFileName((self.website,), (name, "scoredetail", courseid, "result"))
        with open(fn, "a+") as f:
            json.dump(ret, f)
            f.write("\n")
        return ret




    def test(self):
        '''
        with open("history.html", "r") as f:
            data = f.read()
        ret = self.procHistory("test", data)
        print json.dumps(ret)
        '''
        '''
        with open("attance.html", "r") as f:
            data = f.read()
        ret = self.procAttance("test", data)
        print json.dumps(ret)
        '''
        '''
        with open("attancehome.html", "r") as f:
            data = f.read()
        ret = self.procAttanceHome("test", data)
        #print json.dumps(ret)
        '''
        with open("scoredetail.html", "r") as f:
            data = f.read()
        #ret = self.procScoreDetail("test", "ccid_9873", "English", data)
        #print json.dumps(ret)

        els = self.driver.find_elements_by_css_selector(".box-round:nth-of-type(2) table tr")
        print els


    def prooCookies(self):
        cookies = self.driver.get_cookies()
        print cookies


    def _procResult(self, name, data):
        strtime = time.strftime("%Y%m%d-%H%M", time.localtime(time.time()))
        fn = self._genFileName((self.website,), (name, "result", strtime), timeflag=False)
        with open(fn, "a+") as f:
            json.dump(data, f)
            f.write("\n")



    def run(self, username, userpwd):
        driver = self.driver
        #url = "https://capitalchristian.powerschool.com/public/home.html"
        #url = "https://capitalchristian.powerschool.com"
        url = "https://portals.veracross.com/jcs/student ";
        driver.get(url)
        WebDriverWait(driver, 30).until(lambda the_driver: the_driver.find_element_by_xpath(
            "//input[@id='username']").is_displayed())
        WebDriverWait(driver, 30).until(lambda the_driver: the_driver.find_element_by_xpath(
            "//input[@id='password']").is_displayed())

        #print driver.page_source

        #time.sleep(0.5)

        name = driver.find_element_by_xpath("//input[@id='username']")
        pwd = driver.find_element_by_xpath("//input[@id='password']")
        submit = driver.find_element_by_xpath("//input[@id='login-button']")

        print driver.save_screenshot("01.png")

        ActionChains(driver).send_keys_to_element(name, username).perform()
        time.sleep(0.3)
        ActionChains(driver).send_keys_to_element(pwd, userpwd).perform()
        time.sleep(0.5)
        ActionChains(driver).click(on_element=submit).perform()

        time.sleep(10)
        self.prooCookies()
        print driver.save_screenshot("2.png")
        sys.exit()
        '''
        #old attance
        attanceUrl = "https://capitalchristian.powerschool.com/guardian/ppstudentasmtlist.html"
        driver.get(attanceUrl)
        WebDriverWait(driver, 30).until(lambda the_driver: the_driver.find_element_by_css_selector(
            'div[class="ui-jqgrid-bdiv"] table[class="ui-jqgrid-btable"]').is_displayed())
        #print driver.page_source
        #time.sleep(5)
        self.procAttance(username, driver.page_source)
        driver.save_screenshot("3.png")
        '''
        ret = self.procAttanceHome(username, driver.page_source)

        '''
        els = driver.find_elements_by_css_selector("#quickLookup table tr")
        for el in els[2:-1]:
            id = el.get_attribute("id")
            eltds = el.find_elements_by_css_selector("td")
            ela = eltds[12].find_element_by_css_selector("a")
            driver.
        '''
        rscores = []
        for ol in ret["scoreOutline"]:
            '''
            url = ol.get("gradeUrl")
            if not url:
                continue
            if not url.startswith("http"):
                url = "https://capitalchristian.powerschool.com/guardian/" + url
            print url
            '''
            ela = driver.find_element_by_css_selector('#%s' % ol["courseId"])
            eltd = ela.find_elements_by_css_selector("td")
            try:
                ela = eltd[12].find_element_by_css_selector("a")
            except Exception as e:
                print "find score detail href:", e, username, ol["courseId"]
                continue
            rurl = ela.get_attribute("href")
            print rurl
            if not rurl:
                continue
            ela.click()
            #driver.get(url)
            #time.sleep(random.randint(2,5))
            time.sleep(6)
            sdret = self.procScoreDetail(username, ol["courseId"], ol["course"], driver.page_source)
            rscores.append(sdret)
            driver.back()
            time.sleep(2)
        ret["scoreDetail"] = rscores

        try:
            historyUrl = "https://capitalchristian.powerschool.com/guardian/termgrades.html"
            driver.get(historyUrl)
            WebDriverWait(driver, 40).until(lambda the_driver: the_driver.find_element_by_css_selector(
                '#gradesHistory table').is_displayed())
            #print driver.page_source
            #time.sleep(3)
            historyret = self.procHistory(username, driver.page_source)
            ret["history"] = historyret
            #driver.save_screenshot("4.png")
        except:
            print traceback.print_exc()

        strtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        ret["crawltime"] = strtime
        self._procResult(username, ret)

if __name__ == "__main__":
    app = PowerSchool()
    #app.crawl()
    #app.driver.close()
    #app.driver.quit()
    trymax = 2
    for user in JohnCarrolSchool:
        for i in xrange(0, trymax):
            try:
                #start = time.time()
                app.run(user[0], user[1])
                #end = time.time()
                #print end-start
                break
                #app.crawl()
                #app.test()
            except:
                print traceback.print_exc()
            finally:
                app.driver.close()
    try:
        app.driver.quit()
    except:
        pass

