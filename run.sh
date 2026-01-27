#!/bin/bash
# LinkedIn Message Analyzer - Linux/macOS Startup Script
# For those who fear the command line

set -e

echo ""
echo " **** LINKEDIN MESSAGE ANALYZER ****"
echo " 64K RAM SYSTEM  38911 BASIC BYTES FREE"
echo ""
echo " READY."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo " ?PYTHON NOT FOUND ERROR"
    echo ""
    echo " Please install Python 3.9+"
    echo " macOS: brew install python3"
    echo " Linux: sudo apt install python3 python3-pip"
    exit 1
fi

# Determine CSV file location
CSV_FILE=""

# Check if file was passed as argument
if [ -n "$1" ]; then
    CSV_FILE="$1"
elif [ -f "messages.csv" ]; then
    CSV_FILE="messages.csv"
elif [ -f "$HOME/Downloads/messages.csv" ]; then
    echo " Found messages.csv in Downloads folder!"
    CSV_FILE="$HOME/Downloads/messages.csv"
else
    echo " ?FILE NOT FOUND ERROR"
    echo ""
    echo " Please place your LinkedIn messages.csv in this folder"
    echo " or pass it as an argument: ./run.sh /path/to/messages.csv"
    echo ""
    echo " To get your messages:"
    echo " 1. Go to LinkedIn Settings > Data Privacy > Get a copy of your data"
    echo " 2. Select \"Messages\" and request your data"
    echo " 3. Wait for LinkedIn to email you (~24 hours)"
    echo " 4. Extract messages.csv from the download"
    echo ""
    exit 1
fi

echo " LOAD\"$CSV_FILE\",8,1"
echo ""

# Menu function
show_menu() {
    echo " ========================================"
    echo " SELECT MODE:"
    echo " ========================================"
    echo ""
    echo " [1] Quick Analysis (console output)"
    echo " [2] Web Dashboard (C64 style!)"
    echo " [3] Full Report (HTML export)"
    echo " [4] Analysis + LLM (requires API key)"
    echo " [5] Exit"
    echo ""
}

# Open file in browser (cross-platform)
open_file() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$1"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "$1" 2>/dev/null || sensible-browser "$1" 2>/dev/null || echo " Open $1 in your browser"
    else
        echo " Open $1 in your browser"
    fi
}

# Main loop
while true; do
    show_menu
    read -p " Enter choice (1-5): " choice

    case $choice in
        1)
            echo ""
            echo " RUN"
            echo ""
            python3 linkedin_message_analyzer.py "$CSV_FILE" --health-score
            echo ""
            read -p " Press Enter to continue..."
            ;;
        2)
            echo ""
            echo " LOADING WEB DASHBOARD..."
            echo ""
            echo " Open http://localhost:6502 in your browser"
            echo " Press Ctrl+C to stop"
            echo ""
            python3 linkedin_message_analyzer.py "$CSV_FILE" --web
            ;;
        3)
            echo ""
            read -p " Output filename (default: report.html): " htmlfile
            htmlfile=${htmlfile:-report.html}
            echo ""
            echo " SAVING..."
            python3 linkedin_message_analyzer.py "$CSV_FILE" --export-html "$htmlfile" --health-score --trend
            echo ""
            echo " Report saved to $htmlfile"
            open_file "$htmlfile"
            read -p " Press Enter to continue..."
            ;;
        4)
            echo ""
            echo " Available LLM providers:"
            echo "   - openai (requires OPENAI_API_KEY)"
            echo "   - anthropic (requires ANTHROPIC_API_KEY)"
            echo "   - ollama (FREE - local, no API key!)"
            echo "   - gemini (requires GOOGLE_API_KEY)"
            echo "   - groq (requires GROQ_API_KEY)"
            echo "   - mistral (requires MISTRAL_API_KEY)"
            echo ""
            read -p " Enter provider (or 'ollama' for free): " provider
            provider=${provider:-ollama}
            echo ""
            python3 linkedin_message_analyzer.py "$CSV_FILE" --llm "$provider" --summarize --health-score
            echo ""
            read -p " Press Enter to continue..."
            ;;
        5)
            echo ""
            echo " READY."
            echo ""
            exit 0
            ;;
        *)
            echo " ?SYNTAX ERROR"
            ;;
    esac
done
