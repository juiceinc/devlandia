import boto3
from botocore.exceptions import ClientError


def send_email(subject, body, sender, recipient):
    # Set your AWS credentials

    # Initialize the SES client
    ses_client = boto3.client('ses')

    # Create the email message
    email_message = {
        'Subject': {'Data': subject},
        'Body': {'Text': {'Data': body}},
    }

    try:
        # Send the email
        response = ses_client.send_email(
            Source=sender,
            Destination={'ToAddresses': [recipient]},
            Message=email_message
        )

        print("Email sent! Message ID:", response['MessageId'])

    except ClientError as e:
        print("Error sending email:", e)


# Set the email details
email_subject = "Test Email"
email_body = "This is a test email sent using Amazon SES and boto3."
sender_email = "NDR_support@nd.edu"
recipient_email = "cwire4@gmail.com"

if __name__ == '__main__':
    # Send the email
    send_email(email_subject, email_body, sender_email, recipient_email)
