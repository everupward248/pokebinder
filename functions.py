##create functions to be recalled in the main program
import psycopg2.pool
from classes import Binder
import requests
import math
from flask import Flask, render_template, session, redirect
from functools import wraps
from config import config 
import psycopg2
import os
from dotenv import load_dotenv, dotenv_values
import urllib.parse as urlparse

#load the environment variables
load_dotenv()

#establish base URL and API key 
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")



##function for initializing a binder
##prompt user for a binder
def prompt():

    while True: 
        response = input("would you like to create a binder today?[Y/N] ")

        if(response.upper() == 'Y'):
            sheets = int(input("how many sheets? "))
            rows = int(input("how many rows? "))
            columns = int(input("how many columns? "))
            binder = Binder(sheets, rows, columns)

            return binder

        else: 
            print("maybe next time! ")
            
        return
    
#create an empty dictionary to iterate over 
def create_dict(binder):
    inner_keys = ["name", "card number", "set", "price", "cost", "obtained"]
    outer_keys = binder.slots
    master_set = {
        outer_key: {inner_key: None for inner_key in inner_keys}
        for outer_key in range(outer_keys)
    }

    return master_set


#most recent sets
def most_recent(sets):
    length = int(input("What is your length? "))
    # Sort sets by releaseDate in descending order (most recent first)
    data_sorted = sorted(sets, key=lambda x: x['releaseDate'], reverse=True)

    # Get the 5 most recent sets
    recent_sets = data_sorted[:length]

    # Print the 5 most recent sets
    print(f"Top 5 most recent sets:")
    for set_item in recent_sets:
        print(f"{set_item['name']} (ID: {set_item['id']}) - Release Date: {set_item['releaseDate']}")

#headers for authentication
headers = {
    "X-Api-Key": API_KEY
}
#fetch pokemon tcg sets
def fetch_card_sets():
    endpoint ="sets"
    response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)

    if response.status_code == 200:
        data = response.json().get("data", [])
        return data
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

#function to fetch a specific card
def fetch_specific_card(card_id):
    endpoint = "cards"
    base_url = BASE_URL + endpoint
    query_params = {
        "q": f"id:{card_id}"
    }
    
    response = requests.get(base_url, params=query_params, headers=headers)

    if response.status_code == 200:
        card_data = response.json().get("data", [])
        return card_data
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None


#fetch a specific set
def fetch_card(set):
    endpoint = "cards"
    base_url = BASE_URL + endpoint
    query_params = {
        "q": f"set.id:{set}",
    }
    response = requests.get(base_url, params=query_params, headers=headers)

    #check if request was successful
    if response.status_code == 200:
        card_data = response.json().get("data", [])
        return card_data
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None
    
#fetch a specific set
#pokemon tcg api uses pagination, 250 per page
def fetch_cards(set, total):
    #initialize the page and return object
    all_cards = []
    pages = math.ceil(total/250)

    for page in range(1, pages+1):
        endpoint = "cards"
        base_url = BASE_URL + endpoint
        query_params = {
            "q": f"set.id:{set}",
            "page": page
        }
        response = requests.get(base_url, params=query_params, headers=headers)

        #check if request was successful
        if response.status_code == 200:
            card_data = response.json().get("data", [])
            all_cards.extend(card_data)
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return None
    return all_cards


#check if slot is empty
def is_empty(collection):
    boolean = True
    for key in collection.keys():
        if collection[key] != None:
            boolean = False
            break
    if boolean == False:
        return False
    else:
        return True
            

##map cards from JSON onto the binder object
def map_cards(cards, collection):
    ##check if the slot is empty
    for i in range(len(collection)):
        if is_empty(collection[i]):
            place = i
            ##if the slot, is empty, set the slots in the binder equal to the cards in the set
            for place in range(len(cards)):
                card_place = 0
                collection[place]["name"] = cards[card_place]["name"]
                collection[place]["card number"] = cards[card_place]["number"]
                collection[place]["id"] = cards[card_place]["id"]
                collection[place]["prices"] = cards[card_place]["tcgplayer"]
                collection[place]["cost"] = 0
                collection[place]["image"] = cards[card_place]["images"]
                card_place += 1
            return collection
        else:
            pass

