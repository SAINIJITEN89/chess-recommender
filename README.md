# Chess Position Analyzer

A terminal-based chess utility that uses Stockfish to analyze positions and suggest the best moves with detailed reasoning.

## Features

- **Multiple Input Formats**: 
  - FEN notation: `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1`
  - Move sequences: `e4 e5 Nf3 Nc6`
  - Starting position: `start` or `new`

- **Analysis Output**:
  - Top 3 recommended moves
  - Evaluation scores (centipawns or mate distance)
  - Principal variations (first 4 moves)
  - Reasoning behind each move

- **Move Reasoning**: Explains tactical and positional concepts like:
  - Piece captures and values
  - Central control
  - Piece development
  - King safety (castling)
  - Tactical motifs (checks, threats)

## Setup

1. **Install dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install python-chess
   ```

2. **Install Stockfish** (if not already installed):
   ```bash
   # Ubuntu/Debian
   sudo apt install stockfish
   
   # macOS
   brew install stockfish
   
   # Or download from: https://stockfishchess.org/download/
   ```

3. **Verify installation**:
   ```bash
   # Check Stockfish is available
   which stockfish
   
   # Test the chess recommender
   source venv/bin/activate
   python test_positions.py
   ```

## Usage

### Command Line Analysis
```bash
# Activate virtual environment first
source venv/bin/activate

# Analyze starting position (no arguments)
python chess_analyzer.py

# Analyze positions from command line
python chess_analyzer.py e4
python chess_analyzer.py e4 e5
python chess_analyzer.py start
python chess_analyzer.py "e4 e5 Nf3 Nc6 Bb5"
python chess_analyzer.py "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
```

### Easy Usage with Wrapper Script
The repository includes a `chessbuddy` wrapper script for convenient usage:

```bash
# Use the wrapper script directly
./chessbuddy          # Analyze starting position
./chessbuddy e4       # Analyze after 1.e4
./chessbuddy e4 e5    # Analyze after 1.e4 e5
./chessbuddy "e4 e5 Nf3 Nc6"  # Analyze longer sequences
```

### Create a Global Alias
To use `chessbuddy` from anywhere, add this function to your `~/.bash_aliases`:

```bash
# Add this function to ~/.bash_aliases
chessbuddy() {
    cd /path/to/chess-recommender && source venv/bin/activate && python chess_analyzer.py "$@"
}

# Or run the setup script
./setup_alias.sh
```

Then you can use it from anywhere:
```bash
chessbuddy           # Analyze starting position
chessbuddy e4        # Analyze after 1.e4  
chessbuddy e4 e5     # Analyze after 1.e4 e5
chessbuddy "e4 e5 Nf3 Nc6"  # Analyze longer sequences
```

### Test with Sample Positions
```bash
source venv/bin/activate
python test_positions.py
```

### Supported Input Formats

1. **FEN Notation** (complete position):
   ```
   rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
   ```

2. **Move Sequences** (from starting position):
   ```
   e4 e5 Nf3 Nc6
   1.e4 e5 2.Nf3 Nc6
   ```

3. **Starting Position Keywords**:
   ```
   start
   new
   initial
   ```

## Example Output

```
Enter chess position: e4 e5 Nf3 Nc6 Bb5

Position Analysis:
Turn: Black
FEN: r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3

Top 3 Recommended Moves:
--------------------------------------------------------------------------------
1. a6
   Evaluation: -0.11
   Principal Variation: a6 Ba4 Nf6 O-O
   Reasoning: Restricts opponent's options

2. Nf6
   Evaluation: -0.20
   Principal Variation: Nf6 O-O Nxe4 d3
   Reasoning: Develops knight to active square

3. f5
   Evaluation: -0.47
   Principal Variation: f5 exf5 Nf6 Nc3
   Reasoning: Positional improvement
```

## Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: No module named 'chess'"**
   ```bash
   # Ensure virtual environment is activated
   source venv/bin/activate
   pip install python-chess
   ```

2. **"FileNotFoundError: [Errno 2] No such file or directory: '/usr/games/stockfish'"**
   ```bash
   # Install Stockfish or specify custom path
   sudo apt install stockfish
   # Or modify chess_analyzer.py line 15 with correct path
   ```

3. **Analysis takes too long**
   ```bash
   # Reduce analysis depth (default: 15)
   # Modify chess_analyzer.py line 15: depth=10
   ```

## Requirements

- Python 3.8+
- python-chess library
- Stockfish engine
- Linux/Unix/macOS environment

## Files

- `chess_analyzer.py`: Main chess analysis utility
- `test_positions.py`: Test script with sample positions
- `venv/`: Python virtual environment (created during setup)
