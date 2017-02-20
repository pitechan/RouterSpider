# -*- coding: utf-8 -*-

PHANTOMJSPATH = '/Users/apple/Downloads/phantomjs-2.1.1-macosx/bin/phantomjs' # phantomjs的路径

BROWSERMOBPROXYPATH = '/Users/apple/Downloads/browsermob-proxy-2.1.4/bin/browsermob-proxy' # browsermobproxy的路径

# browsermobproxy的设置
PROXYSETTINGS  = {
    "captureHeaders":True,
    "captureContent":True,
    'captureBinaryContent': True
}

URLSUFFIXLIST = ['.asp', '.js', '.html', '.cgi', '.htm', '.php'] # 用于遍历获取URL，可添加新的后缀

# http headers中的授权字段
HEADERS = {
    "Authorization":"Basic YWRtaW46cGFzc3dvcmQ="
}

BASEURL = 'http://192.168.2.1/' # 路由器基础URL，用于URL的拼接

INDEXURL = 'http://192.168.1.1/' # 路由器首页URL，用于URL的遍历

LOGINURL = 'http://192.168.2.1/cgi-bin/luci/admin/login' # 路由器登录URL

AUTHURL = 'http://admin:password@192.168.1.1' # 路由器带http-auth URL，可用于webdriver的登录

MAINSUFFIXLIST = ['.htm', '.html'] # 路由器页面的后缀

FORBIDDENELEMENTLIST = [] # 禁止操作的元素，填入该元素的name或id即可

FORBIDDENURLLIST = [] # 禁止访问的URL

JSINTERCEPTOR = '''
request.headers().add('Request-Uri', request.getUri());
if(request.method() == 'POST')
{
    request.setUri(request.getUri() + 'unreachable');
}
'''

STRTOFILL = [
    "1.1.1.1",
    "255.255.254.0",
    "teststr1",
    "777",
    ""
]