#update price

#####Functions for Flask

#ensures certain pages are only accessible to users logged in
def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

#apology rendered when the request is unsuccessful 
def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            #commented out so that spaces can be returned between words in the error message
            #(" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


#merge sort for sorting the api responses
#1. split the array in half, 2. call merge sort on each half to sort each subset recursively
#3. merge the sorted halves into a sorted array
def merge_sort_example(arr):
    if len(arr) > 1:
        left_arr = arr[:len(arr)//2]
        right_arr = arr[len(arr)//2:]

        #recursive call
        merge_sort_example(left_arr)
        merge_sort_example(right_arr)

        #merge
        i = 0 #left_arr index
        j = 0 #right_arr index
        k = 0 #merged array index

        while i < len(left_arr) and j < len(right_arr):
            if left_arr[i] < right_arr[j]:
                arr[k] = left_arr[i]
                i += 1
            else:
                arr[k] = right_arr[j]
                j += 1
            k += 1

        while i < len(left_arr):
            arr[k] = left_arr[i]
            i += 1
            k += 1
        
        while j < len(right_arr):
            arr[k] = right_arr[j]
            j += 1 
            k += 1

######################
#for sorting cards
def merge_sort(arr):
    if len(arr) == 1:
        return arr
    
    mid = len(arr)//2
    left = arr[:mid]
    right = arr[mid:]

    sorted_left = merge_sort(left)
    sorted_right = merge_sort(right)

    return merge(sorted_left, sorted_right)
    
#try merge and merge_sort as 2 functions
def merge(left, right):
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if int(left[i]["card_number"]) < int(right[j]["card_number"]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])

    return result

#searched page sort
def merge_sort_searched(arr):
    if len(arr) == 1:
        return arr
    
    mid = len(arr)//2
    left = arr[:mid]
    right = arr[mid:]

    sorted_left = merge_sort_searched(left)
    sorted_right = merge_sort_searched(right)

    return merge_s(sorted_left, sorted_right)
    
#try merge and merge_sort as 2 functions
def merge_s(left, right):
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if int(left[i]["number"]) < int(right[j]["number"]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])

    return result

#####Database Functions
#function for connecting to the database
def connect_example():
    try:
        connection = None
        params = config()
        print('Connecting to the postgreSQL database...')
        connection = psycopg2.connect(**params)

        #create a cursor
        crsr = connection.cursor()
        print('PostgresSQL database version: ')
        crsr.execute('SELECT version()')
        db_version = crsr.fetchone()
        print(db_version)
        crsr.close()
    except(Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if connection is not None:
            connection.close()
            print('Database connection terminated')
        
#Create connection function db
def connect():
    try:
        connection = None
        #import params from the config file
        params = config()   
        #unpack paramters from ini file
        connection = psycopg2.connect(**params)
        print("connection successful")
        return connection
        
    except(Exception, psycopg2.DatabaseError) as error:
        print(error)
   


#Connection pool
def connection_pool():
    try:

        #user heroku database url
        if 'DATABASE_URL' in os.environ:
            urlparse.uses_netloc.append("postgres")
            db_url = urlparse.urlparse(os.environ["DATABASE_URL"])

        connection_pool = None
        # #import params from the config file
        # params = config()
        #use heroku config
        connection_pool = psycopg2.pool.SimpleConnectionPool(1, 20, user=db_url.username, password=db_url.password, host=db_url.hostname, port=db_url.port, database=db_url.path[1:], sslmode='require')
        print("connection pool active")
        return connection_pool
    except(Exception, psycopg2.DatabaseError) as error:
        print(error)


#################
#password validator

def is_valid_password(password):

    if (len(password) > 5 and len(password) < 15):

        lower_case = False
        upper_case = False
        number = False
        special = False

        for char in password:
            if(char.isdigit()):
                number = True
            if(char.islower()):
                lower_case = True
            if(char.isupper()):
                upper_case = True
            if(not char.isalnum()):
                special = True

        return lower_case and upper_case and number and special
    else:
        return False
    
