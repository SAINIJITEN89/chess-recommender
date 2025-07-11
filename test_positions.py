#!/usr/bin/env python3
"""Test script to verify the chess analyzer with various positions."""

import sys
sys.path.append('.')
from chess_analyzer import ChessAnalyzer, print_analysis

def test_positions():
    """Test the analyzer with various chess positions."""
    analyzer = ChessAnalyzer()
    
    test_cases = [
        ("Starting position", "start"),
        ("After 1.e4", "e4"),
        ("Sicilian Defense", "e4 c5"),
        ("Scholar's mate setup", "e4 e5 Bc4 Nc6 Qh5"),
        ("FEN - Endgame", "8/8/8/8/8/8/6k1/4K2R w K - 0 1"),
        ("Complex middle game", "e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Be7 Re1 b5 Bb3 d6"),
    ]
    
    for description, position in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: {description}")
        print(f"Input: {position}")
        print('='*60)
        
        try:
            board = analyzer.parse_position(position)
            analysis = analyzer.analyze_position(board)
            print_analysis(board, analysis)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_positions()