# ============================================
# ШАХМАТНЫЙ АНАЛИЗАТОР - ГРАФИЧЕСКИЙ ИНТЕРФЕЙС
# ВЕРСИЯ 2.2 - ИСПРАВЛЕНА ОШИБКА MULTIPV
# ============================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import chess
import chess.engine
import os
import threading
import time
from datetime import datetime
import sys


class ChessAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ШАХМАТНЫЙ АНАЛИЗАТОР v2.2")
        self.root.geometry("1200x800")

        # Центрируем окно
        self.center_window()

        # Настройки программы
        self.engine_path = "stockfish.exe"
        self.engine = None
        self.board = chess.Board()  # Начальная позиция
        self.analysis_time = 3.0
        self.is_analyzing = False
        self.selected_square = None
        self.best_move = None

        # Переменные для превращения пешки
        self.promotion_move = None  # Ход, требующий превращения
        self.promotion_dialog = None  # Окно выбора фигуры

        # Unicode символы для фигур
        self.piece_symbols = {
            'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
            'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙'
        }

        # Названия фигур на русском
        self.piece_names = {
            'r': 'Ладья', 'n': 'Конь', 'b': 'Слон', 'q': 'Ферзь', 'k': 'Король', 'p': 'Пешка',
            'R': 'Ладья', 'N': 'Конь', 'B': 'Слон', 'Q': 'Ферзь', 'K': 'Король', 'P': 'Пешка'
        }

        # Цвета интерфейса
        self.colors = {
            "board_light": "#f0d9b5",
            "board_dark": "#b58863",
            "highlight": "#FFD700",
            "best_move": "#32CD32",
            "good_move": "#90EE90",
            "bad_move": "#FF6B6B",
            "text_light": "#FFFFFF",
            "text_dark": "#000000",
            "bg_dark": "#2E2E2E",
            "bg_light": "#F5F5F5"
        }

        # Настраиваем стили
        self.setup_styles()

        # Создаём интерфейс
        self.create_widgets()

        # Загружаем движок Stockfish
        self.load_engine()

        # Обновляем отображение
        self.update_display()

        # Запускаем обновление времени
        self.update_clock()

    def center_window(self):
        """Центрирование окна на экране"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def setup_styles(self):
        """Настройка стилей Tkinter"""
        style = ttk.Style()

        # Современные стили
        style.theme_use('clam')

        # Настраиваем цвета
        style.configure("TFrame", background=self.colors["bg_light"])
        style.configure("TLabel", background=self.colors["bg_light"], foreground=self.colors["text_dark"])
        style.configure("TLabelframe", background=self.colors["bg_light"], foreground=self.colors["text_dark"])
        style.configure("TLabelframe.Label", background=self.colors["bg_light"], foreground=self.colors["text_dark"])

        # Стиль для акцентных кнопок
        style.configure("Accent.TButton",
                        font=("Arial", 10, "bold"),
                        background="#4CAF50",
                        foreground="white",
                        borderwidth=2,
                        relief="raised")
        style.map("Accent.TButton",
                  background=[('active', '#45a049')])

        # Стиль для опасных кнопок
        style.configure("Danger.TButton",
                        font=("Arial", 10, "bold"),
                        background="#f44336",
                        foreground="white")
        style.map("Danger.TButton",
                  background=[('active', '#d32f2f')])

    def create_widgets(self):
        """Создание всех элементов интерфейса"""

        # ===== ГЛАВНОЕ МЕНЮ =====
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="📁 Файл", menu=file_menu)
        file_menu.add_command(label="🆕 Новая игра", command=self.new_game, accelerator="Ctrl+N")
        file_menu.add_command(label="📂 Загрузить FEN...", command=self.load_fen_dialog, accelerator="Ctrl+O")
        file_menu.add_command(label="💾 Сохранить FEN...", command=self.save_fen_dialog, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="🚪 Выход", command=self.on_closing, accelerator="Alt+F4")

        # Меню "Анализ"
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="🔍 Анализ", menu=analysis_menu)
        analysis_menu.add_command(label="⚡ Быстрый анализ (1 сек)",
                                  command=lambda: self.set_analysis_time(1.0))
        analysis_menu.add_command(label="⏱️ Стандартный анализ (3 сек)",
                                  command=lambda: self.set_analysis_time(3.0))
        analysis_menu.add_command(label="🔍 Глубокий анализ (10 сек)",
                                  command=lambda: self.set_analysis_time(10.0))
        analysis_menu.add_separator()
        analysis_menu.add_command(label="📊 Показать статистику позиции",
                                  command=self.show_position_stats)

        # Меню "Помощь"
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="❓ Помощь", menu=help_menu)
        help_menu.add_command(label="📖 Инструкция", command=self.show_instructions)
        help_menu.add_command(label="ℹ️ О программе", command=self.show_about)

        # Привязываем горячие клавиши
        self.root.bind('<Control-n>', lambda e: self.new_game())
        self.root.bind('<Control-o>', lambda e: self.load_fen_dialog())
        self.root.bind('<Control-s>', lambda e: self.save_fen_dialog())

        # ===== ГЛАВНЫЙ КОНТЕЙНЕР =====
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Конфигурация сетки
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        main_container.rowconfigure(0, weight=1)

        # ===== ЛЕВАЯ ПАНЕЛЬ - ДОСКА =====
        left_panel = ttk.LabelFrame(main_container, text="ШАХМАТНАЯ ДОСКА", padding="15")
        left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        # Холст для шахматной доски
        self.board_canvas = tk.Canvas(left_panel, width=480, height=480,
                                      bg="white", highlightthickness=0)
        self.board_canvas.grid(row=0, column=0, pady=(0, 15))
        self.board_canvas.bind("<Button-1>", self.on_board_click)

        # Панель управления доской
        board_controls = ttk.Frame(left_panel)
        board_controls.grid(row=1, column=0, sticky=(tk.W, tk.E))

        ttk.Button(board_controls, text="🆕 Новая игра",
                   command=self.new_game, width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(board_controls, text="↶ Отменить ход",
                   command=self.undo_move, width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(board_controls, text="♛ Случайная позиция",
                   command=self.random_position, width=15).pack(side=tk.LEFT, padx=2)

        # Информация о позиции
        info_frame = ttk.LabelFrame(left_panel, text="ИНФОРМАЦИЯ О ПОЗИЦИИ", padding="10")
        info_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        # Текстовая информация
        info_text = tk.Text(info_frame, height=8, width=45, font=("Consolas", 9),
                            bg=self.colors["bg_dark"], fg=self.colors["text_light"],
                            relief=tk.FLAT, borderwidth=0)
        info_text.pack()
        self.info_text = info_text

        # ===== ПРАВАЯ ПАНЕЛЬ - АНАЛИЗ =====
        right_panel = ttk.Frame(main_container)
        right_panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Панель настроек анализа
        settings_frame = ttk.LabelFrame(right_panel, text="НАСТРОЙКИ АНАЛИЗА", padding="15")
        settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # Время анализа
        time_frame = ttk.Frame(settings_frame)
        time_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(time_frame, text="⏱️ Время анализа:",
                  font=("Arial", 10, "bold")).pack(side=tk.LEFT)

        self.time_var = tk.DoubleVar(value=3.0)
        time_scale = ttk.Scale(time_frame, from_=0.5, to=30.0,
                               variable=self.time_var, orient=tk.HORIZONTAL,
                               length=200, command=self.on_time_scale)
        time_scale.pack(side=tk.LEFT, padx=10)

        self.time_label = ttk.Label(time_frame, text="3.0 сек",
                                    font=("Arial", 10, "bold"))
        self.time_label.pack(side=tk.LEFT)

        # Уровень сложности
        level_frame = ttk.Frame(settings_frame)
        level_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(level_frame, text="🏆 Уровень сложности:",
                  font=("Arial", 10, "bold")).pack(side=tk.LEFT)

        self.level_var = tk.IntVar(value=20)
        level_combo = ttk.Combobox(level_frame, textvariable=self.level_var,
                                   values=list(range(21)), width=5, state="readonly",
                                   font=("Arial", 10))
        level_combo.pack(side=tk.LEFT, padx=10)
        level_combo.set(20)

        ttk.Label(level_frame, text="(0 - новичок, 20 - гроссмейстер)").pack(side=tk.LEFT)

        # Кнопка анализа
        self.analyze_button = ttk.Button(settings_frame, text="🚀 НАЧАТЬ АНАЛИЗ",
                                         command=self.start_analysis,
                                         style="Accent.TButton", width=25)
        self.analyze_button.grid(row=2, column=0, columnspan=3, pady=(5, 0))

        # Прогресс-бар
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(right_panel, variable=self.progress_var,
                                            maximum=100, length=400)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 5))

        # Статус анализа
        self.status_var = tk.StringVar(value="✅ Готов к анализу")
        status_label = ttk.Label(right_panel, textvariable=self.status_var,
                                 font=("Arial", 9), relief=tk.SUNKEN, padding=5)
        status_label.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # Результаты анализа
        results_frame = ttk.LabelFrame(right_panel, text="РЕЗУЛЬТАТЫ АНАЛИЗА", padding="10")
        results_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        # Текстовая область с прокруткой
        self.results_text = scrolledtext.ScrolledText(results_frame,
                                                      height=15, width=60,
                                                      font=("Consolas", 9),
                                                      bg=self.colors["bg_dark"],
                                                      fg=self.colors["text_light"],
                                                      relief=tk.FLAT,
                                                      borderwidth=0)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Добавляем теги для форматирования
        self.results_text.tag_configure("header", font=("Consolas", 10, "bold"), foreground="#FFD700")
        self.results_text.tag_configure("best", font=("Consolas", 9, "bold"), foreground="#32CD32")
        self.results_text.tag_configure("good", font=("Consolas", 9), foreground="#90EE90")
        self.results_text.tag_configure("neutral", font=("Consolas", 9), foreground="#FFFFFF")
        self.results_text.tag_configure("bad", font=("Consolas", 9), foreground="#FF6B6B")
        self.results_text.tag_configure("mate", font=("Consolas", 9, "bold"), foreground="#FF4500")

        # Панель действий
        action_frame = ttk.Frame(right_panel)
        action_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))

        ttk.Button(action_frame, text="🎯 Сделать лучший ход",
                   command=self.make_best_move, width=20).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="🗑️ Очистить результаты",
                   command=self.clear_results, width=20).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="💾 Сохранить анализ",
                   command=self.save_analysis, width=20).pack(side=tk.LEFT, padx=2)

        # Нижняя строка с часами и версией
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)

        self.clock_label = ttk.Label(bottom_frame, text="", font=("Arial", 8))
        self.clock_label.pack(side=tk.LEFT)

        ttk.Label(bottom_frame, text="ШАХМАТНЫЙ АНАЛИЗАТОР v2.2 © 2024",
                  font=("Arial", 8)).pack(side=tk.RIGHT)

    def load_engine(self):
        """Загрузка шахматного движка Stockfish"""
        self.status_var.set("🔍 Загружаю Stockfish...")

        if not os.path.exists(self.engine_path):
            self.show_error("Stockfish не найден",
                            "Скачайте stockfish.exe с https://stockfishchess.org\n"
                            "и поместите в папку с программой.\n\n"
                            "Можно анализировать позицию без движка?")
            self.engine = None
            return

        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            self.status_var.set(f"✅ Stockfish загружен: {self.engine.id['name']}")
        except Exception as e:
            self.show_error("Ошибка загрузки Stockfish", str(e))
            self.engine = None

    def update_display(self):
        """Обновление всего отображения"""
        self.draw_board()
        self.update_info_text()

    def draw_board(self):
        """Отрисовка шахматной доски"""
        self.board_canvas.delete("all")

        cell_size = 60
        board_size = cell_size * 8

        # Рисуем шахматную доску
        for row in range(8):
            for col in range(8):
                x1 = col * cell_size
                y1 = row * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size

                # Определяем цвет клетки
                if (row + col) % 2 == 0:
                    color = self.colors["board_light"]
                else:
                    color = self.colors["board_dark"]

                # Рисуем клетку
                self.board_canvas.create_rectangle(x1, y1, x2, y2,
                                                   fill=color, width=0)

        # Рисуем координаты
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        numbers = ['8', '7', '6', '5', '4', '3', '2', '1']

        for i in range(8):
            # Буквы снизу
            self.board_canvas.create_text(
                i * cell_size + cell_size // 2,
                board_size - 10,
                text=letters[i],
                font=("Arial", 10, "bold"),
                fill="black"
            )

            # Цифры слева
            self.board_canvas.create_text(
                10,
                i * cell_size + cell_size // 2,
                text=numbers[i],
                font=("Arial", 10, "bold"),
                fill="black"
            )

        # Рисуем фигуры
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                row = 7 - (square // 8)
                col = square % 8

                x = col * cell_size + cell_size // 2
                y = row * cell_size + cell_size // 2

                symbol = self.piece_symbols.get(piece.symbol(), piece.symbol())

                # Цвет фигуры
                if piece.color == chess.WHITE:
                    fill_color = "white"
                    shadow_color = "gray"
                else:
                    fill_color = "black"
                    shadow_color = "#333"

                # Рисуем тень (для объёма)
                self.board_canvas.create_text(
                    x + 1, y + 1,
                    text=symbol,
                    font=("Segoe UI Symbol", 32),
                    fill=shadow_color
                )

                # Рисуем фигуру
                self.board_canvas.create_text(
                    x, y,
                    text=symbol,
                    font=("Segoe UI Symbol", 32),
                    fill=fill_color
                )

        # Подсвечиваем выбранную клетку
        if self.selected_square is not None:
            self.highlight_square(self.selected_square, self.colors["highlight"])

        # Подсвечиваем лучший ход
        if self.best_move:
            self.highlight_move(self.best_move)

    def highlight_square(self, square, color):
        """Подсветка клетки на доске"""
        row = 7 - (square // 8)
        col = square % 8
        cell_size = 60

        x1 = col * cell_size + 2
        y1 = row * cell_size + 2
        x2 = x1 + cell_size - 4
        y2 = y1 + cell_size - 4

        self.board_canvas.create_rectangle(x1, y1, x2, y2,
                                           outline=color, width=3)

    def highlight_move(self, move):
        """Подсветка хода на доске"""
        # Подсвечиваем откуда
        self.highlight_square(move.from_square, self.colors["best_move"])

        # Подсвечиваем куда
        self.highlight_square(move.to_square, self.colors["good_move"])

        # Рисуем стрелку
        self.draw_arrow(move.from_square, move.to_square)

    def draw_arrow(self, from_sq, to_sq):
        """Рисование стрелки на доске"""
        cell_size = 60

        from_row = 7 - (from_sq // 8)
        from_col = from_sq % 8
        to_row = 7 - (to_sq // 8)
        to_col = to_sq % 8

        x1 = from_col * cell_size + cell_size // 2
        y1 = from_row * cell_size + cell_size // 2
        x2 = to_col * cell_size + cell_size // 2
        y2 = to_row * cell_size + cell_size // 2

        # Рисуем линию
        self.board_canvas.create_line(x1, y1, x2, y2,
                                      fill=self.colors["best_move"],
                                      width=2, arrow=tk.LAST,
                                      arrowshape=(10, 12, 6))

    def check_promotion(self, move: chess.Move) -> bool:
        """
        Проверяет, требует ли ход превращения пешки
        """
        piece = self.board.piece_at(move.from_square)
        if not piece or piece.piece_type != chess.PAWN:
            return False

        # Проверяем, достигла ли пешка последней горизонтали
        target_rank = chess.square_rank(move.to_square)
        if piece.color == chess.WHITE and target_rank == 7:
            return True
        elif piece.color == chess.BLACK and target_rank == 0:
            return True

        return False

    def on_board_click(self, event):
        """Обработка клика по шахматной доске"""
        if self.is_analyzing:
            return

        cell_size = 60
        col = event.x // cell_size
        row = event.y // cell_size

        if 0 <= col < 8 and 0 <= row < 8:
            square = chess.square(col, 7 - row)

            if self.selected_square is None:
                # Выбираем фигуру
                piece = self.board.piece_at(square)
                if piece and piece.color == self.board.turn:
                    self.selected_square = square
                    self.highlight_square(square, self.colors["highlight"])
            else:
                # Пытаемся сделать ход
                try:
                    move = chess.Move(self.selected_square, square)

                    # Проверяем, возможен ли ход
                    if move in self.board.legal_moves:
                        # Проверяем, нужно ли превращение
                        if self.check_promotion(move):
                            # Показываем диалог выбора фигуры
                            self.promotion_move = move
                            self.show_promotion_dialog(move)
                        else:
                            # Обычный ход
                            self.board.push(move)
                            self.selected_square = None
                            self.best_move = None
                            self.update_display()
                            self.status_var.set(f"✅ Ход {self.board.san(move)} сделан")
                    else:
                        self.selected_square = None
                        self.update_display()
                        self.status_var.set("❌ Невозможный ход")

                except Exception as e:
                    self.selected_square = None
                    self.update_display()
                    self.status_var.set(f"❌ Ошибка: {str(e)}")

    def show_promotion_dialog(self, move: chess.Move):
        """Показывает диалог выбора фигуры для превращения пешки"""
        # Закрываем предыдущий диалог, если есть
        if self.promotion_dialog:
            try:
                self.promotion_dialog.destroy()
            except:
                pass

        # Создаём новое окно выбора
        dialog = tk.Toplevel(self.root)
        dialog.title("🎯 Превращение пешки")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors["bg_light"])

        # Центрируем окно
        dialog.transient(self.root)
        dialog.grab_set()

        # Определяем цвет фигуры
        piece = self.board.piece_at(move.from_square)
        is_white = piece.color == chess.WHITE

        # Заголовок
        label = ttk.Label(dialog,
                          text="🎯 Пешка достигла конца доски!\nВыберите фигуру для превращения:",
                          font=("Arial", 12, "bold"),
                          justify="center",
                          background=self.colors["bg_light"])
        label.pack(pady=20)

        # Фрейм для кнопок
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        # Символы и названия фигур (зависит от цвета)
        if is_white:
            pieces = [
                ("♕ Ферзь (самая сильная)", chess.QUEEN, "#4CAF50"),
                ("♖ Ладья", chess.ROOK, "#2196F3"),
                ("♗ Слон", chess.BISHOP, "#FF9800"),
                ("♘ Конь (может прыгать)", chess.KNIGHT, "#9C27B0")
            ]
        else:
            pieces = [
                ("♛ Ферзь (самая сильная)", chess.QUEEN, "#4CAF50"),
                ("♜ Ладья", chess.ROOK, "#2196F3"),
                ("♝ Слон", chess.BISHOP, "#FF9800"),
                ("♞ Конь (может прыгать)", chess.KNIGHT, "#9C27B0")
            ]

        # Создаём кнопки для каждой фигуры
        for i, (text, piece_type, color) in enumerate(pieces):
            btn = tk.Button(button_frame, text=text, font=("Arial", 11, "bold"),
                            bg=color, fg="white", relief="raised", borderwidth=2,
                            width=25, height=2,
                            command=lambda pt=piece_type: self.apply_promotion(move, pt, dialog))
            btn.pack(pady=5)

        # Кнопка отмены
        cancel_btn = ttk.Button(dialog, text="Отмена",
                                command=dialog.destroy)
        cancel_btn.pack(pady=10)

        # Сохраняем ссылку на диалог
        self.promotion_dialog = dialog

    def apply_promotion(self, move: chess.Move, promotion_piece: int, dialog: tk.Toplevel):
        """Применяет выбранное превращение"""
        try:
            # Создаём ход с превращением
            promotion_move = chess.Move(
                from_square=move.from_square,
                to_square=move.to_square,
                promotion=promotion_piece
            )

            # Проверяем, возможен ли ход
            if promotion_move in self.board.legal_moves:
                self.board.push(promotion_move)
                self.selected_square = None
                self.best_move = None
                self.promotion_move = None
                self.update_display()

                # Название фигуры для сообщения
                piece_names = {
                    chess.QUEEN: "Ферзя",
                    chess.ROOK: "Ладью",
                    chess.BISHOP: "Слона",
                    chess.KNIGHT: "Коня"
                }

                piece_symbols = {
                    chess.QUEEN: "♕" if self.board.turn == chess.BLACK else "♛",
                    chess.ROOK: "♖" if self.board.turn == chess.BLACK else "♜",
                    chess.BISHOP: "♗" if self.board.turn == chess.BLACK else "♝",
                    chess.KNIGHT: "♘" if self.board.turn == chess.BLACK else "♞"
                }

                self.status_var.set(
                    f"✅ Пешка превращена в {piece_names[promotion_piece]} {piece_symbols[promotion_piece]}")
            else:
                self.status_var.set("❌ Невозможный ход")

        except Exception as e:
            self.status_var.set(f"❌ Ошибка: {str(e)}")

        finally:
            # Закрываем диалог
            try:
                dialog.destroy()
            except:
                pass
            self.promotion_dialog = None

    def update_info_text(self):
        """Обновление текстовой информации о позиции"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)

        # Определяем статус игры
        if self.board.is_checkmate():
            status = "ШАХ И МАТ!"
        elif self.board.is_stalemate():
            status = "ПАТ"
        elif self.board.is_insufficient_material():
            status = "НЕДОСТАТОК МАТЕРИАЛА"
        elif self.board.is_check():
            status = "ШАХ"
        else:
            status = "ИГРА ИДЁТ"

        # Собираем информацию
        info = f"""╔══════════════════════════════════════╗
║         ИНФОРМАЦИЯ О ПОЗИЦИИ         ║
╠══════════════════════════════════════╣
║ Статус: {status:26} ║
║ Ход: {'белых' if self.board.turn == chess.WHITE else 'чёрных':29} ║
║ Всего ходов: {len(self.board.move_stack):22} ║
║ Возможных ходов: {self.board.legal_moves.count():19} ║
╠══════════════════════════════════════╣
║              FEN СТРОКА              ║
╠══════════════════════════════════════╣
{self.board.fen()}
╚══════════════════════════════════════╝
"""

        self.info_text.insert(1.0, info)
        self.info_text.config(state=tk.DISABLED)

    def update_clock(self):
        """Обновление времени в статусной строке"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.clock_label.config(text=f"🕒 {current_time}")
        self.root.after(1000, self.update_clock)

    def on_time_scale(self, value):
        """Обработка изменения шкалы времени"""
        self.analysis_time = float(value)
        self.time_label.config(text=f"{self.analysis_time:.1f} сек")

    def set_analysis_time(self, time):
        """Установка времени анализа"""
        self.analysis_time = time
        self.time_var.set(time)
        self.time_label.config(text=f"{time:.1f} сек")
        self.status_var.set(f"⏱️ Время анализа установлено: {time} сек")

    def new_game(self):
        """Начать новую игру"""
        self.board = chess.Board()
        self.selected_square = None
        self.best_move = None
        self.promotion_move = None
        self.update_display()
        self.clear_results()
        self.status_var.set("🆕 Новая игра начата")

    def undo_move(self):
        """Отменить последний ход"""
        if len(self.board.move_stack) > 0:
            self.board.pop()
            self.selected_square = None
            self.best_move = None
            self.promotion_move = None
            self.update_display()
            self.status_var.set("↶ Ход отменён")

    def random_position(self):
        """Создать случайную позицию"""
        import random

        # Очищаем доску
        self.board.clear()

        # Случайное количество фигур
        pieces = ['r', 'n', 'b', 'q', 'k', 'p']

        # Ставим королей
        self.board.set_piece_at(random.choice(list(chess.SQUARES)), chess.Piece.from_symbol('K'))
        self.board.set_piece_at(random.choice(list(chess.SQUARES)), chess.Piece.from_symbol('k'))

        # Добавляем несколько случайных фигур
        for _ in range(random.randint(5, 15)):
            piece = random.choice(pieces)
            square = random.choice(list(chess.SQUARES))
            if self.board.piece_at(square) is None:
                # Чередуем цвета
                if random.choice([True, False]):
                    piece = piece.upper()  # Белые
                else:
                    piece = piece.lower()  # Черные
                self.board.set_piece_at(square, chess.Piece.from_symbol(piece))

        # Устанавливаем чей ход
        self.board.turn = random.choice([chess.WHITE, chess.BLACK])

        # Обновляем отображение
        self.selected_square = None
        self.best_move = None
        self.promotion_move = None
        self.update_display()
        self.clear_results()
        self.status_var.set("🎲 Случайная позиция создана")

    def start_analysis(self):
        """Запуск анализа позиции"""
        if self.is_analyzing:
            self.status_var.set("⚠️ Анализ уже выполняется")
            return

        if not self.engine:
            self.show_error("Stockfish не загружен",
                            "Проверьте наличие stockfish.exe в папке с программой")
            return

        # Подготавливаем интерфейс
        self.is_analyzing = True
        self.analyze_button.config(state=tk.DISABLED, text="⏳ Анализ...")
        self.status_var.set("🔍 Анализирую позицию...")
        self.progress_var.set(0)

        # Очищаем предыдущие результаты
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Идет анализ...\n\n", "header")
        self.results_text.update()

        # Запускаем анализ в отдельном потоке
        analysis_thread = threading.Thread(target=self.run_analysis)
        analysis_thread.daemon = True
        analysis_thread.start()

    def run_analysis(self):
        """Выполнение анализа в отдельном потоке"""
        try:
            # Настройки анализа
            limit = chess.engine.Limit(time=self.analysis_time)
            skill_level = self.level_var.get()

            # Применяем уровень сложности
            if hasattr(self.engine, 'configure'):
                try:
                    self.engine.configure({"Skill Level": skill_level})
                except:
                    pass

            # Получаем лучший ход (это всегда работает)
            result = self.engine.play(self.board, limit)
            self.best_move = result.move

            # Пытаемся получить оценку позиции
            try:
                # Пробуем получить анализ
                analysis = self.engine.analyse(self.board, limit)

                # Создаем простую структуру для отображения
                best_move_info = {
                    "score": analysis.get("score", chess.engine.Cp(0)),
                    "pv": [result.move]
                }

                variations = [analysis]

            except Exception as analysis_error:
                # Если анализ не сработал, используем только лучший ход
                print(f"Анализ не удался: {analysis_error}")
                best_move_info = {
                    "score": chess.engine.Cp(0),
                    "pv": [result.move]
                }
                variations = []

            # Обновляем прогресс
            self.root.after(0, lambda: self.progress_var.set(100))

            # Обновляем интерфейс
            self.root.after(0, self.update_analysis_results, variations, best_move_info)

        except Exception as e:
            self.root.after(0, self.show_error, "Ошибка анализа", str(e))

        finally:
            # Восстанавливаем интерфейс
            self.root.after(0, self.analysis_finished)

    def update_analysis_results(self, variations, best_move_info):
        """Обновление результатов анализа"""
        self.results_text.delete(1.0, tk.END)

        if not variations or (isinstance(variations, list) and len(variations) == 0):
            self.results_text.insert(tk.END, "❌ Анализ не дал результатов\n", "bad")
            return

        # Заголовок
        self.results_text.insert(tk.END, "РЕЗУЛЬТАТЫ АНАЛИЗА\n", "header")
        self.results_text.insert(tk.END, f"Время анализа: {self.analysis_time:.1f} сек\n\n")

        # Лучший ход
        if best_move_info and "pv" in best_move_info and best_move_info["pv"]:
            best_move = best_move_info["pv"][0]

            if best_move_info.get("score"):
                score = best_move_info["score"]
            elif variations and isinstance(variations, list) and len(variations) > 0:
                score = variations[0].get("score", chess.engine.Cp(0))
            else:
                score = chess.engine.Cp(0)

            self.results_text.insert(tk.END, "🎯 ЛУЧШИЙ ХОД: ", "header")

            if hasattr(score, 'is_mate') and score.is_mate():
                mate_in = score.mate()
                if mate_in > 0:
                    self.results_text.insert(tk.END, f"Мат белым в {mate_in}\n", "mate")
                else:
                    self.results_text.insert(tk.END, f"Мат черным в {-mate_in}\n", "mate")
            else:
                if hasattr(score, 'white'):
                    cp = score.white().score()
                else:
                    cp = score.score() if hasattr(score, 'score') else 0
                eval_str = f"{cp / 100:.2f}"
                if cp > 0:
                    self.results_text.insert(tk.END, f"+{eval_str} (преимущество белых)\n", "best")
                elif cp < 0:
                    self.results_text.insert(tk.END, f"{eval_str} (преимущество черных)\n", "best")
                else:
                    self.results_text.insert(tk.END, "0.00 (равно)\n", "neutral")

            self.results_text.insert(tk.END, f"Ход: {self.board.san(best_move)}\n\n")

        # Анализ позиции
        self.results_text.insert(tk.END, "📊 АНАЛИЗ ПОЗИЦИИ:\n", "header")

        # Если у нас есть варианты, показываем их
        if variations:
            if isinstance(variations, list) and len(variations) > 0:
                # Берем первый (лучший) вариант
                info = variations[0]
                if "score" in info:
                    score = info["score"]

                    if hasattr(score, 'is_mate') and score.is_mate():
                        mate_in = score.mate()
                        eval_text = f"Мат в {abs(mate_in)} ходов"
                        tag = "mate"
                    else:
                        if hasattr(score, 'white'):
                            cp = score.white().score()
                        else:
                            cp = score.score() if hasattr(score, 'score') else 0
                        eval_text = f"{cp / 100:+.2f}"
                        if cp > 0:
                            tag = "best"
                        elif cp < -100:
                            tag = "bad"
                        else:
                            tag = "neutral"

                    self.results_text.insert(tk.END, f"Оценка позиции: {eval_text}\n", tag)

                    # Если есть глубина анализа
                    if "depth" in info:
                        self.results_text.insert(tk.END, f"Глубина анализа: {info['depth']} полуходов\n", "neutral")

                    # Если есть последовательность ходов, показываем ее
                    if "pv" in info and info["pv"]:
                        self.results_text.insert(tk.END, "Последовательность: ", "neutral")
                        board_copy = self.board.copy()
                        moves_displayed = []
                        for j, move in enumerate(info["pv"]):
                            if j >= 5:  # Ограничиваем количество ходов
                                moves_displayed.append("...")
                                break
                            if board_copy.is_legal(move):
                                moves_displayed.append(board_copy.san(move))
                                board_copy.push(move)
                            else:
                                break
                        self.results_text.insert(tk.END, " ".join(moves_displayed) + "\n", "neutral")

        # Дополнительная информация
        self.results_text.insert(tk.END, "\n📈 СОВЕТЫ:\n", "header")
        self.add_analysis_tips()

        # Обновляем отображение доски
        self.update_display()

    def add_analysis_tips(self):
        """Добавление советов по позиции"""
        # Анализ материального баланса
        piece_values = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0}

        white_material = 0
        black_material = 0

        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                value = piece_values.get(piece.symbol().lower(), 0)
                if piece.color == chess.WHITE:
                    white_material += value
                else:
                    black_material += value

        material_diff = white_material - black_material

        tips = []

        if material_diff > 3:
            tips.append("• У вас материальное преимущество - упрощайте позицию")
        elif material_diff < -3:
            tips.append("• Вы в материале - ищите тактические возможности")

        # Количество фигур
        white_pieces = sum(1 for sq in chess.SQUARES
                           if self.board.piece_at(sq) and self.board.piece_at(sq).color == chess.WHITE)
        black_pieces = sum(1 for sq in chess.SQUARES
                           if self.board.piece_at(sq) and self.board.piece_at(sq).color == chess.BLACK)

        if white_pieces <= 3 or black_pieces <= 3:
            tips.append("• Осталось мало фигур - активнее используйте короля")

        # Центр
        center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
        center_control = 0
        for sq in center_squares:
            piece = self.board.piece_at(sq)
            if piece:
                if piece.color == self.board.turn:
                    center_control += 1
                else:
                    center_control -= 1

        if center_control < 0:
            tips.append("• Слабо контролируете центр - укрепляйте его")

        # Добавляем советы
        for tip in tips:
            self.results_text.insert(tk.END, tip + "\n", "neutral")

    def analysis_finished(self):
        """Завершение анализа"""
        self.is_analyzing = False
        self.analyze_button.config(state=tk.NORMAL, text="🚀 НАЧАТЬ АНАЛИЗ")
        self.progress_var.set(100)
        self.status_var.set("✅ Анализ завершён")

    def make_best_move(self):
        """Сделать лучший ход"""
        if not self.best_move:
            self.status_var.set("❌ Сначала выполните анализ")
            return

        try:
            # Проверяем, нужно ли превращение
            if self.check_promotion(self.best_move):
                # Для лучшего хода выбираем ферзя
                promotion_move = chess.Move(
                    from_square=self.best_move.from_square,
                    to_square=self.best_move.to_square,
                    promotion=chess.QUEEN
                )
                if promotion_move in self.board.legal_moves:
                    self.board.push(promotion_move)
                else:
                    self.board.push(self.best_move)
            else:
                self.board.push(self.best_move)

            self.selected_square = None
            self.update_display()
            self.status_var.set(f"✅ Сделан лучший ход: {self.board.san(self.best_move)}")

        except Exception as e:
            self.status_var.set(f"❌ Ошибка: {str(e)}")

    def clear_results(self):
        """Очистка результатов анализа"""
        self.results_text.delete(1.0, tk.END)
        self.best_move = None
        self.update_display()

    def save_analysis(self):
        """Сохранение результатов анализа"""
        if not self.results_text.get(1.0, tk.END).strip():
            self.status_var.set("❌ Нет результатов для сохранения")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Сохранить анализ"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("ШАХМАТНЫЙ АНАЛИЗАТЕР - РЕЗУЛЬТАТЫ АНАЛИЗА\n")
                    f.write("=" * 50 + "\n")
                    f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"FEN: {self.board.fen()}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(self.results_text.get(1.0, tk.END))

                self.status_var.set(f"✅ Анализ сохранён в {filename}")
            except Exception as e:
                self.show_error("Ошибка сохранения", str(e))

    def load_fen_dialog(self):
        """Загрузка позиции из FEN строки"""
        fen = simpledialog.askstring("Загрузка FEN", "Введите FEN строку:",
                                     parent=self.root)
        if fen:
            try:
                self.board = chess.Board(fen)
                self.selected_square = None
                self.best_move = None
                self.update_display()
                self.clear_results()
                self.status_var.set("✅ Позиция загружена")
            except Exception as e:
                self.show_error("Ошибка FEN", f"Некорректная FEN строка:\n{str(e)}")

    def save_fen_dialog(self):
        """Сохранение позиции в FEN строку"""
        fen = self.board.fen()

        filename = filedialog.asksaveasfilename(
            defaultextension=".fen",
            filetypes=[("FEN files", "*.fen"), ("Text files", "*.txt"), ("All files", "*.*")],
            title="Сохранить FEN",
            initialfile="position.fen"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(fen)
                self.status_var.set(f"✅ FEN сохранён в {filename}")
            except Exception as e:
                self.show_error("Ошибка сохранения", str(e))

    def show_position_stats(self):
        """Показать статистику позиции"""
        stats_text = self.get_position_stats()

        # Создаем окно со статистикой
        stats_window = tk.Toplevel(self.root)
        stats_window.title("📊 Статистика позиции")
        stats_window.geometry("500x400")
        stats_window.configure(bg=self.colors["bg_light"])

        # Текстовая область
        text_area = scrolledtext.ScrolledText(stats_window,
                                              font=("Consolas", 10),
                                              bg=self.colors["bg_dark"],
                                              fg=self.colors["text_light"],
                                              wrap=tk.WORD)
        text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Вставляем статистику
        text_area.insert(1.0, stats_text)
        text_area.config(state=tk.DISABLED)

    def get_position_stats(self):
        """Получение статистики позиции"""
        stats = []
        stats.append("=" * 50)
        stats.append("СТАТИСТИКА ПОЗИЦИИ")
        stats.append("=" * 50)
        stats.append(f"FEN: {self.board.fen()}")
        stats.append(f"Ход: {'белых' if self.board.turn == chess.WHITE else 'чёрных'}")
        stats.append(f"Всего ходов: {len(self.board.move_stack)}")
        stats.append(f"Возможных ходов: {self.board.legal_moves.count()}")

        # Материальный баланс
        piece_values = {'p': 1, 'n': 3, 'b': 3.1, 'r': 5, 'q': 9, 'k': 0}

        white_material = 0
        black_material = 0
        white_pieces = {}
        black_pieces = {}

        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                value = piece_values.get(piece.symbol().lower(), 0)
                if piece.color == chess.WHITE:
                    white_material += value
                    white_pieces[piece.symbol().lower()] = white_pieces.get(piece.symbol().lower(), 0) + 1
                else:
                    black_material += value
                    black_pieces[piece.symbol().lower()] = black_pieces.get(piece.symbol().lower(), 0) + 1

        stats.append("\nМАТЕРИАЛЬНЫЙ БАЛАНС:")
        stats.append(f"  Белые: {white_material:.1f}")
        stats.append(f"  Чёрные: {black_material:.1f}")
        stats.append(f"  Разница: {white_material - black_material:+.1f}")

        # Количество фигур
        stats.append("\nФИГУРЫ НА ДОСКЕ:")
        stats.append("  Белые: " + ", ".join([f"{self.piece_names[piece.upper()]}: {count}"
                                              for piece, count in white_pieces.items()]))
        stats.append("  Чёрные: " + ", ".join([f"{self.piece_names[piece]}: {count}"
                                               for piece, count in black_pieces.items()]))

        # Специальные правила
        stats.append("\nСПЕЦИАЛЬНЫЕ ПРАВИЛА:")
        stats.append(f"  Рокировка (белые): {'K' if self.board.castling_rights & chess.BB_H1 else ''}"
                     f"{'Q' if self.board.castling_rights & chess.BB_A1 else ''}")
        stats.append(f"  Рокировка (чёрные): {'k' if self.board.castling_rights & chess.BB_H8 else ''}"
                     f"{'q' if self.board.castling_rights & chess.BB_A8 else ''}")

        if self.board.ep_square:
            stats.append(f"  Взятие на проходе возможно на: {chess.square_name(self.board.ep_square)}")

        stats.append(f"  Правило 50 ходов: {self.board.halfmove_clock}/50")

        # Статус игры
        stats.append("\nСТАТУС ИГРЫ:")
        if self.board.is_checkmate():
            stats.append("  ШАХ И МАТ!")
            stats.append(f"  Победили: {'чёрные' if self.board.turn == chess.WHITE else 'белые'}")
        elif self.board.is_stalemate():
            stats.append("  ПАТ - ничья")
        elif self.board.is_insufficient_material():
            stats.append("  НЕДОСТАТОК МАТЕРИАЛА - ничья")
        elif self.board.is_check():
            stats.append("  ШАХ")
        else:
            stats.append("  Игра продолжается")

        stats.append("\n" + "=" * 50)

        return "\n".join(stats)

    def show_instructions(self):
        """Показать инструкцию"""
        instructions = """
        📖 ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ

        1. ИГРА НА ДОСКЕ:
           • Кликните на фигуру, затем на клетку куда хотите её поставить
           • Пешка при достижении последней горизонтали превращается

        2. АНАЛИЗ ПОЗИЦИИ:
           • Выберите время анализа (0.5-30 секунд)
           • Выберите уровень сложности (0-20)
           • Нажмите "НАЧАТЬ АНАЛИЗ"

        3. ОСНОВНЫЕ ВОЗМОЖНОСТИ:
           • Загрузка/сохранение позиций (FEN)
           • Случайные позиции
           • Сохранение результатов анализа
           • Показать лучший ход
           • Отмена хода

        4. СОВЕТЫ:
           • Для глубокого анализа установите время 10+ секунд
           • Уровень 20 соответствует силе гроссмейстера
           • Сохраняйте интересные позиции в FEN файлы

        Удачи в анализе! ♔♕♖♗♘♙
        """

        messagebox.showinfo("Инструкция", instructions)

    def show_about(self):
        """Показать информацию о программе"""
        about_text = """
        ШАХМАТНЫЙ АНАЛИЗАТОР v2.2

        Полнофункциональная программа для анализа шахматных позиций
        с поддержкой превращения пешки.

        ВОЗМОЖНОСТИ:
        • Графический интерфейс с шахматной доской
        • Полная поддержка правил шахмат
        • Анализ с помощью Stockfish
        • Превращение пешки в любую фигуру
        • Сохранение и загрузка позиций (FEN)
        • Множество вариантов анализа

        ТРЕБОВАНИЯ:
        • Stockfish для полного функционала анализа
        • Python 3.7+
        • Библиотеки: python-chess, tkinter

        © 2024 Шахматный анализатор
        """

        messagebox.showinfo("О программе", about_text)

    def show_error(self, title, message):
        """Показать сообщение об ошибке"""
        messagebox.showerror(title, message)

    def on_closing(self):
        """Обработка закрытия окна"""
        if self.engine:
            try:
                self.engine.quit()
            except:
                pass
        self.root.destroy()


# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = ChessAnalyzerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()