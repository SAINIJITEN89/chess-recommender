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

def print_analysis(board: chess.Board, analysis: List[Tuple[str, float, str, str]]):
    """Print formatted analysis results."""
    print(f"Turn: {'White' if board.turn == chess.WHITE else 'Black'}")
    print(f"FEN: {board.fen()}")
    print("\nTop 3 Recommended Moves:")
    print("-" * 80)
    
    for i, (move, evaluation, pv, reasoning) in enumerate(analysis, 1):
        print(f"{i}. {move}")
        print(f"   Evaluation: {evaluation}")
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
