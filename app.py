from functions import *
import os
from flask import Flask, render_template, session, redirect, flash, request, url_for
from flask_session import Session
from config import config
import requests
import classes
import psycopg2
from psycopg2.extras import execute_batch, execute_values
import os
from dotenv import load_dotenv, dotenv_values
from werkzeug.security import check_password_hash, generate_password_hash

#load variables from .env file
load_dotenv()

#establish base URL and API key
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")


#headers for authentication
headers = {
    "X-Api-Key": API_KEY
}

#create an instance of the Flask class 
app = Flask(__name__)
#get secret key from the environment variable
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

##todo 
#ADD JINJA FILTERS SO THAT JINJA TEMPLATES RECOGNIZE THE FUNCTIONS BEING USED FROM FUNCTIONS

# Configure session to use filesystem (instead of signed cookies)
#Flask-session is primarily designed to be used with permanent sessions
#in a non-permanent session a cookie is stored in the browser and is deleted when the browser or tab is closed (no expiry). Also known as a session cookie or non-persistent cookie.
app.config["SESSION_PERMANENT"] = False
#session information will be stored on disc
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

##todo
##configure the database 

#prevents browser caching of responses, sensitive data returned from the server side will not be cached in the browser
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    
    #render the homepage html file where users land on when accessing the site
    return render_template("index.html")
    #render an apology page using the apology function when there is an issue with the request
    #return apology("TODO")

##create a function which sends a request to the pokemon TCG API based on the input from a user's form
@app.route("/search", methods=["GET", "POST"])
def search():
        """Searches set and returns the images of all cards in a set"""
        #check to see if post request
        if request.method == "POST":
             
             #check to see if user responded with a valid set
             if not request.form.get("search"):
                  return apology("Must input into the search box")
             
             #store the form response as a variable
             set_name = request.form.get("search")
             #utilize fetch set function to make a request to the pokemon tcg api and return the set
             card_sets = fetch_card_sets()
             ##set master set equal to the set chosen and total 
             master_set = {}
             #itertes through all sets in the tcg to determine if the searched set exists
             for set in card_sets: 
                 if(set["name"] == set_name):
                     #set the master set equal to the set searched
                     master_set = set
                    
                     #create request to fetch all cards in the set
                     all_cards = fetch_cards(master_set["id"], master_set["total"])

                     #create for loop to fetch the price of each card and return to jinja template to display under card
                     rarity = ["holofoil", "reverseHolofoil", "normal", "1stEditionHolofoil", "1stEditionNormal"]
                     
                     #create an empty list to store the prices of all the cards
                     prices = [0] * int(master_set["total"])

                     #for loop checks if rarity is present in the card's data and takes the first one and sets the price equal to that rarity's market value
                     for card in range(len(all_cards)):
                        # ##check if these rarities are valid keys for the card
                        for j in range(len(rarity)):
                             try:
                                  prices[card] = all_cards[card]["tcgplayer"]["prices"][rarity[j]]["market"]
                             except:
                                  pass
                     #sort all cards before returning
                     #code below sorts the cards but the prices are incorrect, to map prices before sorting
                     #all_cards = sorted(all_cards, key= lambda d : int(d["number"]))

                     return render_template("searched.html", set_name=master_set["name"], all_cards=all_cards, total=master_set["total"], prices=prices)
                 
                 else:
                      pass
             return apology("Must search a valid set")
        else:
            return render_template("search.html")


