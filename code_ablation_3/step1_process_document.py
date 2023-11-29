import re
import html
import requests
import util.Constant as Constant

def getSkillWeb(SKILL_URL):
    sk_resp, sk_status = getURL(SKILL_URL)
    if sk_status == False:
        print("This skill does not exist.\n")
        return False, '', '', '', []
    try:
        alert = re.findall(Constant.RE_DIC['alert'], sk_resp.text)[0]
        alert = toValidStr(alert)
        if "This skill is not currently available." in alert:
            return False, '', '', '', []
    except:
        pass
    title = re.findall(Constant.RE_DIC['title'], sk_resp.text, re.S)[0]
    title = toValidStr(title)
    descr = ''
    invocation = ''
    try:
        descr = re.findall(Constant.RE_DIC['description'], sk_resp.text)[0]
        descr = toValidStr(descr)
        invocation = re.findall(Constant.RE_DIC['invocation'], sk_resp.text)[0]
        invocation = toValidStr(invocation)
    except:
        return False, '', '', '', []
    pers = []
    try:
        permissions = re.findall(Constant.RE_DIC['permissions'], sk_resp.text, re.S)[0]
        pers = re.findall(Constant.RE_DIC['perm'], permissions)
    except:
        pers = []
    return True, title, descr, invocation, pers
        
def getURL(url):
    resp = requests.get(url,headers=Constant.USER_AGENT)
    resp.encoding = resp.apparent_encoding
    if resp.status_code == 200:
        titles = re.findall(Constant.RE_DIC['tit'], resp.text)
        if len(titles) > 0 and 'Page Not Found' in titles[0]:
            print(titles[0])
            return None, False
        return resp, True
    return None, False

def toValidStr(string):
    string = html.unescape(string)
    string = string.encode(encoding='utf-8', errors = 'ignore').decode(encoding='utf-8')
    string = string.strip()
    string = string.strip('\n')
    string = string.strip()
    string = string.replace("‘", '\'')
    string = string.replace("’", '\'')
    string = string.replace("”", '\"')
    string = string.replace("“", '\"')
    string = string.replace("<br/>", '')
    string = string.replace("\n", '')
    return string
