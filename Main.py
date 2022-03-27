from flask import Flask
from flask import redirect, url_for, render_template,request
import json
import sqlite3
import logging
import functions   #side functions file, for client side

logging.basicConfig(filename="output.log",level='DEBUG',format='%(asctime)s  %(levelname)s  %(message)s ')

app = Flask(__name__)

#global variables:
user_id = 0
password = 'null'
fullName = 'null'
id_number = 'null'

@app.route('/')
def home_page():
    return render_template('HomePage.html')


@app.route('/invalidIDnumber')
def invalidIDnumber():    #invalid ID number upon registration
    logging.error('Invalid_ID_number')
    return render_template('Invalid_ID_number.html')


@app.route('/registrationSuccess')
def after_registration():
    logging.info('SignUp_Successfully')
    return render_template('SignUp_Successfully.html')


@app.route('/registrationError')
def registration_error():    #ID number already exists in the system
    logging.error('Registered_ID_ERROR')
    return render_template('Registered_ID_ERROR.html')


@app.route('/login', methods=['POST'])
def loginUser():
    global user_id,fullName,id_number
    userList = getUsers()      #storing all users in a list
    password = request.form['pwd']
    id_number = request.form['id']
    for user in userList:
        if user["password"] == password and user["real_id"] == id_number:  #checks if user exist,save the following values:
            user_id = user["id_AI"]
            fullName = user["full_name"]
            logging.debug('login successfully')
            return redirect(url_for('account'))     #redirect to the account page
    logging.error('incorrect login')
    return render_template('incorrect_login.html')


@app.route('/myAccount',methods=['GET','POST','DELETE'])
def account():
    global user_id,fullName,id_number
    if request.method == 'GET':
        allTickets = functions.getTicketsByUserID(user_id)  #storing all the user tickets into list for display
        allFlights = functions.getFlights()   ##storing all existing flights into list for display
        return render_template('AccountPage.html',name=fullName,ID=id_number,\
                               lstTickets=allTickets,lstFlights=allFlights)

    elif request.method == 'POST':
        flight_id = request.form["flight_id"]
        if int(flight_id) not in functions.flightIdList():  #validtion for chosing an existing flight id
            logging.error('Flight ID does not exist!')
            return render_template('FlightNotExist.html')
        elif functions.buyTicket(user_id,flight_id):
            return render_template('AfterBuyingTicket.html')  # ticket ordered successfully
        else:
            return render_template('NoRemainingTickets.html')


@app.route('/myAccount/deleteTicket',methods=['POST'])
def deleteTicketFromAccount():
    global user_id
    if request.method == 'POST':
        ticket_id = request.form["ticket_id"]
        if functions.deleteTicket(user_id,ticket_id):
            logging.error("ticket was deleted from your booking succesfully.")
            return render_template('AfterTicketDelete.html')
        else:
            logging.error("Ticket ID does not exist")
            return render_template('TicketIDnotExist.html')


@app.route('/users', methods=['GET'])
def getUsers():
    conn = sqlite3.connect(r'C:\Users\orel.briga\Downloads\Project1.db')
    allUsers = []
    usersTable = conn.execute("SELECT * from Users")
    logging.debug("SELECT * from Users")
    for row in usersTable:
        user = {"id_AI":row[0],"full_name":row[1],"password":row[2],"real_id":row[3]}
        allUsers.append(user)
    conn.close()
    if request.content_type == 'application/json':   # for getting Users via Postman
        return json.dumps(allUsers)
    else:                                            # for calling the function in the code
        return allUsers


@app.route('/users', methods=['POST'])
def addUser():
    if request.method == 'POST':
        conn = sqlite3.connect(r'C:\Users\orel.briga\Downloads\Project1.db')
        if request.content_type == 'application/json':      # getting registration data from json
            newUser = request.get_json()
            full_name = newUser["full_name"]
            password = newUser["password"]
            id_number = newUser["real_id"]
        else:                                               # getting registration data from html
            full_name = request.form['new_name']
            password = request.form['new_pwd']
            id_number = request.form['new_id']

        if not id_number.isdigit() or len(id_number) != 9:   # validation for ID Number input
            return redirect(url_for('invalidIDnumber'))

        idNumberList = conn.execute("SELECT real_id FROM Users")  # checking if user exist already
        logging.debug("SELECT real_id FROM Users")
        for id in idNumberList:
            if id[0] == id_number:
                return redirect(url_for('registration_error'))   # ID number already in the system

        conn.execute(f'INSERT INTO Users ("full_name","password","real_id") \
        VALUES (\"{full_name}\",\"{password}\",\"{id_number}\")')
        conn.commit()
        logging.info(f'INSERT INTO Users ("full_name","password","real_id") \
                VALUES (\"{full_name}\",\"{password}\",\"{id_number}\")')
        conn.close()
        return redirect(url_for('after_registration'))


