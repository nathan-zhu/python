#-*- encoding:utf-8 -*-

import traceback
import os
import time
import json
import re


from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup

from userlist import portalsUsers

class PortalsVs(object):
    def __init__(self):
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        dcap["phantomjs.page.settings.userAgent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:25.0) Gecko/20100101 Firefox/25.0"
        )
        self.driver = webdriver.PhantomJS(executable_path=r"./phantomjs.exe",
                                          port=9988, desired_capabilities=dcap,
                                          service_args=['--load-images=no'])
        self.driver.set_window_size(1024, 768)
        self.website = "portals"

    def close(self):
        self.driver.close()

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

    def procClasses(self, name, data):
        fn = self._genFileName((self.website,), (name, "classes"), suffix="html")
        with open(fn, "a+") as f:
            f.write(data.encode('utf-8'))
            f.write("<!-- === -->\n")

        soup = BeautifulSoup(data, "html.parser")
        lis = soup.select(".class-list.clear li[data-status='active']")
        print "classes:", len(lis)
        ret = []
        for li in lis:
            rs = {}
            rs["courseName"] = li.select(".class-name")[0].text
            rs["teacherName"] = li.select(".teacher-name")[0].text
            try:
                rs["percent"] = li.select(".numeric-grade")[0].text
            except:
                rs["percent"] = ""
            ret.append(rs)
        fn = self._genFileName((self.website,), (name, "classes", "result"))
        with open(fn, "a+") as f:
            json.dump(ret, f)
            f.write("\n")
        return ret


    def procBaseInfo(self, name, data):
        baseinfo = {}
        baseinfo
        soup = BeautifulSoup(data, "html.parser")
        baseinfo["name"] = soup.select(".username")[0].text
        baseinfo["schoolName"] = soup.select(".school-name")[0].text
        return baseinfo

    def procAbsense(self, name, data):
        fn = self._genFileName((self.website,), (name, "absence"), suffix="html")
        with open(fn, "a+") as f:
            f.write(data.encode('utf-8'))
            f.write("<!-- o=== -->\n")
        soup = BeautifulSoup(data, "html.parser")
        abs1 = soup.select("#master")
        tds = abs1[0].select("tr")[1].select("td")
        #print tds
        ret = {}
        rs = {}
        rs["absencesSum"] = tds[2].text.strip()
        rs["tardiesSum"] = tds[5].text.strip()
        trs = soup.select("#master-detail table tr")
        ds = []
        for tr in trs[1:]:
            dd = {}
            tds = tr.select("td")
            dd["date"] = tds[0].text.strip()
            dd["status"] = tds[1].text.strip()
            ds.append(dd)
        rs["detail"] = ds
        ret["master"] = rs

        rs = {}
        trs = soup.select("#class tr")
        cls = []
        for tr in trs[1:-1]:
            dd = {}
            dd["courseId"] = tr["data-id"].strip()
            tds = tr.select("td")
            dd["courseName"] = tds[0].select("span")[0].text.strip()
            dd["absences"] = tds[3].text.strip()
            dd["tardies"] = tds[6].text.strip()

            idname = "#class_%s_detail" % (dd["courseId"])
            div = soup.select(idname)
            if len(div) <= 0:
                continue
            trs2 = div[0].select("table tr")
            detail = []
            for tr in trs2[1:]:
                ds = {}
                tds2 = tr.select("td")
                ds["date"] = tds2[0].text.strip()
                ds["status"] = tds2[1].text.strip()
                detail.append(ds)
            dd["detail"] = detail
            cls.append(dd)
        tds = trs[-1].select("td")
        rs["absencesSum"] = tds[3].text.strip()
        rs["tardiesSum"] = tds[6].text.strip()
        rs["detail"] = cls
        ret["classes"] = rs

        ret = rs
        #print json.dumps(ret)
        fn = self._genFileName((self.website,), (name, "absence", "result"))
        with open(fn, "a+") as f:
            json.dump(ret, f)
            f.write("\n")
        return ret





    def procGrade(self, name, courseid, data):
        fn = self._genFileName((self.website,), (name, courseid, "grade"), suffix="html")
        with open(fn, "a+") as f:
            f.write(data.encode("utf-8"))
            f.write("<!-- === -->\n")

        res = {}
        res["courseId"] = courseid
        soup = BeautifulSoup(data, "html.parser")
        res["score"] = soup.select(".ptd_grade")[0].text.strip()
        res["grade"] = soup.select(".letter_grade")[0].text.strip()
        ps = soup.select("#enrollment_info .enrollment p")
        tmp = soup.select("#header h1")[0].text
        tmp = tmp.split(" - ")
        term = tmp[1].replace("Quarter ", "q")
        res["term"] = term
        try:
            tmp = ps[1].text.rsplit(" - ")
            print ps[1].text
            res["courseName"] = tmp[0].strip()
            res["courseTeacher"] = tmp[1].strip()
        except:
            res["courseName"] = ""
            res["courseTeacher"] = ""

        tbs = soup.select("#assignments table tbody")
        rl =  []
        for tb in tbs:
            rs = {}
            trs = tb.select("tr")
            try:
                rs["groupName"] = trs[0].select("th")[0].text.strip()
                try:
                    tds = trs[-1].select("td")
                    rs["possible"] = tds[5].text.strip()
                    rs["earned"] = tds[4].text.strip()
                    rs["arvg"] = ""
                except:
                    rs["arvg"] = trs[-1].select("td")[-1].text.strip()
                    rs["possible"] = ""
                    rs["earned"] = ""
            except:
                continue
            trl = []
            for tr in trs[1:-1]:
                trd = {}
                tds = tr.select("td")
                trd["date"] = tds[0].text.strip()
                trd["assignment"] = tds[1].text.strip()
                trd["score"] = tds[2].text.strip()
                trd["grade"] = tds[3].text.strip()
                try:
                    trd["pointEarned"] = tds[4].text.strip()
                    trd["pointPossible"] = tds[5].text.strip()
                except:
                    trd["pointEarned"] = ""
                    trd["pointPossible"] = ""
                trl.append(trd)
            rs["detail"] = trl
            rl.append(rs)
        res["detail"] = rl

        fn = self._genFileName((self.website,), (name, courseid, "grade", "result"))
        with open(fn, "a+") as f:
            json.dump(res, f)
            f.write("\n")
        return res

    def _procResult(self, name, data):
        strtime = time.strftime("%Y%m%d-%H%M", time.localtime(time.time()))
        fn = self._genFileName((self.website,), (name, "result", strtime), timeflag=False)
        with open(fn, "a+") as f:
            json.dump(data, f)
            f.write("\n")

    def _saveMail(self, name, data):
        fn = self._genFileName((self.website,), (name, "mail"), suffix="html")
        with open(fn, "a+") as f:
            f.write(data.encode("utf-8"))
            f.write("<!-- === -->\n")

    def run(self, username, passwd):
        driver = self.driver
        #login
        url = "https://portals.veracross.com/jcs/student"
        driver.get(url)

        #time.sleep(3)
        #print driver.page_source

        WebDriverWait(driver, 30).until(lambda the_driver: the_driver.find_element_by_xpath(
            "//input[@id='username']").is_displayed())
        WebDriverWait(driver, 30).until(lambda the_driver: the_driver.find_element_by_xpath(
            "//input[@id='password']").is_displayed())

        name = driver.find_element_by_xpath("//input[@id='username']")
        pwd = driver.find_element_by_xpath("//input[@id='password']")
        submit = driver.find_element_by_xpath("//input[@id='login-button']")

        ActionChains(driver).send_keys_to_element(name, username).perform()
        time.sleep(0.2)
        ActionChains(driver).send_keys_to_element(pwd, passwd).perform()
        time.sleep(0.3)
        ActionChains(driver).click(on_element=submit).perform()
        time.sleep(60)
        driver.save_screenshot("1.png")

        '''
        #print driver.page_source
        try:
            baseinfo = self.procBaseInfo(username, driver.page_source)
            print baseinfo
        except:
            print "baseinfo fail!"
            print traceback.print_exc()
        ela = driver.find_element_by_css_selector(".class-status.active")
        ela.click()
        time.sleep(3)
        classes = self.procClasses(username, driver.page_source)
        print classes
        '''


        result = {}
        ela = driver.find_elements_by_css_selector("#reports .attendance a")[-1]
        url = ela.get_attribute("href")
        driver.get(url)
        time.sleep(6)
        absenceinfo = self.procAbsense(username, driver.page_source)
        driver.back()
        result["absenceInfo"] = absenceinfo
        #driver.back()
        time.sleep(3)

        #teacher info
        #print driver.page_source
        self._saveMail(username, driver.page_source)
        els = driver.find_elements_by_css_selector(".class-list.clear li[data-status='active']")
        allurls = []
        for el in els:
            urls = []
            ela = el.find_element_by_css_selector("a[class='class-name']")
            urls.append(ela.get_attribute("href"))
            try:
                ela = el.find_element_by_css_selector("a[class='calculated-grade']")
                urls.append(ela.get_attribute("href"))
            except:
                try:
                    ela = el.find_element_by_css_selector("a[class='view-assignments']")
                    urls.append(ela.get_attribute("href")+"/")
                except:
                    urls.append("")
            allurls.append(urls)
        print allurls

        '''
        elcls = driver.find_elements_by_css_selector(".class-list.clear li[data-status='active'] .class-name")
        elas = driver.find_elements_by_css_selector(".class-list.clear li[data-status='active'] .calculated-grade")
        curls = [ela.get_attribute("href") for ela in elas]
        print curls
        urls = [el.get_attribute("href") for el in elcls]
        #print urls
        teacherInfo = {}
        prnt len(url), len(curls)
        '''
        teacherInfo = {}
        for url, curl in allurls:
            print url, curl
            tmp = re.search("classes/(\d+)/", curl)
            if not tmp:
                print "not found cid!"
                continue
            cid = tmp.group(1)
            cls = {}
            try:
                driver.get(url)
                time.sleep(6)
                #driver.save_screenshot("3.png")
                #teacherName = driver.find_element_by_css_selector(".info h4").text
                cls["teacherMail"] = driver.find_element_by_css_selector(".info a[href^=mailto]").get_attribute("href").replace("mailto:","")
                cls["teacherPhone"] = driver.find_element_by_css_selector(".info").text.split("\n")[1]
                teacherInfo[cid] = cls
                driver.back()
                time.sleep(6)
            except:
                #print driver.page_source
                continue



        driver.get("https://portals.veracross.com/jcs/student/classes")
        time.sleep(20)
        #print driver.page_source
        driver.save_screenshot("3.png")
        elas = driver.find_elements_by_xpath("//div[@class='enrollment-list clear']/div[1]/a")
        urls = [ela.get_attribute("href") for ela in elas]
        #urls = eldivs[0].find_elements_by_xpath("/a/@href")
        #print "==", urls

        grades = []
        for i, url in enumerate(urls):
            print url
            driver.get(url)
            time.sleep(6)
            #print driver.page_source
            ela = driver.find_element_by_xpath("//div[@class='enrollment-detail-tabs']/a[2]")
            ela.click()
            time.sleep(6)

            elifr = driver.find_element_by_xpath("//iframe[@id='grade-detail-document']")
            surl = elifr.get_attribute("src")
            driver.get(surl)
            time.sleep(6)
            ret = re.search("classes/(\d+)", url)
            if ret:
                cid = ret.group(1)
            else:
                cid = i
            ret = self.procGrade(username, cid, driver.page_source)
            grades.append(ret)
            #driver.back()

        for grade in grades:
            cid = grade["courseId"]
            ti = teacherInfo.get(cid)
            if ti:
                grade["teacherMail"] = ti.get("teacherMail")

        result["scoreDetail"] = grades
        self._procResult(username, result)

        #history
        try:
            history = []
            for i, url in enumerate(urls):
                print url
                driver.get(url)
                time.sleep(6)
                #print driver.page_source
                ela = driver.find_element_by_xpath("//div[@class='enrollment-detail-tabs']/a[2]")
                ela.click()
                time.sleep(6)

                elifr = driver.find_element_by_xpath("//iframe[@id='grade-detail-document']")
                surl = elifr.get_attribute("src")
                driver.get(surl)
                time.sleep(6)
                ret = re.search("classes/(\d+)", url)
                if ret:
                    cid = ret.group(1)
                else:
                    cid = i
                ret = self.procGrade(username, cid, driver.page_source)
                history.append(ret)
        except:
            print "get histroy fail!"



    def test(self):
        '''
        with open("absence_vs.html", "r") as f:
            data = f.read()
        print self.procAbsense("test", data)
        '''
        with open("grade_vs.html", "r") as f:
            data = f.read()
        print json.dumps(self.procGrade("test", 1786, data))


if __name__ == "__main__":
    app = PortalsVs()
    for v in portalsUsers:
        try:
            app.run(v[0], v[1])
            #app.test()
        except:
            traceback.print_exc()
        finally:
            app.close()