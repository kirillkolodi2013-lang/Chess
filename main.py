
import tkinter as tk
from tkinter import messagebox, simpledialog
import chess
import random
import time

# =========================
# НАСТРОЙКИ
# =========================

LIGHT = "#F0D9B5"
DARK = "#B58863"
YELLOW = "#F6E36B"
GREEN = "#A9CF75"
BG = "#20242D"
PANEL = "#292F3B"
TEXT = "#FFFFFF"

PIECES = {
    "K": "♔", "Q": "♕", "R": "♖",
    "B": "♗", "N": "♘", "P": "♙",
    "k": "♚", "q": "♛", "r": "♜",
    "b": "♝", "n": "♞", "p": "♟"
}

VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0
}

PIECE_NAMES = {
    chess.PAWN: "Пешка",
    chess.KNIGHT: "Конь",
    chess.BISHOP: "Слон",
    chess.ROOK: "Ладья",
    chess.QUEEN: "Ферзь",
    chess.KING: "Король"
}

BOT_DEPTH = {
    "Слабый": 1,
    "Средний": 2,
    "Сильный": 3
}


# =========================
# ИСКУССТВЕННЫЙ ИНТЕЛЛЕКТ
# =========================

def evaluate(board):
    if board.is_checkmate():
        return -100000

    if board.is_game_over():
        return 0

    score = 0

    for piece_type, value in VALUES.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value * 100
        score -= len(board.pieces(piece_type, chess.BLACK)) * value * 100

    score += len(list(board.legal_moves)) * (1 if board.turn else -1)

    return score if board.turn == chess.WHITE else -score


def ordered_moves(board):
    moves = list(board.legal_moves)

    moves.sort(
        key=lambda move: (
            board.is_capture(move),
            move.promotion is not None
        ),
        reverse=True
    )

    return moves


def minimax(board, depth, alpha, beta):
    if depth == 0 or board.is_game_over():
        return evaluate(board), None

    best_move = None
    best_score = -float("inf")

    for move in ordered_moves(board):
        board.push(move)

        score = -minimax(
            board,
            depth - 1,
            -beta,
            -alpha
        )[0]

        board.pop()

        if score > best_score:
            best_score = score
            best_move = move

        alpha = max(alpha, score)

        if alpha >= beta:
            break

    return best_score, best_move


def choose_bot_move(board, difficulty):
    moves = list(board.legal_moves)

    if not moves:
        return None

    if difficulty == "Слабый":
        return random.choice(moves)

    depth = BOT_DEPTH[difficulty]

    if difficulty == "Средний":
        depth = 2

    return minimax(
        board,
        depth,
        -float("inf"),
        float("inf")
    )[1]


# =========================
# ИГРА
# =========================

