from secrets import token_urlsafe
from random import randint
import settings
import os
def getResponseForm(datas,*selections):
    if not len(selections):
        return tuple(datas[selection] for selection in list(datas.keys()))
    else:
        datas = tuple(datas[selection] for selection in selections)
        if len(selections)  == 1:
            return datas[0]
        return datas

def getResponseFile(files, *selections):
    if not selections:
        return tuple(files.get(key) for key in files.keys())
    
    datas = tuple(files.get(selection) for selection in selections)
    
    if len(selections) == 1:
        return datas[0]
    
    return datas

def checkUserInput(datas, **msgs):
    missing = []
    for key, msg in msgs.items():
        if not datas[key]:
            missing.append(msg)

    return "、".join(missing)

def getRandomVerifyCode(digits):return "".join(list(str(randint(0,9)) for _ in range(digits)))

def getVerifyToken(digits):return token_urlsafe(digits)

# def getProfilePicture(data):
#     file = data.get("profile_pic")

#     if not file or file.filename == "":
#         return None, "default.jpg"
    
#     extension = file.filename.rsplit(".",1)[-1]
#     filename = settings.PROFILE_TEMP_PATH.format()
#     # path = os.path.join(settings.PROFILE_TEMP_PATH, filename)
#     return file, path
# class ProfilePic:
#     def setProfilePicData(self,data,name):
        
        
#     def setExtension(self,extension):
#         self.extension = extension
    
        
# def buildFileName(account,temp=False):
#     if temp:
#         file_name = settings.PROFILE_PIC_PATH
    