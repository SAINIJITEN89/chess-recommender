#!/bin/bash

# Chess Buddy Alias Setup Script
# This script sets up the alias "sf" function in ~/.bash_aliases

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Setting up sf function..."
echo "================================="

# Create ~/.bash_aliases if it doesn't exist
touch ~/.bash_aliases

# Add the function to ~/.bash_aliases
echo "" >> ~/.bash_aliases
echo 'sf() {'>> ~/.bash_aliases
echo '    cd "/root/workspace/claude-code/chess-recommender"'>> ~/.bash_aliases
echo '    source venv/bin/activate'>> ~/.bash_aliases
echo '    python chess_analyzer.py "$@"'>> ~/.bash_aliases
echo '}'>> ~/.bash_aliases

echo "alias added for chess next move recommender utility - alias name - sf"
echo ""
echo "To use immediately in this session, run:"
echo "source ~/.bash_aliases"
echo ""
echo "Usage examples:"
echo "sf           # Analyze starting position"
echo "sf e4        # Analyze after 1.e4"
echo "sf e4 e5     # Analyze after 1.e4 e5"
echo ""
