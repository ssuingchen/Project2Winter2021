#################################
##### Name:
##### Uniqname:
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key

BASE_URL = "https://www.nps.gov"
CACHE_FILENAME = "cache.json"
CACHE_DICT = {}

CONSUMER_KEY = secrets.CONSUMER_KEY
CONSUMER_SECRET = secrets.CONSUMER_SECRET
MAP_BASE_URL = "http://www.mapquestapi.com/search/v2/radius"

def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close()



def make_request_with_cache(url):
    '''Check the cache for a saved result for this unique_key
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.
   
   Params
   _______
    params: url
    
    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    #TODO Implement function
    
    if url in CACHE_DICT.keys():
        print("Using Cache", url)
        return CACHE_DICT[url]
    else:
        print("Fetching", url)
        response = requests.get(url)
        CACHE_DICT[url] = response.text
        save_cache(CACHE_DICT)
        return CACHE_DICT[url]


def make_request_with_cache_map(url):
    '''Check the cache for a saved result for this unique_key
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.
   
   Params
   _______
    params: url
    
    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    #TODO Implement function
    
    if url in CACHE_DICT.keys():
        print("Using Cache")
        return CACHE_DICT[url]
    else:
        print("Fetching")
        response = requests.get(url)
        CACHE_DICT[url] = response.json()
        save_cache(CACHE_DICT)
        return CACHE_DICT[url]

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category = None, name = None\
                , address = None, zipcode = None, phone = None):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        '''
        return the information of the onject
        '''

        return self.name + " " + "(" + self.category + ")" + ": " + self.address\
         + " " + self.zipcode  

def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    
    soup = BeautifulSoup(make_request_with_cache(BASE_URL), 'html.parser')

    state_url_dict = {}
    all_states_tag = soup.find("div", class_="SearchBar-keywordSearch").find_all("a")
    for state in all_states_tag:
        state_url_dict[state.text.strip().lower()] = BASE_URL+state['href']
    
    return state_url_dict
       

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    soupSite = BeautifulSoup(make_request_with_cache(site_url), 'html.parser')
    site_name = soupSite.find("div", class_="Hero-titleContainer").find("a").text.strip()
    site_category = soupSite.find("div", class_="Hero-titleContainer").find("span", class_="Hero-designation").text.strip()
    site_locality = soupSite.find("div", class_="vcard").find("span", itemprop="addressLocality").text.strip()
    site_region = soupSite.find("div", class_="vcard").find("span", itemprop="addressRegion").text.strip()
    site_zipcode = soupSite.find("div", class_="vcard").find("span", itemprop="postalCode").text.strip()
    site_phone = soupSite.find("div", class_="vcard").find("span", class_="tel").text.strip()
    site_address = site_locality + ", " + site_region
    site_instance = NationalSite(category = site_category, name = site_name\
            , address = site_address, zipcode = site_zipcode, phone = site_phone)

    return site_instance


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    soupState = BeautifulSoup(make_request_with_cache(state_url), 'html.parser')
    state_sites_list = soupState.find("div", id="parkListResultsArea").find_all("li", class_="clearfix")

    #create a list of sites for a state url
    site_instances_list = []
    for state_site in state_sites_list:
        site_url = state_site.find("h3").find("a")
        complete_site_url = BASE_URL + site_url['href']
        
        # create a site instance
        site_instance = get_site_instance(complete_site_url)
        site_instances_list.append(site_instance)

    return site_instances_list


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''

    CACHE_DICT = open_cache()
    site_zipcode = site_object.zipcode
    
    params = {
        "key":CONSUMER_KEY,
        "origin":site_zipcode,
        "radius":10,
        "maxMatches":10,
        "ambiguities":"ignore",
        "outFormat":"json"
    }
    param_strings = []

    for key in params.keys():
        param_strings.append(f'{key}={params[key]}')
    param_strings.sort()
    unique_key = MAP_BASE_URL + '?' +  '&'.join(param_strings)
    
    nearby_sites_dict = make_request_with_cache_map(unique_key) 

    return nearby_sites_dict


def start_app():
    '''
    combine all the functions above and run the interface in terminal
    '''
    
    CACHE_DICT = open_cache()
    # create state url dictionary
    state_url_dict = build_state_url_dict()
    
    while True:

        state = input("Enter a state name (e.g. Michigan / michigan), or 'Exit / exit': ")
        
        while state.isnumeric():
            state = input("[Error] Sorry, that was not a valid input. Enter a state name (e.g. Michigan / michigan), or 'Exit / exit': ")
            
        while state.lower() not in state_url_dict:
            state = input("[Error] Sorry, that was not a valid state name. Enter a complete state name (e.g. Michigan / michigan), or 'Exit / exit': ")
        
        if state.lower() == "exit":
            return

        # get the state url which user asked for
        state_url = state_url_dict[state.lower()]

        # get all the sites instances of the state
        site_instances_list = get_sites_for_state(state_url)

        print("-" * 50)
        print(f"List of national sites in {state}")
        print("-" * 50)

        # print out all the sites in the state
        for i in range(len(site_instances_list)):
            print(f"[{str(i+1)}] {site_instances_list[i].info()}")

        while True:
            detail_num = input(f"Choose the number from 1 to {len(site_instances_list)} for detail search or 'exit' or 'back': ")
            while not detail_num.isnumeric() and detail_num.lower() != "exit" and detail_num.lower() != "back":
                detail_num = input("[Error] Sorry, that was not a valid input. Choose the number for detail search or 'exit' or 'back': ")

            if detail_num.lower() == "exit":
                return
            elif detail_num.lower() == "back":
                break

            while int(detail_num) > len(site_instances_list):
                detail_num = input(f"[Error] Choose the number from 1 to {len(site_instances_list)} or 'exit' or 'back': ")

            nearby_sites_dict = get_nearby_places(site_instances_list[int(detail_num)-1])

            print("-" * 50)
            print(f"Places near {site_instances_list[int(detail_num)-1].name}")
            print("-" * 50)

            for nearby_site in nearby_sites_dict["searchResults"]:
                try:
                    if nearby_site['name'] != "":
                        name = nearby_site['name']
                    else:
                        name = "no name"
                except KeyError:
                    name = "no name"
                try:
                    if nearby_site['category'] != "":
                        category = nearby_site['category']
                    else:
                        category = "no category"
                except KeyError:
                    category = "no category"
                try:
                    if nearby_site["fields"]['address'] != "":
                        address = nearby_site["fields"]['address']
                    else:
                        address = "no address"
                except KeyError:
                    address = "no address"
                try:
                    if nearby_site['fields']['city'] != "":
                        city = nearby_site['fields']['city']
                    else:
                        city = "no city"
                except KeyError:
                    city = "no city"
                print(f"-{name} ({category}): {address}, {city}")

    

if __name__ == "__main__":
    start_app()

    