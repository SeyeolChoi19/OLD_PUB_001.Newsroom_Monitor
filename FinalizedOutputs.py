import pandas   as pd 
import datetime as dt

from SimilarityCheckv3 import SimilarityAnalysis
from GetPageArticles   import GetPageArticles 

class FinalizedOutputs(SimilarityAnalysis):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.similarity_analysis_main()
        
    def similarity_analysis_main(self):
        self.similarity_analysis_settings(**GetPageArticles.config_dict["SimilarityAnalysis"]["similarity_analysis_settings"])
        self.get_tag_similarity_analysis()
        self.add_filters()
        self.save_files(**GetPageArticles.config_dict["SimilarityAnalysis"]["save_files"])

    def output_settings(self):
        self.nlp_result = self.matches_data[self.matches_data["possible_match"] == 1]
        self.smp_data   = self.result_base.copy()
        self.output_df  = self.news_portals.copy()
        self.validation = dict(zip([i for i in self.output_df["url_region"].unique()], [len(self.output_df[self.output_df["url_region"] == i]) for i in self.output_df["url_region"].unique()]))
    
    def merge_outputs(self):
        def inner_func(title: str, date: str):
            data = self.nlp_result[self.nlp_result["translated_title_best_similarity_match"] == title].rename(columns = {"urls" : "nlp_urls", "global_dates" : "nlp_dates"})
            
            data["nlp_yn"]              = "O"
            data["nlp_date_difference"] = (pd.to_datetime(data["nlp_dates"]) - pd.to_datetime(date)).astype(str)
            
            return data

        self.outer_list = []

        for (title, date) in zip(list(self.smp_data["smp_title"]), list(self.smp_data["smp_dates"])):
            inner_data = inner_func(title, date)
            base_data  = pd.merge(self.output_df.astype(str), inner_data.astype(str), how = "left", on = "url_region").astype(str).fillna("-")
            base_data  = base_data[["list_index", "newspage_region", "country", "language", "urls", "url_region", "nlp_yn", "nlp_dates", "nlp_date_difference", "nlp_urls"]]
            self.outer_list.append(base_data.sort_values(by = "list_index"))

    def create_excel_sheets(self):
        def inner_func1(data: pd.core.frame.DataFrame):
            data1 = data.copy()
            value = (lambda x: 8 if len(x) == 62 else (8 + (len(x) - 62)))(data)

            data1["nlp_yn"] = data1["nlp_yn"].replace("-", "X")
            
            for i in range(len(data)):
                data1.loc[i + value] = data.loc[i]

            return data1

        def inner_func2(data1: pd.core.frame.DataFrame, title: str, date: str, url: str, data):
            data1.loc[0] = ["smp_title : "]   + [""] + [""] + [title] + ["" for i in range(len(data.columns) - 4)]
            data1.loc[1] = ["upload_date : "] + [""] + [""] + [date]  + ["" for i in range(len(data.columns) - 4)]
            data1.loc[2] = ["upload_url : "]  + [""] + [""] + [url]   + ["" for i in range(len(data.columns) - 4)]
            data1.loc[3] = ["total_time : "]  + [""] + [""] + [f"{round((dt.datetime.now() - self.start_time).total_seconds() / 60)} minutes"] + ["" for i in range(len(data1.columns) - 4)]

            counter = 4

            for (key, value) in self.validation.items():
                if (len(data[data["url_region"] == key]) != value):
                    data1.loc[counter] = ["ambiguous_region : "] + [""] + [""] + [key] + ["" for i in range(len(data.columns) - 4)]
                    counter += 1
        
            data1.loc[counter]     = ["" for i in range(len(data.columns))]
            data1.loc[counter + 1] = list(data.columns)

            return data1
            
        for (index, data, title, url, date) in zip(list(range(len(self.smp_data))), self.outer_list, list(self.smp_data["smp_title"]), list(self.smp_data["urls"]), list(self.smp_data["smp_dates"])):
            data1 = inner_func1(data)
            data1 = inner_func2(data1, title, date, url, data)
            data1.columns = ["" for i in data1.columns]

            data1.iloc[:, 6]    = data1.iloc[:, 6].replace("nan", "X")
            data1.iloc[:, 7:10] = data1.iloc[:, 7:10].replace("nan", "-") 

            self.outer_list[index] = data1

    def save_output(self, output_filename: str):
        first_page   = self.smp_data[["smp_title", "title_code", "smp_dates", "urls"]]
        sheet_names  = list(first_page["title_code"])
        write_object = pd.ExcelWriter(output_filename.format(str(dt.datetime.now())[0:10]), engine = "xlsxwriter")
        first_page.to_excel(write_object, sheet_name = "General", index = False, encoding = "utf-8-sig")

        for (data, sheet_name) in zip(self.outer_list, sheet_names):
            data = data.drop_duplicates()
            data.to_excel(write_object, sheet_name = sheet_name, index = False, encoding = "utf-8-sig", header = False)
        
        write_object.save()

if __name__ == "__main__":
    fo = FinalizedOutputs(**GetPageArticles.config_dict["NewsRoomMenu"]["constructor"])
    fo.output_settings()
    fo.merge_outputs()
    fo.create_excel_sheets()
    fo.save_output(**GetPageArticles.config_dict["FinalizedOutput"]["save_output"])
