# Deployment Procedures: Larkhall Athletic Fixtures Calendar

This document outlines the complete deployment process for the Larkhall Athletic Fixtures Calendar, from initial setup to ongoing maintenance.

## Initial Deployment

### 1. GitHub Repository Setup

1. **Create Repository**
   ```bash
   # Create a new repository on GitHub
   # Initialize with README, .gitignore (Python), and MIT License
   ```

2. **Clone Repository**
   ```bash
   git clone https://github.com/[username]/larkhall-calendar.git
   cd larkhall-calendar
   ```

3. **Create Basic Structure**
   ```bash
   mkdir -p src
   touch src/__init__.py
   touch src/update_calendar.py
   touch fixtures.ics
   touch requirements.txt
   touch README.md
   ```

### 2. Environment Configuration

1. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install requests icalendar pytz
   pip freeze > requirements.txt
   ```

3. **Configure API Key**
   - For local development:
     ```bash
     # Create .env file (add to .gitignore)
     echo "FOOTBALL_WEB_PAGES_API_KEY=your_api_key" > .env
     ```
   - For GitHub Actions:
     - Go to repository Settings > Secrets
     - Add new repository secret:
       - Name: `FOOTBALL_WEB_PAGES_API_KEY`
       - Value: `<your_api_key>`

### 3. GitHub Pages Configuration

1. **Enable GitHub Pages**
   - Go to repository Settings > Pages
   - Source: Deploy from a branch
   - Branch: main
   - Folder: / (root)
   - Save

2. **Configure Custom Domain (Optional)**
   - Add custom domain in GitHub Pages settings
   - Create CNAME file in repository root
   - Configure DNS settings with domain provider

### 4. GitHub Actions Setup

1. **Create Workflow File**
   ```bash
   mkdir -p .github/workflows
   touch .github/workflows/update-calendar.yml
   ```

2. **Configure Workflow**
   - Edit `.github/workflows/update-calendar.yml` with the scheduled update configuration
   - Commit and push to repository

## Update Process

The calendar update process is automated through GitHub Actions and follows these steps:

### 1. Scheduled Trigger

GitHub Actions workflow runs automatically:
- Daily at 4:00 AM UTC
- On manual trigger via workflow_dispatch

### 2. Environment Setup

```yaml
- uses: actions/checkout@v2
- name: Set up Python
  uses: actions/setup-python@v2
  with:
    python-version: '3.9'
- name: Install dependencies
  run: pip install -r requirements.txt
```

### 3. Calendar Update

```yaml
- name: Update calendar
  run: python src/update_calendar.py
  env:
    FOOTBALL_WEB_PAGES_API_KEY: ${{ secrets.FOOTBALL_WEB_PAGES_API_KEY }}
```

### 4. Commit and Push Changes

```yaml
- name: Commit and push changes
  run: |
    git config --local user.email "action@github.com"
    git config --local user.name "GitHub Action"
    git add fixtures.ics
    git commit -m "Update fixtures calendar" || echo "No changes to commit"
    git push
```

## Manual Deployment

In case manual deployment is needed:

### 1. Local Update

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Set API key
export FOOTBALL_WEB_PAGES_API_KEY=your_api_key

# Run update script
python src/update_calendar.py

# Verify changes
git diff fixtures.ics
```

### 2. Manual Push

```bash
git add fixtures.ics
git commit -m "Manual update of fixtures calendar"
git push
```

## Monitoring and Verification

### 1. GitHub Actions Logs

- Go to repository Actions tab
- Check the latest workflow run
- Review logs for any errors or warnings

### 2. Calendar Verification

- Subscribe to the calendar in a test calendar application
- Verify that fixtures appear correctly
- Check for any formatting issues

## Troubleshooting

### 1. API Issues

If the API is unavailable or returns errors:

```bash
# Check API status manually
curl -G "https://www.footballwebpages.co.uk/api/fixtures-results.json" \
  --data-urlencode "team=1169" \
  --data-urlencode "key=$FOOTBALL_WEB_PAGES_API_KEY"
```

### 2. GitHub Actions Failures

If GitHub Actions workflow fails:

1. Check workflow logs for error messages
2. Verify that the API key secret is correctly set
3. Test the update script locally to identify issues

### 3. Calendar Format Issues

If calendar applications have trouble with the .ics file:

1. Validate the .ics file format using an online validator
2. Check for any non-standard characters or formatting
3. Test with multiple calendar applications to isolate the issue

## Rollback Procedure

If a problematic update needs to be reverted:

```bash
# Identify the commit to roll back to
git log --oneline

# Create a revert commit
git revert [commit-hash]

# Push the revert
git push
```

## Maintenance Tasks

### 1. Regular Checks

- Weekly: Verify that the calendar is updating correctly
- Monthly: Check for any API changes or issues

### 2. Dependency Updates

```bash
# Update dependencies
pip install --upgrade requests icalendar pytz
pip freeze > requirements.txt

# Commit and push updates
git add requirements.txt
git commit -m "Update dependencies"
git push
```

### 3. Documentation Updates

Keep documentation up to date with any changes to:
- API structure
- Deployment process
- Troubleshooting steps
