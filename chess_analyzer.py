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
        
        # Starting position keywords - check this first
        if position_str.lower() in ['start', 'starting', 'initial', 'new']:
            return chess.Board()
        
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
                invalid_moves = []
                
                # First pass: validate all moves before processing any
                temp_board = chess.Board()
                for i, move_str in enumerate(moves):
                    move_str = move_str.strip('.,')
                    if move_str and not move_str.isdigit() and move_str != '...':
                        try:
                            move = temp_board.parse_san(move_str)
                            temp_board.push(move)
                        except ValueError:
                            # Track invalid moves with their position
                            invalid_moves.append((i + 1, move_str))
                
                # If any invalid moves found, reject the entire sequence
                if invalid_moves:
                    invalid_list = ", ".join([f"{Colors.RED}'{move}'{Colors.RESET} (position {pos})" for pos, move in invalid_moves])
                    total_moves = len([m for m in moves if m.strip('.,') and not m.isdigit() and m != '...'])
                    raise ValueError(f"\n{Colors.RED}Invalid move sequence:{Colors.RESET} {invalid_list}\n")
                
                # If all moves are valid, process them
                move_count = 0
                for move_str in moves:
                    move_str = move_str.strip('.,')
                    if move_str and not move_str.isdigit() and move_str != '...':
                        move = board.parse_san(move_str)
                        board.push(move)
                        move_count += 1
                
                # If we successfully parsed at least one move, return the board
                if move_count > 0:
                    return board
            except ValueError:
                # Re-raise ValueError with move parsing details
                raise
            except:
                pass
        
        # If nothing else works, try as FEN
        try:
            return chess.Board(position_str)
        except:
            raise ValueError(f"Could not parse position: {position_str}")
    
    def detect_tactical_patterns(self, board: chess.Board, move: chess.Move) -> List[str]:
        """Detect tactical patterns and motifs in the move."""
        patterns = []
        board_copy = board.copy()
        
        # Check if move creates or exploits tactical motifs
        piece = board.piece_at(move.from_square)
        target_piece = board.piece_at(move.to_square)
        
        # Fork detection
        if piece and piece.piece_type == chess.KNIGHT:
            board_copy.push(move)
            attacks = list(board_copy.attacks(move.to_square))
            valuable_targets = []
            for square in attacks:
                attacked_piece = board_copy.piece_at(square)
                if attacked_piece and attacked_piece.color != piece.color:
                    if attacked_piece.piece_type in [chess.KING, chess.QUEEN, chess.ROOK]:
                        valuable_targets.append(attacked_piece.piece_type)
            if len(valuable_targets) >= 2:
                patterns.append("Creates knight fork")
            board_copy.pop()
        
        # Pin detection
        if piece and piece.piece_type in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
            board_copy.push(move)
            # Check if move creates a pin along the piece's attack lines
            for square in board_copy.attacks(move.to_square):
                pinned_piece = board_copy.piece_at(square)
                if pinned_piece and pinned_piece.color != piece.color:
                    # Check if there's a more valuable piece behind it
                    from_file, from_rank = chess.square_file(move.to_square), chess.square_rank(move.to_square)
                    to_file, to_rank = chess.square_file(square), chess.square_rank(square)
                    
                    # Calculate direction
                    file_diff = to_file - from_file
                    rank_diff = to_rank - from_rank
                    
                    if file_diff != 0:
                        file_diff = file_diff // abs(file_diff)
                    if rank_diff != 0:
                        rank_diff = rank_diff // abs(rank_diff)
                    
                    # Look beyond the pinned piece
                    next_file = to_file + file_diff
                    next_rank = to_rank + rank_diff
                    
                    while 0 <= next_file <= 7 and 0 <= next_rank <= 7:
                        next_square = chess.square(next_file, next_rank)
                        behind_piece = board_copy.piece_at(next_square)
                        if behind_piece:
                            if (behind_piece.color != piece.color and 
                                behind_piece.piece_type > pinned_piece.piece_type):
                                patterns.append(f"Pins {chess.piece_name(pinned_piece.piece_type)}")
                            break
                        next_file += file_diff
                        next_rank += rank_diff
            board_copy.pop()
        
        # Skewer detection (similar to pin but with valuable piece in front)
        if piece and piece.piece_type in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
            if target_piece and target_piece.piece_type in [chess.KING, chess.QUEEN]:
                patterns.append("Creates skewer threat")
        
        # Discovered attack
        if piece:
            # Check if moving this piece reveals an attack from another piece
            for square in chess.SQUARES:
                ally_piece = board.piece_at(square)
                if (ally_piece and ally_piece.color == piece.color and 
                    ally_piece.piece_type in [chess.BISHOP, chess.ROOK, chess.QUEEN]):
                    # Check if move.from_square was blocking ally_piece's attack
                    attacks_before = list(board.attacks(square))
                    board_copy.push(move)
                    attacks_after = list(board_copy.attacks(square))
                    board_copy.pop()
                    
                    new_attacks = set(attacks_after) - set(attacks_before)
                    for new_target in new_attacks:
                        attacked_piece = board.piece_at(new_target)
                        if (attacked_piece and attacked_piece.color != piece.color and
                            attacked_piece.piece_type in [chess.KING, chess.QUEEN, chess.ROOK]):
                            patterns.append("Discovered attack")
                            break
        
        return patterns

    def analyze_positional_factors(self, board: chess.Board, move: chess.Move) -> List[str]:
        """Analyze positional aspects of the move."""
        factors = []
        piece = board.piece_at(move.from_square)
        
        if not piece:
            return factors
        
        board_copy = board.copy()
        
        # Piece activity analysis
        attacks_before = len(list(board.attacks(move.from_square)))
        board_copy.push(move)
        attacks_after = len(list(board_copy.attacks(move.to_square)))
        board_copy.pop()
        
        if attacks_after > attacks_before + 1:
            factors.append(f"Increases {chess.piece_name(piece.piece_type)} activity")
        
        # Central control
        central_squares = {chess.D4, chess.D5, chess.E4, chess.E5}
        extended_center = {chess.C3, chess.C4, chess.C5, chess.C6, 
                          chess.D3, chess.D6, chess.E3, chess.E6,
                          chess.F3, chess.F4, chess.F5, chess.F6}
        
        if move.to_square in central_squares:
            factors.append("Controls central square")
        elif move.to_square in extended_center:
            factors.append("Supports center control")
        
        # King safety considerations
        if piece.piece_type == chess.KING:
            if board.is_castling(move):
                factors.append("Improves king safety through castling")
            else:
                # Check if king is moving to safety
                file_distance = abs(chess.square_file(move.to_square) - 3.5)
                if file_distance > abs(chess.square_file(move.from_square) - 3.5):
                    factors.append("King seeks safety on the flank")
        
        # Piece development
        if piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
            back_rank = 0 if piece.color == chess.WHITE else 7
            if chess.square_rank(move.from_square) == back_rank:
                factors.append(f"Develops {chess.piece_name(piece.piece_type)}")
        
        # Pawn structure considerations
        if piece.piece_type == chess.PAWN:
            # Pawn advancement
            if piece.color == chess.WHITE and chess.square_rank(move.to_square) >= 4:
                factors.append("Advances pawn to strong outpost")
            elif piece.color == chess.BLACK and chess.square_rank(move.to_square) <= 3:
                factors.append("Advances pawn to strong outpost")
            
            # Pawn support
            board_copy.push(move)
            pawn_file = chess.square_file(move.to_square)
            for adjacent_file in [pawn_file - 1, pawn_file + 1]:
                if 0 <= adjacent_file <= 7:
                    support_square = chess.square(adjacent_file, chess.square_rank(move.to_square) - (1 if piece.color == chess.WHITE else -1))
                    if 0 <= support_square <= 63:
                        support_piece = board_copy.piece_at(support_square)
                        if (support_piece and support_piece.piece_type == chess.PAWN and 
                            support_piece.color == piece.color):
                            factors.append("Creates pawn chain")
                            break
            board_copy.pop()
        
        return factors

    def get_opening_context(self, board: chess.Board, move: chess.Move) -> str:
        """Get opening-specific context for the move."""
        # Check if we're still in opening (rough heuristic)
        if len(board.move_stack) > 15:
            return ""
        
        # Get current opening name
        opening = detect_opening(board)
        if not opening:
            return ""
        
        # Make the move and see if it leads to a known opening
        board_copy = board.copy()
        board_copy.push(move)
        new_opening = detect_opening(board_copy)
        
        if new_opening and new_opening != opening:
            return f"Transitions to {new_opening}"
        elif opening:
            # Common opening principles
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.KNIGHT:
                if move.to_square in [chess.F3, chess.C3] and piece.color == chess.WHITE:
                    return "Follows opening principle: knights before bishops"
                elif move.to_square in [chess.F6, chess.C6] and piece.color == chess.BLACK:
                    return "Follows opening principle: knights before bishops"
            
            if piece and piece.piece_type == chess.BISHOP:
                if opening.startswith("Ruy Lopez") and move.to_square == chess.B5:
                    return "Classical Ruy Lopez development"
                elif opening.startswith("Italian") and move.to_square == chess.C4:
                    return "Italian Game bishop development"
        
        return ""

    def evaluate_endgame_factors(self, board: chess.Board, move: chess.Move) -> List[str]:
        """Analyze endgame-specific factors."""
        factors = []
        
        # Simple material count to detect endgame
        material_count = sum(1 for square in chess.SQUARES 
                           if board.piece_at(square) and board.piece_at(square).piece_type != chess.KING)
        
        if material_count <= 12:  # Rough endgame threshold
            piece = board.piece_at(move.from_square)
            
            if piece and piece.piece_type == chess.KING:
                factors.append("King activation in endgame")
                
                # King centralization
                center_distance_before = max(abs(chess.square_file(move.from_square) - 3.5),
                                           abs(chess.square_rank(move.from_square) - 3.5))
                center_distance_after = max(abs(chess.square_file(move.to_square) - 3.5),
                                          abs(chess.square_rank(move.to_square) - 3.5))
                
                if center_distance_after < center_distance_before:
                    factors.append("Centralizes king")
            
            elif piece and piece.piece_type == chess.PAWN:
                # Passed pawn advancement
                pawn_file = chess.square_file(move.to_square)
                is_passed = True
                
                for rank in range(8):
                    for file_offset in [-1, 0, 1]:
                        check_file = pawn_file + file_offset
                        if 0 <= check_file <= 7:
                            check_square = chess.square(check_file, rank)
                            enemy_piece = board.piece_at(check_square)
                            if (enemy_piece and enemy_piece.piece_type == chess.PAWN and 
                                enemy_piece.color != piece.color):
                                # Check if this pawn blocks our pawn's advance
                                if piece.color == chess.WHITE and rank > chess.square_rank(move.to_square):
                                    is_passed = False
                                elif piece.color == chess.BLACK and rank < chess.square_rank(move.to_square):
                                    is_passed = False
                
                if is_passed:
                    factors.append("Advances passed pawn")
        
        return factors

    def get_move_reasoning(self, board: chess.Board, move: chess.Move) -> str:
        """Generate comprehensive reasoning for why a move is good."""
        reasoning_parts = []
        
        # 1. Basic tactical elements
        basic_tactics = []
        if board.is_capture(move):
            captured_piece = board.piece_at(move.to_square)
            if captured_piece:
                basic_tactics.append(f"Captures {captured_piece.symbol().upper()}")
        
        board_copy = board.copy()
        board_copy.push(move)
        
        if board_copy.is_checkmate():
            basic_tactics.append("Checkmate!")
        elif board_copy.is_check():
            basic_tactics.append("Gives check")
        
        if move.promotion:
            basic_tactics.append(f"Promotes to {chess.piece_name(move.promotion)}")
        
        if board.is_castling(move):
            basic_tactics.append("Castles for king safety")
        
        # 2. Advanced tactical patterns
        tactical_patterns = self.detect_tactical_patterns(board, move)
        
        # 3. Positional factors
        positional_factors = self.analyze_positional_factors(board, move)
        
        # 4. Opening context
        opening_context = self.get_opening_context(board, move)
        
        # 5. Endgame considerations
        endgame_factors = self.evaluate_endgame_factors(board, move)
        
        # Compile reasoning with priorities
        if basic_tactics:
            reasoning_parts.extend(basic_tactics)
        
        if tactical_patterns:
            reasoning_parts.extend(tactical_patterns)
        
        if opening_context:
            reasoning_parts.append(opening_context)
        
        if positional_factors:
            reasoning_parts.extend(positional_factors[:2])  # Limit to top 2 positional factors
        
        if endgame_factors:
            reasoning_parts.extend(endgame_factors)
        
        # If no specific reasoning found, provide generic positional assessment
        if not reasoning_parts:
            piece = board.piece_at(move.from_square)
            if piece:
                reasoning_parts.append(f"Improves {chess.piece_name(piece.piece_type)} position")
            else:
                reasoning_parts.append("Positional improvement")
        
        return "; ".join(reasoning_parts)
    
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
        # === KING'S PAWN OPENINGS (1.e4) ===
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1": "King's Pawn Opening",
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2": "King's Pawn Game",
        
        # King's Knight Opening
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2": "King's Knight Opening",
        "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3": "King's Knight Game",
        
        # Italian Game
        "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3": "Italian Game",
        "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4": "Italian Game, Knight Defense",
        "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 5 4": "Italian Game, Classical",
        
        # Spanish/Ruy Lopez
        "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3": "Ruy Lopez",
        "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3": "Spanish Opening",
        "r1bqkbnr/pppp2pp/2n2p2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4": "Ruy Lopez, Steinitz Defense",
        "r1bqkbnr/1ppp1ppp/p1n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4": "Ruy Lopez, Morphy Defense",
        "r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4": "Ruy Lopez, Berlin Defense",
        
        # Scotch Game
        "r1bqkbnr/pppp1ppp/2n5/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 3": "Scotch Game",
        "r1bqkbnr/pppp1ppp/2n5/8/3pP3/5N2/PPP2PPP/RNBQKB1R w KQkq - 0 4": "Scotch Game, Classical",
        
        # Four Knights Game
        "r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 4 4": "Four Knights Game",
        "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/2N2N2/PPPP1PPP/R1B1K2R b KQkq - 5 4": "Four Knights, Fried Liver Attack",
        
        # King's Gambit
        "rnbqkbnr/pppp1ppp/8/4p3/4PP2/8/PPPP2PP/RNBQKBNR b KQkq - 0 2": "King's Gambit",
        "rnbqkbnr/pppp1p1p/8/4p1p1/4PP2/8/PPPP2PP/RNBQKBNR w KQkq - 0 3": "King's Gambit Accepted",
        "rnbqkbnr/pppp1ppp/8/8/4Pp2/8/PPPP2PP/RNBQKBNR w KQkq - 0 3": "King's Gambit Declined",
        
        # Vienna Game
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/2N5/PPPP1PPP/R1BQKBNR b KQkq - 1 2": "Vienna Game",
        "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 3": "Vienna Game, Main Line",
        
        # Center Game
        "rnbqkbnr/pppp1ppp/8/4p3/3PP3/8/PPP2PPP/RNBQKBNR b KQkq - 0 2": "Center Game",
        
        # Petrov's Defense
        "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3": "Petrov's Defense",
        "rnbqkb1r/pppp1ppp/5n2/4N3/4P3/8/PPPP1PPP/RNBQKB1R b KQkq - 3 3": "Petrov's Defense, Classical",
        
        # === SICILIAN DEFENSE VARIATIONS (1.e4 c5) ===
        "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2": "Sicilian Defense",
        "rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2": "Sicilian Defense, Open",
        "rnbqkbnr/pppppppp/8/8/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2": "Sicilian Defense, Closed",
        
        # Sicilian Dragon
        "rnbqkb1r/pp1ppppp/5n2/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3": "Sicilian Defense, Alekhine Variation",
        "rnbqk2r/pp1pppbp/5np1/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 3 4": "Sicilian Defense, Dragon Variation",
        "rnbqkb1r/pp1ppp1p/5np1/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 4": "Sicilian Defense, Accelerated Dragon",
        
        # Sicilian Najdorf
        "rnbqkb1r/1p1ppppp/p4n2/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 4": "Sicilian Defense, Najdorf Variation",
        
        # === FRENCH DEFENSE (1.e4 e6) ===
        "rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2": "French Defense",
        "rnbqkbnr/pppp1ppp/4p3/8/3PP3/8/PPP2PPP/RNBQKBNR b KQkq - 0 2": "French Defense, Advance Variation",
        "rnbqkbnr/ppp2ppp/4p3/3p4/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3": "French Defense, Exchange Variation",
        "rnbqkbnr/ppp2ppp/4p3/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 3": "French Defense, Exchange Variation",
        
        # === CARO-KANN DEFENSE (1.e4 c6) ===
        "rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2": "Caro-Kann Defense",
        "rnbqkbnr/pp1ppppp/2p5/8/3PP3/8/PPP2PPP/RNBQKBNR b KQkq - 0 2": "Caro-Kann Defense, Advance Variation",
        "rnbqkbnr/pp2pppp/2p5/3p4/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3": "Caro-Kann Defense, Exchange Variation",
        
        # === ALEKHINE'S DEFENSE (1.e4 Nf6) ===
        "rnbqkb1r/pppppppp/5n2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 1 2": "Alekhine's Defense",
        "rnbqkb1r/pppppppp/5n2/8/3PP3/8/PPP2PPP/RNBQKBNR b KQkq - 0 2": "Alekhine's Defense, Chase Variation",
        
        # === SCANDINAVIAN DEFENSE (1.e4 d5) ===
        "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2": "Scandinavian Defense",
        "rnbqkbnr/ppp1pppp/8/8/3pP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3": "Scandinavian Defense, Modern Variation",
        
        # === QUEEN'S PAWN OPENINGS (1.d4) ===
        "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1": "Queen's Pawn Opening",
        "rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2": "Queen's Pawn Game",
        
        # Queen's Gambit
        "rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2": "Queen's Gambit",
        "rnbqkbnr/ppp2ppp/8/3pp3/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3": "Queen's Gambit Accepted",
        "rnbqkbnr/ppp1pppp/8/8/2pP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3": "Queen's Gambit Declined",
        
        # King's Indian Defense
        "rnbqkb1r/pppppp1p/5np1/8/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 2 3": "King's Indian Defense",
        "rnbqk2r/ppppppbp/5np1/8/2PP4/2N5/PP2PPPP/R1BQKBNR b KQkq - 3 4": "King's Indian Defense, Classical",
        
        # Nimzo-Indian Defense  
        "rnbqk2r/pppp1ppp/4pn2/8/1bPP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 2 4": "Nimzo-Indian Defense",
        "rnbqk2r/pppp1ppp/4pn2/8/1bPP4/2N2N2/PP2PPPP/R1BQKB1R b KQkq - 3 4": "Nimzo-Indian Defense, Classical",
        
        # Queen's Indian Defense
        "rnbqkb1r/p1pp1ppp/1p2pn2/8/2PP4/5N2/PP2PPPP/RNBQKB1R w KQkq - 0 4": "Queen's Indian Defense",
        
        # Grünfeld Defense
        "rnbqkb1r/ppp1pp1p/5np1/3p4/2PP4/2N5/PP2PPPP/R1BQKBNR b KQkq - 2 4": "Grünfeld Defense",
        "rnbqk2r/ppp1ppbp/5np1/3p4/2PP4/2N2N2/PP2PPPP/R1BQKB1R b KQkq - 3 5": "Grünfeld Defense, Exchange Variation",
        
        # === ENGLISH OPENING (1.c4) ===
        "rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b KQkq - 0 1": "English Opening",
        "rnbqkbnr/pppp1ppp/8/4p3/2P5/8/PP1PPPPP/RNBQKBNR w KQkq - 0 2": "English Opening, King's English",
        "rnbqkbnr/pp1ppppp/8/2p5/2P5/8/PP1PPPPP/RNBQKBNR w KQkq - 0 2": "English Opening, Symmetrical",
        "rnbqkb1r/pppppppp/5n2/8/2P5/8/PP1PPPPP/RNBQKBNR w KQkq - 1 2": "English Opening, Anglo-Indian Defense",
        
        # === FLANK OPENINGS ===
        # Réti Opening
        "rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 1 1": "Réti Opening",
        "rnbqkbnr/ppp1pppp/8/3p4/8/5N2/PPPPPPPP/RNBQKB1R w KQkq - 0 2": "Réti Opening, Queen's Pawn Defense",
        
        # Bird's Opening
        "rnbqkbnr/pppppppp/8/8/5P2/8/PPPPP1PP/RNBQKBNR b KQkq - 0 1": "Bird's Opening",
        "rnbqkbnr/ppp1pppp/8/3p4/5P2/8/PPPPP1PP/RNBQKBNR w KQkq - 0 2": "Bird's Opening, Dutch Defense",
        
        # Larsen's Opening
        "rnbqkbnr/pppppppp/8/8/8/1P6/P1PPPPPP/RNBQKBNR b KQkq - 0 1": "Larsen's Opening",
        
        # Polish Opening
        "rnbqkbnr/pppppppp/8/8/1P6/8/P1PPPPPP/RNBQKBNR b KQkq - 0 1": "Polish Opening",
        
        # === IRREGULAR OPENINGS ===
        "rnbqkbnr/pppp1ppp/8/4p3/4PP2/8/PPPP2PP/RNBQKBNR b KQkq - 0 2": "King's Gambit",
        "rnbqkbnr/pppp2pp/8/4pp2/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3": "Latvian Gambit",
        "rnbq1rk1/ppp2ppp/4pn2/3p4/1bPP4/2N2N2/PP2PPPP/R1BQKB1R w KQ - 4 6": "Nimzo-Indian Defense, Rubinstein Variation",
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

