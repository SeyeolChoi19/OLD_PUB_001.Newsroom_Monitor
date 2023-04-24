import json

import datetime as dt

from selenium import webdriver

from selenium.webdriver.common.by      import By 
from selenium.webdriver.support.ui     import WebDriverWait       as wb 
from selenium.webdriver.support        import expected_conditions as ec
from selenium.webdriver.chrome.service import Service

class NewsRoomMenu:
    def __init__(self, driver_path: str, max_wait_time: int):    
        """
            This class is the first part of a larger program that takes information from Samsung's NewsRoom pages in an effort to see whether or not global subsidiaries are uploading content regularly in 
            accordance with Samsung Mobile Press. This class in particular is designed to form the base dataset for the finalized output by extracting text data from Samsung Newsroom's directory page. The
            program itself is very straight forward as it mostly consists of extracting string data from the aforementioned page and processing it into a usable form. The general program relies heavily on
            Selenium as well as BS4 to extract data from websites.
            
            Parameters
                driver_path   : String variable, the full path of the chrome webdriver executable
                max_wait_time : Integer variable, the number of seconds the program should wait before throwing an error when scraping data with selenium
        """
        self.driver_path    = driver_path
        self.max_wait_time = max_wait_time 

    def settings_method(self, region_dict: dict, replace_dict: dict, url_num_dict: dict, url_link: str):
        """
            The basic settings method for the newsroom data extraction portion of the program.

            Parameters
                region_dict  : Dict variable, a dictionary that contains the countries and regions as shown on the Samsung Newsroom directory page
                replace_dict : Dict variable, a dictionary that contains country name related data to be processed later 
                url_num_dict : Dict variable, a dictionary that contains information on the max number of rows for certain javascript tables from which data will be extracted
                url_link     : String variable, the url for the Samsung Newroom Directory page
        """
        self.region_dict  = region_dict
        self.replace_dict = replace_dict
        self.url_num_dict = url_num_dict
        self.url_link     = url_link
        self.start_time   = dt.datetime.now()
        
        self.output_list = {
            "region"   : [], 
            "country"  : None, 
            "language" : None, 
            "urls"     : None
        }

    def driver_settings(self, added_options: list[str] = None):
        """
            The basic settings for the driver object that will be used throughout the entirety of the program. 

            Parameters
                added_options : List[string] variable, a list that contains strings for the chrome driver options to be used in the program. As the parameter has a default value of None, if left unspecified, 
                                only the options implemented in the method will be applied to the webdriver object
        """
        self.options = webdriver.ChromeOptions()
        self.service = Service(self.driver_path)

        options_list = [
            "window-size=1920x1080",        
            "disable-gpu", 
            "start-maximized",
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
        ]

        options_list = options_list + added_options if type(added_options) == list else options_list

        for i in options_list:
            self.options.add_argument(i)

        self.driver = webdriver.Chrome(options = self.options, service = self.service)        

    def check_if_xpath_exists(self, xpath_string: str):
        """
            This method along with the next method, are both used to check whether or not a given element exists on a given page. The only difference between this method and the next 
            one is the By.METHOD used
        """
        try:
            self.driver.find_element(By.XPATH, xpath_string)
            return True 
        except:
            return False

    def check_if_class_name_exists(self, class_name_string: str):
        try:
            self.driver.find_element(By.CLASS_NAME, class_name_string)
            return True
        except:
            return False

    def create_country_list(self):
        """
            This is the method used to form the main output of this class. There are several nested functions inside this method that were implemented to avoid large blocks of unreadable code. The program creates
            the final output for this part of the program through the following 5 steps:
            
                Step 1 - replace_elements: The method first extracts all text from the website in the form of a large string variable, upon which the keywords specified in replace_dict are replaced to make for 
                                           easier processing later

                Step 2 - get_country_and_language_lists: The output string from step 1 is taken into this method upon which the string is broken into small chunks using indexing methods. As country and region
                                                         names are all stuck together, there is a need to identify the indices with which to separate the main string. This is done by identifying capital letters
                                                         in the string, through which their indices become the breakpoints needed to produce the final output. Once the necessary list of breakpoints is formed, 
                                                         the string is then broken into pieces and forwarded to the next method

                Step 3 - country_values: The outputs from the previous method is taken into this method, where the replaced values from step 1 are restored to their original state. Once restored, the results are 
                                         then stored in output_list

                Step 4 - get_region_column: The method takes the output from step 2 to form a region list. Note that the region column specified here is different from the region column used in later parts of the 
                                            program

                Step 5 - get_url_list: This method utilizes url_num_dict's numbers to extract urls for each country from the newsroom page, with results being stored in output_list
        """
        def replace_elements():
            list_string = self.driver.find_element(By.XPATH, "//*[@id='content']/div/div").text
            
            for (key, values) in self.replace_dict.items():
                list_string = list_string.replace(key, values)

            return list_string

        def get_country_and_language_lists(list_string):
            indexList_1   = [1 if i.isupper() == True else 0 for i in list_string]
            indexList_2   = [a for (a, b) in enumerate(indexList_1) if b == 1]
            indexList_3   = [list_string[indexList_2[-1]:] if (i == (len(indexList_2) - 1)) else list_string[indexList_2[i] : indexList_2[i + 1]] for i in range(len(indexList_2))]
            country_list  = []
            language_list = []

            for (a, b) in enumerate(indexList_3):
                if "/" in b:
                    split_list = f"{b}{indexList_3[a + 1]}".replace("\n", "").split(" / ")
                    country_list.append(split_list[0])
                    language_list.append(split_list[1])

            return country_list, language_list

        def country_values(country_languages):
            for i in range(len(country_languages[0])):
                for (key, value) in self.replace_dict.items():
                    if country_languages[0][i] == value:
                        country_languages[0][i] = country_languages[0][i].replace(value, key)

            self.output_list["country"]  = country_languages[0]
            self.output_list["language"] = country_languages[1]

        def get_region_column(country_languages):
            for country in country_languages[0]:
                for (key, value) in self.region_dict.items():
                    if country in value:
                        break
            
                self.output_list["region"].append(key)

        def get_url_list():
            url_list = [self.driver.find_element(By.XPATH, f"//*[@id='content']/div/div/ul[1]/li[1]/a").get_attribute("href")]

            for (key, value) in self.url_num_dict.items():
                for i in range(1, value):
                    url_string = self.driver.find_element(By.XPATH, f"//*[@id='content']/div/div/ul[{key}]/li[{i}]/a").get_attribute("href")
                    url_list.append(url_string)

            self.output_list["urls"] = url_list

        self.driver.get(self.url_link)
        wb(self.driver, self.max_wait_time).until(ec.presence_of_all_elements_located((By.XPATH, "//*[@id='content']")))
        list_string       = replace_elements()
        country_languages = get_country_and_language_lists(list_string)
        get_region_column(country_languages)
        country_values(country_languages)
        get_url_list()
