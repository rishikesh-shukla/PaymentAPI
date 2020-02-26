from flask import Flask, render_template, jsonify, request
import paypalrestsdk
import os
from bson import ObjectId
app = Flask(__name__)
class Paypal(object):
    """docstring for Paypal"""
    def __init__(self, arg):
        super(Paypal, self).__init__()
        self.arg = arg
        
    paypalrestsdk.configure({
      "mode": "sandbox", # sandbox or live
      "client_id": "AVEFNPNY_6BX6KFKXdaNL6fXPoU_PBkEq4KN_TQnTRkVkBgcOYEqjHKMJYOmgy9dPGq_9Rvu6XGmEkp_",
      "client_secret": "EDy-Uv1gsdy91EfJIP-rKELABm-9D9NUUYUSshb5z8HkEqMc2TAirB94l2A1262Rx1obsz1VL_awRPtD" })
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/payment', methods=['POST'])
    def payment():

        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"},
            "redirect_urls": {
                "return_url": "http://localhost:5000/payment/execute",
                "cancel_url": "http://localhost:3000/"},
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": "testitem",
                        "sku": "12345",
                        "price": "50000.00",
                        "currency": "INR",
                        "quantity": 1}]},
                "amount": {
                    "total": "50000.00",
                    "currency": "INR"},
                "description": "This is the payment transaction description."}]})

        if payment.create():
            print('Payment success! '+  payment.id )
            
        else:
            print(payment.error)
        return jsonify({'paymentID' : payment.id})

    @app.route('/execute', methods=['POST'])
    def execute():
        success = False

        payment = paypalrestsdk.Payment.find(request.form['paymentID'])

        if payment.execute({'payer_id' : request.form['payerID']}):
            print('Execute success!')
            success = True
        else:
            print(payment.error)

        return jsonify({'success' : success})

    if __name__ == '__main__':
        app.run(debug=True)
        print(payment())