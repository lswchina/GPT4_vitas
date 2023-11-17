import re
import time
import selenium.common
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from util.NLP import NLP

RE_DIC = {
    'log_list': r'<div class="askt-log__list-element (?:"|askt-log__list-element--active") title="(.*?)">',
    'log_item': "//div[@class='askt-log__list-element ' and @title='%s']",
    'log_item_clicked': "//div[@class='askt-log__list-element askt-log__list-element--active' and @title='%s']",
    'log_info_list': r'<div class="ace_line" style="height:(\d+(\.\d+)?)px">(.*?)</div>',
    'log_info_item': r'<span class="ace_string">(.*?)</span>',
    'log_info': r'<span class="nav-line-1">(.*?)</span>'
}

dialog_requestId = ''

def wait_for_all_response_data(spider, log_list_before):
    go_on = False
    speech_started = False
    print('zzZ---getting for log list loading ')
    time.sleep(5)
    label = ''
    tmp_e = ''
    time_now = time.time()
    while time.time() - time_now < 10 * 60:
        try:
            if time.time() - time_now > 1 * 60 and not speech_started:
                print('<---not go on: time more than 1 minutes and speech not start--->')
                go_on = False
                label = 'crash'
                break
            log_list_after = re.findall(RE_DIC['log_list'], spider.web_driver.page_source)
            log_list_new = log_list_after[len(log_list_before): ]
            if log_list_after[-1][16:].endswith('Error'):
                go_on = False
                print('<---not go on: Something error--->')
                break
            if log_list_after == log_list_before:
                print('<---nothing update, same as before--->')
                if not speech_started:
                    time.sleep(5)
                    label = 'nothing update'
                else:
                    time.sleep(2)
                continue
            elif "Directive: AudioPlayer.Play" in ' '.join(log_list_new):
                speech_started = True
                go_on = True
                label = ''
                time.sleep(3)
                break
            elif (len(log_list_new) == 3 or len(log_list_after) == 4) and 'Directive: SpeechSynthesizer.Speak' not in ' '.join(log_list_new):
                time.sleep(5)
                log_list_after = re.findall(RE_DIC['log_list'], spider.web_driver.page_source)
                log_list_new = log_list_after[len(log_list_before): ]
                if (len(log_list_new) == 3 or len(log_list_after) == 4) and 'Directive: SpeechSynthesizer.Speak' not in ' '.join(log_list_new):
                    print('<---nothing update, only insignificance content--->')
                    go_on = False
                    label = 'nothing update'
                    break
                else:
                    continue
            # 过零点之后时间位数变少了一位
            elif log_list_after[-1][17:] == 'Event: SpeechSynthesizer.SpeechStarted' or log_list_after[-1][
                                                                                        16:] == 'Event: SpeechSynthesizer.SpeechStarted':
                speech_started = True
                label = ''
                time.sleep(3)
            elif log_list_after[-1][17:] == 'Event: SpeechSynthesizer.SpeechFinished' or log_list_after[-1][
                16:] == 'Event: SpeechSynthesizer.SpeechFinished' or (len(log_list_after) >= 2 and (log_list_after[-2][
                17:] == 'Event: SpeechSynthesizer.SpeechFinished' or log_list_after[-2][
                        16:] == 'Event: SpeechSynthesizer.SpeechFinished')):
                # print(log_list_after[-1][16:])
                go_on = True
                label = ''
                time.sleep(3)
                break
            elif log_list_after[-1][17:] == 'Directive: ApplicationMabreaknager.Navigation' or log_list_after[-1][
                                                                                          16:] == 'Directive: ApplicationManager.Navigation':
                # print(log_list_after[-1][16:])
                go_on = True
                label = ''
                break
            else:
                continue
        except Exception as e:
            tmp_e = str(e)
            if 'list index out of range' in tmp_e:
                label = 'cookie wrong'
                go_on = False
                print(label)
                break
    return go_on, label

def open_log_page(spider):
    spider.open_log_page()

def re_open(spider):
    time_start = time.time()
    time.sleep(0.5)
    while time.time() - time_start <= 10:
        try:
            just_input(spider, 'exit')
            break
        except selenium.common.exceptions.NoSuchElementException:
            continue
    while time.time() - time_start <= 60:
        try:
            spider.judge_curUrl()
        except selenium.common.exceptions.TimeoutException:
            continue
        try:
            deviceLevel_element = spider.web_driver.find_element(By.ID, 'deviceLevel-label')
            spider.web_driver.execute_script("arguments[0].click()", deviceLevel_element)
            # spider.web_driver.find_element_by_id('deviceLevel-label').click()
        except selenium.common.exceptions.NoSuchElementException:
            continue
        return True
    return False

