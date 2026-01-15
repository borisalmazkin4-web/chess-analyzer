# ============================================
# ШАХМАТНЫЙ АНАЛИЗАТОР - ГРАФИЧЕСКИЙ ИНТЕРФЕЙС
# ВЕРСИЯ 1.0 - ПОЛНЫЙ ФУНКЦИОНАЛ
# ============================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import chess
import chess.engine
import os
import threading
import time
from datetime import datetime


class ChessAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ШАХМАТНЫЙ АНАЛИЗАТОР v2.0")
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
        file_menu.add_command(label="📷 Загрузить фото доски...", command=self.load_board_photo)
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
        analysis_menu.add_command(label="🧠 Очень глубокий анализ (30 сек)",
                                  command=lambda: self.set_analysis_time(30.0))
        analysis_menu.add_separator()
        analysis_menu.add_command(label="📊 Показать статистику позиции",
                                  command=self.show_position_stats)

        # Меню "Помощь"
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="❓ Помощь", menu=help_menu)
        help_menu.add_command(label="📖 Инструкция", command=self.show_instructions)
        help_menu.add_command(label="ℹ️ О программе", command=self.show_about)
        help_menu.add_command(label="🐛 Отладить", command=self.debug_info)

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
        ttk.Button(board_controls, text="↷ Повторить",
                   command=self.redo_move, width=15).pack(side=tk.LEFT, padx=2)

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

        # Количество вариантов
        multipv_frame = ttk.Frame(settings_frame)
        multipv_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

        ttk.Label(multipv_frame, text="📊 Количество вариантов:",
                  font=("Arial", 10, "bold")).pack(side=tk.LEFT)

        self.multipv_var = tk.IntVar(value=3)
        multipv_combo = ttk.Combobox(multipv_frame, textvariable=self.multipv_var,
                                     values=[1, 2, 3, 5, 10], width=5, state="readonly",
                                     font=("Arial", 10))
        multipv_combo.pack(side=tk.LEFT, padx=10)
        multipv_combo.set(3)

        # Кнопка анализа
        self.analyze_button = ttk.Button(settings_frame, text="🚀 НАЧАТЬ АНАЛИЗ",
                                         command=self.start_analysis,
                                         style="Accent.TButton", width=25)
        self.analyze_button.grid(row=3, column=0, columnspan=3, pady=(5, 0))

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

        ttk.Label(bottom_frame, text="ШАХМАТНЫЙ АНАЛИЗАТОР v2.0 © 2024",
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

        cell_size = 60  # Увеличили размер клетки
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
                row = 7 - (square // 8)  # Инвертируем строки
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

    def on_board_click(self, event):
        """Обработка клика по шахматной доске"""
        if self.is_analyzing:
            return

        cell_size = 60
        col = event.x // cell_size
        row = event.y // cell_size

        if 0 <= col < 8 and 0 <= row < 8:
            square = chess.square(col, 7 - row)  # Преобразуем координаты

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

                    # Проверяем, правильный ли это ход
                    if move in self.board.legal_moves:
                        self.board.push(move)
                        self.selected_square = None
                        self.best_move = None
                        self.update_display()
                        self.status_var.set(f"✅ Ход {self.board.san(move)} сделан")
                    else:
                        self.selected_square = None
                        self.update_display()
                        self.status_var.set("❌ Невозможный ход")

                except:
                    self.selected_square = None
                    self.update_display()

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
        self.update_display()
        self.clear_results()
        self.status_var.set("🆕 Новая игра начата")

    def undo_move(self):
        """Отменить последний ход"""
        if len(self.board.move_stack) > 0:
            self.board.pop()
            self.selected_square = None
            self.best_move = None
            self.update_display()
            self.status_var.set("↶ Ход отменён")

    def redo_move(self):
        """Повторить отменённый ход"""
        # В этой версии просто очищаем результаты
        self.status_var.set("Функция в разработке")

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
                self.board.set_piece_at(square, chess.Piece.from_symbol(piece))

        self.selected_square = None
        self.best_move = None
        self.update_display()
        self.clear_results()
        self.status_var.set("🎲 Создана случайная позиция")

    def load_fen_dialog(self):
        """Диалог загрузки FEN"""
        fen = simpledialog.askstring("Загрузка FEN",
                                     "Введите FEN строку:",
                                     initialvalue=self.board.fen())
        if fen:
            try:
                self.board = chess.Board(fen)
                self.selected_square = None
                self.best_move = None
                self.update_display()
                self.clear_results()
                self.status_var.set("✅ FEN загружен успешно")
            except Exception as e:
                self.show_error("Ошибка загрузки FEN", str(e))

    def save_fen_dialog(self):
        """Диалог сохранения FEN"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".fen",
            filetypes=[("FEN files", "*.fen"), ("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="chess_position.fen"
        )

        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.board.fen())
                self.status_var.set(f"💾 FEN сохранён в {filename}")
            except Exception as e:
                self.show_error("Ошибка сохранения", str(e))

    def load_board_photo(self):
        """Загрузка фото шахматной доски"""
        self.status_var.set("📷 Загрузка фото в разработке...")
        messagebox.showinfo("В разработке",
                            "Функция загрузки фото доски будет добавлена в следующей версии.\n"
                            "Пока используйте FEN для загрузки позиций.")

    def show_position_stats(self):
        """Показать статистику позиции"""
        stats = self.calculate_position_stats()

        stats_text = f"""📊 СТАТИСТИКА ПОЗИЦИИ:

Материальный баланс: {stats['material']}
Контроль центра: {stats['center_control']}
Активность фигур: {stats['piece_activity']}
Безопасность королей: {stats['king_safety']}

Количество фигур:
• Белые: {stats['white_pieces']}
• Чёрные: {stats['black_pieces']}
• Всего: {stats['total_pieces']}

Свободных клеток: {stats['empty_squares']}
"""

        messagebox.showinfo("Статистика позиции", stats_text)

    def calculate_position_stats(self):
        """Вычисление статистики позиции"""
        # Подсчёт материала
        piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
        material = 0

        white_pieces = 0
        black_pieces = 0

        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                if piece.color == chess.WHITE:
                    material += piece_values.get(piece.symbol().upper(), 0)
                    white_pieces += 1
                else:
                    material -= piece_values.get(piece.symbol().upper(), 0)
                    black_pieces += 1

        material_text = f"{'+' if material > 0 else ''}{material}"

        return {
            'material': material_text,
            'center_control': self.calculate_center_control(),
            'piece_activity': "Средняя",
            'king_safety': "Нормальная",
            'white_pieces': white_pieces,
            'black_pieces': black_pieces,
            'total_pieces': white_pieces + black_pieces,
            'empty_squares': 64 - (white_pieces + black_pieces)
        }

    def calculate_center_control(self):
        """Оценка контроля центра"""
        center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
        control = 0

        for square in center_squares:
            attackers_white = len(self.board.attackers(chess.WHITE, square))
            attackers_black = len(self.board.attackers(chess.BLACK, square))
            control += attackers_white - attackers_black

        if control > 2:
            return "Сильный контроль белых"
        elif control > 0:
            return "Контроль белых"
        elif control == 0:
            return "Равный контроль"
        elif control > -2:
            return "Контроль чёрных"
        else:
            return "Сильный контроль чёрных"

    def start_analysis(self):
        """Начало анализа позиции"""
        if self.is_analyzing:
            return

        if not self.engine:
            self.show_error("Stockfish не загружен",
                            "Не удалось загрузить шахматный движок.\n"
                            "Проверьте наличие stockfish.exe в папке программы.")
            return

        # Получаем настройки
        try:
            level = self.level_var.get()
            multipv = self.multipv_var.get()
        except:
            self.show_error("Ошибка настроек", "Проверьте настройки анализа")
            return

        # Подготавливаем интерфейс
        self.is_analyzing = True
        self.analyze_button.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.status_var.set(f"🔍 Анализирую позицию... ({self.analysis_time:.1f} сек)")

        # Запускаем анализ в отдельном потоке
        thread = threading.Thread(target=self.run_analysis,
                                  args=(level, multipv))
        thread.daemon = True
        thread.start()

    def run_analysis(self, level, multipv):
        """Выполнение анализа в отдельном потоке"""
        try:
            # Настройка движка
            self.engine.configure({"Skill Level": level})

            # Прогресс-бар имитация
            for i in range(101):
                time.sleep(self.analysis_time / 100)
                self.root.after(0, lambda v=i: self.progress_var.set(v))

            # Выполнение анализа
            if multipv > 1:
                result = self.engine.analyse(
                    self.board,
                    chess.engine.Limit(time=self.analysis_time),
                    multipv=multipv
                )
                analysis_results = result
            else:
                result = self.engine.analyse(
                    self.board,
                    chess.engine.Limit(time=self.analysis_time)
                )
                analysis_results = [result]

            # Обновляем интерфейс
            self.root.after(0, self.display_results, analysis_results)

        except Exception as e:
            self.root.after(0, lambda: self.show_error("Ошибка анализа", str(e)))
        finally:
            self.is_analyzing = False
            self.root.after(0, lambda: self.analyze_button.config(state=tk.NORMAL))

    def display_results(self, results):
        """Отображение результатов анализа"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)

        best_result = results[0]
        self.best_move = best_result["pv"][0]
        best_score = best_result["score"].white()

        # Заголовок
        self.results_text.insert(tk.END, "=" * 70 + "\n", "header")
        self.results_text.insert(tk.END, "🎯 РЕЗУЛЬТАТЫ АНАЛИЗА\n", "header")
        self.results_text.insert(tk.END, "=" * 70 + "\n\n", "header")

        # Лучший ход
        move_san = self.board.san(self.best_move)
        self.results_text.insert(tk.END, "ЛУЧШИЙ ХОД:\n", "header")
        self.results_text.insert(tk.END, f"  {move_san} ({self.best_move})\n\n", "best")

        # Оценка позиции
        self.results_text.insert(tk.END, "📊 ОЦЕНКА ПОЗИЦИИ:\n", "header")

        if best_score.is_mate():
            mate_in = best_score.mate()
            if mate_in > 0:
                self.results_text.insert(tk.END, f"  Мат белым в {mate_in} ходов\n", "mate")
                self.results_text.insert(tk.END, "  ⚡ РЕШАЮЩЕЕ ПРЕИМУЩЕСТВО БЕЛЫХ!\n\n", "best")
            else:
                self.results_text.insert(tk.END, f"  Мат чёрным в {-mate_in} ходов\n", "mate")
                self.results_text.insert(tk.END, "  ⚡ РЕШАЮЩЕЕ ПРЕИМУЩЕСТВО ЧЁРНЫХ!\n\n", "best")
        else:
            eval_score = best_score.score() / 100.0

            if eval_score > 3.0:
                tag = "best"
                comment = "🏆 РЕШАЮЩЕЕ ПРЕИМУЩЕСТВО БЕЛЫХ"
            elif eval_score > 1.0:
                tag = "best"
                comment = "⭐ БОЛЬШОЕ ПРЕИМУЩЕСТВО БЕЛЫХ"
            elif eval_score > 0.5:
                tag = "good"
                comment = "↑ ПРЕИМУЩЕСТВО БЕЛЫХ"
            elif eval_score > 0.2:
                tag = "good"
                comment = "↗ НЕБОЛЬШОЕ ПРЕИМУЩЕСТВО БЕЛЫХ"
            elif eval_score > -0.2:
                tag = "neutral"
                comment = "↔ РАВНАЯ ПОЗИЦИЯ"
            elif eval_score > -0.5:
                tag = "bad"
                comment = "↘ НЕБОЛЬШОЕ ПРЕИМУЩЕСТВО ЧЁРНЫХ"
            elif eval_score > -1.0:
                tag = "bad"
                comment = "↓ ПРЕИМУЩЕСТВО ЧЁРНЫХ"
            elif eval_score > -3.0:
                tag = "bad"
                comment = "⭐ БОЛЬШОЕ ПРЕИМУЩЕСТВО ЧЁРНЫХ"
            else:
                tag = "bad"
                comment = "🏆 РЕШАЮЩЕЕ ПРЕИМУЩЕСТВО ЧЁРНЫХ"

            self.results_text.insert(tk.END, f"  {eval_score:+.2f} пешки\n", tag)
            self.results_text.insert(tk.END, f"  {comment}\n\n", tag)

        # Все варианты
        self.results_text.insert(tk.END, f"📋 ТОП-{len(results)} ВАРИАНТОВ:\n", "header")
        self.results_text.insert(tk.END, "-" * 70 + "\n\n")

        for i, result in enumerate(results, 1):
            move = result["pv"][0]
            score = result["score"].white()
            move_san = self.board.san(move)

            # Форматирование оценки
            if score.is_mate():
                eval_text = f"Мат в {abs(score.mate())}"
                tag = "mate"
            else:
                eval_score = score.score() / 100.0
                eval_text = f"{eval_score:+.2f}"

                if i == 1:
                    tag = "best"
                elif eval_score > 0.3:
                    tag = "good"
                elif eval_score > -0.3:
                    tag = "neutral"
                else:
                    tag = "bad"

            # Вариант (первые 4 хода)
            variant_moves = []
            temp_board = self.board.copy()
            for mv in result["pv"][:4]:
                try:
                    variant_moves.append(temp_board.san(mv))
                    temp_board.push(mv)
                except:
                    variant_moves.append(str(mv))

            # Вывод варианта
            self.results_text.insert(tk.END, f"{i:2}. {move_san:8} → {eval_text:12}\n", tag)

            if variant_moves:
                variant_text = " → ".join(variant_moves)
                self.results_text.insert(tk.END, f"    {variant_text}\n\n", "neutral")

        # Статистика анализа
        depth = best_result.get('depth', 'N/A')
        nodes = best_result.get('nodes', 0)
        nps = nodes / best_result.get('time', self.analysis_time)

        self.results_text.insert(tk.END, "📈 СТАТИСТИКА АНАЛИЗА:\n", "header")
        self.results_text.insert(tk.END, f"  • Глубина анализа: {depth}\n", "neutral")
        self.results_text.insert(tk.END, f"  • Узлов рассмотрено: {nodes:,}\n", "neutral")
        self.results_text.insert(tk.END, f"  • Скорость анализа: {nps / 1000:.0f} тыс.узлов/сек\n", "neutral")
        self.results_text.insert(tk.END, f"  • Время анализа: {self.analysis_time:.1f} сек\n", "neutral")
        self.results_text.insert(tk.END, f"  • Уровень сложности: {self.level_var.get()}/20\n\n", "neutral")

        # Рекомендация
        self.results_text.insert(tk.END, "💡 РЕКОМЕНДАЦИЯ:\n", "header")

        if best_score.is_mate() and best_score.mate() > 0:
            recommendation = f"СРОЧНО делайте {move_san}! Этот ход ведёт к мату."
        elif not best_score.is_mate() and best_score.score() > 300:
            recommendation = f"Ход {move_san} даёт большое преимущество. Рекомендуется!"
        elif not best_score.is_mate() and best_score.score() > 100:
            recommendation = f"Ход {move_san} - хорошее продолжение."
        elif not best_score.is_mate() and best_score.score() > -100:
            recommendation = f"Ход {move_san} - стандартное продолжение."
        else:
            recommendation = f"Ход {move_san} - лучший из плохих вариантов. Будьте осторожны!"

        self.results_text.insert(tk.END, f"  {recommendation}\n\n", "neutral")

        # Обновляем доску с подсветкой
        self.update_display()

        # Обновляем статус
        self.status_var.set(f"✅ Анализ завершён. Найдено {len(results)} вариантов.")

        # Прокручиваем в начало
        self.results_text.see(1.0)
        self.results_text.config(state=tk.DISABLED)

    def make_best_move(self):
        """Сделать лучший ход на доске"""
        if self.best_move:
            try:
                self.board.push(self.best_move)
                self.selected_square = None
                self.best_move = None
                self.update_display()
                self.clear_results()
                self.status_var.set(f"✅ Ход {self.board.san(self.best_move)} сделан")
            except Exception as e:
                self.show_error("Ошибка", f"Не удалось сделать ход: {e}")
        else:
            messagebox.showinfo("Информация", "Сначала выполните анализ позиции")

    def clear_results(self):
        """Очистка результатов анализа"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)

        welcome_text = """Добро пожаловать в ШАХМАТНЫЙ АНАЛИЗАТОР!

Для начала анализа:
1. Установите параметры анализа справа
2. Нажмите кнопку "НАЧАТЬ АНАЛИЗ"
3. Дождитесь результатов

Возможности программы:
• Анализ любой шахматной позиции
• Несколько вариантов продолжения
• Оценка позиции в пешках
• Рекомендации по лучшим ходам
• Подсветка ходов на доске
• Сохранение и загрузка позиций

Удачи в анализе! 🏆
"""

        self.results_text.insert(1.0, welcome_text)
        self.results_text.config(state=tk.DISABLED)
        self.status_var.set("✅ Готов к анализу")

    def save_analysis(self):
        """Сохранение анализа в файл"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"chess_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if filename:
            try:
                analysis_text = self.results_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Анализ шахматной позиции\n")
                    f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"FEN: {self.board.fen()}\n")
                    f.write("=" * 70 + "\n\n")
                    f.write(analysis_text)

                self.status_var.set(f"💾 Анализ сохранён в {filename}")
            except Exception as e:
                self.show_error("Ошибка сохранения", str(e))

    def show_error(self, title, message):
        """Показать сообщение об ошибке"""
        messagebox.showerror(title, message)
        self.status_var.set(f"❌ {title}")

    def show_instructions(self):
        """Показать инструкцию по использованию"""
        instructions = """=== ШАХМАТНЫЙ АНАЛИЗАТОР - ИНСТРУКЦИЯ ===

🎯 ОСНОВНЫЕ ВОЗМОЖНОСТИ:

1. АНАЛИЗ ПОЗИЦИЙ:
   • Загрузка любой позиции (FEN или новая игра)
   • Анализ движком Stockfish
   • Несколько вариантов продолжения
   • Оценка позиции в пешках или матовые варианты

2. УПРАВЛЕНИЕ ДОСКОЙ:
   • Кликните по фигуре, затем по клетке для хода
   • Кнопки "Отменить ход" и "Новая игра"
   • Случайные позиции для тренировки

3. НАСТРОЙКИ АНАЛИЗА:
   • Время анализа: 0.5 - 30 секунд
   • Уровень сложности: 0 (новичок) - 20 (гроссмейстер)
   • Количество вариантов: 1-10

4. РАБОТА С ФАЙЛАМИ:
   • Сохранение/загрузка позиций (FEN)
   • Сохранение результатов анализа
   • Экспорт в текстовый файл

📊 КАК ЧИТАТЬ РЕЗУЛЬТАТЫ:

• +1.50 = преимущество белых в 1.5 пешки
• Мат в 3 = мат через 3 хода
• Зелёный текст = лучшие ходы
• Красный текст = плохие ходы
• Стрелки на доске показывают рекомендуемые ходы

💡 СОВЕТЫ:

• Для тренировки используйте уровень 5-10
• Для глубокого анализа - 20+ секунд и уровень 20
• Сохраняйте интересные позиции для дальнейшего изучения
• Используйте случайные позиции для разнообразия

⚠️ ТРЕБОВАНИЯ:

• Stockfish.exe в папке с программой
• Python 3.6 или новее
• Библиотеки: python-chess, tkinter

📞 ПОДДЕРЖКА:

Программа разработана для учебного проекта.
Все вопросы и предложения приветствуются!
"""

        # Создаём окно с инструкцией
        help_window = tk.Toplevel(self.root)
        help_window.title("📖 Инструкция по использованию")
        help_window.geometry("700x600")

        text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD,
                                         font=("Arial", 10), padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert(tk.END, instructions)
        text.config(state=tk.DISABLED)

        ttk.Button(help_window, text="Закрыть",
                   command=help_window.destroy).pack(pady=10)

    def show_about(self):
        """Показать информацию о программе"""
        about_text = """=== ШАХМАТНЫЙ АНАЛИЗАТОР v2.0 ===

🎮 ПРОГРАММА ДЛЯ АНАЛИЗА ШАХМАТНЫХ ПОЗИЦИЙ

ОСНОВНЫЕ ФУНКЦИИ:
• Анализ позиций движком Stockfish
• Графический интерфейс с шахматной доской
• Подробные рекомендации и варианты
• Сохранение и загрузка позиций
• Подсветка рекомендуемых ходов

ТЕХНОЛОГИИ:
• Python 3
• Stockfish 16 (сильнейший шахматный движок)
• Библиотека python-chess
• Графический интерфейс Tkinter

ВОЗМОЖНОСТИ АНАЛИЗА:
• Оценка позиции в пешках
• Поиск матовых комбинаций
• Несколько вариантов продолжения
• Статистика позиции
• Рекомендации на русском языке

ДЛЯ КОГО ЭТА ПРОГРАММА:
• Шахматистов-любителей для анализа партий
• Тренеров для подготовки учеников
• Студентов для изучения алгоритмов
• Всех, кто хочет улучшить свою игру

🌟 ОСОБЕННОСТИ:
• Простой и понятный интерфейс
• Быстрый и глубокий анализ
• Подробные объяснения
• Работа без интернета

АВТОР: Разработано для учебного проекта по
компьютерному зрению и искусственному интеллекту.

ВЕРСИЯ: 2.0 (Январь 2024)

📧 Контакт: Для вопросов и предложений
"""

        messagebox.showinfo("О программе", about_text)

    def debug_info(self):
        """Отладочная информация"""
        info = f"""=== ОТЛАДОЧНАЯ ИНФОРМАЦИЯ ===

Программа: Шахматный анализатор v2.0
Python: {sys.version}
Движок: {'Загружен' if self.engine else 'Не загружен'}
Текущая позиция: {self.board.fen()}
Ход: {'белых' if self.board.turn == chess.WHITE else 'чёрных'}
Количество ходов: {len(self.board.move_stack)}

Путь к Stockfish: {self.engine_path}
Существует: {'Да' if os.path.exists(self.engine_path) else 'Нет'}

Параметры анализа:
• Время: {self.analysis_time} сек
• Уровень: {self.level_var.get()}/20
• Вариантов: {self.multipv_var.get()}

Память: {len(self.board.move_stack)} ходов в истории
"""

        # Для sys.version нужно импортировать sys
        import sys

        messagebox.showinfo("Отладочная информация", info)

    def on_closing(self):
        """Обработка закрытия окна"""
        if messagebox.askyesno("Выход", "Вы уверены, что хотите выйти?"):
            if self.engine:
                try:
                    self.engine.quit()
                except:
                    pass
            self.root.destroy()


# ============================================
# ЗАПУСК ПРОГРАММЫ
# ============================================

if __name__ == "__main__":
    import sys

    root = tk.Tk()

    # Устанавливаем иконку (если есть)
    try:
        root.iconbitmap("chess_icon.ico")
    except:
        pass

    # Создаём экземпляр программы
    app = ChessAnalyzerGUI(root)

    # Обработка закрытия окна
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # Запуск главного цикла
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nПрограмма завершена пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        messagebox.showerror("Ошибка", f"Критическая ошибка:\n{e}")