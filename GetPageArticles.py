import json

import pandas   as pd 
import datetime as dt

from selenium.webdriver.common.by            import By
from selenium.webdriver.common.keys          import Keys
from selenium.webdriver.support.ui           import WebDriverWait       as wb 
from selenium.webdriver.support              import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains

from GetBaseData import GetBaseData
from googletrans import Translator 

class GetPageArticles(GetBaseData):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_base_data_main()

    def get_base_data_main(self):
        self.base_data_settings(**GetBaseData.config_dict["GetBaseData"]["base_data_settings"])
        self.get_feature_release_urls()
        self.convert_to_dataframe()

    def base_settings(self, switch_dict: dict, special_switch: dict, logic_switch: dict, parse_dict: dict, article_limit: int = 10, us_limit: int = 10):
        self.switch_dict    = switch_dict
        self.special_switch = special_switch
        self.logic_switch   = logic_switch
        self.parse_dict     = parse_dict
        self.article_limit  = article_limit
        self.us_limit       = us_limit

        self.urls_list = {
            "title"                  : [],
            "dates"                  : [],
            "urls"                   : [],
            "press_corporate_string" : []
        }

        self.switch_functions = {
            "logic_1" : self.logic_1_method,
            "logic_2" : self.logic_2_method,
            "logic_3" : self.logic_3_method
        }
    
    def logic_1_method(self, url_string: str, press_corporate_string: str):
        def inner_while_loop(new_number: int) -> int:
            wb(self.driver, self.max_wait_time).until(ec.presence_of_all_elements_located((By.XPATH, f"//*[@id='ae-skip-to-content']/div[3]/ul/li[{number}]/div[1]/ul/li[{upper_limit - 1}]/div/div/a/div/div[2]/h3[2]")))

            for i in range(lower_limit, upper_limit):
                self.urls_list["title"].append(self.driver.find_element(By.XPATH, f"//*[@id='ae-skip-to-content']/div[3]/ul/li[{number}]/div[1]/ul/li[{i}]/div/div/a/div/div[2]/h3[2]").text)
                self.urls_list["dates"].append(self.driver.find_element(By.XPATH, f"//*[@id='ae-skip-to-content']/div[3]/ul/li[{number}]/div[1]/ul/li[{i}]/div/div/a/div/div[2]/p").text)
                self.urls_list["urls"].append(self.driver.find_element(By.XPATH, f"//*[@id='ae-skip-to-content']/div[3]/ul/li[{number}]/div[1]/ul/li[{i}]/div/div/a").get_attribute("href"))
                self.urls_list["press_corporate_string"].append(None)

                new_number  += 1

                if (new_number == self.us_limit):
                    break
            
            return new_number

        for number in range(1, 4):
            new_number  = 0
            lower_limit = 1
            upper_limit = 10

            self.driver.get(f"https://news.samsung.com/us/")
            wb(self.driver, self.max_wait_time).until(ec.presence_of_all_elements_located((By.XPATH, f"//*[@id='ae-skip-to-content']/div[3]/div/div/ul/li[{number}]/a")))
            self.driver.find_element(By.XPATH, f"//*[@id='ae-skip-to-content']/div[3]/div/div/ul/li[{number}]/a").click()

            while (new_number < self.us_limit):
                new_number = inner_while_loop(new_number)
                self.driver.find_element(By.XPATH, f"//*[@id='ae-skip-to-content']/div[3]/ul/li[{number}]/div[2]/button").click()

                lower_limit += 9
                upper_limit += 9
    # logic_1
    def logic_2_method(self, url_string: str, press_corporate_string: str):
        def inside_loop_func(items_num: int, counter: int):
            for i in range(1, items_num + 1):
                true_num = 1 if "/pl/" in url_string or "/cl/" in url_string else 2
                self.urls_list["title"].append(self.driver.find_element(By.XPATH, f"/html/body/div[{true_num}]/div[2]/div/div[1]/div/ul/li[{i}]/div/a/span").text)
                self.urls_list["dates"].append(self.driver.find_element(By.XPATH, f"/html/body/div[{true_num}]/div[2]/div/div[1]/div/ul/li[{i}]/div/div/span").text)
                self.urls_list["urls"].append(self.driver.find_element(By.XPATH, f"/html/body/div[{true_num}]/div[2]/div/div[1]/div/ul/li[{i}]/div/a").get_attribute("href"))
                self.urls_list["press_corporate_string"].append(press_corporate_string)

                counter += 1

                if (counter == self.article_limit):
                    break

            return counter
            
        counter = 0

        for number in range(1, 6):
            self.driver.get(url_string.format(number))
            wb(self.driver, self.max_wait_time).until(ec.presence_of_all_elements_located((By.XPATH, "//*[@id='template_item']/div/div/span")))
            items_num = len(self.driver.find_elements(By.XPATH, "//*[@id='template_item']/div/div/span"))
            counter   = inside_loop_func(items_num, counter)

            if (counter == self.article_limit):
                break
    # def logic_2
    def logic_3_method(self, url_string: str, press_corporate_string: str):
        def inside_loop_func(number_of_articles_on_screen: int, counter):
            for elem in range(1, number_of_articles_on_screen + 1):
                title       = self.driver.find_element(By.XPATH, f"//*[@id='content']/div/ul/li[{elem}]/a/div[2]/div/span[1]").text
                upload_date = self.driver.find_element(By.XPATH, f"//*[@id='content']/div/ul/li[{elem}]/a/div[2]/div/span[2]").text
                article_url = self.driver.find_element(By.XPATH, f"//*[@id='content']/div/ul/li[{elem}]/a").get_attribute("href")
                                                                    
                if (title in self.logic_switch["logic_3"]["title_names"]):
                    title       = self.driver.find_element(By.XPATH, f"//*[@id='content']/div/ul/li[{elem}]/a/div[2]/div/span[2]").text
                    upload_date = self.driver.find_element(By.XPATH, f"//*[@id='content']/div/ul/li[{elem}]/a/div[2]/div/span[3]").text

                self.urls_list["title"].append(title)
                self.urls_list["dates"].append(upload_date)
                self.urls_list["urls"].append(article_url)
                self.urls_list["press_corporate_string"].append(press_corporate_string)
  
                counter += 1
                
                if (counter == self.article_limit):
                    break

            return counter
                
        counter = 0

        for num in range(1, 20):
            self.driver.get(url_string.format(num))
            wb(self.driver, self.max_wait_time).until(ec.presence_of_all_elements_located((By.XPATH, "//*[@id='content']")))
            article_num = len(self.driver.find_elements(By.CLASS_NAME, "thumb_wrap"))
            counter     = inside_loop_func(article_num, counter)

            if (counter == self.article_limit):
                break

    def get_article_urls(self):
        string_lambda = lambda x: "US" if x == "us" else "KR" if x == "kr" else "MX" if x == "mx" else "Other"
        logic_lambda  = lambda x: "logic_1" if x in self.logic_switch["logic_1"] else "logic_2" if x in self.logic_switch["logic_2"] else "logic_3"
        distinct_urls = list(set(self.output_list["urls"]))

        for press_corporate_string in ["products", "corporate", "press-resources"]:
            for url in distinct_urls:
                logic_trigger = url.split("/")[-2]
                logic_string  = string_lambda(logic_trigger)
                url_extension = self.switch_dict[press_corporate_string][logic_string]
                extended_url  = f"{url}{url_extension}/page/" + "{}"
                self.switch_functions[logic_lambda(logic_trigger)](extended_url, press_corporate_string)
    
    def get_insight_urls(self):
        string_lambda = lambda x: "latin_mena" if x in ["latin", "mena"] else "ph_sg_cz" if x in ["sg", "cz", "ph"] else "it"
        logic_lambda  = lambda x: "logic_1" if x in self.logic_switch["logic_1"] else "logic_2" if x in self.logic_switch["logic_2"] else "logic_3"
        
        for region in ["latin", "mena", "sg", "cz", "ph", "it"]:
            if (region not in ["mena", "latin"]):
                url_extension = self.special_switch[string_lambda(region)].format(region)
                extended_url  = f"{url_extension}/page/" + "{}"
                self.switch_functions[logic_lambda(region)](extended_url, "other_pages")
            else:
                base_url = f"https://news.samsung.com/{region}/country/page/"

                for country in self.special_switch[string_lambda(region)][region]:
                    extended_url = base_url + "{}?cd=" + country
                    self.switch_functions[logic_lambda(region)](extended_url, "other_pages")

    def parse_dates(self):
        def remove_brackets(string_data):
            if (("]" in string_data) | ("】" in string_data)):
                index_val   = string_data.index("]") + 2 if "]" in string_data else string_data.index("】") + 2
                string_data = string_data[index_val:]

            return string_data.lower()

        def parse_us(df: pd.core.frame.DataFrame):
            df = df[df["region"] == "us"].drop_duplicates(subset = ["title", "dates", "urls"])
            
            df["dates"] = "20" + df["dates"].str.split("-").str[2].astype(str) + "-" + df["dates"].str.split("-").str[0].astype(str).str.zfill(2) + "-" + df["dates"].str.split("-").str[1].astype(str).str.zfill(2)

            return df

        translator_object = Translator()

        self.df = pd.DataFrame(self.urls_list)

        self.df["region"] = self.df["urls"].str.split("/").str[3]
        self.df["dates"]  = self.df["dates"].str.replace("/", "-").str.replace(".", "-")
        
        df_1 = self.df[self.df["region"].isin(self.parse_dict["dd-mm-yyyy"])]
        df_2 = self.df[self.df["region"].isin(self.parse_dict["dd-mmm-yy"])]
        df_3 = self.df[self.df["region"] == "mena"]

        df_1["dates"] = df_1["dates"].str[-4:] + "-" + df_1["dates"].str[3:5] + "-" + df_1["dates"].str[:2]
        df_2["dates"] = pd.to_datetime(df_2["dates"]).astype(str)
        df_3["dates"] = pd.to_datetime(df_3["dates"]).astype(str)
           
        self.df_1          = pd.concat([parse_us(self.df), self.df[self.df["region"] == "kr"], df_1, df_2, df_3], ignore_index = True).reset_index(drop = True)
        self.complete_data = self.df_1.drop_duplicates(subset = ["title", "region"])
        self.complete_data = self.complete_data[self.complete_data["dates"] >= str(pd.to_datetime(self.date_limit) - dt.timedelta(1))[0:10]]
        
        self.complete_data["title"]                   = self.complete_data.apply(lambda x: remove_brackets(x["title"]), axis = 1)
        self.complete_data["translated_global_title"] = self.complete_data.apply(lambda x: translator_object.translate(x["title"]).text, axis = 1)

        self.urls_list = dict(zip([i for i in self.complete_data.columns], [list(self.complete_data[i]) for i in self.complete_data.columns]))
