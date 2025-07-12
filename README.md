# Chess Position Analyzer

A powerful terminal-based chess utility that uses Stockfish to analyze positions and suggest the best moves with **comprehensive, grandmaster-level reasoning**. Features advanced tactical pattern recognition, opening theory integration, positional analysis, and endgame expertise.

## Features

- **Multiple Input Formats**: 
  - FEN notation: `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1`
  - Move sequences: `e4 e5 Nf3 Nc6`
  - Starting position: `start` or `new`

- **Enhanced Analysis Output**:
  - Top 3 recommended moves with player-perspective color coding
  - Accurate evaluation scores (centipawns or mate distance)
  - Principal variations (first 4 moves)
  - **Rich multi-layered move reasoning**
  - Move sequence display with ellipsis for long games
  - Opening name detection and transitions

- **Comprehensive Move Reasoning**: 
  
  **🎯 Advanced Tactical Pattern Recognition**:
  - Knight forks, pins, skewers, discovered attacks
  - Checkmate detection and check analysis
  - Piece capture evaluation with values
  
  **📚 Opening Theory Integration**:
  - Opening name detection (100+ patterns)
  - Opening transitions and theoretical moves
  - Classical opening principles (knights before bishops)
  - Specific opening context (Ruy Lopez, Italian Game, etc.)
  
  **⚡ Deep Positional Analysis**:
  - Piece activity and mobility improvements
  - Central square control and support
  - King safety considerations and castling
  - Pawn structure analysis (chains, outposts)
  - Piece development from starting positions
  
  **👑 Endgame Expertise**:
  - King activation and centralization
  - Passed pawn advancement detection
  - Endgame-specific strategic principles
  - Material count-based endgame recognition

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

### Enhanced Analysis with Rich Reasoning

**Opening Position Analysis (Ruy Lopez):**
```
Move Sequence: 1.e4 e5 2.Nf3 Nc6 3.Bb5
FEN: r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3
Opening: Spanish Opening

Turn: ⚫ Black

Top 3 Recommended Moves:
------------------------------------------------------------
1. a6
   Evaluation: +0.39
   Principal Variation: a6 Ba4 Nf6 O-O
   Reasoning: Transitions to Ruy Lopez, Morphy Defense; Creates pawn chain

2. Nf6
   Evaluation: +0.39
   Principal Variation: Nf6 O-O Nxe4 Re1
   Reasoning: Transitions to Ruy Lopez, Berlin Defense; Increases knight activity; Supports center control

3. Bc5
   Evaluation: +0.47
   Principal Variation: Bc5 c3 Nge7 O-O
   Reasoning: Increases bishop activity; Supports center control
```

**Tactical Position with Advanced Pattern Recognition:**
```
Move Sequence: ...3.d4 exd4 4.Nxd4 Bc5 5.Be3
FEN: r1bqk1nr/pppp1ppp/2n5/2b5/3NP3/4B3/PPP2PPP/RN1QKB1R b KQkq - 2 5

Turn: ⚫ Black

Top 3 Recommended Moves:
------------------------------------------------------------
1. Qf6
   Evaluation: +0.10
   Principal Variation: Qf6 c3 Nge7 Bc4
   Reasoning: Pins pawn; Increases queen activity; Supports center control

2. Nxd4
   Evaluation: +0.39
   Principal Variation: Nxd4 Bxd4 Bxd4 Qxd4
   Reasoning: Captures N; Controls central square

3. Bxd4
   Evaluation: +0.41
   Principal Variation: Bxd4 Bxd4 Nxd4 Qxd4
   Reasoning: Captures N; Pins pawn; Controls central square
```

**Endgame Analysis with King Activation:**
```
Move Sequence: (starting position)
FEN: 8/2k5/8/8/3K4/8/3P4/8 w - - 0 1

Turn: ⚪ White

Top 3 Recommended Moves:
------------------------------------------------------------
1. Kd5
   Evaluation: +7.46
   Principal Variation: Kd5 Kd7 d4 Ke7
   Reasoning: Controls central square; King activation in endgame

2. Kc5
   Evaluation: +7.46
   Principal Variation: Kc5 Kd7 Kd5 Ke7
   Reasoning: Supports center control; King activation in endgame

3. Ke4
   Evaluation: +7.46
   Principal Variation: Ke4 Kd6 Kd4 Ke6
   Reasoning: Controls central square; King activation in endgame
```

### Key Improvements Over Basic Analysis

**Before (Basic):**
- `"Develops knight to active square"`
- `"Restricts opponent's options"`
- `"Positional improvement"`

**After (Enhanced):**
- `"Transitions to Ruy Lopez, Berlin Defense; Increases knight activity; Supports center control"`
- `"Pins pawn; Increases queen activity; Supports center control"`
- `"Controls central square; King activation in endgame"`

The enhanced system provides **3-5x more detailed reasoning** with tactical awareness, opening theory, and strategic understanding.

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
