"""
Google Drive Uploader
Upload generated resumes and cover letters to Google Drive
"""
import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import config


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file']


class GoogleDriveUploader:
    def __init__(self):
        """Initialize Google Drive Uploader"""
        self.service = None
        self.credentials = None
        self.folder_id = None
    
    def authenticate(self):
        """Authenticate with Google Drive API"""
        creds = None
        
        # The file token.json stores the user's access and refresh tokens
        if os.path.exists(config.GOOGLE_DRIVE_TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(config.GOOGLE_DRIVE_TOKEN_FILE, SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(config.GOOGLE_DRIVE_CREDENTIALS_FILE):
                    print(f"Error: {config.GOOGLE_DRIVE_CREDENTIALS_FILE} not found!")
                    print("Please download your OAuth 2.0 credentials from Google Cloud Console")
                    print("and save it as 'credentials.json' in the project directory.")
                    return False
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        config.GOOGLE_DRIVE_CREDENTIALS_FILE, SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"Error during OAuth flow: {e}")
                    return False
            
            # Save the credentials for the next run
            with open(config.GOOGLE_DRIVE_TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        try:
            self.credentials = creds
            self.service = build('drive', 'v3', credentials=creds)
            print("✓ Google Drive service initialized")
            return True
        except Exception as e:
            print(f"Error building Drive service: {e}")
            return False
    
    def create_folder(self, folder_name, parent_folder_id=None):
        """
        Create a folder in Google Drive
        
        Args:
            folder_name: Name of the folder to create
            parent_folder_id: ID of parent folder (None for root)
        
        Returns:
            str: Folder ID
        """
        if not self.service:
            print("Not authenticated! Call authenticate() first.")
            return None
        
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            print(f"Created folder '{folder_name}' with ID: {folder_id}")
            return folder_id
            
        except HttpError as error:
            print(f"Error creating folder: {error}")
            return None
    
    def upload_file(self, file_path, folder_id=None, new_name=None):
        """
        Upload a file to Google Drive
        
        Args:
            file_path: Path to the file to upload
            folder_id: ID of the folder to upload to (None for root)
            new_name: New name for the file (None to keep original)
        
        Returns:
            str: File ID
        """
        if not self.service:
            print("Not authenticated! Call authenticate() first.")
            return None
        
        try:
            file_name = new_name if new_name else os.path.basename(file_path)
            
            file_metadata = {'name': file_name}
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Determine MIME type based on file extension
            mime_type = self._get_mime_type(file_path)
            
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            file_id = file.get('id')
            web_link = file.get('webViewLink')
            
            print(f"✓ Uploaded '{file_name}' to Google Drive")
            print(f"  Link: {web_link}")
            
            return file_id
            
        except HttpError as error:
            print(f"Error uploading file: {error}")
            return None
    
    def _get_mime_type(self, file_path):
        """Determine MIME type based on file extension"""
        extension = file_path.split('.')[-1].lower()
        
        mime_types = {
            'txt': 'text/plain',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'csv': 'text/csv',
            'json': 'application/json',
            'md': 'text/markdown',
            'tex': 'text/plain'
        }
        
        return mime_types.get(extension, 'application/octet-stream')
    
    def find_folder(self, folder_name):
        """
        Find a folder by name
        
        Args:
            folder_name: Name of the folder to find
        
        Returns:
            str: Folder ID or None if not found
        """
        if not self.service:
            print("Not authenticated! Call authenticate() first.")
            return None
        
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                return files[0]['id']
            else:
                return None
                
        except HttpError as error:
            print(f"Error finding folder: {error}")
            return None
    
    def get_or_create_folder(self, folder_name):
        """
        Get folder ID if it exists, or create it if it doesn't
        
        Args:
            folder_name: Name of the folder
        
        Returns:
            str: Folder ID
        """
        folder_id = self.find_folder(folder_name)
        
        if folder_id:
            print(f"Found existing folder '{folder_name}'")
            return folder_id
        else:
            return self.create_folder(folder_name)
    
    def upload_application_documents(self, resume_path, cover_letter_path, 
                                    company_name, job_title, parent_folder="Job Applications"):
        """
        Upload resume and cover letter for a specific job application
        
        Args:
            resume_path: Path to tailored resume (PDF preferred)
            cover_letter_path: Path to cover letter
            company_name: Company name
            job_title: Job title
            parent_folder: Parent folder name in Google Drive
        
        Returns:
            dict: Links to uploaded documents
        """
        # Get or create main folder
        main_folder_id = self.get_or_create_folder(parent_folder)
        
        if not main_folder_id:
            print("Failed to create/find main folder")
            return None
        
        # Clean company name for folder/file names
        clean_company = company_name.replace('/', '-').replace('\\', '-').strip()
        
        # Use simple naming format: CompanyName_CV and CompanyName_CoverLetter
        resume_new_name = f"{clean_company}_CV.pdf"
        cover_new_name = f"{clean_company}_CoverLetter.docx"
        
        # Check if files already exist in this folder
        existing_files = self._list_files_in_folder_by_name(main_folder_id)
        
        # Upload files with new naming
        results = {}
        
        if resume_path and os.path.exists(resume_path):
            # Check for duplicate
            if resume_new_name in existing_files:
                print(f"   ⚠️  Skipping duplicate: {resume_new_name} already exists")
                results['resume_id'] = 'duplicate'
            else:
                resume_id = self.upload_file(resume_path, main_folder_id, new_name=resume_new_name)
                if resume_id:
                    results['resume_id'] = resume_id
        
        if cover_letter_path and os.path.exists(cover_letter_path):
            # Check for duplicate
            if cover_new_name in existing_files:
                print(f"   ⚠️  Skipping duplicate: {cover_new_name} already exists")
                results['cover_letter_id'] = 'duplicate'
            else:
                cover_letter_id = self.upload_file(cover_letter_path, main_folder_id, new_name=cover_new_name)
                if cover_letter_id:
                    results['cover_letter_id'] = cover_letter_id
        
        return results
    
    def _list_files_in_folder_by_name(self, folder_id=None):
        """
        List file names in a folder (for duplicate checking)
        
        Args:
            folder_id: Folder ID (None for root)
        
        Returns:
            set: Set of file names in the folder
        """
        if not self.service:
            return set()
        
        try:
            query = f"'{folder_id}' in parents and trashed=false" if folder_id else "trashed=false"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(name)',
                pageSize=1000
            ).execute()
            
            files = results.get('files', [])
            return {file['name'] for file in files}
            
        except HttpError as error:
            print(f"Error listing files: {error}")
            return set()
    
    def list_files_in_folder(self, folder_id=None):
        """
        List files in a folder
        
        Args:
            folder_id: Folder ID (None for root)
        
        Returns:
            list: List of files
        """
        if not self.service:
            print("Not authenticated! Call authenticate() first.")
            return []
        
        try:
            query = f"'{folder_id}' in parents" if folder_id else "trashed=false"
            
            results = self.service.files().list(
                q=query,
                fields='files(id, name, mimeType, createdTime)'
            ).execute()
            
            return results.get('files', [])
            
        except HttpError as error:
            print(f"Error listing files: {error}")
            return []


# Example usage
if __name__ == "__main__":
    uploader = GoogleDriveUploader()
    
    print("Authenticating with Google Drive...")
    if uploader.authenticate():
        print("✓ Successfully authenticated!")
        
        # Example: Create a test folder
        # folder_id = uploader.get_or_create_folder("Job Applications Test")
        # print(f"Folder ID: {folder_id}")
    else:
        print("✗ Authentication failed!")