def re_open_open(spider):
    time_start = time.time()
    time.sleep(0.5)
    while time.time() - time_start <= 10:
        try:
            just_input(spider, 'exit')
            time.sleep(2)
            return True
        except selenium.common.exceptions.NoSuchElementException:
            continue
    while time.time() - time_start <= 60:
        try:
            spider.judge_curUrl()
        except selenium.common.exceptions.TimeoutException:
            continue
        try:
            deviceLevel_element = spider.web_driver.find_element(By.ID, 'deviceLevel-label')
            spider.web_driver.execute_script("arguments[0].click()", deviceLevel_element)
            # spider.web_driver.find_element_by_id('deviceLevel-label').click()
        except selenium.common.exceptions.NoSuchElementException:
            continue
        return True
    return False

def re_open_with_no_exit(spider):
    spider.web_driver.refresh()
    time.sleep(5)
    time_start = time.time()
    while time.time() - time_start <= 60:
        try:
            deviceLevel_element = spider.web_driver.find_element(By.ID, 'deviceLevel-label')
            spider.web_driver.execute_script("arguments[0].click()", deviceLevel_element)
            break
        except selenium.common.exceptions.NoSuchElementException:
            continue
        except selenium.common.exceptions.WebDriverException:
            print("wait for opening the simulator")
            time.sleep(15)

#def get_text_message(spider, request):
def get_text_message(spider):
    time_start = time.time()
    source = spider.web_driver.page_source
    log_info = re.findall(RE_DIC['log_info_list'], source)
    while len(log_info) < 9 and time.time() - time_start <= 1 * 60:
        time.sleep(1)
        print('zzZ---time sleeping 1s for Text.TextMessage get source wrong, loading')
        source = spider.web_driver.page_source
        '''with open("text.txt", "wt", encoding='utf8') as rr:
            rr.write(source)
            rr.close()'''
        log_info = re.findall(RE_DIC['log_info_list'], source)
    if time.time() - time_start > 1 * 60:
        #return request, 'time out'
        return 'time out'
    time_start = time.time()
    is_data = False
    while not is_data and (time.time() - time_start) <= 1 * 60:
        for index, item in enumerate(log_info):
            if 'dialogRequestId' in item[2]:
                id = re.findall(RE_DIC['log_info_item'], item[2])[0][1:-1]
                #print("text message:")
                #print(id)
                dialog_requestId = str(id)
                #request.setID(id)
                is_data = True
                break
        source = spider.web_driver.page_source
        log_info = re.findall(RE_DIC['log_info_list'], source)
    if time.time() - time_start > 1 * 60:
        #return request, 'time out'
        return 'time out'
    #return request, ''
    return ''

#def get_speak_info(spider, request):
def get_speak_info(spider):
    time_start = time.time()
    response = ''
    source = spider.web_driver.page_source
    log_info = re.findall(RE_DIC['log_info_list'], source)
    while len(log_info) < 8 and time.time() - time_start <= 1 * 60:
        time.sleep(1)
        print('zzZ---time sleeping 1s for SpeechSynthesizer.Speak source wrong, loading ')
        source = spider.web_driver.page_source
        log_info = re.findall(RE_DIC['log_info_list'], source)
    if time.time() - time_start > 1 * 60:
        return '', '', 'time out'
    time_start = time.time()
    is_data = False
    is_equal = False
    is_start = False
    request_caption, request_url, request_token = '', '', ''
    while not is_data and not is_equal and time.time() - time_start <= 1 * 60:
        for index, item in enumerate(log_info):
            if 'dialogRequestId' in item[2]:
                '''id = re.findall(RE_DIC['log_info_item'], item[2])[0][1:-1]
                if str(id).strip('\"') != dialog_requestId:
                    break'''
                is_equal = True
            if "payload" in item[2]:
                if is_equal == True:
                    is_start = True
                else:
                    break
            if is_start == False:
                continue
            if 'caption' in item[2]:
                request_captions = re.findall(RE_DIC['log_info_item'], item[2])
                if len(request_captions) == 0:
                    request_caption = ' '
                else:
                    for cap in request_captions:
                        request_caption = request_caption + str(cap)
                    request_caption = NLP.toValidStr(request_caption)
                    request_caption = request_caption.strip()
                    request_caption = request_caption.strip("\"")
                    request_caption = request_caption.replace("!", ".")
                    request_caption = request_caption.replace("?", ".")
                    request_caption = request_caption.replace("\\\"", "\"")
                    request_caption = request_caption.replace("\\n", "")
                    request_caption = request_caption.replace("\n", "")
                    request_caption = request_caption.replace("\\t", "")
                    request_caption = request_caption.replace("\t", "")
                    request_caption = request_caption.strip()
                    if not request_caption.endswith('.'):
                        request_caption += '.'
                is_data = True
            if 'url' in item[2]:
                request_url = re.findall(RE_DIC['log_info_item'], item[2])[0][1:-1]
            if 'token' in item[2]:
                request_token = re.findall(RE_DIC['log_info_item'], item[2])[0][1:-1]
            if request_caption != '' and request_token != '' and request_url != '':
                break  
        source = spider.web_driver.page_source
        log_info = re.findall(RE_DIC['log_info_list'], source)
    if request_token != '':
        if 'ThirdParty' in request_token:
            speaker = 'ThirdParty'
        else:
            speaker = 'Alexa'
    else:
        speaker = 'Alexa'
    return request_caption, speaker, ''