#Register route so that users can create an account
@app.route("/register", methods=["GET", "POST"])
def register():
     
     #forget any user id
     session.clear()

     #check if http request was successful
     if request.method == "POST":
          
          #check user form submission
          if not request.form.get("username"):
               return apology("must submit a username", 400)
          
          if not request.form.get("password"):
               return apology("must submit a password", 400)
          
          if not request.form.get("confirm"):
               return apology("must submit a password confirmation", 400)
          
          #check if password and password confirmation match
          if not request.form.get("confirm") == request.form.get("password"):
            return apology("passwords do not match", 400)
          
          #store username
          username = request.form.get("username")
          #hash the password to store in the database
          password = generate_password_hash(request.form.get("password"))

          #use try/except block to check the database if the username already exists and then add the new data
          try:
            connection = connect()
            crsr = connection.cursor()

            #check to see if username already exists
            crsr.execute("SELECT * FROM users WHERE username = %s", (username,))

            rows = crsr.fetchone()

            if rows != None:
                return apology("username already exists", 400)
            
            #use execute method and insert query to add data to the database
            crsr.execute(
                        "INSERT INTO users (username, passphrase) VALUES(%s, %s)", 
                        (username, password)
                        )

            #commit changes before closing
            connection.commit()

            #query the database for the username to store as session id
            print("user created")
            crsr.execute("SELECT * FROM users WHERE username = %s", (username,))
            rows = crsr.fetchone()
           
            #close the cursor and the connection
            crsr.close()
            connection.close()
          except(Exception, psycopg2.DatabaseError) as error:
            print(error) 

          #store the session id
          #the crsr object calls the execute method to get the username of the account just registered and sets it to a tuple 'rows'
          #the first element of the tuple is the user id, set the session to the users id
          session["user_id"] = rows[0]


          #redirect user to the index
          return redirect("/")
                
     else:
          return render_template("register.html")



#create the login page for the application
@app.route("/login", methods=["GET", "POST"])
def login():
    """log user in"""

    #forget user id
    session.clear()

    #check user submitted form
    if request.method == "POST":
        #check that username was submitted 
        if not request.form.get("username"):
            return apology("must provide a username", 400)
        
        #check that password was submitted
        elif not request.form.get("password"):
            return apology("must provid a password", 400)
        
        #query the database for the username
        #execute the database connection with try blocks
        try:
            #create the connection to the database
            connection = connect()
            #create a cursor to iterate through the data table
            crsr = connection.cursor()
            #execute a query to fetch the username
            crsr.execute("SELECT * FROM users WHERE username = %s", (request.form.get("username"),))
            #fetch the user data
            rows = crsr.fetchone()
            #check that the user exists
            if rows == None:
                return apology("username name does not exist", 400)
            if not check_password_hash(rows[2], request.form.get("password")):
                return apology("password incorrect", 400)
            
            #close the cursor and the connection
            crsr.close()
            connection.close()
            
        except(Exception, psycopg2.DatabaseError) as error:
            print(error)

        session["user_id"] = rows[0]

        return redirect("/")
    else:
        # Redirect user to home page
        return render_template("login.html")
    
#Add binder route where users can add binders to their collection
@app.route("/add_binder", methods=["GET", "POST"])
@login_required
def add_binder():
    """User can utilize the provided form to add binders. Upon submission should check how many binders the user has in their collection, if it is 9 then apology should be returned"""
    
    #Check to see if POST request
    if request.method == "POST":

        #check for inputs
        if not request.form.get("name"):
            return apology("Must submit a name.", 400)
        
        #add the form data to the database
        name = request.form.get("name")
        sheets = int(request.form.get("sheets"))
        rows = int(request.form.get("rows"))
        cols = int(request.form.get("cols"))
        pages = int(sheets * 2)
        slots = int(pages * rows * cols)

        session_id = session["user_id"]

        #execute the database connection with try/except block
        try:
            #connect to the db
            connection = connect()
            crsr = connection.cursor()

            #check binder counter in the users table, if it is equal to 9 then return apology
            crsr.execute("SELECT binder FROM users WHERE user_id = %s", (session_id,))
            binder_count = crsr.fetchone()
            #used to print to terminal
            app.logger.info("%s", binder_count)

            #check the binder count in the binder col, if 9 then return an error
            if binder_count == None:
                pass
            else:
                try:
                    if binder_count[0] == 9:
                        return apology("Can only have up to 9 binders in a collection", 400)
                except:
                    pass

            #check if the submitted name already exists in the database
            crsr.execute("SELECT name FROM collection WHERE name = %s AND user_id = %s", (name,session_id,))
            #fetch the user data
            binder_name = crsr.fetchone()
            app.logger.info("%s", binder_name)

            if binder_name == None:
                pass
            else:
                try:
                    if name == binder_name[0]:
                        return apology("Cannot have duplicate binder names in collection", 400)
                except:
                    pass
            
            #use execute method and insert query to add data to the database
            crsr.execute(
                        "INSERT INTO collection (user_id, sheets, pages, binder_rows, binder_columns, slots, name) VALUES(%s, %s, %s, %s, %s, %s, %s)", 
                        (session_id, sheets, pages, rows, cols, slots, name)
                        )

            #commit changes before closing
            connection.commit()

            #close the cursor and the connection
            crsr.close()
            connection.close()
            app.logger.info("connection closed")

        except(Exception, psycopg2.DatabaseError) as error:
            print(error) 

        return render_template("add_binder.html")
    
    else:
        return render_template("add_binder.html")