@app.route('/users/<int:id>', methods=['GET','DELETE','PUT'])
def userById(id):
    conn = sqlite3.connect(r'C:\Users\orel.briga\Downloads\Project1.db')
    if request.method=='GET':
        userTable = conn.execute(f"SELECT * FROM Users where id_AI = {id}")
        logging.debug(f"SELECT * FROM Users where id_AI = {id}")
        for row in userTable:
            user = {"id_AI": row[0], "full_name": row[1], "password": row[2], "real_id": row[3]}
            conn.close()
            return json.dumps(user)

    elif request.method=='DELETE':
        conn.execute(f"DELETE from Users where id_AI = {id}")
        conn.commit()
        logging.info(f"DELETE from Users where id_AI = {id}")
        conn.close()
        return f'User-{id} was deleted successfully'

    elif request.method=='PUT':
        try:
            editedUser = request.get_json()
            fullName = editedUser['full_name']
            password = editedUser['password']
            id_number = editedUser['real_id']
            conn.execute(f"UPDATE Users SET password = \"{password}\", full_name = \"{fullName}\",\
            real_id = \"{id_number}\" WHERE id_AI = {id}")
            conn.commit()
            logging.info(f"UPDATE Users SET password = \"{password}\", full_name = \"{fullName}\",\
            real_id = \"{id_number}\" WHERE id_AI = {id}")
            conn.close()
            return f'Changes to User-{id} were saved successfully'

        except: # scenario for trying to update value for UNIQUE column when the value already exist in a different row
            logging.error("ID Number is a UNIQUE field and the value exist on different user")
            return 'PUT request has failed, choose a valid ID number'


@app.route('/countries', methods=['GET','POST'])
def add_getCountires():
    conn = sqlite3.connect(r'C:\Users\orel.briga\Downloads\Project1.db')
    allCountires = []
    if request.method == 'GET':
        countriesTable = conn.execute("SELECT * from Countries")
        logging.debug("SELECT * from Countries")
        for row in countriesTable:
            country = {"code_AI":row[0],"name":row[1]}
            allCountires.append(country)
        return json.dumps(allCountires)

    elif request.method == 'POST':
        try:
            newCountry = request.get_json()
            countryName = newCountry['name']
            conn.execute(f'INSERT INTO Countries ("name") VALUES (\"{countryName}\")')
            conn.commit()
            logging.info(f'INSERT INTO Countries ("name") VALUES (\"{countryName}\")')
            conn.close()
            return f'Country {countryName} was inserted successfully into the Countries table'

        except:   ## scenario for trying to insert a value in a UNIQUE column when the value already exist in a different row
            logging.error("Country name is a UNIQUE field and the value exist on different country")
            return 'The Country is already defined in the countries table'



@app.route('/countries/<int:id>', methods=['GET','DELETE','PUT'])
def countryById(id):
    conn = sqlite3.connect(r'C:\Users\orel.briga\Downloads\Project1.db')
    if request.method=='GET':
        countriesTable = conn.execute(f"SELECT * FROM Countries where code_AI = {id}")
        logging.debug(f"SELECT * FROM Countries where code_AI = {id}")
        for row in countriesTable:
            country = {"code_AI": row[0], "name": row[1]}
        conn.close()
        return json.dumps(country)

    elif request.method=='DELETE':
        temp = conn.execute(f"SELECT name from Countries where code_AI = {id}")
        logging.debug(f"SELECT name from Countries where code_AI = {id}")
        for row in temp:
            countryName = row[0]
        conn.execute(f"DELETE from Countries where code_AI ={id}")
        conn.commit()
        logging.info(f"DELETE from Countries where code_AI ={id}")
        conn.close()
        return f'Country {countryName} was deleted from the system'

    elif request.method=='PUT':
        try:
            editedCountry = request.get_json()
            countryName = editedCountry['name']
            conn.execute(f"UPDATE Countries SET name = \"{countryName}\" WHERE code_AI = {id}")
            conn.commit()
            logging.info(f"UPDATE Countries SET name = \"{countryName}\" WHERE code_AI = {id}")
            conn.close()
            return f'Changes to Country-{id} were saved successfully'

        except:# scenario for trying to update a UNIQUE column when the value already exist in a different row
            logging.error("Country name is a UNIQUE field and the value exist on different country")
            return 'The Country is already defined in the countries table'

