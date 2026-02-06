# Git Repository Importer to GitHub

A universal Python tool to import any Git repository to GitHub with support for custom configuration including tokens, organizations, branches, and repository names.

## Features

- Import from any Git repository (GitHub, GitLab, Bitbucket, custom servers, etc.)
- Support for both user accounts and organizations
- Custom branch selection as default branch
- Custom repository naming
- Automatic dependency checking
- Token validation before import
- Progress feedback and error handling
- Interactive and command-line modes
- Mirror clone (preserves all branches, tags, and history)

## Requirements

- Python 3.6 or higher
- Git
- curl
- GitHub Personal Access Token with repo permissions

## Installation

1. Download the script:
```bash
wget https://raw.githubusercontent.com/N1709/git-repo-importer.py
# or
curl -O https://raw.githubusercontent.com/N1709/git-repo-importer.py
```

2. Make it executable:
```bash
chmod +x git-repo-importer.py
```

## GitHub Token Setup

1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` (Full control of private repositories)
   - `admin:org` (if importing to organization)
4. Generate and copy the token

## Usage

### Interactive Mode

Run the script without arguments for interactive mode:

```bash
python3 git-repo-importer.py --interactive
```

You will be prompted to enter:
- GitHub token
- Target username or organization
- Source repository URL
- Custom default branch (optional)
- Custom repository name (optional)

### Command Line Mode

#### Basic Usage

```bash
python3 git-repo-importer.py \
  --token YOUR_GITHUB_TOKEN \
  --user target-username \
  --source https://source-repo.git
```

#### Import to Organization

```bash
python3 git-repo-importer.py \
  --token YOUR_GITHUB_TOKEN \
  --user organization-name \
  --source https://android.googlesource.com/kernel/common.git
```

#### Import with Custom Branch

```bash
python3 git-repo-importer.py \
  --token YOUR_GITHUB_TOKEN \
  --user username \
  --source https://source-repo.git \
  --branch android-mainline
```

#### Import with Custom Repository Name

```bash
python3 git-repo-importer.py \
  --token YOUR_GITHUB_TOKEN \
  --user username \
  --source https://source-repo.git \
  --name my-custom-repo-name
```

#### Complete Example

```bash
python3 git-repo-importer.py \
  --token ghp_xxxxxxxxxxxxxxxxxxxx \
  --user my-organization \
  --source https://android.googlesource.com/kernel/common.git \
  --branch android-mainline \
  --name android-kernel-mainline
```

### Command Line Options

| Option | Short | Description | Required |
|--------|-------|-------------|----------|
| `--token` | `-t` | GitHub personal access token | Yes |
| `--user` | `-u` | Target GitHub username or organization | Yes |
| `--source` | `-s` | Source repository URL | Yes |
| `--branch` | `-b` | Custom default branch | No |
| `--name` | `-n` | Custom repository name | No |
| `--interactive` | `-i` | Run in interactive mode | No |

## Examples

### Example 1: Import Android Kernel Mainline

```bash
python3 git-repo-importer.py \
  -t ghp_your_token_here \
  -u your-username \
  -s https://android.googlesource.com/kernel/common.git \
  -b android-mainline
```

### Example 2: Import to Organization

```bash
python3 git-repo-importer.py \
  -t ghp_your_token_here \
  -u sm6125-devs \
  -s https://github.com/sm6125-mainline/linux.git \
  -b master
```

### Example 3: Import with Custom Name

```bash
python3 git-repo-importer.py \
  -t ghp_your_token_here \
  -u your-username \
  -s https://gitlab.com/some-project.git \
  -n my-forked-project
```

### Example 4: Import from Private Source

```bash
python3 git-repo-importer.py \
  -t ghp_your_token_here \
  -u your-username \
  -s https://username:password@private-git-server.com/repo.git
```

## How It Works

1. **Dependency Check**: Verifies Git and curl are installed
2. **Token Validation**: Validates GitHub token with API
3. **Repository Check**: Checks if target repository already exists
4. **Repository Creation**: Creates new repository on GitHub
5. **Clone Source**: Mirror clones the source repository
6. **Push to GitHub**: Pushes all branches and tags to GitHub
7. **Branch Setup**: Sets custom default branch if specified
8. **Cleanup**: Removes temporary files

## Error Handling

The tool handles various error scenarios:

- Missing dependencies
- Invalid GitHub token
- Repository already exists (prompts for confirmation)
- Clone failures
- Push failures
- Network errors

## Supported Source Repositories

- GitHub (public and private)
- GitLab (public and private)
- Bitbucket
- Gitea
- Gogs
- Android AOSP (googlesource.com)
- Custom Git servers
- Any Git repository accessible via HTTP/HTTPS

## Security Notes

- Never commit your GitHub token to version control
- Use environment variables for tokens in automation:
  ```bash
  export GITHUB_TOKEN=ghp_your_token_here
  python3 git-repo-importer.py -t $GITHUB_TOKEN -u username -s https://repo.git
  ```
- Tokens are only used for GitHub API authentication
- Source repository credentials should be in the URL if needed

## Troubleshooting

### Token Authentication Failed

```
Error: Invalid GitHub token. Status code: 401
```

**Solution**: Check your token has `repo` scope and is not expired

### Repository Already Exists

```
Warning: Repository username/repo-name already exists
Do you want to overwrite it? (yes/no):
```

**Solution**: Type `yes` to overwrite or `no` to cancel

### Clone Failed

```
Error: Failed to clone source repository
```

**Solution**: 
- Check source URL is correct
- Verify you have access to source repository
- Check network connection

### Push Failed

```
Error executing command: git push --mirror
```

**Solution**:
- Verify GitHub token has write permissions
- Check repository size limits
- Verify network connection

## Advanced Usage

### Batch Import Multiple Repositories

Create a script file `batch-import.sh`:

```bash
#!/bin/bash

TOKEN="ghp_your_token_here"
USER="your-username"

# Array of repositories to import
repos=(
  "https://repo1.git"
  "https://repo2.git"
  "https://repo3.git"
)

for repo in "${repos[@]}"; do
  python3 git-repo-importer.py -t $TOKEN -u $USER -s $repo
done
```

### Import with Specific Branches Only

For importing only specific branches, modify the push command in the script or use:

```bash
# After cloning, before pushing
cd /tmp/git-import-*
git remote add github https://TOKEN@github.com/user/repo.git
git push github refs/heads/main:refs/heads/main
git push github refs/heads/develop:refs/heads/develop
```

## Contributing

Contributions are welcome. Please ensure:

- Code follows PEP 8 style guide
- All functions have docstrings
- Error handling is comprehensive
- Changes are tested

## License

MIT License - Feel free to use and modify

## Changelog

### Version 1.0.0
- Initial release
- Support for user and organization imports
- Custom branch selection
- Custom repository naming
- Interactive and CLI modes
- Comprehensive error handling
