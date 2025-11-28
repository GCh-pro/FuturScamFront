import os
import requests
from msal import ConfidentialClientApplication
import base64
from pathlib import Path
from typing import List, Optional


class MailSender:
    """Send emails with attachments using Microsoft Graph API."""
    
    def __init__(self, client_id: str, authority: str, client_secret: str, mailbox_email: str, scopes: list):
        self.client_id = client_id
        self.authority = authority
        self.client_secret = client_secret
        self.mailbox_email = mailbox_email
        self.scopes = scopes
        self.access_token = None
        self.headers = {}

    def authenticate(self):
        """Authenticate using MSAL with client secret (Application permissions)."""
        app = ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )
        result = app.acquire_token_for_client(scopes=self.scopes)

        if "access_token" not in result:
            raise RuntimeError(f"Erreur d'authentification: {result.get('error_description')}")
        
        self.access_token = result["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        print("[OK] Authentification réussie.")

    def send_email(
        self,
        to_addresses: List[str],
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
        cc_addresses: Optional[List[str]] = None,
        bcc_addresses: Optional[List[str]] = None,
        is_html: bool = True
    ) -> bool:
        """
        Send an email with optional attachments.
        
        Args:
            to_addresses: List of recipient email addresses
            subject: Email subject
            body: Email body (plain text or HTML)
            attachments: List of file paths to attach
            cc_addresses: List of CC recipient addresses
            bcc_addresses: List of BCC recipient addresses
            is_html: Whether body is HTML (default True)
        
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.access_token:
            print("[ERROR] Not authenticated. Call authenticate() first.")
            return False
        
        try:
            # Build recipient lists
            to_recipients = [{"emailAddress": {"address": addr}} for addr in to_addresses]
            
            message_data = {
                "subject": subject,
                "body": {
                    "contentType": "HTML" if is_html else "text",
                    "content": body
                },
                "toRecipients": to_recipients
            }
            
            # Add CC recipients if provided
            if cc_addresses:
                message_data["ccRecipients"] = [{"emailAddress": {"address": addr}} for addr in cc_addresses]
            
            # Add BCC recipients if provided
            if bcc_addresses:
                message_data["bccRecipients"] = [{"emailAddress": {"address": addr}} for addr in bcc_addresses]
            
            # Handle attachments
            attachments_list = []
            if attachments:
                for attachment_path in attachments:
                    attachment_data = self._prepare_attachment(attachment_path)
                    if attachment_data:
                        attachments_list.append(attachment_data)
                
                if attachments_list:
                    message_data["attachments"] = attachments_list
            
            # Send email using the specific mailbox (required for application permissions)
            # Format: /users/{email}/sendMail instead of /me/sendMail
            url = f"https://graph.microsoft.com/v1.0/users/{self.mailbox_email}/sendMail"
            payload = {"message": message_data}
            
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            
            if response.status_code in [200, 202]:
                print(f"[OK] Email sent successfully to {', '.join(to_addresses)}")
                return True
            else:
                print(f"[ERROR] Failed to send email: status {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error sending email: {e}")
            return False

    def _prepare_attachment(self, file_path: str) -> Optional[dict]:
        """
        Prepare an attachment for the email.
        
        Args:
            file_path: Path to the file to attach
        
        Returns:
            Dictionary with attachment data, or None if file doesn't exist
        """
        try:
            if not os.path.exists(file_path):
                print(f"[WARN] Attachment file not found: {file_path}")
                return None
            
            file_size = os.path.getsize(file_path)
            
            # Microsoft Graph has a 25MB limit per attachment
            if file_size > 25 * 1024 * 1024:
                print(f"[WARN] File {file_path} is too large (> 25MB), skipping")
                return None
            
            # Read and encode file
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Encode to base64
            encoded_content = base64.b64encode(file_content).decode('utf-8')
            
            # Get filename from path
            filename = os.path.basename(file_path)
            
            return {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": filename,
                "contentBytes": encoded_content
            }
            
        except Exception as e:
            print(f"[ERROR] Error preparing attachment {file_path}: {e}")
            return None