@app.route('/tickets')
def getAllTickets():  # of all users
    allTickets = []
    conn = sqlite3.connect(r'C:\Users\orel.briga\Downloads\Project1.db')
    ticketsTable = conn.execute("SELECT * from Tickets")
    logging.debug("SELECT * from Tickets")
    for row in ticketsTable:
        ticket = {"ticket_id":row[0],"user_id":row[1],"flight_id":row[2]}
        allTickets.append(ticket)
    if request.content_type == 'application/json':
        return json.dumps(allTickets)
    else:
        logging.error('NOT AUTHORIZED')   # preventing from client side (WEB) to access all tickets data.
        return 'NOT AUTHORIZED'


@app.route('/users/<int:user_id>/tickets', methods=['GET','POST'])
def ticketsById(user_id):
    conn = sqlite3.connect(r'C:\Users\orel.briga\Downloads\Project1.db')
    allTickets = []
    if request.method == 'GET':
        ticketsTable = conn.execute(f"SELECT * from Tickets where user_id = {user_id}")
        logging.debug(f"SELECT * from Tickets where user_id = {user_id}")
        for row in ticketsTable:
            ticket = {"ticket_id":row[0],"user_id":row[1],"flight_id":row[2]}
            allTickets.append(ticket)
        conn.close()
        return json.dumps(allTickets)

    if request.method == 'POST':
        remaining_seats = 0  # initial value
        newTicket = request.get_json()
        flight_id = newTicket["flight_id"]
        remaining_seatsTable = conn.execute(f'SELECT remaining_seats from Flights where flight_id = {flight_id}')
        logging.debug(f'SELECT remaining_seats from Flights where flight_id = {flight_id}')
        for row in remaining_seatsTable:
            remaining_seats = row[0]   # storing the correct reamining seats of this flight
        if remaining_seats > 0:
            # add new ticket to the user and decrease the remaining seats by one:
            conn.execute(f"INSERT INTO Tickets (user_id,flight_id) VALUES ({user_id},{flight_id})")
            remaining_seats -= 1
            conn.execute(f"UPDATE Flights SET remaining_seats = {remaining_seats} WHERE flight_id = {flight_id}")
            conn.commit()
            logging.info(f"INSERT INTO Tickets (user_id,flight_id) VALUES ({user_id},{flight_id})")
            logging.info(f"UPDATE Flights SET remaining_seats = {remaining_seats} WHERE flight_id = {flight_id}")
            conn.close()
            return f'Your ticket was purchased successfully, remaining tickets for this flight: {remaining_seats}'
        else:
            return 'There are no remaining tickets for this flight'


@app.route('/users/<int:user_id>/tickets/<int:ticket_id>', methods=['GET','DELETE'])
def ticketById(user_id,ticket_id):
    conn = sqlite3.connect(r'C:\Users\orel.briga\Downloads\Project1.db')
    if request.method == 'GET':
        ticketTable = conn.execute(f"SELECT * from Tickets where ticket_id = {ticket_id}")
        logging.debug(f"SELECT * from Tickets where ticket_id = {ticket_id}")
        for row in ticketTable:
            ticket = {"ticket_id": row[0], "user_id": row[1], "flight_id": row[2]}
        conn.close()
        return json.dumps(ticket)

    if request.method == 'DELETE':
        temp = conn.execute(f"SELECT flight_id from Tickets where ticket_id = {ticket_id} AND user_id = {user_id}")
        logging.debug(f"SELECT flight_id from Tickets where ticket_id = {ticket_id} AND user_id = {user_id}")
        for row in temp:
            flight_id = row[0]   #saving flight_id for updating the remaining seats of this flight
        conn.execute(f"DELETE from Tickets WHERE ticket_id = {ticket_id} AND user_id = {user_id}")
        remaining_seatsTable = conn.execute(f"SELECT remaining_seats from Flights where flight_id = {flight_id}")
        logging.debug((f"SELECT remaining_seats from Flights where flight_id = {flight_id}"))
        for row in remaining_seatsTable:
            remaining_seats = row[0]
        remaining_seats += 1
        # after ticket delete, increase the remaining seats by one:
        conn.execute(f"UPDATE Flights SET remaining_seats = {remaining_seats} WHERE flight_id = {flight_id}")
        conn.commit()
        logging.info(f"DELETE from Tickets WHERE ticket_id = {ticket_id} AND user_id = {user_id}")
        logging.info(f"UPDATE Flights SET remaining_seats = {remaining_seats} WHERE flight_id = {flight_id}")
        return f'Ticket #{ticket_id} was deleted from your booking.'


