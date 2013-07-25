def __init__():
    pass
    
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def emailBlast(subject=None, text=None, html=None, to='brmscc.sec@gmail.com', bcc=None):
    if not text:
        return 'Nothing to send.'
    
    FROM = 'rallymaster@brmscc.org'
    TO = to
    
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = FROM
    msg['To'] = TO
    if bcc:
        msg['Bcc'] = ', '.join(bcc)
    msg.add_header('reply-to', TO)
    # Create the body of the message (a plain-text and an HTML version).

    unsub_html = '<br /><br /><br /><a href="http://www.brmscc.org/email/unsubscribe">Unsubscribe from these emails.</a>'
    unsub_text = '\n\n\nTo unsubscribe go to http://www.brmscc.org/email/unsubscribe to unsubscribe from this mailing list.'

    if html:
        msg_html = html + unsub_html
        plain_text = html + unsub_text
    else:
        plain_text = text + unsub_text
        msg_html = text.replace('\n','<br />') + unsub_html
        

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(plain_text, 'plain')
    msg.attach(part1)
    part2 = MIMEText(msg_html, 'html')
    msg.attach(part2)
    
    # Send the message via local SMTP server.
    s = smtplib.SMTP('localhost')
    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    s.send_message(msg=msg)
    s.quit()
    return 'Message sent.'


