# Deployment Guide: Larkhall Athletic Fixtures Calendar

This guide provides step-by-step instructions for deploying the Larkhall Athletic Fixtures Calendar to GitHub Pages.

*Last Updated: March 28, 2025*

## Prerequisites

- GitHub account
- Git installed on your local machine
- API key for FootballWebPages API

## Deployment Steps

### 1. Create a GitHub Repository

1. Go to [GitHub](https://github.com) and sign in to your account
2. Click the "+" icon in the top-right corner and select "New repository"
3. Name the repository `larkhall-calendar` (or another name of your choice)
4. Add a description: "Automatically updating calendar for Larkhall Athletic fixtures"
5. Choose "Public" visibility
6. Check "Add a README file" (we'll replace it with our own)
7. Click "Create repository"

### 2. Push the Local Repository to GitHub

1. Open a terminal in your local project directory
2. Initialize the local repository (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```
3. Add the remote repository:
   ```bash
   git remote add origin https://github.com/[your-username]/larkhall-calendar.git
   ```
4. Push to GitHub:
   ```bash
   git push -u origin main
   ```

### 3. Set Up GitHub Secret for API Key

1. In your GitHub repository, go to "Settings" > "Secrets and variables" > "Actions"
2. Click "New repository secret"
3. Name: `FOOTBALL_WEB_PAGES_API_KEY`
4. Value: Your FootballWebPages API key
5. Click "Add secret"

### 4. Configure GitHub Pages

1. In your GitHub repository, go to "Settings" > "Pages"
2. Under "Source", select "Deploy from a branch"
3. Under "Branch", select "main" and "/ (root)"
4. Click "Save"
5. Wait for the deployment to complete (this may take a few minutes)
6. Note the URL where your site is published (e.g., `https://[your-username].github.io/larkhall-calendar/`)

### 5. Update the Calendar URL in index.html

1. Edit the `index.html` file in your repository
2. Replace `https://[username].github.io/larkhall-calendar/fixtures.ics` with your actual URL:
   `https://[your-username].github.io/larkhall-calendar/fixtures.ics`
3. Commit and push the changes

### 6. Trigger the Workflow Manually

1. In your GitHub repository, go to "Actions"
2. Select the "Update Fixtures Calendar" workflow
3. Click "Run workflow" > "Run workflow"
4. Wait for the workflow to complete

### 7. Verify the Deployment

1. Visit your GitHub Pages URL: `https://[your-username].github.io/larkhall-calendar/`
2. Follow the subscription instructions to add the calendar to your preferred application
3. Verify that the fixtures appear correctly in your calendar

## Troubleshooting

### Calendar Not Updating

- Check the Actions tab in your GitHub repository to see if the workflow is running successfully
- Verify that the API key is correctly set up as a repository secret
- Check the workflow logs for any error messages

### Subscription Issues

- Ensure you're using the correct URL for subscription
- Try refreshing the calendar in your application
- Check that your calendar application supports iCalendar subscriptions

## Maintenance

The calendar will update automatically every day at 4:00 AM UTC. You can also trigger manual updates through the Actions tab in your GitHub repository.

If you need to make changes to the code or configuration:

1. Clone the repository
2. Make your changes
3. Commit and push to GitHub
4. The changes will be reflected in the deployed application
