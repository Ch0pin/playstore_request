from os import walk
import requests, sys, re, urllib3, os
from investigator import Investigator, Printer,Filter
from flask import *
from threading import Thread
import webbrowser
from db import application_database

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://play.google.com/"
DEFAULT_HOST = "localhost"
DEFAULT_PORT = "8081"
keyword = ""
cluster_quantify = 20
threshold_c = 1
package_names = []
results = ""
clusters = []
proxies = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}


app = Flask(__name__,static_url_path='/static')

@app.route('/phase1', methods = ['GET'])
def return_phase1():
    return send_from_directory("static","phase1.html")

@app.route('/js/<path:path>', methods = ['GET'])
def return_js(path):
    return send_from_directory("static/js",path)

@app.route('/css/<path:path>', methods = ['GET'])
def return_css(path):
    return send_from_directory("static/css",path)

@app.route('/index', methods = ['GET'])
def return_index():
    return send_file('./static/index.html')

@app.route('/advancedSearch/<path:path>', methods = ['GET'])
def advanced_search(path):
    return send_from_directory("static",path)

@app.route('/img/<path:path>', methods = ['GET'])
def return_img(path):
    return send_from_directory("static/img",path)

@app.route('/status', methods = ['GET'])
def return_status():
    status = []
    with open("progress.txt",'r') as fobj:
        status = fobj.readlines()
    
    l = int(status[0])/int(status[1]) * 100

    return "You searched for: " + keyword + ", max results: " + str(threshold_c) + ", overal progress: "+ str(l) + "%"

@app.route('/simplequery', methods = ['POST'])
def simple_request_handler():
    global keyword
    global threshold_c
    try:
        with open("results.txt",'w') as f:
            f.write("")

        data = request.form
        filter = Filter()
        filter.threshold=1
        keyword = data['query']
        if data['maxresults'] == '':
            maxResults = 30
        else:
            maxResults = int(data['maxresults'])
        if keyword == '':
            raise Exception("Keyword is required!")
  
        threshold_c = maxResults 

        new_thread = Thread(target=start_search,args=(keyword,maxResults,filter,None,None,None))
        new_thread.start()
            
        return redirect("./phase1?keyword="+keyword+"&maxresults="+str(maxResults), code=302)
                        
    except Exception as e:
        return str(e)

@app.route('/query', methods = ['POST'])
def request_handler():
    global keyword
    global threshold_c
    try:
        with open("results.txt",'w') as f:
            f.write("")

        data = request.form
        filter = Filter()
        telegram_bot_token = data['TELEGRAM_BOT_TOKEN']
        telegram_chat_id = data['chatid']
        maxResults = int(data['maxresults'])
        threshold_c = maxResults
        filter.threshold=int(data['threshold'])
        keyword = data['query']
        filename = data['saveresults']
        if keyword == '':
            raise Exception("Keyword is required!")
        elif filter.threshold == 0:
            raise Exception("Threshold is 0 or invalid")
        elif filter.threshold > 0:
            receivedData = ''
            for entry in list(data)[5:-1]:          #skipping first five form fields
                if (data[entry]).isdigit() and int(data[entry])>0:
                    setattr(filter,entry[:-6],(data[entry[:-6]],int(data[entry])))
                    receivedData  += "\n{} {} {}".format(entry[:-6],data[entry[:-6]],int(data[entry]))+"\n"
            print(receivedData)
            new_thread = Thread(target=start_search,args=(keyword,maxResults,filter,telegram_bot_token,telegram_chat_id,filename))
            new_thread.start()
            
        return redirect("./phase1?query="+keyword+"&maxresults="+str(maxResults), code=302)
                        
    except Exception as e:
        return str(e)

@app.route('/results', methods = ['GET'])
def present_results():
    dbname = request.args.get('query')
    reply = ""
    #prologue
    with open("./static/results.html",'r') as htmlcode:
        for line in htmlcode.readlines():
            if "<!-- CUT HERE -->" in line:
                break
            reply += line
            
    try:
        if dbname == None:
            with open("results.txt",'r') as fobj:
                dbname = fobj.readline()
        if dbname != "":
            applicationDatabase = application_database(dbname)
            res = applicationDatabase.show_results()

            for entry in res:
                i = 0
                reply  += "<tr>"
                for col in entry:
                    i+=1
                    reply += "<td>"
                    reply += """<div style="width: auto; max-width: 200px; height: 50px; overflow: auto; overflow-wrap: break-word;">"""

                    if i== 16 or i==17:
                        reply += "<img src='" + str(col) + "' style='height:80%; width=80%'>"
                    elif i==2:
                        reply += "<a href='" + str(col) + "'>Google Play link</a>"
                    elif i==11:
                        reply += "<a href='https://play.google.com/store/apps/dev?id=" + str(col) + "'>"+str(col)+"</a>" 
                    elif i==13 or i==14:
                        reply += "<a href='" + str(col) + "'>"+str(col)+"</a>"
                    else:
                        reply += str(col)
                    reply += "</div></td>"
                
                reply  += "</tr>"

            with open("./static/results.html",'r') as htmlcode:
                kr = False
                for line in htmlcode.readlines():
                    if "<!-- CUT HERE -->" in line:
                        kr = True
                    if kr==True:
                        reply += line
                    
            return reply
        else:
            packages_so_far = len(package_names)
            print("Total package {} threshold {}".format(packages_so_far, threshold_c))
            return str(packages_so_far/threshold_c *100)
            
                        
    except Exception as e:
        return str(e)