#Collection route where user can view their collection
@app.route("/collection", methods=["GET", "POST"])
@login_required
def collection():
    #users should land on a page which displays in a 3x3 grid the available binders in their collection
    #there should be buttons underneath the image which allow sets to be added to binders and binders to be deleted
    #total market_value and name should be displayed underneath the binder
    #The binder images should be clickable links which lands on a page showing the contents of the binder
    
    if request.method == "POST":
        #write function to delete the selected binder_id from the database

        #use logger to see if the JSON data is being sent
        binder_id = request.form.get('delete')
        #binder_id = data.get('binder_id')
        app.logger.info("%s", binder_id)

        #the binder id is being transfered so now query the database to delete that from the db
        try:
            #connect to the db
            connection = connect()
            crsr = connection.cursor()

            #delete that binder_id from the collections table
            crsr.execute("DELETE FROM collection WHERE binder_id = %s", (binder_id,))

            #commit changes before closing
            connection.commit()

            #close the cursor and the connection
            crsr.close()
            connection.close()
            #app.logger.info("connection closed", user_data)

        except(Exception, psycopg2.DatabaseError) as error:
            print(error) 

        return redirect(url_for('collection'))
    
    else:
        try:
            #connect to the db
            connection = connect()
            crsr = connection.cursor()

            #query the database to retrieve the user's collection data and then store that data in python variables to passed onto the jinja template
            crsr.execute("SELECT * FROM collection WHERE user_id = %s", (session["user_id"], ))
            #description method takes the columns from the database, combine this with the rows with fetchall to make 
            #a list of dicctionaries to store python variables
            table_cols = [desc[0] for desc in crsr.description] #extract column names
            
            #combine these rows and columns into a list of dictionaries python object
            user_data =[dict(zip(table_cols, row)) for row in crsr.fetchall()]
            #app.logger.info("%s", user_data)

            #close the cursor and the connection
            crsr.close()
            connection.close()
            app.logger.info("connection closed")

        except(Exception, psycopg2.DatabaseError) as error:
            print(error) 

        #now that data is being stored properly in python, extract the relevant values to pass onto jinja
        return render_template("collection.html", user_data=user_data)

    
