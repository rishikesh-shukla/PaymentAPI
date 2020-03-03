from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
from paypal import Paypal
import pyjwt
app = Flask(__name__)
api = Api(app)

client =  MongoClient("localhost", 27017)
db = client.MoneyManagementDB
users = db["Users"]

def UserExist(username):
    if users.find({"Username":username}).count() == 0:
        return False
    else:
        return True

class Register(Resource):
    def post(self):
        #Step 1 is to get posted data by the user
        postedData = request.get_json()

        #Get the data
        username = postedData["username"]
        password = postedData["password"] #"123xyz"

        if UserExist(username):
            retJson = {
                'status':301,
                'msg': 'Invalid Username'
            }
            return jsonify(retJson)

        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        #Store username and pw into the database
        users.insert({
            "Username": username,
            "Password": hashed_pw,
            "Own":0,
            "Debt":0
        })

        retJson = {
            "status": 201,
            "msg": "You successfully signed up for the API"
        }
        return jsonify(retJson)

def verifyPw(username, password):
    if not UserExist(username):
        return False

    hashed_pw = users.find({
        "Username":username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode('utf8'), hashed_pw) == hashed_pw:
        return True
    else:
        return False

def cashWithUser(username):
    cash = users.find({
        "Username":username})[0]["Own"]
    return cash

def debtWithUser(username):
    debt = users.find({
        "Username":username
    })[0]["Debt"]
    return debt

def generateReturnDictionary(status, msg):
    retJson = {
        "status": status,
        "msg": msg
    }
    return retJson

def verifyCredentials(username, password):
    if not UserExist(username):
        return generateReturnDictionary(301, "Invalid Username"), True

    correct_pw = verifyPw(username, password)

    if not correct_pw:
        return generateReturnDictionary(302, "Incorrect Password"), True

    return None, False

def updateAccount(username, balance):
    users.update({
        "Username": username
    },{
        "$set":{
            "Own": balance
        }
    })

def updateDebt(username, balance):
    users.update({
        "Username": username
    },{
        "$set":{
            "Debt": balance
        }
    })



class Add(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        money = postedData["amount"]

        retJson, error = verifyCredentials(username, password)
        if error:
            return jsonify(retJson)

        if money<=0:
            return jsonify(generateReturnDictionary(304, "The money amount entered must be greater than 0"))

        cash = cashWithUser(username)
        money-= 1 #Transaction fee
        #Add transaction fee to bank account
        bank_cash = cashWithUser("BANK")
        updateAccount("BANK", bank_cash+1)

        #Add remaining to user
        updateAccount(username, cash+money)

        return jsonify(generateReturnDictionary(200, "Amount Added Successfully to account"))

class Transfer(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        to       = postedData["to"]
        money    = postedData["amount"]


        retJson, error = verifyCredentials(username, password)
        if error:
            return jsonify(retJson)

        cash = cashWithUser(username)
        if cash <= 0:
            return jsonify(generateReturnDictionary(303, "You are out of money, please Add Cash or take a loan"))

        if money<=0:
            return jsonify(generateReturnDictionary(304, "The money amount entered must be greater than 0"))

        if not UserExist(to):
            return jsonify(generateReturnDictionary(301, "Recieved username is invalid"))

        cash_from = cashWithUser(username)
        cash_to   = cashWithUser(to)
        bank_cash = cashWithUser("BANK")

        updateAccount("BANK", bank_cash+1)
        updateAccount(to, cash_to+money-1)
        updateAccount(username, cash_from - money)

        retJson = {
            "status":200,
            "msg": "Amount added successfully to account"
        }
        return jsonify(generateReturnDictionary(200, "Amount added successfully to account"))

class Balance(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        retJson, error = verifyCredentials(username, password)
        if error:
            return jsonify(retJson)

        retJson = users.find({
            "Username": username
        },{
            "Password": 0, #projection
            "_id":0
        })[0]

        return jsonify(retJson)

class Take(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        money    = postedData["amount"]

        retJson, error = verifyCredentials(username, password)
        if error:
            return jsonify(retJson)

        cash = cashWithUser(username)
        debt = debtWithUser(username)
        updateAccount(username, cash+money)
        updateDebt(username, debt + money)

        return jsonify(generateReturnDictionary(200, "Loan Added to Your Account"))

class Pay(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        money    = postedData["amount"]

        retJson, error = verifyCredentials(username, password)
        if error:
            return jsonify(retJson)

        cash = cashWithUser(username)
        if cash >= money:
            print(Paypal.payment())
            
        if cash < money:
            return jsonify(generateReturnDictionary(303, "Not Enough Cash in your account"))

        debt = debtWithUser(username)
        updateAccount(username, cash-money)
        updateDebt(username, debt - money)

        return jsonify(generateReturnDictionary(200, "Amount Paid"))

api.add_resource(Register, '/register')
api.add_resource(Add, '/add')
api.add_resource(Transfer, '/transfer')
api.add_resource(Balance, '/balance')
api.add_resource(Take, '/take')
api.add_resource(Pay, '/pay')
api.add_resource(Payment,'/PS')


if __name__=="__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
