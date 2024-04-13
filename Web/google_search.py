from googleapiclient.discovery import build

def google_search(search_term, api_key, cse_id, **kwargs):
      service = build("customsearch", "v1", developerKey=api_key)
      res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
      return res['items']

def get_links(search_subject):
      my_api_key = "AIzaSyDhRrLcVm7KwRMgYI_1GSg778zP6IRsM2U"
      my_cse_id = "e4282ee790a254180"
      links = []
      results= google_search(search_subject,my_api_key,my_cse_id,num=3) 
      for result in results:
            links.append(result["link"])
      return links
