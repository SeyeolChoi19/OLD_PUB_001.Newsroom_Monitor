import json

import pandas   as pd
import datetime as dt

from NewsRoomMenu import NewsRoomMenu

from selenium.webdriver.common.by   import By 
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui  import WebDriverWait       as wb 
from selenium.webdriver.support     import expected_conditions as ec

class GetBaseData(NewsRoomMenu):
    with open("./config/NewsRoomConfig.json", "r", encoding = "utf-8") as f:
        config_dict = json.load(f)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.news_room_menu_main()

    def news_room_menu_main(self):       
        self.settings_method(**GetBaseData.config_dict["NewsRoomMenu"]["settings_method"])
        self.driver_settings()
        self.create_country_list()

    def base_data_settings(self, press_release_url: str, feature_stories_url: str, page_numbers: int):
        self.press_release_url   = press_release_url 
        self.feature_stories_url = feature_stories_url
        self.page_numbers        = page_numbers
        self.date_limit          = input("Input date in YYYY-MM-DD format")

        self.base_url_data = {
            "title" : [],
            "dates" : [],
            "urls"  : []
        }

    def get_feature_release_urls(self):      
        def append_func(date_string: str):
            if (date_string == self.date_limit):
                self.base_url_data["title"].append(article_title)
                self.base_url_data["dates"].append(date_string)
                self.base_url_data["urls"].append(web_element.get_attribute("href"))

        def page_num_func(page_counter: int, counter_number: int):
            if (counter_number == 10):
                page_counter += 1
            
            return 

        for page_type in [self.press_release_url, self.feature_stories_url]:
            counter_number = 0
            page_counter   = 1
            date_string    = str(dt.datetime.now())[0:10]
            self.driver.get(page_type.format(page_counter))

            while date_string >= self.date_limit:
                wb(self.driver, self.max_wait_time).until(ec.presence_of_all_elements_located((By.XPATH, f"//*[@id='container']/section[2]/div/div[2]/ul/li[9]/div/a[2]")))
                counter_number += 1
                web_element     = self.driver.find_element(By.XPATH, f"//*[@id='container']/section[2]/div/div[2]/ul/li[{counter_number}]/div/a[2]")
                title_string    = web_element.text
                article_title   = title_string[title_string.index("\n") + 1:]
                date_string     = str(pd.to_datetime(title_string[:title_string.index("\n")]))[0:10]
                append_func(date_string)
                page_counter = page_num_func(page_counter, counter_number)
 
    def convert_to_dataframe(self):
        def remove_brackets(string_data):
            if ("]" in string_data):
                string_data = string_data[string_data.index("]") + 2:]

            return string_data.lower()

        self.base_dataframe = pd.DataFrame(self.base_url_data)

        self.base_dataframe["title"] = self.base_dataframe.apply(lambda x: remove_brackets(x["title"]), axis = 1)
