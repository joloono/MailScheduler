"""
The check_time() function checks the current time against each message in the list, and if it's time to send a message,
it reads the message text from the appropriate file and sends it to the recipients.

The main event loop runs the check_time() function once every minute using the time.sleep(60) function call.
This means that the script will only check for message send events once per minute, which should be sufficient
for most use cases.
As before, make sure to replace 'your_email@gmail.com' and 'your_email_password'
with your own email address and password, and make sure that the list recipients contains the email addresses
of the people you want to send the emails to. Also, make sure that you have text files named MessageX.txt
in the same directory as the Python script, and that these files contain the text of the messages you want to send.

"""
import asyncio
import signal
import smtplib
import datetime
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

PERIODIC_CHECKUP_INTERVAL = 30

SMTP_MAIL_SERVER = "mail.your-server.de"

MY_NAME = "MrX"
MY_MAIL = "x@y.com"
MY_PASSWORD = "123456"

RECIPIENTS = [
    "your-mail@x.com",
]

MESSAGES_ON_TIME = [
    ("Message1.txt", "21:28:40"),
    ]


# Set up list of recipients
class MessageOnTime:
    def __init__(self, time: list, filename: str):
        self.sendTime = datetime.datetime.now().replace(hour=int(time[0]), minute=int(time[1]), second=int(time[2]))
        self.messageFile = filename


class ScheduledSender():
    def __init__(self):
        self.messagesSent = list()
        self.messagesOnTime = list(map(lambda x: (x[1].split(":") if len(x[1].split(":")) == 3 else ["0"] * 3, x[0]), MESSAGES_ON_TIME))
        self.messages = [MessageOnTime(i[0], i[1]) for i in self.messagesOnTime]

    # Define function to check if it's time to send an email
    def checkTimeAndSend(self):
        currentTime = datetime.datetime.now()
        for message in self.messages:

            if message.sendTime < message.sendTime + datetime.timedelta(minutes=PERIODIC_CHECKUP_INTERVAL*2):
                server = setupServerConnection()
                try:
                    self.sendMailToAllRecipients(server, message)
                finally:
                    server.quit()  # Close the email server connection

    def sendMailToAllRecipients(self, server, message):
        """ sends message to all RECIPIENTS """
        if message not in self.messagesSent:
            with open(message.messageFile, 'r') as f:
                content = f.readlines()
                for recipient in RECIPIENTS:
                    mailMsg = self.getMessageAsMail(content, MY_MAIL, recipient)
                    server.send_message(mailMsg, MY_MAIL, recipient)
                    print(f'Sent Mail to {recipient} ...')
                    self.messagesSent.append(message)
        else:
           return


    def getMessageAsMail(self, content, senderMail, recipientMail):
        """Get subject and body from input"""
        subject = content[0].split('#')[1].strip()
        body = ''.join(content[1:]).strip()

        # Create MIME message
        msg = MIMEMultipart()
        msg['From'] = f'{MY_NAME} <{senderMail}>'
        msg['To'] = recipientMail
        msg['Subject'] = subject
        msg.attach(MIMEText(body))
        return msg


def setupServerConnection():
    """Set up email server connection"""
    server = smtplib.SMTP(SMTP_MAIL_SERVER)
    server.starttls()
    server.login(MY_MAIL, MY_PASSWORD)
    return server
    

def handleSignals(mailerLoop):
    for signame in {'SIGINT', 'SIGTERM'}:
        mailerLoop.add_signal_handler(getattr(signal, signame), shutdown)

def shutdown():
    """ Cancel all tasks"""
    for task in asyncio.all_tasks():
        task.cancel()


async def sendAndSleep():
    runForever = True
    sender = ScheduledSender()
    while runForever:
        sender.checkTimeAndSend()
        try:
            print(f'Checkin in {PERIODIC_CHECKUP_INTERVAL} seconds again...')
            await asyncio.sleep(PERIODIC_CHECKUP_INTERVAL)
        except asyncio.CancelledError:
            # This coroutine was cancelled, shutdown gracefully
            print("Shutting down mail scheduler program...")
            runForever = False
            return

if __name__ == "__main__":
    """Run task peridically to check if it's time to send an email"""
    mailerLoop = asyncio.get_event_loop()
    handleSignals(mailerLoop)
    mailerLoop.run_until_complete(mailerLoop.create_task(sendAndSleep()))
    mailerLoop.close()
