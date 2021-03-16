import os
import threading
from os import path
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError, ConnectionError
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText


class AlertSmsEmailNotifier:
    def __init__(self):
        self.alarm_email_to_list = []  # to email address
        self.alarm_email_cc_list = []  # cc email address
        self.alarm_email_bcc_list = []  # bcc email address
        self.alarm_mobile_list = []  # mobile number list
        self.sms_sns_client = None
        self.email_ses_client = None
        self.email_template = None

        self.__initialise_aws_clients()
        self.email_sender = "email sender address"
        self.sms_sender_id = "sms sender ID"
        self.email_subject = "email subject"
        email_template_file = 'path to email template'
        if path.exists(email_template_file):
            with open(email_template_file) as file:
                self.email_template = file.read()

    def __initialise_aws_clients(self):
        # Create an SNS client
        self.sms_sns_client = boto3.client(
            "sns",
            aws_access_key_id="YOUR ACCES KEY",
            aws_secret_access_key="OUR SECRET KEY",
            region_name="us-east-1"
        )
        self.email_ses_client = boto3.client(
            "ses",
            aws_access_key_id="OUR ACCES KEY",
            aws_secret_access_key="OUR SECRET KEY",
            region_name="us-east-1"
        )

    def send_alert_sms(self):
        # Send your sms message.
        sms_message = "sample text sm"
        for mobile_num in self.alarm_mobile_list:
            if len(mobile_num) != 0:
                try:
                    self.sms_sns_client.publish(
                        PhoneNumber=mobile_num,
                        Message=sms_message,
                        MessageAttributes={
                            'AWS.SNS.SMS.SenderID': {'DataType': 'String', 'StringValue': self.sms_sender_id},
                            'AWS.SNS.SMS.SMSType': {'DataType': 'String', 'StringValue': 'Transactional'}}
                    )
                except ClientError as e:
                    print(e.response['Error']['Message'])
                except EndpointConnectionError as exp:
                    print(exp)
                except ConnectionError as exp:
                    print(exp)
                except:
                    print("Done")
                else:
                    pass

    def send_alert_email(self, alert_attach_file):

        # not process if list empty
        if len(self.alarm_email_to_list):

            # The email body for recipients with non-HTML email clients.
            email_body_text = "email text body if html format not supported"

            # The HTML body of the email.
            email_body_html = "default html body "
            if self.email_template is not None:
                email_body_html = self.email_template  # load html contents and replace with your changes

            # The character encoding for the email.
            email_charset = "UTF-8"
            email_msg = MIMEMultipart('mixed')
            # Add subject, from and to lines.
            email_msg['Subject'] = self.email_subject
            email_msg['From'] = self.email_sender
            email_msg['To'] = ', '.join(self.alarm_email_to_list)
            email_msg['Cc'] = ', '.join([self.alarm_email_cc_list])
            email_msg['Bcc'] = ', '.join([self.alarm_email_bcc_list])

            email_msg_body = MIMEMultipart('alternative')
            textpart = MIMEText(email_body_text.encode(email_charset), 'plain', email_charset)
            htmlpart = MIMEText(email_body_html.encode(email_charset), 'html', email_charset)
            # Add the text and HTML parts to the child container.
            email_msg_body.attach(textpart)
            email_msg_body.attach(htmlpart)

            # Attach the multipart/alternative child container to the multipart/mixed
            # parent container.
            email_msg.attach(email_msg_body)

            if not os.path.exists(alert_attach_file):
                print("no attachment file found")
            else:
                # Define the attachment part and encode it using MIMEApplication.
                email_attachment = MIMEApplication(open(alert_attach_file, 'rb').read())
                file_name = Path(alert_attach_file).name
                email_attachment.add_header('Content-Disposition', 'attachment', filename=file_name)
                # Add the attachment to the parent container.
                email_msg.attach(email_attachment)

            try:
                # Provide the contents of the email.
                response = self.email_ses_client.send_raw_email(
                    Source=email_msg['From'],
                    Destinations=self.alarm_email_to_list + self.alarm_email_cc_list + self.alarm_email_bcc_list,
                    RawMessage={
                        'Data': email_msg.as_string(),
                    }
                )
            # Display an error if something goes wrong.
            except ClientError as e:
                print(e.response['Error']['Message'])
            except EndpointConnectionError as exp:
                print(exp)
            except ConnectionError as exp:
                print(exp)
            except:
                print("Unknown Exception")
            else:
                print("Done")

    def send_alerts(self, alert_attach_file):
        sms_thread = threading.Thread(target=self.send_alert_sms, daemon=True)
        sms_thread.start()

        email_alert = threading.Thread(target=self.send_alert_email, args=(alert_attach_file,), daemon=True)
        email_alert.start()