def get_evaluation_color(eval_str: str, board: chess.Board) -> str:
    """Get color for evaluation based on advantage level and current player perspective."""
    try:
        # Handle mate evaluations
        if "Mate" in eval_str:
            # Extract mate sign and consider player perspective
            mate_is_positive = not eval_str.startswith('-')
            
            # Mate evaluations are from White's perspective:
            # Positive mate = White delivers mate
            # Negative mate = Black delivers mate
            if board.turn == chess.WHITE:
                # White's turn: positive mate = good, negative mate = bad
                if mate_is_positive:
                    return Colors.GREEN + Colors.BOLD  # White delivers mate
                else:
                    return Colors.RED + Colors.BOLD    # Black delivers mate (bad for White)
            else:
                # Black's turn: negative mate = good, positive mate = bad  
                if mate_is_positive:
                    return Colors.RED + Colors.BOLD    # White delivers mate (bad for Black)
                else:
                    return Colors.GREEN + Colors.BOLD  # Black delivers mate
        
        # Extract numeric value keeping the sign
        eval_num = float(eval_str.replace('+', ''))
        
        # Adjust evaluation based on whose turn it is
        # Chess evaluations are from White's perspective
        if board.turn == chess.BLACK:
            eval_num = -eval_num  # Flip for Black's perspective
        
        # Color based on advantage for current player
        if eval_num >= 1.0:
            return Colors.GREEN  # Strong advantage
        elif eval_num >= 0.3:
            return Colors.YELLOW  # Slight advantage
        elif eval_num <= -1.0:
            return Colors.RED  # Strong disadvantage
        elif eval_num <= -0.3:
            return Colors.YELLOW  # Slight disadvantage
        else:
            return Colors.WHITE  # Equal/minimal advantage
    except:
        return Colors.WHITE  # Default

