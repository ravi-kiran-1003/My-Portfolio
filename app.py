# app.py
import os
import smtplib
import ssl
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, abort, redirect, url_for
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Configuration ---
# Your name and email details
YOUR_NAME = "P Ravi Kiran"  # <<< CHANGE THIS to your name
OWNER_EMAIL = os.getenv("EMAIL_ADDRESS")
OWNER_PASSWORD = os.getenv("EMAIL_PASSWORD")

# In-memory storage for access requests. For a real application, use a database!
access_requests = {}

# --- Email Sending Function ---
def send_email(receiver_email, subject, html_content):
    """A helper function to send emails."""
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{YOUR_NAME} <{OWNER_EMAIL}>"
    message["To"] = receiver_email
    message.attach(MIMEText(html_content, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(OWNER_EMAIL, OWNER_PASSWORD)
            server.sendmail(OWNER_EMAIL, receiver_email, message.as_string())
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# --- Flask Routes ---
@app.route("/")
def index():
    """Renders the access request page."""
    return render_template("index.html")

@app.route("/request_access", methods=["POST"])
def request_access():
    """Handles the access request from a visitor."""
    visitor_email = request.form.get("email")
    if not visitor_email:
        return "Email is required.", 400

    request_id = str(uuid.uuid4())
    access_requests[request_id] = {"email": visitor_email, "status": "pending"}

    # Create the approval link for you to click
    approval_link = url_for('approve_request', request_id=request_id, _external=True)
    
    email_subject = "New Portfolio Access Request"
    email_body = f"""
    <h3>Hi {YOUR_NAME},</h3>
    <p>You have a new request to access your portfolio from: <strong>{visitor_email}</strong></p>
    <p>To approve this request, click the link below:</p>
    <a href="{approval_link}" style="padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">Approve Access</a>
    <p>This link is unique to this request.</p>
    """
    
    # TEMPORARILY DISABLED FOR HIRING DRIVE TO PREVENT CRASH
    # send_email(OWNER_EMAIL, email_subject, email_body)
    
    return render_template("index.html", message="Your request has been sent! You will receive an email if it is approved.")

@app.route("/approve/<request_id>")
def approve_request(request_id):
    """The link you click in your email to approve a request."""
    if request_id in access_requests and access_requests[request_id]["status"] == "pending":
        # Generate a unique token for portfolio access
        access_token = str(uuid.uuid4())
        access_requests[request_id]["status"] = "approved"
        access_requests[request_id]["token"] = access_token
        
        visitor_email = access_requests[request_id]["email"]
        portfolio_link = url_for('view_portfolio', token=access_token, _external=True)

        # Send the approval email to the visitor
        email_subject = "Your Portfolio Access is Approved!"
        email_body = f"""
        <h3>Hi there,</h3>
        <p>Your request to view {YOUR_NAME}'s portfolio has been approved!</p>
        <p>Click the unique link below to access it:</p>
        <a href="{portfolio_link}" style="padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px;">View Portfolio</a>
        <p>This link is for you only. Please do not share it.</p>
        """
        send_email(visitor_email, email_subject, email_body)

        return "Access approved! The visitor has been notified."
    
    return "Invalid or expired approval link.", 404

@app.route("/portfolio/<token>")
def view_portfolio(token):
    """Displays the portfolio if the token is valid."""
    is_valid_token = False
    for req in access_requests.values():
        if req.get("token") == token and req.get("status") == "approved":
            is_valid_token = True
            break
            
    if is_valid_token:
        return render_template("portfolio.html", your_name=YOUR_NAME)
    else:
        abort(403) # Forbidden access

@app.route("/send_message", methods=["POST"])
def send_message():
    """Handles the contact form submission from the portfolio page."""
    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("message")

    email_subject = f"New Message from {name} via Portfolio"
    email_body = f"""
    <h3>You have a new message!</h3>
    <p><strong>Name:</strong> {name}</p>
    <p><strong>Email:</strong> {email}</p>
    <p><strong>Message:</strong></p>
    <p>{message}</p>
    """
    
    send_email(OWNER_EMAIL, email_subject, email_body)

    # Redirect back to the portfolio with a success query
    # Find the token from the referrer URL to redirect correctly
    referer_url = request.headers.get("Referer")
    token = referer_url.split('/')[-1] if referer_url else ''
    
    return redirect(url_for('view_portfolio', token=token, message_sent='true'))


if __name__ == "__main__":
    app.run(debug=True)