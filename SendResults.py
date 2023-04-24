import json, time, pytz

import datetime as dt

from GmailAPIv2      import *
from GetPageArticles import GetPageArticles
from FinalizedOutput import FinalizedOutputs

def send_email(func):
    def inner_wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        
        gapi = GmailAPI(**response["GmailAPI"]["constructor"])
        gapi.gmail_settings(**response["GmailAPI"]["gmail_settings"])
        gapi.send_message()
    
    return inner_wrapper

@send_email 
def get_outputs(configDict):
    fo = FinalizedOutputs(**GetPageArticles.config_dict["NewsRoomMenu"]["constructor"])
    fo.output_settings()
    fo.merge_outputs()
    fo.create_excel_sheets()
    fo.save_output(**GetPageArticles.config_dict["FinalizedOutput"]["save_output"])

    configDict["GmailAPI"]["gmail_settings"]["attachment_filenames"] = [
        GetPageArticles.config_dict["SimilarityAnalysis"]["save_files"]["output_filename"].format(str(dt.datetime.now())[0:10]),
        GetPageArticles.config_dict["FinalizedOutput"]["save_output"]["output_filename"].format(str(dt.datetime.now())[0:10])
    ]

    return configDict

def run_function(config_dict: dict) -> None:
    try:
        get_outputs(config_dict)
    except:
        run_function(config_dict)

if __name__ == "__main__":
    with open("./config/gmail_api_config.json", "r") as f:
        config_dict = json.load(f)
        
    get_outputs(config_dict)