@app.route('/flights', methods=['GET', 'POST'])
def get_add_Flights():
    conn = sqlite3.connect(r'C:\Users\orel.briga\Downloads\Project1.db')
    if request.method == 'GET':
        allFlights = []
        flightsTable = conn.execute("SELECT * from Flights")
        logging.debug("SELECT * from Flights")
        for row in flightsTable:
            flight = {"flight_id":row[0],"timestamp":row[1],"remaining_seats":row[2],\
                      "origin_country_id":row[3],"dest_country_id":row[4]}
            allFlights.append(flight)
        return json.dumps(allFlights)

    elif request.method == 'POST':
        newFlight = request.get_json()
        timestamp = newFlight["timestamp"]
        remaining_seats = newFlight["remaining_seats"]
        originCountryId = newFlight["origin_country_id"]
        destCountryId = newFlight["dest_country_id"]
        conn.execute(f'INSERT into Flights (timestamp,remaining_seats,origin_country_id,dest_country_id) \
        VALUES (\"{timestamp}\",{remaining_seats},{originCountryId},{destCountryId})')
        conn.commit()
        logging.info(f'INSERT into Flights (timestamp,remaining_seats,origin_country_id,dest_country_id) \
        VALUES (\"{timestamp}\",{remaining_seats},{originCountryId},{destCountryId})')
        conn.close()
        return f'New flight was added to the table successfully'


@app.route('/flights/<int:id>', methods=['GET','DELETE','PUT'])
def flightById(id):
    conn = sqlite3.connect(r'C:\Users\orel.briga\Downloads\Project1.db')
    if request.method=='GET':
        flightTable = conn.execute(f"SELECT * FROM Flights where flight_id = {id}")
        logging.debug(f"SELECT * FROM Flights where flight_id = {id}")
        for row in flightTable:
            flight = {"flight_id": row[0], "timestamp": row[1], "remaining_seats": row[2], \
                      "origin_country_id": row[3], "dest_country_id": row[4]}
            conn.close()
            return json.dumps(flight)

    elif request.method=='DELETE':
        conn.execute(f"DELETE from Flights where flight_id = {id}")
        conn.commit()
        logging.info(f"DELETE from Flights where flight_id = {id}")
        conn.close()
        return f'Flight-{id} was deleted from the system'

    elif request.method=='PUT':
        flightTable = conn.execute(f"SELECT * FROM Flights where flight_id = {id}")
        logging.debug(f"SELECT * FROM Flights where flight_id = {id}")
        for row in flightTable:
            flight = {"flight_id":row[0],"timestamp":row[1],"remaining_seats":row[2],\
                      "origin_country_id":row[3],"dest_country_id":row[4]}

        timestamp = flight["timestamp"]
        remaining_seats = flight["remaining_seats"]
        originCountryId = flight["origin_country_id"]
        destCountryId = flight["dest_country_id"]
        editedFlight = request.get_json()
        for key in editedFlight:     # a loop that checks if PUT requset includes all keys,
                                     # if not - send UPADTE to DB with the existing values.
            if key == "timestamp":
                timestamp = editedFlight["timestamp"]
                continue
            elif key == "remaining_seats":
                remaining_seats = editedFlight["remaining_seats"]
                continue
            elif key == "origin_country_id":
                originCountryId = editedFlight["origin_country_id"]
                continue
            elif key == "dest_country_id":
                destCountryId = editedFlight["dest_country_id"]
                continue

        conn.execute(f"UPDATE Flights SET timestamp = \"{timestamp}\", remaining_seats = {remaining_seats},\
        origin_country_id = {originCountryId}, dest_country_id = {destCountryId} WHERE flight_id = {id}")
        conn.commit()
        logging.info(f"UPDATE Flights SET timestamp = \"{timestamp}\", remaining_seats = {remaining_seats},\
        origin_country_id = {originCountryId}, dest_country_id = {destCountryId} WHERE flight_id = {id}")
        conn.close()
        return f'Changes to Flight-{id} were saved successfully'


app.run()

