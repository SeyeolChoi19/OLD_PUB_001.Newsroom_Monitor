import torch, six, pytz

import pandas   as pd 
import numpy    as np 
import datetime as dt

from sentence_transformers import SentenceTransformer 
from sentence_transformers import util 
from GetPageArticles       import GetPageArticles
from fuzzywuzzy            import fuzz 
from fuzzywuzzy            import process

class SimilarityAnalysis(GetPageArticles):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_page_articles_main()

    def get_page_articles_main(self):
        self.base_settings(**GetPageArticles.config_dict["GetPageArticles"]["base_settings"])
        self.get_insight_urls()
        self.get_article_urls()
        self.parse_dates()

    def similarity_analysis_settings(self, model_string: str, filters_by_countries: dict, filter_var1: str = "translated_title_best_similarity_score", filter_var2: str = "translated_title_best_token_score"):
        self.filters_by_countries = filters_by_countries
        self.model_string         = model_string
        self.filter_var1          = filter_var1
        self.filter_var2          = filter_var2
        self.base_dataframe       = pd.DataFrame(self.base_url_data)
        self.nlp_model_object     = SentenceTransformer(self.model_string)
        self.base_data_titles     = list(self.base_dataframe["title"])
        self.base_data_urls       = list(self.base_dataframe["urls"])
        self.base_date_values     = list(self.base_dataframe["dates"])
        self.model_corpus_data    = self.nlp_model_object.encode(self.base_data_titles, convert_to_tensor = True, normalize_embeddings = True)
        
        self.base_dataframe = self.base_dataframe.rename(columns = {"title" : "smp_title", "dates" : "smp_dates"})
        self.complete_data  = self.complete_data.rename(columns = {"title" : "global_title", "dates" : "global_dates"})
      
    def get_tag_similarity_analysis(self):   
        def get_match_score(global_string: str) -> pd.Series([str, str, str, float, int]): 
            def remove_brackets(string_data):
                if ("]" in string_data):
                    string_data = string_data[string_data.index("]") + 2:]

                return string_data.lower()

            query_embedding = self.nlp_model_object.encode(remove_brackets(global_string), convert_to_tensor = True, normalize_embeddings = True)
            cosine_scores   = util.semantic_search(query_embedding, self.model_corpus_data, score_function = util.dot_score)[0]
            best_score      = cosine_scores[0]["score"]
            best_string     = self.base_data_titles[cosine_scores[0]["corpus_id"]]
            token_score     = fuzz.token_set_ratio(remove_brackets(best_string), remove_brackets(global_string))
            best_date       = self.base_date_values[cosine_scores[0]["corpus_id"]]
            best_url        = self.base_data_urls[cosine_scores[0]["corpus_id"]]

            return pd.Series([best_string, best_date, best_url, best_score, token_score])

        self.complete_data[["untranslated_title_best_similarity_match", "untranslated_title_best_similarity_date", "untranslated_title_best_similarity_url", "untranslated_title_best_similarity_score", "untranslated_title_best_score"]] = self.complete_data.apply(lambda x: get_match_score(x["global_title"]), axis = 1)
        self.complete_data[["translated_title_best_similarity_match", "translated_title_best_similarity_date", "translated_title_best_similarity_url", "translated_title_best_similarity_score", "translated_title_best_token_score"]]     = self.complete_data.apply(lambda x: get_match_score(x["translated_global_title"]), axis = 1)

    def add_filters(self):
        def date_differences():
            data_table = self.complete_data.copy()
            date_cols  = [i for i in data_table.columns if "date" in i and "dates" not in i]

            for col in date_cols:
                data_table[f"{col}_difference"] = pd.to_datetime(data_table["global_dates"]) - pd.to_datetime(data_table[col])
                
            df = data_table[["global_title", "global_dates", "region", "urls", "translated_global_title"] + [i for i in data_table.columns if "best" in i]]

            return df

        def identify_matches(df: pd.core.frame.DataFrame):
            new_lists = []

            for (key, value) in self.filters_by_countries.items():
                temp_data = df[df["region"].isin(value["countries"])]

                if (len(temp_data) > 0):
                    temp_data["index_col"] = temp_data["translated_title_best_similarity_date_difference"].astype(str).str.index(" ")
                    temp_data["date_diff"] = temp_data.apply(lambda x: int(str(x["translated_title_best_similarity_date_difference"])[:x["index_col"]]), axis = 1)

                    temp_data.loc[(temp_data[self.filter_var1] >= value["thresholds"][0]) & (temp_data[self.filter_var2] >= value["thresholds"][1]) & (temp_data["date_diff"] >= -1), "possible_match"] = 1
                    temp_data["possible_match"] = temp_data["possible_match"].fillna(0)
                    new_lists.append(temp_data.drop(columns = ["date_diff", "index_col"]))

            return pd.concat(new_lists).reset_index(drop = True)

        self.result_data = identify_matches(date_differences())    
        
    def save_files(self, output_filename: str):
        def modify_output():
            df = pd.DataFrame(self.output_list)
            df = df.rename(columns = {"region" : "newspage_region"})

            df["url_region"] = df['urls'].str.split("/").str[3]
            df["list_index"] = list(range(1, len(df) + 1))

            return df

        def get_title_codes():
            new_list     = []
            base_outputs = self.base_dataframe.copy()
  
            for i in base_outputs["smp_dates"].unique():
                temp_data = base_outputs[base_outputs["smp_dates"] == i]
                temp_data["title_code"] = [f"{i.replace('-', '')}_{str(j).zfill(4)}" for j in range(1, len(temp_data) + 1)]
                new_list.append(temp_data)

            return pd.concat(new_list).reset_index(drop = True)

        writer_object  = pd.ExcelWriter(output_filename.format(str(dt.datetime.now(pytz.timezone('Asia/Seoul')))[:10]), "xlsxwriter")

        self.news_portals = modify_output()
        self.result_base  = get_title_codes()[["smp_title"] + ["title_code"] + [i for i in self.base_dataframe.columns if "smp_title" not in i and "article_tags" not in i]]
        self.matches_data = self.result_data.copy().rename(columns = {"region" : "url_region"})

        for (data, filename) in zip([self.news_portals, self.result_base, self.matches_data], ["Global_Portal_Urls", "SMP_Articles", "Global_Matches"]):
            data.to_excel(writer_object, sheet_name = filename, index = False, encoding = "utf-8-sig")

        writer_object.save()

if __name__ == "__main__":
    sa = SimilarityAnalysis(**GetPageArticles.config_dict["NewsRoomMenu"]["constructor"])
    sa.similarity_analysis_settings(**GetPageArticles.config_dict["SimilarityAnalysis"]["similarity_analysis_settings"])
    sa.get_tag_similarity_analysis()
    sa.add_filters()
    sa.save_files(**GetPageArticles.config_dict["SimilarityAnalysis"]["save_files"])
