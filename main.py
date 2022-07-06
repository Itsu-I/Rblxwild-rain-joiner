from websocket import WebSocketApp
from twocaptcha import TwoCaptcha
from threading import Thread
from constants import *
import termcolor
import requests 
import json
import time 


solver = TwoCaptcha(twocaptcha_key)
class Bot(WebSocketApp):
    def __init__(self):
        self.prize = 3000
        self.joined = 0

        super().__init__(
            url=wss,
            on_open=self.on_open, 
            on_close=self.on_close,
            on_message=self.on_message
        )
        super().run_forever()
    

    def printl(self, text, color="green"):
        print(termcolor.colored(text=text, color=color, attrs=["bold"]))


    def ping(self, ws):
        while True:
            time.sleep(10)
            try: ws.send("3") 
            except: break
            

    def on_open(self, ws):
        ws.send("40")
        time.sleep(1)
        ws.send('42["authentication",{"authToken":"'+str(authentications[0])+'","clientTime":'+str(time.time_ns())+'}]')
        time.sleep(1)
        ws.send('42["chat:subscribe",{"channel":"EN"}]')
        Thread(target=self.ping, args=(ws,)).start()
        Thread(target=self.daily).start()
        self.printl("started", "blue")
    
    

    def on_close(self, ws):
        self.printl("connection closed, retrying;", "blue")
        time.sleep(10)
        super().__init__(
            url=wss,
            on_open=self.on_open, 
            on_close=self.on_close,
            on_message=self.on_message,
            header=[
                "Accept-Encoding: gzip, deflate, br", 
                "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
            ]            
        )
        super().run_forever()


    def on_message(self, ws, message):
        try:
            data = json.loads(message[2:])

            match data[0]:
                case "events:rain:updatePotVariables":
                    self.prize = data[1]["newPrize"]
                
                case "user:updateBalance":
                    balance = data[1]["value"]
                    if balance >= 50:
                        Thread(target=self.withdraw, args=(balance,)).start()

                case "events:rain:setPot":
                    potId = data[1]["newPot"]["id"]
                    Thread(target=self.pots, args=(potId,)).start()
        except: 
            pass



    def pots(self, potId):
        time.sleep(1680)
        self.printl("new rain!", "cyan")

        if self.prize >= 6000:
            self.printl(f"attempting to join rain worth {self.prize}R$ on {len(authentications)} accounts", "magenta")
            for auth in authentications:
                Thread(
                    target=self.join,
                    args=(potId, auth)
                ).start()
        else:
            self.printl(f"{self.prize}R$ rain isnt worth joining :(", "red")



    def join(self, potid, auth):
        try:
            data = solver.hcaptcha(sitekey=site_key, url=site)   

            captcha_answer = data["code"]
            captcha_id = data["captchaId"]


            data = requests.post(api, 
                headers={
                    "User-Agent": agent,
                    "Content-Type": "application/json",
                    "authorization": auth
                }, 
                data=json.dumps({
                    "captchaToken": captcha_answer,
                    "iloveu": True,
                    "potId": int(potid)
                })
            )

            success = data.json()["success"]
            message = data.json()["message"]

            match success:
                case True:
                    self.printl(message)
                    solver.report(captcha_id, True)

                case False:
                    self.printl(message, "red")
                    solver.report(captcha_id, False)

        except Exception as Err:
            self.printl(Err, "red")      


    def withdraw(self, balance): 
        time.sleep(5)
        if balance > 50:
            self.printl("withdrawing", "cyan")

            for auth in authentications:
                data = requests.post(withdraw_url, 
                    headers={
                        "authorization": auth,
                        "content-type": "application/json",
                        "user-agent": agent                   
                    },
                    data=json.dumps({
                        "amount": 50,
                        "dummyAssetId": 0,
                        "instant": False,
                        "type": "WITHDRAW"
                    })
                )

                self.printl(data.json()["message"], "blue") 
                time.sleep(5)


    def daily(self):
        while True:
            try:
                for auth in authentications:
                    req = requests.post(crate_url, 
                        data=json.dumps({"caseId": 37}),
                        headers={
                            "user-agent": agent,
                            "content-type": "application/json",
                            "authorization": auth
                        }
                    )
                    success = req.json()["success"]
                    message = req.json()["message"]

                    if success == True:
                        self.printl(message, "cyan")
                    
                    time.sleep(5)
            except:
                break

Bot()