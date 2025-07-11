#!/usr/bin/env python3
"""
Chess Position Analyzer - A one-shot utility to analyze chess positions using Stockfish
Usage: 
  python chess_analyzer.py                    # Analyze starting position
  python chess_analyzer.py e4                 # Analyze after 1.e4
  python chess_analyzer.py e4 e5              # Analyze after 1.e4 e5
  python chess_analyzer.py "start"            # Analyze starting position
  python chess_analyzer.py "<FEN string>"     # Analyze specific position

Supports multiple input formats and provides move recommendations with reasoning.
"""

import chess
import chess.engine
import chess.pgn
import sys
import re
from typing import List, Tuple, Optional

class ChessAnalyzer:
    def __init__(self, stockfish_path="/usr/games/stockfish", depth=15):
        """Initialize the chess analyzer with Stockfish engine."""
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        self.depth = depth
        
    def __del__(self):
        """Clean up the engine when object is destroyed."""
        if hasattr(self, 'engine'):
            self.engine.quit()
    
    def parse_position(self, position_str: str) -> chess.Board:
        """Parse various chess position formats into a chess.Board object."""
        position_str = position_str.strip()
        
        # FEN notation
        if len(position_str.split()) >= 4 and ('/' in position_str):
            try:
                return chess.Board(position_str)
            except ValueError:
                pass
        
        # PGN notation (sequence of moves) - try parsing as moves if it looks like algebraic notation
        if not ('/' in position_str and len(position_str.split()) >= 4):  # Not FEN
            try:
                board = chess.Board()
                # Split by spaces and clean up
                moves = position_str.replace(',', ' ').split()
                move_count = 0
                for move_str in moves:
                    move_str = move_str.strip('.,')
                    if move_str and not move_str.isdigit() and move_str != '...':
                        try:
                            move = board.parse_san(move_str)
                            board.push(move)
                            move_count += 1
                        except ValueError:
                            continue
                # If we successfully parsed at least one move, return the board
                if move_count > 0:
                    return board
            except:
                pass
        
        # Starting position keywords
        if position_str.lower() in ['start', 'starting', 'initial', 'new']:
            return chess.Board()
        
        # If nothing else works, try as FEN
        try:
            return chess.Board(position_str)
        except:
            raise ValueError(f"Could not parse position: {position_str}")
    
    def get_move_reasoning(self, board: chess.Board, move: chess.Move) -> str:
        """Generate reasoning for why a move is good."""
        reasoning = []
        
        # Make the move temporarily to analyze
        board_copy = board.copy()
        board_copy.push(move)
        
        # Basic move type analysis
        if board.is_capture(move):
            captured_piece = board.piece_at(move.to_square)
            if captured_piece:
                reasoning.append(f"Captures {captured_piece.symbol().upper()}")
        
        if board.is_check():
            reasoning.append("Gives check")
        
        if move.promotion:
            reasoning.append(f"Promotes to {chess.piece_name(move.promotion)}")
        
        # Castling
        if board.is_castling(move):
            reasoning.append("Castles for king safety")
        
        # Piece development/positioning
        piece = board.piece_at(move.from_square)
        if piece:
            piece_name = chess.piece_name(piece.piece_type).capitalize()
            
            # Central squares
            central_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
            if move.to_square in central_squares:
                reasoning.append(f"Controls center with {piece_name}")
            
            # Knight moves
            if piece.piece_type == chess.KNIGHT:
                if move.to_square in central_squares or move.to_square in [chess.C3, chess.F3, chess.C6, chess.F6]:
                    reasoning.append("Develops knight to active square")
            
            # Bishop moves
            if piece.piece_type == chess.BISHOP:
                if len(list(board_copy.attacks(move.to_square))) > len(list(board.attacks(move.from_square))):
                    reasoning.append("Improves bishop activity")
        
        # Tactical motifs
        if board_copy.is_checkmate():
            reasoning.append("Checkmate!")
        elif len(list(board_copy.legal_moves)) < len(list(board.legal_moves)):
            reasoning.append("Restricts opponent's options")
        
        return "; ".join(reasoning) if reasoning else "Positional improvement"
    
    def analyze_position(self, board: chess.Board, num_moves=3) -> List[Tuple[str, float, str, str]]:
        """Analyze position and return top moves with evaluations and reasoning."""
        try:
            # Get analysis from Stockfish
            info = self.engine.analyse(board, chess.engine.Limit(depth=self.depth), multipv=num_moves)
            
            results = []
            for i, analysis in enumerate(info[:num_moves]):
                if 'pv' in analysis and analysis['pv']:
                    move = analysis['pv'][0]
                    score = analysis.get('score', chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE))
                    
                    # Convert score to centipawns from White's perspective (always)
                    if score.is_mate():
                        mate_value = score.white().mate()
                        if mate_value > 0:
                            eval_str = f"Mate in {mate_value}"
                        else:
                            eval_str = f"Mate in {-mate_value}"
                    else:
                        # Always show score from White's perspective
                        cp_score = score.white().score()
                        eval_str = f"{cp_score/100:+.2f}"
                    
                    # Get principal variation (first few moves)
                    pv_moves = analysis['pv'][:4]  # Show first 4 moves of PV
                    board_copy = board.copy()
                    pv_moves_san = []
                    for pv_move in pv_moves:
                        if pv_move in board_copy.legal_moves:
                            pv_moves_san.append(board_copy.san(pv_move))
                            board_copy.push(pv_move)
                        else:
                            break
                    pv_str = " ".join(pv_moves_san)
                    
                    reasoning = self.get_move_reasoning(board, move)
                    
                    results.append((board.san(move), eval_str, pv_str, reasoning))
            
            return results
        except Exception as e:
            raise Exception(f"Analysis failed: {e}")

