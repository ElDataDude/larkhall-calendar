#!/bin/bash
# Setup script for Larkhall Athletic Fixtures Calendar

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create empty .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    echo "FOOTBALL_WEB_PAGES_API_KEY=your_api_key_here" > .env
    echo "Please edit .env file and add your Football Web Pages API key."
fi

echo ""
echo "Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To test the API, run:"
echo "  python src/test_api.py"
echo ""
echo "To update the calendar, run:"
echo "  python src/update_calendar.py"
echo ""
