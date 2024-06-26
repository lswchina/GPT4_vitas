import os
import re
import sys
import argparse
from model.FSM import FSM
import util.deal_with_UI as UI
from util.Spider import Spider
from util.ChatGPT import askChatGPT
import util.Constant as Constant
from skill.Skill import Skill
import step2_test_skill as test

def getArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", help = "input the configuration file id", dest = "id", type=str, default="1")
    parser.add_argument("-e", help = "input the name of an excel file in the dataset_2022 directory", dest = "excel_name", type = str, default = "elevate13+vitas2.xlsx")
    parser.add_argument("-l", help = "input the path to save logs", dest = "log_path", type = str, default = "../../output/elevate13+vitas2_10min/")
    parser.add_argument("-o", help = "input the path to save results", dest = "res_path", type = str, default = "../../output/elevate13+vitas2_10min/result/")
    parser.add_argument("-g", help = "input the path to save logs of GPT4_vitas", dest = "log_path_gpt", type = str, default = "../../output/elevate+gpt4_10min/")
    args = parser.parse_args()
    CONFIG_ID = args.id
    EXCEL_PATH = os.path.join(os.path.abspath(r".."), "dataset_2022", args.excel_name)
    LOG_PATH = args.log_path
    if LOG_PATH[-1] != '/':
        LOG_PATH = LOG_PATH + '/'
    RESULT_PATH = args.res_path
    if RESULT_PATH[-1] != '/':
        RESULT_PATH = RESULT_PATH + '/'
    LOG_PATH_GPT = args.log_path_gpt
    if LOG_PATH_GPT[-1] != '/':
        LOG_PATH_GPT = LOG_PATH_GPT + '/'
    return CONFIG_ID, EXCEL_PATH, LOG_PATH, RESULT_PATH, LOG_PATH_GPT

def init_dir(LOG_PATH, RESULT_PATH):
    if not os.path.exists(RESULT_PATH):
        os.makedirs(RESULT_PATH)
    if not os.path.exists('../cookie'):
        os.makedirs("../cookie/")
    if not os.path.exists(LOG_PATH):
        os.makedirs(LOG_PATH)

def init_constant(config_id):
    if len(config_id) == 1:
        Constant.CONFIG_PATH = os.path.join(os.path.abspath(r".."), 'config', 'config00' + config_id + '.ini')
    elif len(config_id) == 2:
        Constant.CONFIG_PATH = os.path.join(os.path.abspath(r".."), 'config', 'config0' + config_id + '.ini')
    else:
        print("invalid configuration file id")
        sys.exit(-1)
    Constant.LOGOUT_URL = "https://www.amazon.com/ap/signin?_encoding=UTF8&openid.assoc_handle=usflex&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.mode=checkid_setup&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&openid.ns.pape=http%3A%2F%2Fspecs.openid.net%2Fextensions%2Fpape%2F1.0&openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2Fgp%2Fyourstore%2Fhome%3Fie%3DUTF8%26action%3Dsign-out%26path%3D%252Fgp%252Fyourstore%252Fhome%26ref_%3Dnav_AccountFlyout_signout%26signIn%3D1%26useRedirectOnSuccess%3D1"
    Constant.CHROME_PATH = os.path.join(os.path.abspath(r".."), "chrome", "chromedriver_new.exe") #"/snap/bin/chromium.chromedriver"
    Constant.COOKIE_DIR = os.path.join(os.path.abspath(r".."), "cookie", "console_cookie7_" + config_id + ".pkl")
    Constant.WEB = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
    Constant.USER_AGENT = {'User-Agent':Constant.WEB,'Host':'www.amazon.com'}
    Constant.RE_DIC = {
        'alert': f'<div class="a-alert-content">(.*?)</div>',
        'title': f'<meta name="title" content=(.*?)>',
        'description': '<div data-cy="skill-product-description-see-more" class="sc-kIeTtH dfCbWS">(.*?)</div>',
        'invocation': f'''<span data-cy="invocation-name-value-detail" font-size="14px" class="sc-eggNIi sc-bsipQr eCEvt hsFSWY">(.*?)</span>''',
        'permissions': f'<li class="a2s-permissions-list-item">(.*?)</li>',
        'perm': f'''<span class="a-list-item">
            
            
            
            
            (.*?)
        
        
        </span>''',
        'tit': f'<title>(.*?)</title>'
    }
    Constant.TIME_LIMIT = 10 * 60
    Constant.StopSign = ['Stop', 'stop', 'Exit', 'exit', 'cancel', 'Cancel', 'quit', 'Quit']
    Constant.SYSTEM_LEVEL_LABEL = "system-level"
    Constant.HELP_EMBEDDED_LABEL = "help-embedded"
    Constant.CONTEXT_RELATED_LABEL = "context-related"

if __name__ == '__main__':
    CONFIG_ID, EXCEL_PATH, LOG_PATH, RESULT_PATH, LOG_PATH_GPT = getArgs()
    if not os.path.exists(EXCEL_PATH):
        print("the excel path does not exist")
        sys.exit()
    init_constant(CONFIG_ID)
    init_dir(LOG_PATH, RESULT_PATH)
    spider = Spider(Constant.CONFIG_PATH)
    UI.open_log_page(spider)
    index = 1
    while True:
        skill = Skill(EXCEL_PATH, index)
        if skill.skillName == '<end_of_excel>' or index > 100:
            break
        if skill.skillName != '':
            skill_log_path = os.path.join(LOG_PATH, re.sub(r'(\W+)', '_', skill.skillName))
            if not os.path.exists(skill_log_path):
                os.makedirs(skill_log_path)
            else:
                index = index + 1
                continue
            skill_log_path_gpt = os.path.join(LOG_PATH_GPT, re.sub(r'(\W+)', '_', skill.skillName))
            if not os.path.exists(skill_log_path_gpt):
                print(skill_log_path_gpt, " does not exist")
            else:    
                gpt = askChatGPT(skill.skillName, skill_log_path, skill_log_path_gpt, True, Constant.CONFIG_PATH)
                fsm = FSM(gpt)
                test.generateTest(skill_log_path, RESULT_PATH, spider, skill, gpt, fsm)
                UI.re_open_with_no_exit(spider)
        index = index + 1
    UI.close_spider(spider)