#route to render html of selected_binders
@app.route("/collection/selected_binder/<int:binder_id>", methods=["GET", "POST"])
@login_required
def selected_binder(binder_id):

    #select all data from the binders table based on the binder_id then fetchall to store as a variable
    #initalizes the user data
    try:
        #connect to the db
        connection = connect()
        crsr = connection.cursor()

        #query the database to retrieve the user's collection data and then store that data in python variables to passed onto the jinja template
        crsr.execute("SELECT * FROM binders WHERE binder_id = %s", (binder_id, ))
        #description method takes the columns from the database, combine this with the rows with fetchall to make 
        #a list of dicctionaries to store python variables
        table_cols = [desc[0] for desc in crsr.description] #extract column names
        
        #combine these rows and columns into a list of dictionaries python object
        user_data =[dict(zip(table_cols, row)) for row in crsr.fetchall()]
        #app.logger.info("%s", user_data)

        #close the cursor and the connection
        crsr.close()
        connection.close()
        app.logger.info("connection closed")

    except(Exception, psycopg2.DatabaseError) as error:
        print(error) 

        

    if request.method == "POST":
        #add behavior to handle added the set to the binder and then for when the user updates obtained
        #check to see if user responded with a valid set

        #sort the data by slot_id
        user_data.sort(key=lambda x: x["slot_id"])

        if request.form.get("set"):
            #store the set name set name as a variable then use this in API call
            search_set = request.form.get("set")
            
            #utilize fetch set function to make a request to the pokemon tcg api and return the set
            card_sets = fetch_card_sets()
            if search_set not in [card["name"]for card in card_sets]:
                return apology("Must search a valid set", 400)
            ##set master set equal to the set chosen and total 
            master_set = {}
            #itertes through all sets in the tcg to determine if the searched set exists
            for set in card_sets: 
                if(set["name"] == search_set):
                    #set the master set equal to the set searched
                    master_set = set
                    #create request to fetch all cards in the set
                    all_cards = fetch_cards(master_set["id"], master_set["total"])
                    break

            #create for loop to fetch the price of each card and return to jinja template to display under card
            rarity = ["holofoil", "reverseHolofoil", "normal", "1stEditionHolofoil", "1stEditionNormal"]
            
            #create an empty list to store the prices of all the cards
            prices = [0] * int(master_set["total"])

            #for loop checks if rarity is present in the card's data and takes the first one and sets the price equal to that rarity's market value
            for card in range(len(all_cards)):
            # ##check if these rarities are valid keys for the card
                for j in range(len(rarity)):
                    try:
                        prices[card] = all_cards[card]["tcgplayer"]["prices"][rarity[j]]["market"]
                    except:
                        pass
            #check if the length of the set exceeds the space in the binder starting from the first null value
            i = 0
            count = 0
            index_start = None
            for user in user_data:
                if user_data[i]["set_name"] == None and index_start == None:
                    #update the index_start to the first slot which is empty
                    index_start = i

                elif user_data[i]["set_name"] != None:
                    #if the slot is not empty, then reset the counter
                    count = 0
                else:
                    count += 1
                    if count > len(all_cards):
                        break
                i += 1
                
            
            # l=len(user_data)
            # print(f"the length of the data is {count}")
            #if the set is larger than the space available in the binder then do not add data to the binder
            #counter is designed to give the amount of consecutive space
            #if there is not enough consecutive space the request will be rejected
            if count < len(all_cards):
                print(count)
                return apology("Sorry not enough space in the binder.", 400)

            #if there is enough space in the binder, add the set to the binder
            #need to create the object which will be used to update the values in the database
            #map the data from all_card and prices on to the user_data object

            #start by updating the set name and id for user_data
            #now map the data from all_cards on to user_data
            #use the index_start as the starting position
            i = 0
            user_data = user_data[index_start:]
            for user in user_data:
                if i < int(len(all_cards)):
                    
                    user["set_name"] = master_set["name"]
                    user["set_id"] = master_set["id"]
                    user["card_name"] = all_cards[i]["name"]
                    user["card_number"] = all_cards[i]["number"]
                    user["card_id"] = all_cards[i]["id"]
                    user["market_value"] = prices[i]
                    user["image_url"] = all_cards[i]["images"]["small"]

                    i += 1
                else:
                    break
            index_end = index_start + i
            #the data from the API fetch is coming back unsorted, sort the data before mogrify to commit data to the table
            #the user data which is passed is already starting from the first position with no set
            #pass the start and end to sort this data 
            
            #user_data = merge_sort(user_data[index_start:index_end])
            
            #see below for a different implementation of sort using builtin python sorted
            #user_data = sorted(user_data[index_start:index_end], key= lambda d : int(d["card_number"]))
            
            #Update the data in binders table where the binder_id and slot_id are equal
            #1. Covert the list of dictionaries to a list of tuples
            user_data = [tuple(d.values()) for d in user_data]
            user_data = [(val[0], val[1], val[2], val[3], val[4], val[5], val[6], val[9],) for val in user_data]
            
            #connect to db
            try:
                #connect to the db
                connection = connect()
                crsr = connection.cursor()

                #use update to update the values based on the query string produced by mogrify
                # stmt = """

                #     UPDATE binders
                #     SET set_name = %s, set_id = %s, card_name = %s, card_number = %s, card_id = %s, image_url = %s
                #     WHERE binder_id = %s AND slot_id = %s;
                
                # """

                #attempt for execute_values
                stmt = """
                    UPDATE binders
                    SET set_name = user_data.set_name, set_id = user_data.set_id, card_name = user_data.card_name, card_number = user_data.card_number, card_id = user_data.card_id, image_url = user_data.image_url FROM (VALUES %s)
                    AS user_data (binder_id, slot_id, set_name, set_id, card_name, card_number, card_id, image_url)
                    WHERE binders.binder_id = user_data.binder_id AND binders.slot_id = user_data.slot_id;
                 """

                #use execute_values to execute the sql and bring in the values from user_data
                execute_values(crsr, stmt, user_data)

                #commit changes before closing
                connection.commit()

                #close the cursor and the connection
                crsr.close()
                connection.close()
                

            except(Exception, psycopg2.DatabaseError) as error:
                print(error) 
                                
        #functionality for adding cards which will update the obtained status and tell the user which page and slot to add the card
        elif request.form.get("addCard"):
            #if the user uses the add card button, then update the obtained status and market value of the card in the db based off of the binder_id 
            #store the user's form data as a variable which will passed into the query
            slot_id = request.form.get("addCard")

            try:    
                connection = connect()
                crsr = connection.cursor()

                #execute the update to the obtained and market value on the binder_id and slot_id
                stmt = """
                UPDATE binders
                SET  
                    obtained = CASE 
                        WHEN obtained = FALSE THEN TRUE  
                        ELSE obtained  
                    END
                WHERE binder_id = %s AND slot_id = %s;
                """

                crsr.execute(stmt, (binder_id, slot_id,))
              
                #commit changes 
                connection.commit()
                #close cursor and the connection
                crsr.close()
                connection.close()
            
            except(Exception, psycopg2.DatabaseError) as error:
                print(error)


            
        else:
            return apology("Must input into the search box")

        return redirect(url_for('selected_binder', binder_id=binder_id))

    else:
        #query the database to retrieve the correct binder data to pass to this render_template
        #query the data based on the binder_id passed as input 
        #select all data from the binders table based on the binder_id then fetchall to store as a variable
        try:
            #connect to the db
            connection = connect()
            crsr = connection.cursor()

            #query the database to retrieve the user's collection data and then store that data in python variables to passed onto the jinja template
            crsr.execute("SELECT * FROM binders WHERE binder_id = %s", (binder_id, ))
            #description method takes the columns from the database, combine this with the rows with fetchall to make 
            #a list of dicctionaries to store python variables
            table_cols = [desc[0] for desc in crsr.description] #extract column names
            
            #combine these rows and columns into a list of dictionaries python object
            user_data =[dict(zip(table_cols, row)) for row in crsr.fetchall()]
            #app.logger.info("%s", user_data)

            #close the cursor and the connection
            crsr.close()
            connection.close()
            app.logger.info("connection closed")

        except(Exception, psycopg2.DatabaseError) as error:
            print(error) 

        #sort the data by slot_id
        #this is to ensure the sets are contiguous
        user_data.sort(key=lambda x: x["slot_id"])

        #disassemble the lists into sublists which are separated by set, merge sort by card_number for each sublist and the merge back together the entire list
        #extract all unique sets in the binder by making a set of the set_name with a set comprehension
        
        #initialize an empty list to append the sets in order
        unique_sets = []
        #create the set of the sets in user_data
        seen = {user["set_name"] for user in user_data}

        for slot in user_data:
            if slot["set_name"] in seen and slot["set_name"] not in unique_sets:
                unique_sets.append(slot["set_name"])
            else:
                pass
        
        #initialize dictionary with empty lists for each set in the binder with a dictionary comprehension
        #makes a key value pair with the set and all its cards
        grouped_data = {set_name : [] for set_name in unique_sets}

        #iterate through the list of dictionaries and append them to the right set list
        #for every slot, if its set_name is in the list of 
        for slot in user_data:
            set_name = slot["set_name"]
            if set_name in grouped_data:
                grouped_data[set_name].append(slot)

        #Now the data is separated by the set so now I need to merge_sort each list by card_number and nothing if None
        #add back the list starting from the first list with the cards in order and return to the template
        merged_list = []

        #wrap in try/except block so that None is only appended after all the sets
        try:
            for val in grouped_data:
                if val != None:
                    set = grouped_data[val]
                    set = merge_sort(set)
                    for card in set:
                        merged_list.append(card)
                else:
                    pass
        except:
            pass
        finally:    
            for val in grouped_data:    
                if val == None:
                    set = grouped_data[val]
                    for card in set:
                        merged_list.append(card)
    
        user_data = merged_list
        

        return render_template("selected_binder.html", binder_id=binder_id, user_data=user_data)

if __name__ == "__main__":
    #server will detect changes and update in real time so will not have to repeatedly rerun
    app.run(debug=True)