class ChessGame:

    def __init__(self, root):
        self.root = root
        self.root.title("Chess — Шахматы")
        self.root.geometry("1050x720")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.mode = "Компьютер"
        self.difficulty = "Средний"
        self.player_color = chess.WHITE
        self.time_limit = 0

        self.board = chess.Board()
        self.history = []
        self.captured_white = []
        self.captured_black = []

        self.timeline = []
        self.position = 0

        self.remaining = {
            chess.WHITE: 0,
            chess.BLACK: 0
        }

        self.last_tick = time.monotonic()
        self.finished = False
        self.bot_thinking = False
        self.timer_job = None

        self.show_menu()

    # =====================
    # ГЛАВНОЕ МЕНЮ
    # =====================

    def show_menu(self):
        self.menu = tk.Frame(self.root, bg=BG)
        self.menu.pack(fill="both", expand=True)

        tk.Label(
            self.menu,
            text="♟ CHESS",
            font=("Arial", 38, "bold"),
            fg=TEXT,
            bg=BG
        ).pack(pady=35)

        tk.Label(
            self.menu,
            text="ШАХМАТЫ",
            font=("Arial", 19, "bold"),
            fg="#D8B77A",
            bg=BG
        ).pack(pady=5)

        self.mode_var = tk.StringVar(value="Компьютер")
        self.bot_var = tk.StringVar(value="Средний")
        self.color_var = tk.StringVar(value="Белые")
        self.time_var = tk.StringVar(value="Без ограничения")

        self.add_option("Режим игры", self.mode_var,
                        ["Компьютер", "Два игрока"])

        self.add_option("Сложность компьютера", self.bot_var,
                        ["Слабый", "Средний", "Сильный"])

        self.add_option("Твой цвет", self.color_var,
                        ["Белые", "Чёрные", "Случайный"])

        self.add_option("Время", self.time_var,
                        ["1 минута", "5 минут", "10 минут",
                         "Без ограничения"])

        tk.Button(
            self.menu,
            text="НАЧАТЬ ИГРУ",
            font=("Arial", 17, "bold"),
            bg="#C49A54",
            fg="#171717",
            width=22,
            height=2,
            command=self.start_game
        ).pack(pady=30)

    def add_option(self, title, variable, options):
        tk.Label(
            self.menu,
            text=title,
            font=("Arial", 12, "bold"),
            fg=TEXT,
            bg=BG
        ).pack(pady=(12, 3))

        tk.OptionMenu(
            self.menu,
            variable,
            *options
        ).pack()

    # =====================
    # НАЧАЛО ПАРТИИ
    # =====================

    def start_game(self):
        self.mode = self.mode_var.get()
        self.difficulty = self.bot_var.get()

        color = self.color_var.get()

        if color == "Белые":
            self.player_color = chess.WHITE
        elif color == "Чёрные":
            self.player_color = chess.BLACK
        else:
            self.player_color = random.choice(
                [chess.WHITE, chess.BLACK]
            )

        times = {
            "1 минута": 60,
            "5 минут": 300,
            "10 минут": 600,
            "Без ограничения": 0
        }

        self.time_limit = times[self.time_var.get()]

        self.remaining = {
            chess.WHITE: self.time_limit,
            chess.BLACK: self.time_limit
        }

        self.board = chess.Board()
        self.history = []
        self.captured_white = []
        self.captured_black = []
        self.timeline = []
        self.position = 0
        self.finished = False
        self.bot_thinking = False

        self.menu.destroy()
        self.create_game_screen()
        self.save_state()
        self.update_screen()

        self.last_tick = time.monotonic()
        self.tick()

        if self.mode == "Компьютер":
            if self.board.turn != self.player_color:
                self.root.after(300, self.bot_move)

    # =====================
    # ЭКРАН ИГРЫ
    # =====================

    def create_game_screen(self):
        self.game_frame = tk.Frame(self.root, bg=BG)
        self.game_frame.pack(fill="both", expand=True, padx=12, pady=12)

        self.top_label = tk.Label(
            self.game_frame,
            text="ШАХМАТЫ",
            font=("Arial", 21, "bold"),
            fg=TEXT,
            bg=BG
        )
        self.top_label.pack(pady=5)

        self.main_area = tk.Frame(
            self.game_frame,
            bg=BG
        )
        self.main_area.pack()

        self.canvas = tk.Canvas(
            self.main_area,
            width=576,
            height=576,
            bg=BG,
            highlightthickness=0
        )
        self.canvas.pack(side="left", padx=8)

        self.canvas.bind("<Button-1>", self.board_click)

        self.side = tk.Frame(
            self.main_area,
            bg=PANEL,
            width=320,
            height=576
        )
        self.side.pack(side="left", fill="y", padx=8)
        self.side.pack_propagate(False)

        self.status_label = tk.Label(
            self.side,
            text="Ход белых",
            font=("Arial", 16, "bold"),
            fg=TEXT,
            bg=PANEL
        )
        self.status_label.pack(pady=10)

        self.white_clock = tk.Label(
            self.side,
            text="Белые: --:--",
            font=("Arial", 14, "bold"),
            fg=TEXT,
            bg=PANEL
        )
        self.white_clock.pack(pady=4)

        self.black_clock = tk.Label(
            self.side,
            text="Чёрные: --:--",
            font=("Arial", 14, "bold"),
            fg=TEXT,
            bg=PANEL
        )
        self.black_clock.pack(pady=4)

        tk.Label(
            self.side,
            text="ИСТОРИЯ ХОДОВ",
            font=("Arial", 12, "bold"),
            fg=TEXT,
            bg=PANEL
        ).pack(pady=(12, 4))

        self.move_list = tk.Listbox(
            self.side,
            width=35,
            height=10,
            font=("Arial", 10)
        )
        self.move_list.pack(padx=8, fill="x")

        tk.Label(
            self.side,
            text="СЪЕДЕННЫЕ ФИГУРЫ",
            font=("Arial", 12, "bold"),
            fg=TEXT,
            bg=PANEL
        ).pack(pady=(12, 5))

        self.white_captured_label = tk.Label(
            self.side,
            text="Белые съели: —",
            font=("Arial", 10),
            fg=TEXT,
            bg=PANEL,
            wraplength=290
        )
        self.white_captured_label.pack(pady=4)

        self.black_captured_label = tk.Label(
            self.side,
            text="Чёрные съели: —",
            font=("Arial", 10),
            fg=TEXT,
            bg=PANEL,
            wraplength=290
        )
        self.black_captured_label.pack(pady=4)

        buttons = tk.Frame(self.side, bg=PANEL)
        buttons.pack(pady=15)

        tk.Button(
            buttons,
            text="↶ Отменить",
            command=self.undo,
            width=13
        ).grid(row=0, column=0, padx=3, pady=3)

        tk.Button(
            buttons,
            text="↷ Вернуть",
            command=self.redo,
            width=13
        ).grid(row=0, column=1, padx=3, pady=3)

        tk.Button(
            buttons,
            text="Новая партия",
            command=self.ask_new_game,
            width=13
        ).grid(row=1, column=0, padx=3, pady=3)

        tk.Button(
            buttons,
            text="В меню",
            command=self.back_to_menu,
            width=13
        ).grid(row=1, column=1, padx=3, pady=3)

        self.selected = None
        self.legal_targets = []

    # =====================
    # ДОСКА
    # =====================

    def square_to_xy(self, square):
        file = chess.square_file(square)
        rank = chess.square_rank(square)

        if self.player_color == chess.WHITE:
            col = file
            row = 7 - rank
        else:
            col = 7 - file
            row = rank

        return col, row

    def xy_to_square(self, x, y):
        col = int(x // 72)
        row = int(y // 72)

        if not (0 <= col < 8 and 0 <= row < 8):
            return None

        if self.player_color == chess.WHITE:
            file = col
            rank = 7 - row
        else:
            file = 7 - col
            rank = row

        return chess.square(file, rank)

    def draw_board(self):
        self.canvas.delete("all")

        for row in range(8):
            for col in range(8):
                x1 = col * 72
                y1 = row * 72
                x2 = x1 + 72
                y2 = y1 + 72

                color = LIGHT if (row + col) % 2 == 0 else DARK

                square = self.xy_to_square(
                    x1 + 10,
                    y1 + 10
                )

                if self.last_move and square in (
                    self.last_move.from_square,
                    self.last_move.to_square
                ):
                    color = YELLOW

                if square in self.legal_targets:
                    color = GREEN

                if square == self.selected:
                    color = "#E8D34D"

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline=color
                )

                piece = self.board.piece_at(square)

                if piece:
                    self.canvas.create_text(
                        x1 + 36,
                        y1 + 36,
                        text=PIECES[piece.symbol()],
                        font=("Arial", 43),
                        fill="#171717" if piece.color == chess.BLACK
                        else "#FFFFFF"
                    )

                if square in self.legal_targets:
                    if self.board.piece_at(square):
                        self.canvas.create_oval(
                            x1 + 5, y1 + 5,
                            x2 - 5, y2 - 5,
                            outline="#398B36",
                            width=4
                        )
                    else:
                        self.canvas.create_oval(
                            x1 + 28, y1 + 28,
                            x1 + 44, y1 + 44,
                            fill="#398B36",
                            outline=""
                        )

        if self.last_move:
            start_col, start_row = self.square_to_xy(
                self.last_move.from_square
            )
            end_col, end_row = self.square_to_xy(
                self.last_move.to_square
            )

            self.canvas.create_line(
                start_col * 72 + 36,
                start_row * 72 + 36,
                end_col * 72 + 36,
                end_row * 72 + 36,
                fill="#D4A900",
                width=4,
                arrow=tk.LAST,
                arrowshape=(14, 16, 6)
            )

    def board_click(self, event):
        if self.finished or self.bot_thinking:
            return

        if self.mode == "Компьютер":
            if self.board.turn != self.player_color:
                return

        square = self.xy_to_square(event.x, event.y)

        if square is None:
            return

        if self.selected is not None:
            move = chess.Move(self.selected, square)

            piece = self.board.piece_at(self.selected)

            if piece and piece.piece_type == chess.PAWN:
                if chess.square_rank(square) in (0, 7):
                    promotion = self.ask_promotion()

                    if promotion is None:
                        return

                    move.promotion = promotion

            if move in self.board.legal_moves:
                self.make_move(move)

                if self.mode == "Компьютер" and not self.finished:
                    self.root.after(200, self.bot_move)

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

    # =====================
    # ПРЕВРАЩЕНИЕ ПЕШКИ
    # =====================

    def ask_promotion(self):
        answer = simpledialog.askstring(
            "Превращение пешки",
            "Напиши: ферзь, ладья, слон или конь",
            parent=self.root
        )

        options = {
            "ферзь": chess.QUEEN,
            "ладья": chess.ROOK,
            "слон": chess.BISHOP,
            "конь": chess.KNIGHT
        }

        if answer is None:
            return None

        return options.get(
            answer.lower().strip(),
            chess.QUEEN
        )

    # =====================
    # ВЫПОЛНЕНИЕ ХОДА
    # =====================

    def make_move(self, move):
        san = self.board.san(move)
        mover = "Белые" if self.board.turn else "Чёрные"

        captured_piece = None

        if self.board.is_capture(move):
            capture_square = move.to_square

            if self.board.is_en_passant(move):
                capture_square = (
                    move.to_square - 8
                    if self.board.turn == chess.WHITE
                    else move.to_square + 8
                )

            captured_piece = self.board.piece_at(capture_square)

        if captured_piece:
            if self.board.turn == chess.WHITE:
                self.captured_white.append(captured_piece.symbol())
            else:
                self.captured_black.append(captured_piece.symbol())

        self.board.push(move)

        self.history.append(
            mover + ": " + san
        )

        self.last_move = move
        self.selected = None
        self.legal_targets = []

        self.save_state()
        self.update_screen()
        self.check_end()

    # =====================
    # СОХРАНЕНИЕ СОСТОЯНИЙ
    # =====================

    def save_state(self):
        state = {
            "board": self.board.copy(stack=True),
            "history": list(self.history),
            "white": list(self.captured_white),
            "black": list(self.captured_black),
            "remaining": dict(self.remaining),
            "last_move": self.last_move
        }

        self.timeline = self.timeline[:self.position + 1]
        self.timeline.append(state)
        self.position = len(self.timeline) - 1

    def restore_state(self):
        state = self.timeline[self.position]

        self.board = state["board"].copy(stack=True)
        self.history = list(state["history"])
        self.captured_white = list(state["white"])
        self.captured_black = list(state["black"])
        self.remaining = dict(state["remaining"])
        self.last_move = state["last_move"]

        self.selected = None
        self.legal_targets = []
        self.finished = False

        self.last_tick = time.monotonic()
        self.update_screen()

    def undo(self):
        if self.position == 0:
            return

        steps = 1

        if self.mode == "Компьютер":
            if len(self.history) >= 2:
                steps = 2

        self.position = max(0, self.position - steps)
        self.restore_state()

    def redo(self):
        if self.position >= len(self.timeline) - 1:
            return

        steps = 1

        if self.mode == "Компьютер":
            if self.position + 2 < len(self.timeline):
                steps = 2

        self.position = min(
            len(self.timeline) - 1,
            self.position + steps
        )

        self.restore_state()

        if self.mode == "Компьютер":
            if self.board.turn != self.player_color:
                self.root.after(200, self.bot_move)

    # =====================
    # КОМПЬЮТЕРНЫЙ СОПЕРНИК
    # =====================

    def bot_move(self):
        if self.finished or self.mode != "Компьютер":
            return

        if self.board.turn == self.player_color:
            return

        self.bot_thinking = True
        self.status_label.config(text="Компьютер думает...")
        self.root.update_idletasks()

        move = choose_bot_move(
            self.board,
            self.difficulty
        )

        self.bot_thinking = False

        if move and not self.finished:
            self.make_move(move)

    # =====================
    # ОБНОВЛЕНИЕ ИНТЕРФЕЙСА
    # =====================

    def update_screen(self):
        self.draw_board()

        if self.board.is_check():
            self.status_label.config(text="ШАХ!")
        else:
            self.status_label.config(
                text="Ход белых" if self.board.turn
                else "Ход чёрных"
            )

        self.move_list.delete(0, tk.END)

        for index, move in enumerate(self.history):
            self.move_list.insert(
                tk.END,
                str(index + 1) + ". " + move
            )

        
        self.white_captured_label.config(
            text="Белые съели: " +
            (" ".join(PIECES[p] for p in self.captured_white)
             if self.captured_white else "—")
        )

        self.black_captured_label.config(
            text="Чёрные съели: " +
            (" ".join(PIECES[p] for p in self.captured_black)
             if self.captured_black else "—")
        )

        self.update_clocks()

    def update_clocks(self):
        def format_time(seconds):
            seconds = max(0, int(seconds))
            return "{:02d}:{:02d}".format(
                seconds // 60,
                seconds % 60
            )

        if self.time_limit == 0:
            self.white_clock.config(text="Белые: ∞")
            self.black_clock.config(text="Чёрные: ∞")
        else:
            self.white_clock.config(
                text="Белые: " + format_time(
                    self.remaining[chess.WHITE]
                )
            )
            self.black_clock.config(
                text="Чёрные: " + format_time(
                    self.remaining[chess.BLACK]
                )
            )

    def tick(self):
        if self.finished:
            return

        now = time.monotonic()
        elapsed = now - self.last_tick
        self.last_tick = now

        if self.time_limit > 0:
            self.remaining[self.board.turn] -= elapsed

            if self.remaining[self.board.turn] <= 0:
                self.remaining[self.board.turn] = 0
                self.update_clocks()
                self.finish_by_time()
                return

        self.update_clocks()
        self.timer_job = self.root.after(200, self.tick)

    def finish_by_time(self):
        self.finished = True

        loser = "Белые" if self.board.turn else "Чёрные"
        winner = "Чёрные" if self.board.turn else "Белые"

        messagebox.showinfo(
            "Время закончилось",
            loser + " потеряли всё время.\nПобедили: " + winner
        )

        self.show_points()

    def check_end(self):
        if not self.board.is_game_over(claim_draw=True):
            return

        self.finished = True

        if self.board.is_checkmate():
            winner = "Белые" if self.board.turn == chess.BLACK else "Чёрные"
            result = "ШАХ И МАТ!\nПобедили: " + winner
        elif self.board.is_stalemate():
            result = "ПАТ! Ничья."
        elif self.board.is_insufficient_material():
            result = "Недостаточно фигур. Ничья."
        else:
            result = "Партия закончилась вничью."

        messagebox.showinfo("Конец партии", result)
        self.show_points()

    def show_points(self):
        def points(symbols):
            total = 0

            for symbol in symbols:
                piece_type = chess.PIECE_SYMBOLS.index(
                    symbol.lower()
                )
                total += VALUES[piece_type]

            return total

        white_points = points(self.captured_white)
        black_points = points(self.captured_black)

        messagebox.showinfo(
            "Очки за съеденные фигуры",
            "Белые: " + str(white_points) + " очков\n"
            "Чёрные: " + str(black_points) + " очков\n\n"
            "Очки не изменяют результат шахматной партии."
        )

    def undo(self):
        if self.position == 0:
            return

        steps = 1

        if self.mode == "Компьютер" and len(self.history) >= 2:
            steps = 2

        self.position = max(0, self.position - steps)
        self.restore_state()

    def redo(self):
        if self.position >= len(self.timeline) - 1:
            return

        steps = 1

        if self.mode == "Компьютер":
            if self.position + 2 < len(self.timeline):
                steps = 2

        self.position = min(
            len(self.timeline) - 1,
            self.position + steps
        )

        self.restore_state()

        if self.mode == "Компьютер":
            if self.board.turn != self.player_color:
                self.root.after(200, self.bot_move)

    def restore_state(self):
        state = self.timeline[self.position]

        self.board = state["board"].copy(stack=True)
        self.history = list(state["history"])
        self.captured_white = list(state["white"])
        self.captured_black = list(state["black"])
        self.remaining = dict(state["remaining"])
        self.last_move = state["last_move"]

        self.selected = None
        self.legal_targets = []
        self.finished = False
        self.last_tick = time.monotonic()

        self.update_screen()

    def bot_move(self):
        if self.finished or self.mode != "Компьютер":
            return

        if self.board.turn == self.player_color:
            return

        self.bot_thinking = True
        self.status_label.config(text="Компьютер думает...")
        self.root.update_idletasks()

        move = choose_bot_move(
            self.board,
            self.difficulty
        )

        self.bot_thinking = False

        if move and not self.finished:
            self.make_move(move)

    def ask_new_game(self):
        if messagebox.askyesno(
            "Новая партия",
            "Начать новую партию?"
        ):
            self.game_frame.destroy()
            self.show_menu()

    def back_to_menu(self):
        if messagebox.askyesno(
            "Выход",
            "Вернуться в главное меню?"
        ):
            if self.timer_job:
                self.root.after_cancel(self.timer_job)

            self.game_frame.destroy()
            self.show_menu()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChessGame(root)
    root.mainloop()
    
