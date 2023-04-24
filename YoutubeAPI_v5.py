import json, os
import datetime as dt 
import pandas   as pd 

from googletrans               import Translator
from googleapiclient.discovery import build 

class GetYoutubeData:
    def __init__(self, service_name: str = "youtube", api_ver = "v3"):
        """
            서비스명, API 버전 설정. 기본값이 있어 parameter 값 입력 없이 instance변수 생성 가능 
            
            Parameters 
                service_name : string 변수, 서비스명. 기본 값 'youtube'
                api_ver      : string 변수, api 버전. 기존 프로그램은 api version v3 기준으로 작성한 프로그램임에 따라 기타 버전을 입력하면 오류 발생할 수 있음 
        """
        self.service_name = service_name 
        self.api_version  = api_ver

    def base_settings(self, search_keywords: list[str], query_unit: str, channel_name: list[str], channel_id: list[str], api_key: str, timezone: str, output_path: str, start_date: str, end_date: str, max_results: int = 10, ids_for_comment_data: list[str] = None):
        self.search_keywords = search_keywords
        self.query_unit      = query_unit.lower()
        self.channel_name    = [channel_name] if type(channel_name) == str else channel_name 
        self.playlist_ids    = ["UU" + i[2:] for i in channel_id]
        self.api_key         = api_key 
        self.timezone        = timezone 
        self.max_results     = max_results 
        self.comment_ids     = ids_for_comment_data 
        self.reduction_date  = 1 if query_unit == "day" else 30 if query_unit == "month" else None
        self.earliest_date   = start_date
        self.current_date    = str(dt.datetime.now())[0:10] if end_date == None else end_date
        self.output_path     = output_path
        self.changed_tz      = self.timezone.replace("/", "_").lower()

        self.results_list = {      
            "upload_date_utc"       : [], f"upload_date_{self.changed_tz}" : [], 
            "account"               : [], "video_likes"                    : [], 
            "comment_no"            : [], "total_engagements"              : [], 
            "view_count"            : [], "video_title"                    : [], 
            "video_url"             : [], "video_id"                       : [], 
            "shorts_yn"             : [], "video_tags"                     : [], 
            "number_of_video_tags"  : [], "video_htags"                    : [], 
            "number_of_video_htags" : []
        }     

        self.comment_data = {
            "comment_channel_id"  : [], "comment_channel_url" : [],
            "comment_author_name" : [], "comment_date"        : [],
            "text_comment"        : [], "like_count"          : [],
            "replies_count"       : [], "comment_language"    : [],
            "video_id"            : []
        }

        self.youtube_api = build(self.service_name, self.api_version, developerKey = self.api_key)
        self.tl_object   = Translator()

        if (os.path.exists(self.output_path) != True):
            os.makedirs(self.output_path)

    def get_video_ids(self):
        """
            타겟 영상 id를 API로 호출하는 method. 기준일 -30일 범위내 영상별 데이터 추출을 위한 영상 ID를 가져와 self.results_list에 저장. 한 번 API 호출 시 max_results로
            지정한 건수 만큼 데이터를 받는 구조이되, 추출 범위를 초과한 데이터는 가져와도 삭재되는 형태로 프로그램이 동작됨에 따라 max_results 크기 조율 필요 
        """
        def convert_to_utc(time_string: str, hour_difference: int = 9) -> str: 
            time_dict = {
                "year"   : int(time_string[0:4]),
                "month"  : int(time_string[5:7]),
                "day"    : int(time_string[8:10]),
                "hour"   : int(time_string[11:13]),
                "minute" : int(time_string[14:16])
            }

            local_date = str(dt.datetime(**time_dict) + dt.timedelta(hours = hour_difference))

            return local_date
        
        def save_results(response, account: str) -> str:
            """
                channel, 업로드 일자, 계정명, 영상 제목, 영상 url, 영상 식별번호, shorts 여부 데이터 생성하는 method 
                Note: 
                    1. API Documentation내 youtube shorts / 일반 영상 구분자가 없음
                    2. 현재 로직상 영상 제목내 #shorts가 있으면 youtube shorts로 분류 하고있으나, 무조건 #shorts가 있는게 아니므로 오분류할 가능성 존재
            """
            for i in range(0, self.max_results):
                upload_date_utc   = response["items"][i]["snippet"]["publishedAt"].replace("T", " ").replace("Z", "")
                upload_date_local = convert_to_utc(upload_date_utc)

                if upload_date_utc >= self.earliest_date:
                    video_id     = response["items"][i]["snippet"]["resourceId"]["videoId"]
                    account_name = account 
                    video_title  = response["items"][i]["snippet"]["title"]
                    shorts_yn    = "youtube_shorts" if "#shorts" in video_title.lower() else "video"
                    video_url    = f"https://www.youtube.com/watch?v={video_id}"
                    results_list = [upload_date_utc, upload_date_local, account_name, video_title, video_url, video_id, shorts_yn]                
                    keys_list    = ["upload_date_utc", f"upload_date_{self.changed_tz}", "account", "video_title", "video_url", "video_id", "shorts_yn"]

                    for (keys, results) in zip(keys_list, results_list):
                        self.results_list[keys].append(results)
            
            return upload_date_utc
   
        for (account, play_id) in zip(self.channel_name, self.playlist_ids):
            upload_date = self.current_date
            page_token  = None

            while (upload_date >= self.earliest_date):
                response = self.youtube_api.playlistItems().list(
                    playlistId = play_id,
                    part       = "snippet",
                    maxResults = self.max_results,
                    pageToken  = page_token
                ).execute()

                page_token  = response["nextPageToken"]
                upload_date = save_results(response, account)

    def get_video_stats(self):
        """
            영상 좋아요수, 댓글수, engagement 회수 (좋아요 + 댓글수), 조회수 method 
        """
        def get_tags(response_json: dict):
            video_tags = response_json["items"][0]["snippet"]["tags"] if "tags" in response_json["items"][0]["snippet"] else ""
            tag_count  = len(video_tags)
            tag_string = "" 

            if len(video_tags) > 0:
                tag_string = ""

                for tag in video_tags:
                    tag_string += f"TAG_{tag}_" 
        
            return tag_count, (lambda x: x[:-1] if x != "" else x)(tag_string)
        
        def get_hashtags1(response_json: dict):
            description = response_json["items"][0]["snippet"]["description"]
            index_list  = [index for (index, value) in enumerate(description) if value == "#"] 
            tags_string = ""

            for i in index_list:
                description1 = description[i:]
                description1 = description[i:i + description1.index(" ")] if i != index_list[-1]  else description[i:]
                description1 = description1[:description1.index("\n")]    if "\n" in description1 else description1
                tags_string += f"HTAG_{description1}_"

            return len(index_list), tags_string[:-1]

        def get_hashtags2(response_json: dict):
            def parse_tags(x):
                return sum([1 for i in x if x == "#"])

            hashtag_str = ""
            description = response_json["items"][0]["snippet"]["description"]
            tag_count   = 0

            while ("#" in description):
                description1 = description[description.index("#"):]
                description2 = description1[:description1.index("\n")] 
                description  = description[description.index(description2) + len(description2) + 2 :]
                added_value  = [description2] if (parse_tags(description2) == 1) else [i for i in description2.split("#") if i != ""]
                
                for tag in added_value:
                    hashtag_str += f"HTAG_{tag.strip()}_"
                    tag_count   += 1

            return tag_count, hashtag_str[:-1]
        
        for video_id in self.results_list["video_id"]:
            self.response = self.youtube_api.videos().list(
                id   = video_id,
                part = "statistics,snippet"
            ).execute()

            likes       = int(self.response["items"][0]["statistics"]["likeCount"])    if "likeCount"    in self.response["items"][0]["statistics"] else 0
            comments    = int(self.response["items"][0]["statistics"]["commentCount"]) if "commentCount" in self.response["items"][0]["statistics"] else 0
            views       = int(self.response["items"][0]["statistics"]["viewCount"])    if "viewCount"    in self.response["items"][0]["statistics"] else 0
            engagements = likes + comments

            tag_count, tag_string = get_tags(self.response)

            try:
                htag_count, htag_string = get_hashtags1(self.response)
            except Exception:
                htag_count, htag_string = get_hashtags2(self.response)

            keys    = ["video_likes", "comment_no", "total_engagements", "view_count", "video_tags", "number_of_video_tags", "video_htags", "number_of_video_htags"]
            results = [likes, comments, engagements, views, tag_string, tag_count, htag_string.replace("#", ""), htag_count]

            for (key, result) in zip(keys, results):
                self.results_list[key].append(result)        

    def get_youtube_comments(self):
        def parse_json_object(response_json: dict, id: str) -> bool:
            page_token = response_json["nextPageToken"] if "nextPageToken" in response_json else None

            for json_object in response_json["items"]:
                comment_channel_id  = json_object["snippet"]["topLevelComment"]["snippet"]["authorChannelId"]["value"]
                comment_channel_url = json_object["snippet"]["topLevelComment"]["snippet"]["authorChannelUrl"]
                comment_author_name = json_object["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"]
                comment_date        = json_object["snippet"]["topLevelComment"]["snippet"]["publishedAt"]
                text_comment        = json_object["snippet"]["topLevelComment"]["snippet"]["textOriginal"].replace("\n", "")
                like_counts         = json_object["snippet"]["topLevelComment"]["snippet"]["likeCount"]
                replies_count       = json_object["snippet"]["totalReplyCount"]       
                comment_language    = self.tl_object.detect(text_comment).lang
                results_data        = [
                    comment_channel_id, comment_channel_url, comment_author_name, comment_date,
                    text_comment, like_counts, replies_count, comment_language, id
                ]

                for (key, value) in zip(self.comment_data.keys(), results_data):
                    self.comment_data[key].append(value)
    
            return page_token

        for id in self.results_list["video_id"]:
            page_token = None

            while True:
                response_json = gyd.youtube_api.commentThreads().list(
                    videoId   = id, 
                    part      = "snippet,id,replies",
                    pageToken = page_token
                ).execute()
                
                page_token = parse_json_object(response_json, id)

                if (page_token == None):
                    break

    def process_files(self):
        """
            Samsung_YN 구분자 생성 method. 영상 제목, 태그, 해시태그내 삼성 관련 keyword가 있으면 1, 없으면 0
        """
        self.video_stats  = pd.DataFrame(self.results_list)
        self.vid_comments = pd.DataFrame(self.comment_data)

        self.vid_comments["youtube_url"] = "https://www.youtube.com/watch?v=" + self.vid_comments["video_id"]
        self.video_stats.loc[self.video_stats["video_htags"].str.lower().str.contains("shorts"), "shorts_yn"] = "youtube_shorts"
        self.video_stats.loc[self.video_stats["video_tags"].str.lower().str.contains("shorts"), "shorts_yn"]  = "youtube_shorts"
        
        for key in self.search_keywords.keys():
            for words in self.search_keywords[key]:
                for column in ["title", "tags", "htags"]:
                    self.video_stats.loc[self.video_stats[f"video_{column}"].str.lower().str.contains(words.lower()), f"{key}_YN"] = 1
                
            self.video_stats[f"{key}_YN"] = self.video_stats[f"{key}_YN"].fillna(0)                

    def save_files(self, stats_file_name: str, comments_file_name: str) -> None:
        """
            결과 데이터 저장 method 
        """
        self.video_stats.to_excel(os.path.join(self.output_path, stats_file_name.format(self.current_date)), index = False, encoding = "utf-8-sig")
        self.vid_comments.to_excel(os.path.join(self.output_path, comments_file_name.format(self.current_date)), index = False, encoding = "utf-8-sig")
        
if __name__ == "__main__":
    with open("./config/GetDataFromSourcesConfig.json", "r", encoding = "utf-8-sig") as f:
        configDict = json.load(f)

    gyd = GetYoutubeData(**configDict["GetYoutubeData"]["constructor"])
    gyd.base_settings(**configDict["GetYoutubeData"]["base_settings"])
    gyd.get_video_ids()
    gyd.get_video_stats()
    gyd.get_youtube_comments()
    gyd.process_files()
    gyd.save_files(**configDict["GetYoutubeData"]["save_files"])