@app.route('/prevqueries', methods = ['GET'])
def prev_queries():
    filenames = next(walk("./"),(None,None,[]))[2]
    result = ""
    for i in filenames:
        if i[-3:] == ".db":
            result += "<a href='http://localhost:8081/results?query="+i+"'>" + i + "</a><button type='button' onclick='deletePreviousQuery(\""+i+"\")'>&nbsp;&nbsp;&nbsp;&nbsp;del</button>"
    return result

@app.route('/delquery', methods = ['POST'])
def delete_previous_query():
    db_to_delete = request.form.get('query')
    try_delete = (db_to_delete.replace('/','')).replace('..','')
    try:
        if os.path.exists(try_delete):
            os.remove(try_delete)
            return "success"
        else:
            return "Invalid query"
    except Exception as e:
        print(e)
        return e


def start_search(keyword,threshold,filter,botid,chatid,filename):
    
    print("[i] PHASE 1: Collecting Package Names...")

    s = requests.Session()
    r = s.get(BASE_URL + "store/search?q="+keyword+"&c=apps",verify=False)

    for package in re.findall(r"\/store\/apps\/details\?id=([a-zA-Z0-9.]*)",r.text):
        package_names.append(package)


    search_by_package_name(s, threshold)
    print("[i] PHASE 1 Finished. Total packages: {}".format(len(package_names)))
    
    if len(package_names) > threshold:
        print("[!] (Warning) Found {} packages, kept first {} (try to increase the threshold).".format(len(package_names),len(package_names[:threshold])))
    print("[i] PHASE 2: Filtering...")

    investigator = Investigator(filter,botid,chatid,filename)
    investigator.investigate(package_names[:threshold])

    sys.exit()
  
def search_by_package_name(s, threshold, start=0, clusterstart=0):
    threshold_c = threshold
    cursz = start

    for package_name in package_names[start:start+cluster_quantify]:
        cursz += 1
   
        Printer.printProgressBar(cursz,start+cluster_quantify,"[Buffering:",'',1,cluster_quantify,'*')
        r = s.get(BASE_URL+"store/apps/details?id="+package_name+"&hl=en&gl=US",verify=False)
        cluster = re.findall(r"\/store\/apps\/collection\/cluster\?gsr=([a-zA-Z0-9.=%:-]*)",r.text)
        if cluster not in cluster:
            clusters.append(cluster)
    #print()
    currsz_1 = len(package_names)
    for cluster in clusters[clusterstart:]:
        if currsz_1 > threshold:
            Printer.printProgressBar(currsz_1,currsz_1)
            break
        Printer.printProgressBar(currsz_1,threshold)
        for c in cluster:
            r = s.get(BASE_URL+"store/apps/collection/cluster?gsr="+c,verify=False)
            for package in re.findall(r"\/store\/apps\/details\?id=([a-zA-Z0-9.]*)",r.text):
                if package not in package_names:
                    currsz_1+=1
                    package_names.append(package)
    print()
    if  len(package_names) < threshold:
        search_by_package_name(s,threshold,cursz+1,len(clusters))





if __name__ == "__main__":



# Initialize parser
    with open("results.txt",'w') as f:
        f.write("")
    webbrowser.open('http://localhost:8081/index')
    app.run(host=DEFAULT_HOST,port=DEFAULT_PORT)

#     parser = argparse.ArgumentParser()
#     parser.add_argument("-k","--keywords",help="key word to search for")
#     parser.add_argument("-t","--threshold",type=int, help="maximum number of packages to collect")
#     parser.add_argument("-s","--server", help="ip to listen to")
#     parser.add_argument("-p","--port", help="port to listen to")
 
# # Read arguments from command line
#     args = parser.parse_args()


#     if args.server:
#         if args.port:
#             # webbrowser.open('file://'+os.path.realpath('index.html'))
#             app.run(host=DEFAULT_HOST,port=DEFAULT_PORT)
#             webbrowser.open('http://localhost:8081/index')
#             #app.run(host=args.server,port=args.port)
            
#         else:
#             print("ip and port is required")
#             sys.exit()

#     elif args.keywords and args.threshold:
#         print("Searching for: % s" % args.keywords)
#         start_search (args.keywords,args.threshold)
        
#     else:
#             print("Server mode or keyword (-k) and threshold (-t) is required !")
#             sys.exit()