def format_move_sequence(board: chess.Board) -> str:
    """Format the move sequence in a readable format."""
    if not board.move_stack:
        return "(starting position)"
    
    moves = []
    temp_board = chess.Board()
    
    for i, move in enumerate(board.move_stack):
        move_number = (i // 2) + 1
        if i % 2 == 0:  # White's move
            moves.append(f"{move_number}.{temp_board.san(move)}")
        else:  # Black's move
            moves.append(temp_board.san(move))
        temp_board.push(move)
    
    total_pairs = (len(board.move_stack) + 1) // 2
    
    if total_pairs <= 3:
        return " ".join(moves)
    else:
        # Show last 3 pairs with ellipsis
        last_moves = []
        start_index = max(0, len(moves) - 6)  # Last 6 half-moves = 3 pairs
        
        # Adjust start_index to begin with a move number
        while start_index < len(moves) and not moves[start_index].split('.')[0].isdigit():
            start_index += 1
        
        if start_index < len(moves):
            last_moves = moves[start_index:]
            return "..." + " ".join(last_moves)
        else:
            # Fallback to last few moves
            return "..." + " ".join(moves[-6:])

def print_analysis(board: chess.Board, analysis: List[Tuple[str, float, str, str]]):
    """Print formatted analysis results with color coding."""
    # Color indicators for turn
    white_indicator = "⚪"
    black_indicator = "⚫"
    
    if board.turn == chess.WHITE:
        turn_display = f"\n{Colors.BOLD}Turn:{Colors.RESET} {Colors.WHITE}{white_indicator} White{Colors.RESET}"
    else:
        turn_display = f"\n{Colors.BOLD}Turn:{Colors.RESET} {Colors.BLACK}{Colors.BOLD}{black_indicator} Black{Colors.RESET}"
    
    move_sequence = format_move_sequence(board)
    print(f"{Colors.BOLD}Move Sequence:{Colors.RESET} {move_sequence}")
    print(f"{Colors.BOLD}FEN:{Colors.RESET} {board.fen()}")
    
    # Detect and display opening name if available
    opening = detect_opening(board)
    if opening:
        print(f"{Colors.BOLD}Opening:{Colors.RESET} {Colors.BLUE}{Colors.BOLD}{opening}{Colors.RESET}")
    
    print(turn_display)
    print(f"\n{Colors.BOLD}Top 3 Recommended Moves:{Colors.RESET}")
    print("-" * 60)
    
    for i, (move, evaluation, pv, reasoning) in enumerate(analysis, 1):
        eval_color = get_evaluation_color(evaluation, board)
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
            print(f"{Colors.RED}{e}{Colors.RESET}")
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
