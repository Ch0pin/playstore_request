from google_play_scraper import app, permissions
import requests, time
from db import application_database

class Application:
    general_info = {}
    permissions = {}

    def __init__(self,info,perms) -> None:
        self.general_info = info 
        self.permissions = perms




class Printer:

    @classmethod
    def printProgressBar (self,iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
            printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
        """
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
        # Print New Line on Complete
        if iteration == total: 
            print()
    
    def printAppinfo(self,application):
        output = "\n"+"-"*80+"""\nDeveloper Name: {}
Developer Email:{}
Installs: {}
URL: {}""".format(application.general_info["developer"],application.general_info["developerEmail"],application.general_info["minInstalls"],application.general_info["url"])
        print(output)
        return output



class Filter:
    permissions=None
    comments = None
    title = None
    description = None
    package_name=None
    url = None
    minInstalls = None
    score = None
    ratings = None
    number_of_reviews = None
    developer = None
    developerEmail = None
    developerWebsite = None
    developerAddress = None
    privacyPolicy = None
    threshold = 0


class Investigator:
    applicationDatabase = None
    filter = Filter()
    botid = None
    chatid = None 
    filename = None
    dbname = ""

    def __init__(self,filter, botid = '', chatid = '', filename='') -> None:
        self.filter = filter
        self.botid = botid
        self.chatid = chatid
        self.filename = filename
        self.dbname = str(int(time.time()) )+".db"

        self.applicationDatabase = application_database(self.dbname)

    def investigate(self,package_list):
        results = []

        total_apps = len(package_list)
        app_indx = 0

        with open("results.txt",'w') as fobj:
            fobj.write(self.dbname)


        for package_name in package_list:
            
            try:

                app_indx = app_indx+1
                general_info = app(package_name)
                application_permissions = permissions(package_name)
                application = Application(general_info,application_permissions)
                self.applicationDatabase.insert_application(self.prepare_statement_tuple(general_info,application_permissions))

                #print(" {} {}".format(app_indx,total_apps))
                # print("Checking: {}".format(application.general_info["appId"]))
                # Printer.printAppinfo(self,application)
                # print(application.permissions)

                Printer.printProgressBar(app_indx,total_apps)
                with open("progress.txt",'w') as fobj:
                    fobj.write(str(app_indx) + "\n" +str(total_apps))

                if self.filter_result(application):
                    print("Found a much: ")
                    print()
                    #Printer.printAppinfo(self,application)
                    output = Printer.printAppinfo(self,application)
                    results.append(output)
                    if self.botid != '' and self.chatid != '':
                        self.notify_telegram_bot(output,self.botid,self.chatid)
                    if self.filename != '':
                        self.save_result(output+"\n",self.filename)
 

            except Exception as e:
             #   pass
                print(e)

        else:
            print("Investigation finished !")

            return self.dbname






    def save_result(self,result, filename):
        with open(filename,'a') as file_obj:
            file_obj.write(result)

    def notify_telegram_bot(self,msg, botid, chatid):
        requests.post("https://api.telegram.org/bot" +botid+
        "/sendMessage",verify=False,json={"chat_id": chatid,
        "text":msg,"disable_notification":False})


    def prepare_statement_tuple(self,general_info,application_permissions):
        perms = ""
        permdict =  application_permissions.values()
        for listval in permdict:
            perms += '\n'.join(listval)

        return general_info["appId"],general_info["url"], general_info["title"],general_info["description"], general_info["minInstalls"], general_info["realInstalls"],general_info["reviews"],general_info["score"],general_info["ratings"],general_info["developer"],general_info["developerId"], general_info["developerEmail"],general_info["developerWebsite"], general_info["privacyPolicy"],general_info["developerAddress"],general_info["icon"],  general_info["headerImage"], general_info["released"], general_info["updated"], general_info["version"], '||'.join(list(general_info["comments"])) ,perms
        

    def filter_result(self,application):
     

        weight = 0

        if self.filter.comments:
            for query in application.general_info["comments"]:
                q,w = self.filter.comments
                if q.lower() in query.lower():
                    weight += w
                    break

        if self.filter.description:
            q,w = self.filter.description
            if q.lower() in application.general_info["description"].lower():
                 weight += w
        

        if self.filter.title:
            q,w = self.filter.title
            if q.lower() in application.general_info["title"].lower():
                weight += w
        
        if self.filter.developerEmail:
            q,w = self.filter.developerEmail
            if q.lower() in application.general_info["developerEmail"].lower():
                weight += w
        
        if self.filter.developer:
            q,w = self.filter.developer
            if q.lower() in application.general_info["developer"].lower():
                weight += w
        
        if self.filter.minInstalls:
            q,w = self.filter.minInstalls
            if q <= application.general_info["minInstalls"]:
                weight += w

        if self.filter.score:
            q,w = self.filter.score
            if q <= application.general_info["score"]:
                 weight += w

        if self.filter.ratings:
            q,w = self.filter.ratings
            if q <= application.general_info["ratings"]:
                weight += w
        
        if self.filter.number_of_reviews:
            q,w = self.filter.number_of_reviews
            if q <= application.general_info["reviews"]:
                weight += w
    
        if self.filter.privacyPolicy:
            q, w = self.filter.privacyPolicy
            if q.lower() in application.general_info["privacyPolicy"].lower():
                weight += w





        if self.filter.developerWebsite:
            q, w = self.filter.developerWebsite
            if q == "None":
                if not application.general_info["developerWebsite"]:
                    weight += w
            elif q.lower() in application.general_info["developerWebsite"].lower():
                weight += w

        if self.filter.developerAddress == "None":
            q, w = self.filter.developerAddress
            if not application.general_info["developerAddress"]:
                weight += w




        
        appperm = 0

        if self.filter.permissions:
            permnum = len(self.filter.permissions)
            q, w = self.filter.permissions
            perms = permissions(application.general_info["appId"])
            lst = q.split(',')
            #print(lst)
            for val in perms.values():
                for entry in val:
                    for p in lst:
                        if  p.lower() in entry.lower():
                            appperm += 1
            if appperm >= permnum:
                weight += w

        #print('WEIGHT------->>>>{}'.format(weight))

        return weight >= self.filter.threshold

             