def get_started_info(spider, request):
    source = spider.web_driver.page_source
    log_info = re.findall(RE_DIC['log_info_list'], source)
    while len(log_info) < 11:
        time.sleep(1)
        print('zzZ---time sleeping 1s for SpeechSynthesizer.SpeechStarted source wrong, loading ')
        source = spider.web_driver.page_source
        log_info = re.findall(RE_DIC['log_info_list'], source)
    time_start = time.time()
    is_data = False
    while not is_data and time.time() - time_start <= 1 * 60:
        for index, item in enumerate(log_info):
            if '"token"' in item[2]:
                start_token = re.findall(RE_DIC['log_info_item'], item[2])[0][1:-1]
                request.addStartToken(start_token)
                is_data = True
                break
        source = spider.web_driver.page_source
        log_info = re.findall(RE_DIC['log_info_list'], source)
    if time.time() - time_start > 1 * 60:
        return request, 'time out'
    return request, ''

#def get_play_info(spider, request):
def get_play_info(spider):
    time_start = time.time()
    source = spider.web_driver.page_source
    log_info = re.findall(RE_DIC['log_info_list'], source)
    while len(log_info) < 8 and time.time() - time_start <= 1 * 60:
        time.sleep(1)
        print('zzZ---time sleeping 1s for AudioPlayer.Play source wrong, loading ')
        source = spider.web_driver.page_source
        '''with open("play.txt",'wt',encoding='utf8') as tt:
            tt.write(source)
            tt.close()'''
        log_info = re.findall(RE_DIC['log_info_list'], source)
    if time.time() - time_start > 1 * 60:
        #return request, 'time out'
        return '', '', 'time out'
    time_start = time.time()
    is_data = False
    play_url, play_token = None, None
    while not is_data and time.time() - time_start <= 1 * 60:
        for index, item in enumerate(log_info):
            if '"url"' in item[2]:
                play_url = re.findall(RE_DIC['log_info_item'], item[2])[0][1:-1]
            elif '"token"' in item[2]:
                play_token = re.findall(RE_DIC['log_info_item'], item[2])[0][1:-1]
                is_data = True
                break
        source = spider.web_driver.page_source
        log_info = re.findall(RE_DIC['log_info_list'], source)
    if time.time() - time_start > 1 * 60:
        #return request, 'time out'
        return '', '', 'time out'
    #request.addMP3(play_url, play_token)
    print("play url:", play_url)
    print("play token: ", play_token)
    #return request, ''
    if play_token != '':
        if 'ThirdParty' in str(play_token):
            speaker = 'ThirdParty'
        else:
            speaker = 'Alexa'
    else:
        speaker = 'Alexa'
    return '<Play audio>.', speaker, ''

