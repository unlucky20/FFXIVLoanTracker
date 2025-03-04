import os
import subprocess
from datetime import datetime
import streamlit as st

class GitSync:
    def __init__(self, data_dir, repo_url=None):
        self.data_dir = data_dir
        self.repo_url = repo_url
        self.git_token = os.getenv('GITHUB_TOKEN')

    def run_git_command(self, command):
        """Execute a git command and return the output"""
        try:
            result = subprocess.run(
                command,
                cwd=self.data_dir,
                capture_output=True,
                text=True,
                shell=True
            )
            if result.returncode != 0:
                st.error(f"Git command failed: {result.stderr}")
                return False
            return True
        except Exception as e:
            st.error(f"Error executing git command: {str(e)}")
            return False

    def init_repo(self):
        """Initialize git repository if it doesn't exist"""
        try:
            if not os.path.exists(os.path.join(self.data_dir, '.git')):
                if not self.run_git_command('git init'):
                    return False

                # Configure git
                self.run_git_command('git config user.name "FC Data Sync"')
                self.run_git_command('git config user.email "fc-data-sync@noreply.github.com"')

                if self.repo_url:
                    remote_url = self.repo_url.replace('https://', f'https://{self.git_token}@')
                    self.run_git_command(f'git remote add origin {remote_url}')

                st.success("Git repository initialized successfully")
            return True
        except Exception as e:
            st.error(f"Error initializing Git repository: {str(e)}")
            return False

    def commit_and_push(self):
        """Commit changes and push to remote"""
        try:
            # Show sync status
            with st.spinner("Syncing data to Git..."):
                # Stage all changes in data directory
                self.run_git_command('git add *.csv')

                # Create commit with timestamp
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.run_git_command(f'git commit -m "Data sync: {timestamp}"')

                # Push changes if remote is configured
                if self.repo_url:
                    self.run_git_command('git push origin main')

                st.success("Data synced successfully!")
            return True
        except Exception as e:
            st.error(f"Error in commit_and_push: {str(e)}")
            return False

    def pull_changes(self):
        """Pull latest changes from remote"""
        try:
            with st.spinner("Pulling latest data..."):
                if self.repo_url:
                    self.run_git_command('git pull origin main')
                st.success("Latest data pulled successfully")
            return True
        except Exception as e:
            st.error(f"Error pulling changes: {str(e)}")
            return False