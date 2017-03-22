 1. /var/www/crawl
 2. source vpy27crawl/bin/activate; cd /var/www/crawl/codes

 3.在userlist.py中添加学生信息：
 capitalchristian.powerschool.com:
 users = [
    ("用户名","密码"),
    ("用户名","密码")
]

cathedral.powerschool.com
cathedralUsers = [
   ("用户名","密码")
   ("用户名","密码")
]

4.python capitalchristian_ps.py
  python cathedral_ps.py
    
5.一段时间后在data/capitalchristian/或者data/cathedral查看结果：
/var/www/crawl/codes # ll data/capitalchristian/
2017-2-21/
Che149_result_20170221.json