#def get_request(spider, request, reply_list):
def get_request(spider, reply_list):
    #global log_info, source, text
    requests = []
    request = []
    response = ''
    speaker = ''
    text = ''
    for r in reply_list:
        if 'Event: Text.TextMessage' not in r and 'Directive: SpeechSynthesizer.Speak' not in r \
                and 'Directive: AudioPlayer.Play' not in r: #and 'Event: SpeechSynthesizer.SpeechStarted' not in r
            continue
        time_start = time.time()
        clicked = True
        try:
            spider.web_driver.find_element(By.XPATH, RE_DIC['log_item_clicked'] % r)
        except selenium.common.exceptions.NoSuchElementException:
            clicked = False
        while time.time() - time_start <= 0.5 * 60 and clicked == False:
            try:
                tmp_element = spider.web_driver.find_element(By.XPATH,
                    RE_DIC['log_item'] % r)
                spider.web_driver.execute_script("arguments[0].click()", tmp_element)
                time.sleep(1)
                clicked = True
                break
            except selenium.common.exceptions.ElementClickInterceptedException:
                print('zzZ---time sleeping 1s for SpeechSynthesizer.SpeechStarted click wrong ')
        if time.time() - time_start > 0.5 * 60:
            #return request, 'time out'
            return requests, 'time out'
        if 'Event: Text.TextMessage' in r:
            #request, text = get_text_message(spider, request)
            text = get_text_message(spider)
        elif 'Directive: SpeechSynthesizer.Speak' in r:
            #request, text = get_speak_info(spider, request)
            res, spe, text = get_speak_info(spider)
            if spe != speaker:
                if response != '':
                    request = [response, speaker]
                    requests.append(request)
                    response = ''
                speaker = spe
            response += res
            
        # elif 'Event: SpeechSynthesizer.SpeechStarted' in r:
        #     request, text = get_started_info(spider, request)
        elif 'Directive: AudioPlayer.Play' in r:
            #request, text = get_play_info(spider, request)
            res, spe, text = get_play_info(spider)
            if spe != speaker:
                if response != '':
                    request = [response, speaker]
                    requests.append(request)
                    response = ''
                speaker = spe
            response += res
    if response != '':
        request = [response, speaker]
        requests.append(request)
        response = ''
    return requests, text

def deal_all_list(go_on, spider, log_list_before, input_string, label):
    if not go_on:
        '''if input_string != 'Stop.' and label != 'nothing update':
            re_open(spider)'''
        if label == 'cookie wrong':
            return [[label, '']]
        return []
    log_list_after = re.findall(RE_DIC['log_list'], spider.web_driver.page_source)
    reply_list = log_list_after[len(log_list_before):]
    try:
        last_element = spider.web_driver.find_element(By.XPATH,
            RE_DIC['log_item'] % reply_list[-1])
        spider.web_driver.execute_script("arguments[0].click()", last_element)
    except selenium.common.exceptions.ElementClickInterceptedException as e:
        print(e)
    request, time_result = get_request(spider, reply_list)
    if time_result != '':
        print('deal response time out')
        return []
    return request

def input_and_response(spider, inpt, FileName, isSkillStart):
    input_string = inpt
    requests = []
    log_list_before = re.findall(RE_DIC['log_list'], spider.web_driver.page_source)
    time_input = time.time()
    while time.time() - time_input < 60:
        try:
            spider.web_driver.find_element(By.CLASS_NAME, 'react-autosuggest__input').send_keys(input_string)
            spider.web_driver.find_element(By.CLASS_NAME, 'react-autosuggest__input').send_keys(Keys.ENTER)
            break
        except selenium.common.exceptions.NoSuchElementException:
            re_open(spider)
    go_on, label = wait_for_all_response_data(spider, log_list_before)
    requests = deal_all_list(go_on, spider, log_list_before, input_string, label)
    if len(requests) == 1 and requests[0][0] == 'cookie wrong':
        spider.deal_with_cookie_wrong()
        return requests
    with open(FileName, "a", encoding='utf-8') as file:
        file.write(input_string)
        file.write("\n")
        if len(requests) != 0:
            for response, speaker in requests:
                if isSkillStart == True and speaker == "Alexa":
                    file.write("<--skill exit-->" + response)
                else:
                    file.write(response)
        file.write("\n")
        file.close()
    return requests

def just_input(spider, input_string):
    spider.web_driver.find_element(By.CLASS_NAME, 'react-autosuggest__input').send_keys(input_string)
    spider.web_driver.find_element(By.CLASS_NAME, 'react-autosuggest__input').send_keys(Keys.ENTER)
    time.sleep(2)

def close_spider(spider):
    driver = spider.web_driver
    driver.close()
    driver.quit()