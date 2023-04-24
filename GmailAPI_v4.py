import os, pickle, json

from googleapiclient.discovery      import build
from google_auth_oauthlib.flow      import InstalledAppFlow 
from google.auth.transport.requests import Request
from email.mime.text                import MIMEText
from email.mime.multipart           import MIMEMultipart
from email.mime.image               import MIMEImage
from email.mime.audio               import MIMEAudio
from email.mime.base                import MIMEBase
from email                          import encoders
from base64                         import urlsafe_b64decode
from base64                         import urlsafe_b64encode 
from mimetypes                      import guess_type as gmt

class GmailAPI:
    SCOPES = "https://mail.google.com/"

    def __init__(self, secret_json_filename: str, token_filename: str):
        self.secret_json_filename = secret_json_filename
        self.token_filename       = token_filename

    def gmail_settings(self, personal_address: str, destination_address: str, subject_object: str, messages: str = None, attachment_filenames: list[str] = None):
        self.personal_address    = personal_address 
        self.destination_address = destination_address 
        self.subject_object      = subject_object
        self.__message_body      = messages 
        self.filenames_list      = attachment_filenames

        self.type_dict = {
            "text"    : MIMEText, 
            "image"   : MIMEImage, 
            "audio"   : MIMEAudio, 
            "default" : MIMEBase
        }

        with open(self.token_filename, "rb") as token:
            self.__creds = pickle.load(token)
        
        self.gmail_service = build("gmail", "v1", credentials = self.__creds)

    def build_message(self) -> dict:
        def if_else_block(message, filename):
            content_type, encoding = gmt(filename)
            content_type = "application/octet-stream" if content_type is None or encoding is not None else content_type 
            
            main_type, sub_type = content_type.split("/", 1)
            
            fp = open(filename, "rb")
            if main_type in ["image", "audio"]:
                msg = self.type_dict[main_type](fp.read(), _subtype = sub_type)
            elif main_type == "text":
                msg = self.type_dict[main_type](fp.read().decode(), _subtype = sub_type)
            else:
                msg = self.type_dict["default"](main_type, sub_type)
                msg.set_payload(fp.read())

            fp.close()
            filename = filename.split("/")[-1]
            encoders.encode_base64(msg)
            msg.add_header("Content-Disposition", "attachment", filename = filename)
            message.attach(msg)

        message = MIMEText(self.__message_body) if self.filenames_list == None else MIMEMultipart()
        
        message["to"]      = self.destination_address
        message["from"]    = self.personal_address
        message["subject"] = self.subject_object 

        if (self.filenames_list != None):
            message.attach(MIMEText(self.__message_body))

            for attachment in self.filenames_list:
                if_else_block(message, attachment)

        return {"raw" : urlsafe_b64encode(message.as_bytes()).decode()}

    def send_message(self):
        self.send_executor = self.gmail_service.users().messages().send(
            userId = "me", 
            body   = self.build_message()
        )
        
        self.send_executor.execute()

    @property
    def message_body(self):
        return self.__message_body

    @message_body.setter
    def set_message_body(self, message_str):
        self.__message_body = message_str

if __name__ == "__main__":
    with open("./config/gmail_api_config.json", "r") as f:
        config_dict = json.load(f)

    gapi = GmailAPI(**config_dict["GmailAPI"]["constructor"])
    gapi.gmail_settings(**config_dict["GmailAPI"]["gmail_settings"])
    gapi.send_message()


# def gmail_authenticate():
#     creds = None

#     if os.path.exists(r"C:\Users\User\Youtube\config\token.pickle"):
#         with open(r"C:\Users\User\Youtube\config\token.pickle", "rb") as token:
#             creds = pickle.load(token)
    
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(r"C:\Users\User\Youtube\config\client_secret_758651627849-hf13b9bki5pk0v230r30ocqkhvctq95r.apps.googleusercontent.com.json", SCOPES)
#             creds = flow.run_local_server(port=0)
    
#         with open(r"C:\Users\User\Youtube\config\token.pickle", "wb") as token:
#             pickle.dump(creds, token)

#     return build('gmail', 'v1', credentials=creds)

# SCOPES = ["https://mail.google.com/"]

# service_object = gmail_authenticate()
