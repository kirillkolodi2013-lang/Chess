
import tkinter as tk
from tkinter import messagebox
import chess

SQUARE_SIZE = 72

COLORS = {
    "light": "#F0D9B5",
    "dark": "#B58863",
    "selected": "#F7EC55",
    "move": "#A9CF75",
    "last": "#F6E36B"
}

PIECES = {
    "K": "♔", "Q": "♕", "R": "♖",
    "B": "♗", "N": "♘", "P": "♙",
    "k": "♚", "q": "♛", "r": "♜",
    "b": "♝", "n": "♞", "p": "♟"
}


class ChessGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess — Шахматы")
        self.root.resizable(False, False)

        self.board = chess.Board()
        self.selected = None
        self.legal_targets = []
        self.last_move = None
        self.history = []

        self.status = tk.Label(
            root,
            text="Ход белых",
            font=("Arial", 16, "bold")
        )
        self.status.pack(pady=10)

        self.board_frame = tk.Frame(root)
        self.board_frame.pack(padx=12, pady=5)

        self.buttons = []

        for row in range(8):
            button_row = []

            for col in range(8):
                button = tk.Button(
                    self.board_frame,
                    width=3,
                    height=1,
                    font=("Arial", 30),
                    relief="flat",
                    command=lambda r=row, c=col: self.click(r, c)
                )
                button.grid(row=row, column=col)
                button_row.append(button)

            self.buttons.append(button_row)

        self.draw_board()

    def draw_board(self):
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                piece = self.board.piece_at(square)

                color = (
                    COLORS["light"]
                    if (row + col) % 2 == 0
                    else COLORS["dark"]
                )

                if self.last_move and square in (
                    self.last_move.from_square,
                    self.last_move.to_square
                ):
                    color = COLORS["last"]

                if square in self.legal_targets:
                    color = COLORS["move"]

                if square == self.selected:
                    color = COLORS["selected"]

                symbol = PIECES[piece.symbol()] if piece else ""

                self.buttons[row][col].config(
                    text=symbol,
                    bg=color,
                    activebackground=color
                )

    def click(self, row, col):
        if self.board.is_game_over():
            return

        square = chess.square(col, 7 - row)

        if self.selected is not None:
            move = chess.Move(self.selected, square)

            piece = self.board.piece_at(self.selected)

            if piece and piece.piece_type == chess.PAWN:
                if chess.square_rank(square) in (0, 7):
                    promotion = self.choose_promotion()
                    if promotion is None:
                        return
                    move.promotion = promotion

            if move in self.board.legal_moves:
                self.history.append(self.board.fen())
                self.board.push(move)
                self.last_move = move
                self.selected = None
                self.legal_targets = []
                self.update_game()
                return

        piece = self.board.piece_at(square)

        if piece and piece.color == self.board.turn:
            self.selected = square
            self.legal_targets = [
                move.to_square
                for move in self.board.legal_moves
                if move.from_square == square
            ]
        else:
            self.selected = None
            self.legal_targets = []

        self.draw_board()

    def choose_promotion(self):
        choice = tk.simpledialog.askstring(
            "Превращение пешки",
            "Выбери фигуру: ферзь, ладья, слон или конь",
            parent=self.root
        )

        choices = {
            "ферзь": chess.QUEEN,
            "ладья": chess.ROOK,
            "слон": chess.BISHOP,
            "конь": chess.KNIGHT
        }

        if choice is None:
            return None

        return choices.get(choice.lower().strip(), chess.QUEEN)

    def update_game(self):
        self.draw_board()

        if self.board.is_checkmate():
            winner = "Чёрные" if self.board.turn else "Белые"
            self.status.config(text="ШАХ И МАТ!")
            messagebox.showinfo(
                "Конец игры",
                winner + " победили!"
            )

        elif self.board.is_stalemate() or self.board.is_insufficient_material():
            self.status.config(text="Ничья!")
            messagebox.showinfo("Конец игры", "Партия закончилась вничью.")

        elif self.board.is_check():
            self.status.config(text="ШАХ!")

        else:
            self.status.config(
                text="Ход белых" if self.board.turn else "Ход чёрных"
            )


if __name__ == "__main__":
    import tkinter.simpledialog

    root = tk.Tk()
    game = ChessGame(root)
    root.mainloop()
                
