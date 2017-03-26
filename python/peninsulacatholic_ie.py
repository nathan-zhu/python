#-*- coding:utf8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import traceback
import os
import time
import re
import json

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup

from userlist import penieUsers

class PeninsulacatholicIe(object):
    def __init__(self):
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        dcap["phantomjs.page.settings.userAgent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:25.0) Gecko/20100101 Firefox/25.0"
        )
        self.driver = webdriver.PhantomJS(executable_path=r"./phantomjs.exe",
                                          port=9987, desired_capabilities=dcap,
                                          service_args=['--load-images=no'])
        self.driver.set_window_size(1024, 768)
        self.website = "peninsulacatholic"

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

    def procBaseinfo(self, name, data):
        rep = re.compile("ENV = (.*?);")
        ret = rep.search(data)
        #print ret.group(1)
        baseinfo = {}
        try:
            envinfo = json.loads(ret.group(1))
            userinfo = envinfo["current_user"]
            baseinfo["id"] = userinfo["id"]
            baseinfo["name"] = userinfo["display_name"]
            baseinfo["avatarUrl"] = userinfo["avatar_image_url"]
        except:
            pass
        strtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        baseinfo["crawltime"] = strtime
        fn = self._genFileName((self.website,), (name, "baseinfo"))
        with open(fn, "a+") as f:
            json.dump(baseinfo, f)
            f.write("\n")
        return baseinfo


    def procGrades(self, name, data, coursename, term, courseid):
        fn = self._genFileName((self.website,), (name, courseid, "scores"), suffix="html")
        with open(fn, "a+") as f:
            f.write(data)
            f.write("<!-- === -->\n")
        soup = BeautifulSoup(data,"html.parser")
        #trs = soup.select('#grades_summary tr[id|=submission]')
        trs = soup.select('#grades_summary tr[class~="student_assignment"]')
        rs = []
        cnt = 0
        print len(trs), courseid
        #print trs
        for tr in trs[1:-5]:
            #print cnt
            cnt += 1
            res = {}
            if "dropped" in tr["class"]:
                res["courses_status"] = "dropped"
            res["subId"] = tr["id"].replace("submission_", "")
            res["courseName"] = tr.select("th a")[0].text.strip().replace("\n", "")
            #res["context"] = tr.select("th div")[0].text.replace(" ", "").replace("\n", "")

            tds = tr.select("td")
            res["due"] = tds[0].text.strip().replace("\n", "")
            score = tds[1].select(".grade")[0]
            ret = re.search("span>.*?(\d+)", str(score), re.S)
            if ret:
                res["score"] = ret.group(1)
            else:
                res["score"] = ""
            res["outof"] = tds[2].text.replace(" ", "").replace("\n", "")

            rs.append(res)
        #print rs

        sumrs = []
        for tr in trs[-5:-1]:
            res = {}
            res["name"] = tr.select("th")[0].text.strip().replace("\n", "")
            tds = tr.select("td")
            percent = re.search("([0-9.]+%)", tds[1].select("span[class='grade']")[0].text)
            if percent:
                res["percent"] = percent.group(1)
            else:
                res["percent"] = ""
            final = re.search("([0-9.]+%)", tds[2].text)
            if final:
                res["final"] = final.group(1)
            else:
                res["final"] = ""

            sumrs.append(res)
        tr = trs[-1]
        res = {}
        res["name"] = tr.select("th")[0].text.strip().replace("\n", "")
        tds = tr.select("td")
        percent = re.search("([0-9.]+%)", tds[1].select("span[class='grade']")[0].text)
        if percent:
            res["percent"] = percent.group(1)
        else:
            res["percent"] = ""
        sumrs.append(res)

        courseinfo = {}
        courseinfo["course"] = {"detail": rs, "sum": sumrs}
        #print json.dumps(ret)
        courseinfo["courseName"] = coursename
        courseinfo["term"] = term
        courseinfo["courseId"] = courseid
        rightcontent = soup.select("#student-grades-right-content")
        try:
            courseinfo["grade"] = rightcontent[0].select("#final_letter_grade_text")[0].text
        except:
            courseinfo["grade"] = ""
            print "no grade", rightcontent, coursename

        try:
            courseinfo["percent"] =  rightcontent[0].select(".grade")[0].text
        except:
            courseinfo["percent"] = ""
            print "no percent", rightcontent, coursename
        ret = courseinfo

        fn = self._genFileName((self.website,), (name, courseid, "scores", "result"))
        with open(fn, "a+") as f:
            json.dump(ret, f)
            f.write("\n")
        return ret

    def procAllCourse(self, name, data):
        fn = self._genFileName((self.website,), (name, "allcourse"), suffix="html")
        with open(fn, "a+") as f:
            f.write(data)
            f.write("<!-- === -->\n")

        ret = []
        soup = BeautifulSoup(data, "html.parser")
        trs = soup.select("#my_courses_table tr")
        for tr in trs[1:]:
            rs = {}
            tds = tr.select("td")
            rs["courseid"] = tds[0].select('span')[0]["data-course-id"]
            rs["coursename"] = tds[1].select('.name')[0].text.strip().replace("\n", "")
            rs["term"] = tds[3].text.strip().replace("\n", "")
            print rs
            ret.append(rs)
        #print ret
        fn = self._genFileName((self.website,), (name, "allcourse", "result"))
        with open(fn, "a+") as f:
            json.dump(ret, f)
            f.write("\n")
        return ret


    def saveResult(self, name, ret):
        strtime = time.strftime("%Y%m%d-%H%M", time.localtime(time.time()))
        fn = self._genFileName((self.website,), (name, "result", strtime), timeflag=False)
        with open(fn, "a+") as f:
            json.dump(ret, f)
            f.write("\n")

    def run(self, username, passwd):
        driver = self.driver
        #login
        driver.delete_all_cookies()
        url = "https://peninsulacatholic.instructure.com/login/canvas"
        driver.get(url)

        time.sleep(10)
        #print driver.page_source

        WebDriverWait(driver, 60).until(lambda the_driver: the_driver.find_element_by_xpath(
            "//input[@id='pseudonym_session_unique_id']").is_displayed())
        #WebDriverWait(driver, 60).until(lambda the_driver: the_driver.find_element_by_xpath(
        #    "//input[@id='pseudonym_session_password']").is_displayed())

        name = driver.find_element_by_xpath("//input[@id='pseudonym_session_unique_id']")
        pwd = driver.find_element_by_xpath("//input[@id='pseudonym_session_password']")
        submit = driver.find_element_by_xpath("//button[@class='Button Button--login']")

        ActionChains(driver).send_keys_to_element(name, username).perform()
        time.sleep(0.2)
        ActionChains(driver).send_keys_to_element(pwd, passwd).perform()
        time.sleep(0.3)
        ActionChains(driver).click(on_element=submit).perform()

        time.sleep(6)
        #driver.save_screenshot("1.png")
        #print driver.page_source

        #couser
        driver.get("https://peninsulacatholic.instructure.com/courses")
        time.sleep(5)
        allcourse = self.procAllCourse(username, driver.page_source)
        allret = []
        for course in allcourse:
            url = "https://peninsulacatholic.instructure.com/courses/%s/grades" % course["courseid"]
            driver.get(url)
            time.sleep(6)
            rs = self.procGrades(username, driver.page_source, course["coursename"], course["term"], course["courseid"])
            allret.append(rs)
        baseinfo = self.procBaseinfo(username, driver.page_source)
        #driver.save_screenshot("2.png")
        ret = {"courses": allret, "baseinfo": baseinfo}
        self.saveResult(username, ret)

    def test(self):
        '''
        with open("peninsulacatholic_grade.html", "r") as f:
            data = f.read()
        self.procGrades("test", data, "English", "S1", "8763")
        '''
        with open("peninsulacatholic_grade.html", "r") as f:
            data = f.read()
        print self.procGrades("test", data, "English", "S1", "8763")
        print self.procBaseinfo("test", data)
        '''
        with open("pn_course.html", "r") as f:
            data = f.read()
        self.procAllCourse("test", data)
        '''



if __name__ == "__main__":
    app = PeninsulacatholicIe()
    for v in penieUsers:
        try:
            app.run(v[0], v[1])
            #app.test()
        except:
            traceback.print_exc()
        finally:
            app.close()