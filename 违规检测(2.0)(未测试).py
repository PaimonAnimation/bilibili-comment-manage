# coding=utf-8
import time
import random
from selenium.webdriver.common.by import By
from selenium import webdriver
from datetime import datetime


def get_element(driver, locator, timeout=30):
    for _ in range(timeout):
        try:
            elements = driver.find_elements(*locator)
            return elements
        except:
            time.sleep(0.5)
    return []


def clean_comments(driver, video_url, violation_words, user_violation_count):
    driver.get(video_url)
    time.sleep(5)  # 等待页面加载

    # 展开所有评论
    expand_all_comments = get_element(driver, (By.XPATH, "//span[text()='展开全部评论']/.."))
    if expand_all_comments:
        expand_all_comments[0].click()
        time.sleep(2)

    # 获取所有评论
    comment_blocks = get_element(driver, (By.CSS_SELECTOR, ".comment-item"))
    new_violations = False

    for comment_block in comment_blocks:
        try:
            # 获取评论内容
            comment_content = comment_block.find_element(By.CSS_SELECTOR, ".text").text
            # 获取用户 UID
            user_uid = comment_block.find_element(By.CSS_SELECTOR, ".name a").get_attribute("href").split("/")[-1]

            # 检查是否包含违规词
            has_violation = any(word in comment_content for word in violation_words)
            if has_violation:
                # 增加用户的违规计数
                user_violation_count[user_uid] = user_violation_count.get(user_uid, 0) + 1

                # 点击删除按钮
                delete_btn = comment_block.find_element(By.CSS_SELECTOR, ".delete-btn")
                driver.execute_script("arguments[0].scrollIntoView();", delete_btn)
                delete_btn.click()
                time.sleep(2)

                # 确认删除
                confirm_btn = get_element(driver, (By.CSS_SELECTOR, ".v muit-dialog [text()='确认']"))
                if confirm_btn:
                    confirm_btn[0].click()
                    time.sleep(2)
                    new_violations = True

                # 检查是否需要拉黑用户
                if user_violation_count[user_uid] >= 3:
                    # 拉黑用户
                    blacklist_user(driver, user_uid)
        except:
            print("评论结构发生变化，请检查元素定位器！")

    if new_violations:
        print("已删除违规评论！")


def blacklist_user(driver, user_uid):
    # 这里需要实现拉黑用户的逻辑
    # 假设拉黑用户需要进入用户的个人页面，然后点击拉黑按钮
    driver.get(f"https://space.bilibili.com/{user_uid}/")
    time.sleep(5)

    # 找到拉黑按钮并点击
    blacklist_btn = get_element(driver, (By.XPATH, "//button[text()='拉黑用户']"))
    if blacklist_btn:
        driver.execute_script("arguments[0].click();", blacklist_btn)
        time.sleep(2)

        # 确认拉黑
        confirm_btn = get_element(driver, (By.CSS_SELECTOR, ".van-dialog__confirm"))
        if confirm_btn:
            driver.execute_script("arguments[0].click();", confirm_btn)
            time.sleep(2)
            print(f"已拉黑用户 UID: {user_uid}")


def auto_monitor_comments(driver, video_urls, violation_words):
    user_violation_count = {}
    failure_counter = 0

    while True:
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"{current_time} - 正在轮询评论区")

        try:
            for video_url in video_urls:
                clean_comments(driver, video_url, violation_words, user_violation_count)
        except Exception as e:
            failure_counter += 1
            print(f"发生错误: {e}, 连续失败次数: {failure_counter}")
            if failure_counter >= 3:
                print("连续失败三次，程序稍后重试...")
                time.sleep(300)  # 5分钟后重试
                failure_counter = 0
        else:
            failure_counter = 0

        # 轮询间隔：随机 2-5 分钟
        sleep_time = random.randint(120, 300)
        print(f"下一轮询时间: {datetime.now() + datetime.timedelta(seconds=sleep_time)}")
        time.sleep(sleep_time)


# 示例调用
if __name__ == "__main__":
    options = webdriver.EdgeOptions()
    options.add_argument('--user-data-dir=C:\\Users\\用户名\\AppData\\Local\\Microsoft\\Edge\\User Data\\Profile 1')
    driver = webdriver.Edge(options=options, executable_path="C:\\Users\\用户名\\Desktop\\msedgedriver.exe")

    violation_words = ["敏感词1", "敏感词2", "敏感词3"]  # 替换为实际的违规词
    video_urls = ["https://www.bilibili.com/video/BVxxxxxxxx"]  # 替换为需要监控的视频链接

    try:
        auto_monitor_comments(driver, video_urls, violation_words)
    except KeyboardInterrupt:
        driver.quit()