from flask import Flask
from flask import redirect, url_for, render_template,request
import json
import sqlite3
import logging


def getTicketsByUserID(user_id):   #JOIN TABLES for more informative data to the user on client side:
    conn = sqlite3.connect(r'C:\Users\orel.briga\Downloads\Project1.db')
    allTickets = []
    ticketsTable = conn.execute(f"SELECT * from Tickets JOIN Flights on \
    (Tickets.flight_id = Flights.flight_id) where user_id = {user_id}")
    logging.debug(f"SELECT * from Tickets JOIN Flights on \
    (Tickets.flight_id = Flights.flight_id) where user_id = {user_id}")
    for row in ticketsTable:
        ticket = {"ticket_id":row[0],"flight_id":row[2],"timestamp":row[4],"origin_county_id":row[6],\
                  "dest_country_id":row[7]}
        allTickets.append(ticket)
    conn.close()
    return allTickets


def getFlights():
    conn = sqlite3.connect(r'C:\Users\orel.briga\Downloads\Project1.db')
    if request.method == 'GET':
        allFlights = []
        flightsTable = conn.execute("SELECT * from Flights")
        logging.debug("SELECT * from Flights")
        for row in flightsTable:
            flight = {"flight_id":row[0],"timestamp":row[1],"remaining_seats":row[2],\
                      "origin_country_id":row[3],"dest_country_id":row[4]}
            allFlights.append(flight)
        conn.close()
        return allFlights


def buyTicket(user_id,flight_id):   #buy ticket of any seats available:
    conn = sqlite3.connect(r'C:\Users\orel.briga\Downloads\Project1.db')
    remaining_seats = 0
    remaining_seatsTable = conn.execute(f'SELECT remaining_seats from Flights where flight_id = {flight_id}')
    logging.debug(f'SELECT remaining_seats from Flights where flight_id = {flight_id}')
    for row in remaining_seatsTable:
        remaining_seats = row[0]
    if remaining_seats > 0:
        conn.execute(f"INSERT INTO Tickets (user_id,flight_id) VALUES ({user_id},{flight_id})")
        remaining_seats -= 1
        conn.execute(f"UPDATE Flights SET remaining_seats = {remaining_seats} WHERE flight_id = {flight_id}")
        conn.commit()
        logging.info(f"INSERT INTO Tickets (user_id,flight_id) VALUES ({user_id},{flight_id})")
        logging.info(f"UPDATE Flights SET remaining_seats = {remaining_seats} WHERE flight_id = {flight_id}")
        conn.close()
        return True
    else:
        logging.error("No remaining tickets for this flight")
        return False


def flightIdList():   # function that stores a list of all existing flight id:
    conn = sqlite3.connect(r'C:\Users\orel.briga\Downloads\Project1.db')
    allFlightIDs = []
    flightIDtable = conn.execute("SELECT flight_id from Flights")
    logging.debug("SELECT flight_id from Flights")
    for flightID in flightIDtable:
        allFlightIDs.append(flightID[0])
    return allFlightIDs


def deleteTicket(user_id,ticket_id):
    try:
        conn = sqlite3.connect(r'C:\Users\orel.briga\Downloads\Project1.db')
        temp = conn.execute(f"SELECT flight_id from Tickets where ticket_id = {ticket_id} AND user_id = {user_id}")
        logging.debug(f"SELECT flight_id from Tickets where ticket_id = {ticket_id} AND user_id = {user_id}")
        for row in temp:
            flight_id = row[0]  # saving flight_id for updataing the remaining seats of this flight
        conn.execute(f"DELETE from Tickets WHERE ticket_id = {ticket_id} AND user_id = {user_id}")
        remaining_seatsTable = conn.execute(f"SELECT remaining_seats from Flights where flight_id = {flight_id}")
        logging.debug(f"SELECT remaining_seats from Flights where flight_id = {flight_id}")
        for row in remaining_seatsTable:
            remaining_seats = row[0]
        remaining_seats += 1
        conn.execute(f"UPDATE Flights SET remaining_seats = {remaining_seats} WHERE flight_id = {flight_id}")
        conn.commit()
        logging.info(f"DELETE from Tickets WHERE ticket_id = {ticket_id} AND user_id = {user_id}")
        logging.info(f"UPDATE Flights SET remaining_seats = {remaining_seats} WHERE flight_id = {flight_id}")
        conn.close
        return True
    except:
        return False


