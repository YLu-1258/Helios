import requests
import lxml.etree
import json



def getSongs(url):
    results = []
    def getIDs(url):
        raw = requests.get(url).text
        js = lxml.etree.HTML(raw).findall('.//body/script')
        for i in js:
            if "ytInitialData" in str(i.text):
                data = json.loads(i.text[20:-1])
                break
        json_object = json.dumps(data, indent = 4)
        return json_object

    def build_list(a_dict):
        try:
            if "https://www.youtube.com/watch?v="+a_dict['videoId'] not in results:
                results.append("https://www.youtube.com/watch?v="+a_dict['videoId'])
        except KeyError:
            pass
        return a_dict

    json.loads(getIDs(url), object_hook=build_list)
    
    return results
