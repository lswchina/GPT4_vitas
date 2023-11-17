from Spider import Spider

for id in range(1, 20):
    if len(id) == 1:
        config_path = '../config/config00' + id + '.ini'
    else:
        config_path = '../config/config0' + id + '.ini'
    cookie_dir = "../cookie/console_cookie7_" + str(id) + ".pkl"
    spider = Spider(config_path, cookie_dir, False)
    spider.web_driver.close()
    spider.web_driver.quit()