# ANSI color codes for terminal output
class Colors:
    WHITE = '\033[97m'
    BLACK = '\033[90m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def detect_opening(board: chess.Board) -> Optional[str]:
    """Detect opening name from current position."""
    # Reconstruct moves from starting position
    temp_board = chess.Board()
    moves = []
    
    # This is a simplified approach - in practice, we'd need to track the actual game
    # For now, we'll use common opening patterns based on piece positions
    
    opening_patterns = {
        # Starting position
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1": "Starting Position",
        
        # After 1.e4
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1": "King's Pawn Opening",
        
        # After 1.e4 e5
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2": "King's Pawn Game",
        
        # After 1.e4 c5
        "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2": "Sicilian Defense",
        
        # After 1.d4
        "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1": "Queen's Pawn Opening",
        
        # After 1.d4 d5
        "rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2": "Queen's Pawn Game",
        
        # After 1.e4 e5 2.Nf3
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2": "King's Knight Opening",
        
        # After 1.e4 e5 2.Nf3 Nc6
        "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3": "King's Knight Game",
        
        # After 1.e4 e5 2.Nf3 Nc6 3.Bb5 (Ruy Lopez)
        "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3": "Ruy Lopez",
        
        # After 1.e4 e5 2.Nf3 Nc6 3.Bc4 (Italian Game)
        "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3": "Italian Game",
        
        # After 1.e4 e5 2.Nf3 f5 (Latvian Gambit)
        "rnbqkbnr/pppp2pp/8/4pp2/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3": "Latvian Gambit",
    }
    
    fen_without_move_counters = " ".join(board.fen().split()[:4])
    full_fen = board.fen()
    
    # Check for exact FEN match first
    if full_fen in opening_patterns:
        return opening_patterns[full_fen]
    
    # Check for positional match (without move counters)
    for pattern_fen, name in opening_patterns.items():
        pattern_without_counters = " ".join(pattern_fen.split()[:4])
        if fen_without_move_counters == pattern_without_counters:
            return name
    
    return None

def get_evaluation_color(eval_str: str) -> str:
    """Get color for evaluation based on advantage level."""
    try:
        # Extract numeric value from evaluation string
        if "Mate" in eval_str:
            return Colors.GREEN + Colors.BOLD  # Mate is always significant
        
        eval_num = float(eval_str.replace('+', '').replace('-', ''))
        
        if eval_num >= 1.0:
            return Colors.GREEN  # Strong advantage
        elif eval_num >= 0.3:
            return Colors.YELLOW  # Slight advantage
        else:
            return Colors.WHITE  # Equal/minimal advantage
    except:
        return Colors.WHITE  # Default

def print_analysis(board: chess.Board, analysis: List[Tuple[str, float, str, str]]):
    """Print formatted analysis results with color coding."""
    # Color indicators for turn
    white_indicator = "⚪"
    black_indicator = "⚫"
    
    if board.turn == chess.WHITE:
        turn_display = f"\nTurn: {Colors.WHITE}{white_indicator} White{Colors.RESET}"
    else:
        turn_display = f"\nTurn: {Colors.BLACK}{Colors.BOLD}{black_indicator} Black{Colors.RESET}"
    
    print(f"FEN: {board.fen()}")
    
    # Detect and display opening name if available
    opening = detect_opening(board)
    if opening:
        print(f"Opening: {Colors.BLUE}{Colors.BOLD}{opening}{Colors.RESET}")
    
    print(turn_display)
    print(f"\n{Colors.BOLD}Top 3 Recommended Moves:{Colors.RESET}")
    print("-" * 60)
    
    for i, (move, evaluation, pv, reasoning) in enumerate(analysis, 1):
        eval_color = get_evaluation_color(evaluation)
        print(f"{Colors.BOLD}{i}.{Colors.RESET} {Colors.BOLD}{move}{Colors.RESET}")
        print(f"   Evaluation: {eval_color}{evaluation}{Colors.RESET}")
        print(f"   Principal Variation: {pv}")
        print(f"   Reasoning: {reasoning}")
        print()

def main():
    if len(sys.argv) > 1:
        # Analyze position from command line arguments
        position_input = " ".join(sys.argv[1:])
        
        try:
            analyzer = ChessAnalyzer()
            
            # Parse the position
            board = analyzer.parse_position(position_input)
            
            # Analyze the position
            analysis = analyzer.analyze_position(board)
            
            # Print results
            print_analysis(board, analysis)
            
        except ValueError as e:
            print(f"Error parsing position: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Analysis error: {e}")
            sys.exit(1)
    else:
        # No arguments = analyze starting position
        try:
            analyzer = ChessAnalyzer()
            
            # Parse starting position
            board = analyzer.parse_position("start")
            
            # Analyze the position
            analysis = analyzer.analyze_position(board)
            
            # Print results
            print_analysis(board, analysis)
            
        except Exception as e:
            print(f"Analysis error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
