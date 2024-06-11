import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def fetch_linkedin_data(api_url):
    # Send a GET request to the LinkedIn API
    response = requests.get(api_url)
    if response.status_code != 200:
        print(f'Error fetching data: {response.status_code}')
        return None
    
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Select all anchor elements with href containing 'linkedin.com/company'
    company_links = soup.select('a[href*="linkedin.com/company"]')

    # Extract company names from the URLs without duplicates
    company_names = set()
    for link in company_links:
        url_parts = link['href'].split('/')
        print(url_parts)  # Add this line to see the content of url_parts
        for i, part in enumerate(url_parts):
            if part.startswith('company'):
                if i + 1 < len(url_parts):
                    company_name = url_parts[i+1].split('?')[0]
                    company_names.add(company_name)

    return list(company_names)  # Convert set to list before returning



def send_email(csv_file_path, city, state):
    # Email configuration
    sender_email = 'dakotarmain@gmail.com'
    receiver_email = 'tsipes@ascensionlogistics.com'
    password = 'olys kgep wpar mfgm'
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587

    # Create message container
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f'Leads in {city}, {state}'

    # Add message body
    body = 'Please find attached the cached data report.'
    msg.attach(MIMEText(body, 'plain'))

    # Attach data as CSV file
    with open(csv_file_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={csv_file_path}')
        msg.attach(part)

    try:
        # Start SMTP session
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, password)
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, text)

        print('Email sent successfully.')
    except smtplib.SMTPAuthenticationError as e:
        print(f'Failed to authenticate: {e}')
    except Exception as e:
        print(f'Error sending email: {e}')

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run-script', methods=['GET'])
def run_script():
    # Define the list of cities and states
    cities_states = [('Seattle', 'WA'), ('New Orleans', 'LA'), ('Denver', 'CO'), ('Portland', 'CT')]

    for city, state in cities_states:
        # Define the URL of the LinkedIn API endpoint
        API_URL = f'https://www.linkedin.com/jobs/logistics-manager-jobs-{city.lower().replace(" ", "-")}-{state.lower()}?position=1&pageNum=0'

        # Fetch LinkedIn data from the API
        fetched_urls = fetch_linkedin_data(API_URL)

        if fetched_urls:
            # Save the fetched data to a local CSV file
            csv_file_path = 'cached_data.csv'
            with open(csv_file_path, 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(['Company Name', 'Location'])
                for company_name in fetched_urls:
                    csvwriter.writerow([company_name, f'{city}, {state}'])

            # Send email with the cached data
            send_email(csv_file_path, city, state)

    return jsonify({'message': 'Leads Updated. Email Sent. Love you!'}), 200

if __name__ == '__main__':
    app.run(debug=True)
