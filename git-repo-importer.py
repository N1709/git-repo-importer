#!/usr/bin/env python3
"""
Git Repository Importer to GitHub
A universal tool to import any git repository to GitHub with custom configuration
"""

import os
import sys
import subprocess
import json
import argparse
import re
from pathlib import Path
from urllib.parse import urlparse

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class GitHubImporter:
    """Main class for importing repositories to GitHub"""
    
    def __init__(self, token, target_user, source_url, custom_branch=None, repo_name=None):
        self.token = token
        self.target_user = target_user
        self.source_url = source_url
        self.custom_branch = custom_branch
        self.repo_name = repo_name or self._extract_repo_name(source_url)
        self.temp_dir = None
        
    def _extract_repo_name(self, url):
        """Extract repository name from URL"""
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')
        
        # Remove .git extension if present
        if path.endswith('.git'):
            path = path[:-4]
        
        # Get last part of path
        repo_name = path.split('/')[-1]
        
        if not repo_name:
            raise ValueError("Could not extract repository name from URL")
        
        return repo_name
    
    def _run_command(self, command, cwd=None, check=True, capture_output=False):
        """Run shell command with error handling"""
        try:
            if capture_output:
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=cwd,
                    check=check,
                    capture_output=True,
                    text=True
                )
                return result.stdout.strip()
            else:
                subprocess.run(command, shell=True, cwd=cwd, check=check)
                return None
        except subprocess.CalledProcessError as e:
            print(f"{Colors.FAIL}Error executing command: {command}{Colors.ENDC}")
            print(f"{Colors.FAIL}{e}{Colors.ENDC}")
            if capture_output and e.stderr:
                print(f"{Colors.FAIL}Error output: {e.stderr}{Colors.ENDC}")
            raise
    
    def _check_dependencies(self):
        """Check if required tools are installed"""
        print(f"{Colors.OKBLUE}Checking dependencies...{Colors.ENDC}")
        
        dependencies = ['git', 'curl']
        missing = []
        
        for dep in dependencies:
            try:
                self._run_command(f"which {dep}", capture_output=True)
            except subprocess.CalledProcessError:
                missing.append(dep)
        
        if missing:
            print(f"{Colors.FAIL}Missing dependencies: {', '.join(missing)}{Colors.ENDC}")
            print(f"{Colors.WARNING}Please install missing dependencies and try again{Colors.ENDC}")
            sys.exit(1)
        
        print(f"{Colors.OKGREEN}All dependencies are installed{Colors.ENDC}")
    
    def _validate_token(self):
        """Validate GitHub token"""
        print(f"{Colors.OKBLUE}Validating GitHub token...{Colors.ENDC}")
        
        curl_command = f"""curl -s -o /dev/null -w "%{{http_code}}" \
            -H "Authorization: token {self.token}" \
            -H "Accept: application/vnd.github.v3+json" \
            https://api.github.com/user"""
        
        status_code = self._run_command(curl_command, capture_output=True)
        
        if status_code != "200":
            print(f"{Colors.FAIL}Invalid GitHub token. Status code: {status_code}{Colors.ENDC}")
            sys.exit(1)
        
        print(f"{Colors.OKGREEN}GitHub token is valid{Colors.ENDC}")
    
    def _check_repo_exists(self):
        """Check if repository already exists on GitHub"""
        print(f"{Colors.OKBLUE}Checking if repository already exists...{Colors.ENDC}")
        
        curl_command = f"""curl -s -o /dev/null -w "%{{http_code}}" \
            -H "Authorization: token {self.token}" \
            -H "Accept: application/vnd.github.v3+json" \
            https://api.github.com/repos/{self.target_user}/{self.repo_name}"""
        
        status_code = self._run_command(curl_command, capture_output=True)
        
        if status_code == "200":
            print(f"{Colors.WARNING}Repository {self.target_user}/{self.repo_name} already exists{Colors.ENDC}")
            response = input("Do you want to overwrite it? (yes/no): ").strip().lower()
            if response != 'yes':
                print(f"{Colors.WARNING}Import cancelled by user{Colors.ENDC}")
                sys.exit(0)
            return True
        
        return False
    
    def _create_github_repo(self):
        """Create new repository on GitHub"""
        print(f"{Colors.OKBLUE}Creating repository on GitHub...{Colors.ENDC}")
        
        # Check if target is organization or user
        org_check = f"""curl -s -H "Authorization: token {self.token}" \
            -H "Accept: application/vnd.github.v3+json" \
            https://api.github.com/users/{self.target_user}"""
        
        user_info = self._run_command(org_check, capture_output=True)
        
        try:
            user_data = json.loads(user_info)
            is_org = user_data.get('type') == 'Organization'
        except json.JSONDecodeError:
            print(f"{Colors.FAIL}Failed to check if target is organization or user{Colors.ENDC}")
            is_org = False
        
        # Prepare API endpoint
        if is_org:
            api_endpoint = f"https://api.github.com/orgs/{self.target_user}/repos"
        else:
            api_endpoint = "https://api.github.com/user/repos"
        
        # Create repository
        repo_data = {
            "name": self.repo_name,
            "private": False,
            "description": f"Imported from {self.source_url}"
        }
        
        curl_command = f"""curl -s -X POST \
            -H "Authorization: token {self.token}" \
            -H "Accept: application/vnd.github.v3+json" \
            -H "Content-Type: application/json" \
            -d '{json.dumps(repo_data)}' \
            {api_endpoint}"""
        
        result = self._run_command(curl_command, capture_output=True)
        
        try:
            response = json.loads(result)
            if 'id' in response:
                print(f"{Colors.OKGREEN}Repository created: {response['html_url']}{Colors.ENDC}")
                return True
            else:
                print(f"{Colors.FAIL}Failed to create repository{Colors.ENDC}")
                print(f"{Colors.FAIL}{result}{Colors.ENDC}")
                return False
        except json.JSONDecodeError:
            print(f"{Colors.FAIL}Failed to parse GitHub API response{Colors.ENDC}")
            print(f"{Colors.FAIL}{result}{Colors.ENDC}")
            return False
    
    def _clone_source_repo(self):
        """Clone source repository"""
        print(f"{Colors.OKBLUE}Cloning source repository...{Colors.ENDC}")
        
        self.temp_dir = f"/tmp/git-import-{self.repo_name}-{os.getpid()}"
        
        if os.path.exists(self.temp_dir):
            self._run_command(f"rm -rf {self.temp_dir}")
        
        clone_command = f"git clone --mirror {self.source_url} {self.temp_dir}"
        
        try:
            self._run_command(clone_command)
            print(f"{Colors.OKGREEN}Source repository cloned successfully{Colors.ENDC}")
        except subprocess.CalledProcessError:
            print(f"{Colors.FAIL}Failed to clone source repository{Colors.ENDC}")
            sys.exit(1)
    
    def _push_to_github(self):
        """Push repository to GitHub"""
        print(f"{Colors.OKBLUE}Pushing to GitHub...{Colors.ENDC}")
        
        github_url = f"https://{self.token}@github.com/{self.target_user}/{self.repo_name}.git"
        
        if self.custom_branch:
            # Push specific branch
            push_command = f"git push --mirror {github_url}"
            self._run_command(push_command, cwd=self.temp_dir)
            
            # Update default branch if custom branch is specified
            print(f"{Colors.OKBLUE}Setting default branch to {self.custom_branch}...{Colors.ENDC}")
            
            update_branch_command = f"""curl -s -X PATCH \
                -H "Authorization: token {self.token}" \
                -H "Accept: application/vnd.github.v3+json" \
                -H "Content-Type: application/json" \
                -d '{{"default_branch": "{self.custom_branch}"}}' \
                https://api.github.com/repos/{self.target_user}/{self.repo_name}"""
            
            self._run_command(update_branch_command, capture_output=True)
        else:
            # Push all branches
            push_command = f"git push --mirror {github_url}"
            self._run_command(push_command, cwd=self.temp_dir)
        
        print(f"{Colors.OKGREEN}Repository pushed successfully{Colors.ENDC}")
    
    def _cleanup(self):
        """Clean up temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            print(f"{Colors.OKBLUE}Cleaning up temporary files...{Colors.ENDC}")
            self._run_command(f"rm -rf {self.temp_dir}")
            print(f"{Colors.OKGREEN}Cleanup completed{Colors.ENDC}")
    
    def import_repo(self):
        """Main method to import repository"""
        try:
            print(f"{Colors.HEADER}=== Git Repository Importer ==={Colors.ENDC}")
            print(f"Source: {self.source_url}")
            print(f"Target: {self.target_user}/{self.repo_name}")
            if self.custom_branch:
                print(f"Custom branch: {self.custom_branch}")
            print()
            
            # Check dependencies
            self._check_dependencies()
            
            # Validate token
            self._validate_token()
            
            # Check if repo exists
            repo_exists = self._check_repo_exists()
            
            # Create repository if it doesn't exist
            if not repo_exists:
                if not self._create_github_repo():
                    sys.exit(1)
            
            # Clone source repository
            self._clone_source_repo()
            
            # Push to GitHub
            self._push_to_github()
            
            # Success message
            print()
            print(f"{Colors.OKGREEN}{'='*50}{Colors.ENDC}")
            print(f"{Colors.OKGREEN}Import completed successfully!{Colors.ENDC}")
            print(f"{Colors.OKGREEN}Repository URL: https://github.com/{self.target_user}/{self.repo_name}{Colors.ENDC}")
            print(f"{Colors.OKGREEN}{'='*50}{Colors.ENDC}")
            
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}Import cancelled by user{Colors.ENDC}")
            sys.exit(1)
        except Exception as e:
            print(f"\n{Colors.FAIL}Unexpected error: {e}{Colors.ENDC}")
            sys.exit(1)
        finally:
            self._cleanup()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Import Git repository to GitHub',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import repository to user account
  python3 git-repo-importer.py -t TOKEN -u username -s https://source.git

  # Import to organization with custom branch
  python3 git-repo-importer.py -t TOKEN -u org-name -s https://source.git -b main

  # Import with custom repository name
  python3 git-repo-importer.py -t TOKEN -u username -s https://source.git -n custom-name

Interactive mode:
  python3 git-repo-importer.py --interactive
        """
    )
    
    parser.add_argument('-t', '--token', help='GitHub personal access token')
    parser.add_argument('-u', '--user', help='Target GitHub username or organization')
    parser.add_argument('-s', '--source', help='Source repository URL')
    parser.add_argument('-b', '--branch', help='Custom default branch (optional)')
    parser.add_argument('-n', '--name', help='Custom repository name (optional)')
    parser.add_argument('-i', '--interactive', action='store_true', help='Interactive mode')
    
    args = parser.parse_args()
    
    # Interactive mode
    if args.interactive or not (args.token and args.user and args.source):
        print(f"{Colors.HEADER}=== Interactive Mode ==={Colors.ENDC}\n")
        
        token = args.token or input("Enter GitHub token: ").strip()
        user = args.user or input("Enter target username/organization: ").strip()
        source = args.source or input("Enter source repository URL: ").strip()
        branch = args.branch or input("Enter custom default branch (press Enter to skip): ").strip() or None
        name = args.name or input("Enter custom repository name (press Enter to use default): ").strip() or None
        
        print()
    else:
        token = args.token
        user = args.user
        source = args.source
        branch = args.branch
        name = args.name
    
    # Validate inputs
    if not token:
        print(f"{Colors.FAIL}Error: GitHub token is required{Colors.ENDC}")
        sys.exit(1)
    
    if not user:
        print(f"{Colors.FAIL}Error: Target user/organization is required{Colors.ENDC}")
        sys.exit(1)
    
    if not source:
        print(f"{Colors.FAIL}Error: Source repository URL is required{Colors.ENDC}")
        sys.exit(1)
    
    # Create importer and run
    importer = GitHubImporter(token, user, source, branch, name)
    importer.import_repo()

if __name__ == '__main__':
    main()
