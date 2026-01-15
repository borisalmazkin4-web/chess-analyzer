# ============================================
# ПРОДВИНУТЫЙ ШАХМАТНЫЙ АНАЛИЗАТОР
# Версия 2.0 с расширенными функциями
# ============================================

import chess
import chess.engine
import chess.pgn
import os
import sys
import json
from datetime import datetime
import time

print("=" * 70)
print("🎯 ПРОДВИНУТЫЙ ШАХМАТНЫЙ АНАЛИЗАТОР v2.0")
print("=" * 70)
print()

class ChessAnalyzer:
    def __init__(self):
        self.engine = None
        self.board = None
        self.analysis_time = 3.0
        self.depth_limit = 20
        self.engine_level = 20  # Уровень Stockfish (0-20)
        
    def clear_screen(self):
        """Очистка экрана консоли"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title):
        """Печать красивого заголовка"""
        print("\n" + "=" * 70)
        print(f"📊 {title}")
        print("=" * 70)
    
    def load_stockfish(self):
        """Загрузка шахматного движка"""
        self.print_header("ЗАГРУЗКА ДВИЖКА")
        
        # Поиск Stockfish
        possible_paths = [
            "stockfish.exe",
            "./stockfish.exe",
            "C:\\stockfish\\stockfish.exe",
            "stockfish",
            "/usr/local/bin/stockfish",
            "/usr/bin/stockfish",
        ]
        
        engine_path = None
        for path in possible_paths:
            if os.path.exists(path):
                engine_path = path
                print(f"✅ Найден Stockfish: {path}")
                break
        
        if not engine_path:
            print("❌ Stockfish не найден!")
            print("\n📥 Установите Stockfish:")
            print("1. Скачайте с https://stockfishchess.org/download/")
            print("2. Распакуйте в папку с программой")
            print("3. Переименуйте в stockfish.exe")
            return False
        
        # Запуск движка
        try:
            print("🚀 Запускаю движок...")
            self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
            
            # Настройка уровня сложности (0-20)
            self.engine.configure({"Skill Level": self.engine_level})
            
            print(f"✅ Движок запущен: {self.engine.id['name']}")
            print(f"📈 Уровень сложности: {self.engine_level}/20")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка запуска: {e}")
            return False
    
    def load_position(self):
        """Загрузка шахматной позиции"""
        self.print_header("ЗАГРУЗКА ПОЗИЦИИ")
        
        print("Выберите источник позиции:")
        print("1. 🎯 Начальная позиция")
        print("2. 📁 FEN из Шага 3 (step3_results.txt)")
        print("3. ✏️  Ввести FEN вручную")
        print("4. 📝 Ввести ходы вручную")
        print("5. 🗂️  Загрузить PGN файл")
        
        choice = input("\nВаш выбор (1-5): ").strip()
        
        if choice == "1":
            self.board = chess.Board()
            print("✅ Загружена начальная позиция")
            
        elif choice == "2":
            if self.load_fen_from_step3():
                print("✅ FEN загружен из Шага 3")
            else:
                print("⚠️  Использую начальную позицию")
                self.board = chess.Board()
                
        elif choice == "3":
            fen = input("Введите FEN строку: ").strip()
            try:
                self.board = chess.Board(fen)
                print("✅ FEN загружен успешно")
            except:
                print("❌ Неверный FEN. Использую начальную позицию")
                self.board = chess.Board()
                
        elif choice == "4":
            self.board = chess.Board()
            print("Вводите ходы в шахматной нотации (например, e4, Nf3)")
            print("Для завершения введите 'done'")
            
            while True:
                print(f"\nТекущая позиция (ход {'белых' if self.board.turn == chess.WHITE else 'чёрных'}):")
                print(self.board.unicode(invert_color=True, borders=True))
                
                move_input = input("Введите ход (или 'done'): ").strip()
                if move_input.lower() == 'done':
                    break
                
                try:
                    move = self.board.parse_san(move_input)
                    self.board.push(move)
                    print(f"✅ Ход {move_input} добавлен")
                except:
                    print(f"❌ Неверный ход: {move_input}")
                    
        elif choice == "5":
            pgn_file = input("Введите имя PGN файла: ").strip()
            if os.path.exists(pgn_file):
                with open(pgn_file) as f:
                    game = chess.pgn.read_game(f)
                    self.board = game.board()
                    for move in game.mainline_moves():
                        self.board.push(move)
                print("✅ PGN файл загружен")
            else:
                print("❌ Файл не найден. Использую начальную позицию")
                self.board = chess.Board()
        
        else:
            print("⚠️  Неверный выбор. Использую начальную позицию")
            self.board = chess.Board()
        
        print(f"\n📊 Информация о позиции:")
        print(f"   • FEN: {self.board.fen()}")
        print(f"   • Ход: {'белых' if self.board.turn == chess.WHITE else 'чёрных'}")
        print(f"   • Возможных ходов: {self.board.legal_moves.count()}")
        print(f"   • Материал: {self.get_material_count()}")
        
        return True
    
    def load_fen_from_step3(self):
        """Загрузка FEN из результатов Шага 3"""
        if not os.path.exists("step3_results.txt"):
            return False
        
        try:
            with open("step3_results.txt", "r", encoding="utf-8") as f:
                content = f.read()
                
            # Ищем FEN в файле
            lines = content.split('\n')
            for line in lines:
                if line.startswith("FEN: "):
                    fen = line.replace("FEN: ", "").strip()
                    self.board = chess.Board(fen)
                    return True
                    
            # Если не нашли "FEN: ", ищем просто FEN строку
            for line in lines:
                if "/" in line and len(line.split("/")) == 8:
                    # Проверяем, похоже ли на FEN
                    parts = line.strip().split()
                    if len(parts) >= 1:
                        try:
                            self.board = chess.Board(line.strip())
                            return True
                        except:
                            continue
        except:
            pass
        
        return False
    
    def get_material_count(self):
        """Подсчёт материала на доске"""
        piece_values = {
            'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0,
            'p': -1, 'n': -3, 'b': -3, 'r': -5, 'q': -9, 'k': 0
        }
        
        total = 0
        board_fen = self.board.board_fen()
        for char in board_fen:
            if char in piece_values:
                total += piece_values[char]
        
        return f"{'+' if total > 0 else ''}{total}"
    
    def configure_analysis(self):
        """Настройка параметров анализа"""
        self.print_header("НАСТРОЙКА АНАЛИЗА")
        
        print("⏱️  Время анализа на ход:")
        print("1. ⚡ Быстрый (1 сек)")
        print("2. ⏳ Стандартный (3 сек)")
        print("3. 🔍 Глубокий (10 сек)")
        print("4. 🎯 Пользовательский")
        
        time_choice = input("\nВыберите время (1-4): ").strip()
        
        if time_choice == "1":
            self.analysis_time = 1.0
        elif time_choice == "2":
            self.analysis_time = 3.0
        elif time_choice == "3":
            self.analysis_time = 10.0
        elif time_choice == "4":
            try:
                custom_time = float(input("Введите время в секундах: "))
                self.analysis_time = max(0.5, min(custom_time, 60.0))
            except:
                print("⚠️  Неверное значение. Использую 3 сек")
                self.analysis_time = 3.0
        else:
            print("⚠️  Неверный выбор. Использую 3 сек")
            self.analysis_time = 3.0
        
        print(f"\n📈 Уровень сложности движка (0-20):")
        print("  0 - Новичок, 10 - Средний, 20 - Максимальный")
        
        try:
            level = int(input("Введите уровень (0-20): "))
            self.engine_level = max(0, min(level, 20))
            self.engine.configure({"Skill Level": self.engine_level})
        except:
            print("⚠️  Неверное значение. Использую уровень 20")
        
        print(f"\n✅ Настройки сохранены:")
        print(f"   • Время анализа: {self.analysis_time} сек")
        print(f"   • Уровень сложности: {self.engine_level}/20")
    
    def analyze_position(self):
        """Основной анализ позиции"""
        self.print_header("АНАЛИЗ ПОЗИЦИИ")
        
        print("Текущая позиция:")
        print(self.board.unicode(invert_color=True, borders=True))
        print()
        
        print(f"🔬 Анализирую... (это займёт ~{self.analysis_time} сек)")
        start_time = time.time()
        
        try:
            # Анализ с несколькими вариантами
            analysis = self.engine.analyse(
                self.board, 
                chess.engine.Limit(time=self.analysis_time),
                multipv=5  # 5 лучших вариантов
            )
            
            analysis_time = time.time() - start_time
            
            print(f"✅ Анализ завершён за {analysis_time:.1f} сек")
            print()
            
            # Вывод результатов
            self.print_analysis_results(analysis)
            
            # Сохранение результатов
            self.save_analysis_results(analysis)
            
            # Дополнительные опции
            self.show_analysis_options(analysis)
            
        except Exception as e:
            print(f"❌ Ошибка анализа: {e}")
    
    def print_analysis_results(self, analysis):
        """Вывод результатов анализа"""
        print("🎯 ЛУЧШИЕ ХОДЫ:")
        print("-" * 50)
        
        for i, result in enumerate(analysis, 1):
            best_move = result["pv"][0]
            score = result["score"].white()
            
            # Форматирование хода
            move_san = self.board.san(best_move)
            
            # Форматирование оценки
            if score.is_mate():
                eval_text = f"Мат в {abs(score.mate())}"
                eval_symbol = "♔" if score.mate() > 0 else "♚"
            else:
                eval_score = score.score() / 100.0
                eval_text = f"{eval_score:+.2f}"
                eval_symbol = "↑" if eval_score > 0 else "↓" if eval_score < 0 else "="
            
            # Информация о анализе
            depth = result.get("depth", "N/A")
            nodes = result.get("nodes", 0)
            nps = nodes / result.get("time", 1) if result.get("time", 0) > 0 else 0
            
            print(f"{i}. {eval_symbol} {move_san:6} | {eval_text:10} | Глубина: {depth:2} | {nodes//1000}K узлов")
            
            # Показываем вариант (первые 4 хода)
            if i <= 3:  # Только для топ-3 вариантов
                variant_moves = []
                temp_board = self.board.copy()
                
                for j, move in enumerate(result["pv"][:4]):
                    if j >= 4:
                        variant_moves.append("...")
                        break
                    variant_moves.append(temp_board.san(move))
                    temp_board.push(move)
                
                print(f"   Вариант: {' → '.join(variant_moves)}")
                print()
        
        print("-" * 50)
        
        # Оценка позиции
        best_result = analysis[0]
        score = best_result["score"].white()
        
        print("\n📊 ОЦЕНКА ПОЗИЦИИ:")
        if score.is_mate():
            mate_in = score.mate()
            if mate_in > 0:
                print(f"   ♔ Решающее преимущество белых: мат в {mate_in} ходов")
            else:
                print(f"   ♚ Решающее преимущество чёрных: мат в {-mate_in} ходов")
        else:
            eval_score = score.score() / 100.0
            if abs(eval_score) > 3.0:
                print(f"   🏆 Решающее преимущество: {eval_score:+.2f}")
            elif abs(eval_score) > 1.0:
                print(f"   ⭐ Значительное преимущество: {eval_score:+.2f}")
            elif abs(eval_score) > 0.5:
                print(f"   📈 Небольшое преимущество: {eval_score:+.2f}")
            elif abs(eval_score) > 0.2:
                print(f"   ⚖️  Минимальное преимущество: {eval_score:+.2f}")
            else:
                print(f"   🤝 Равная позиция: {eval_score:+.2f}")
        
        # Рекомендация
        print("\n💡 РЕКОМЕНДАЦИЯ:")
        best_move = best_result["pv"][0]
        move_san = self.board.san(best_move)
        
        if score.is_mate():
            if score.mate() > 0:
                print(f"   Срочно делайте {move_san}! Это ведёт к мату.")
            else:
                print(f"   Ход {move_san} отдаляет мат. Ищите лучшие продолжения.")
        else:
            eval_score = score.score() / 100.0
            if eval_score > 1.0:
                print(f"   Ход {move_san} даёт большое преимущество.")
            elif eval_score > 0.3:
                print(f"   Ход {move_san} - солидное продолжение.")
            elif eval_score > -0.3:
                print(f"   Ход {move_san} - примерно равноправный вариант.")
            else:
                print(f"   Ход {move_san} - лучший из плохих вариантов.")
    
    def show_analysis_options(self, analysis):
        """Показать дополнительные опции после анализа"""
        print("\n" + "=" * 50)
        print("📋 ДОПОЛНИТЕЛЬНЫЕ ОПЦИИ:")
        print("1. 📤 Сделать лучший ход на доске")
        print("2. 🔄 Проанализировать новую позицию")
        print("3. 📊 Детальная статистика")
        print("4. 💾 Сохранить анализ в файл")
        print("5. 🎮 Продолжить анализ с этой позиции")
        print("6. 🏠 Вернуться в главное меню")
        print("7. 🚪 Выйти")
        
        choice = input("\nВаш выбор (1-7): ").strip()
        
        if choice == "1":
            best_move = analysis[0]["pv"][0]
            self.board.push(best_move)
            print(f"\n✅ Ход {self.board.san(best_move)} сделан")
            print("Новая позиция:")
            print(self.board.unicode(invert_color=True, borders=True))
            input("\nНажмите Enter для продолжения...")
            
        elif choice == "2":
            self.load_position()
            self.analyze_position()
            
        elif choice == "3":
            self.show_detailed_stats(analysis[0])
            
        elif choice == "4":
            self.save_analysis_to_file(analysis)
            
        elif choice == "5":
            self.analyze_position()  # Анализ новой позиции
            
        elif choice == "6":
            return
            
        elif choice == "7":
            self.cleanup()
            print("\n👋 До свидания!")
            sys.exit(0)
    
    def show_detailed_stats(self, analysis_result):
        """Показать детальную статистику анализа"""
        self.print_header("ДЕТАЛЬНАЯ СТАТИСТИКА")
        
        print("📈 ПАРАМЕТРЫ АНАЛИЗА:")
        print(f"   • Глубина: {analysis_result.get('depth', 'N/A')}")
        print(f"   • Узлов: {analysis_result.get('nodes', 0):,}")
        print(f"   • Время: {analysis_result.get('time', 0):.2f} сек")
        
        nps = analysis_result.get('nodes', 0) / analysis_result.get('time', 1)
        print(f"   • Скорость: {nps/1000:.0f} тыс. узлов/сек")
        
        print(f"   • Ходов в варианте: {len(analysis_result.get('pv', []))}")
        
        # Информация о позиции
        print("\n🎲 ХАРАКТЕРИСТИКИ ПОЗИЦИИ:")
        print(f"   • Активность фигур: {self.calculate_piece_activity()}")
        print(f"   • Контроль центра: {self.calculate_center_control()}")
        print(f"   • Безопасность короля: {self.estimate_king_safety()}")
    
    def calculate_piece_activity(self):
        """Оценка активности фигур"""
        # Упрощённая оценка
        return "Средняя"
    
    def calculate_center_control(self):
        """Оценка контроля центра"""
        center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
        control = 0
        
        for square in center_squares:
            attackers = self.board.attackers(chess.WHITE, square)
            defenders = self.board.attackers(chess.BLACK, square)
            control += len(attackers) - len(defenders)
        
        if control > 2:
            return "Сильный"
        elif control > 0:
            return "Умеренный"
        elif control == 0:
            return "Равный"
        else:
            return "Слабый"
    
    def estimate_king_safety(self):
        """Оценка безопасности королей"""
        # Упрощённая оценка
        return "Нормальная"
    
    def save_analysis_results(self, analysis):
        """Сохранение результатов анализа"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{timestamp}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("АНАЛИЗ ШАХМАТНОЙ ПОЗИЦИИ\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Движок: {self.engine.id['name']}\n")
            f.write(f"Уровень: {self.engine_level}/20\n")
            f.write(f"Время анализа: {self.analysis_time} сек\n\n")
            
            f.write(f"Позиция (FEN): {self.board.fen()}\n\n")
            
            f.write("Доска:\n")
            f.write(str(self.board.unicode(invert_color=True, borders=True)) + "\n\n")
            
            f.write("ЛУЧШИЕ ХОДЫ:\n")
            for i, result in enumerate(analysis[:5], 1):
                best_move = result["pv"][0]
                score = result["score"].white()
                
                move_san = self.board.san(best_move)
                
                if score.is_mate():
                    eval_text = f"Мат в {abs(score.mate())}"
                else:
                    eval_score = score.score() / 100.0
                    eval_text = f"{eval_score:+.2f}"
                
                f.write(f"{i}. {move_san}: {eval_text}\n")
                
                # Вариант
                variant_moves = []
                temp_board = self.board.copy()
                for move in result["pv"][:6]:
                    variant_moves.append(temp_board.san(move))
                    temp_board.push(move)
                
                f.write(f"   Вариант: {' → '.join(variant_moves)}\n\n")
        
        print(f"✅ Результаты сохранены в {filename}")
    
    def save_analysis_to_file(self, analysis):
        """Сохранение анализа в разные форматы"""
        self.print_header("СОХРАНЕНИЕ АНАЛИЗА")
        
        print("Выберите формат:")
        print("1. 📝 Текстовый файл (анализ)")
        print("2. 📄 PGN файл (шахматная партия)")
        print("3. 📊 JSON (для программного анализа)")
        print("4. 📋 Все форматы")
        
        choice = input("\nВаш выбор (1-4): ").strip()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if choice in ["1", "4"]:
            # Текстовый файл
            with open(f"analysis_{timestamp}.txt", "w", encoding="utf-8") as f:
                f.write(f"Анализ позиции: {self.board.fen()}\n")
                f.write(f"Лучший ход: {self.board.san(analysis[0]['pv'][0])}\n")
            print("✅ Текстовый файл сохранён")
        
        if choice in ["2", "4"]:
            # PGN файл
            game = chess.pgn.Game()
            game.headers["Event"] = "Computer Analysis"
            game.headers["Site"] = "Chess Analyzer"
            game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
            game.headers["FEN"] = self.board.fen()
            
            with open(f"analysis_{timestamp}.pgn", "w") as f:
                f.write(str(game))
            print("✅ PGN файл сохранён")
        
        if choice in ["3", "4"]:
            # JSON файл
            analysis_data = {
                "fen": self.board.fen(),
                "best_move": str(analysis[0]['pv'][0]),
                "evaluation": str(analysis[0]['score']),
                "analysis_time": self.analysis_time,
                "timestamp": timestamp
            }
            
            with open(f"analysis_{timestamp}.json", "w") as f:
                json.dump(analysis_data, f, indent=2)
            print("✅ JSON файл сохранён")
        
        input("\nНажмите Enter для продолжения...")
    
    def batch_analysis(self):
        """Пакетный анализ нескольких позиций"""
        self.print_header("ПАКЕТНЫЙ АНАЛИЗ")
        
        print("Введите FEN строки (по одной, пустая строка для завершения):")
        
        fens = []
        while True:
            fen = input("FEN: ").strip()
            if not fen:
                break
            fens.append(fen)
        
        if not fens:
            print("⚠️  Не введено ни одной позиции")
            return
        
        print(f"\n🔬 Анализирую {len(fens)} позиций...")
        
        results = []
        for i, fen in enumerate(fens, 1):
            try:
                board = chess.Board(fen)
                result = self.engine.analyse(board, chess.engine.Limit(time=1.0))
                best_move = result["pv"][0]
                score = result["score"].white()
                
                results.append({
                    "fen": fen,
                    "best_move": str(best_move),
                    "evaluation": str(score)
                })
                
                print(f"✅ Позиция {i}/{len(fens)} проанализирована")
                
            except Exception as e:
                print(f"❌ Ошибка при анализе позиции {i}: {e}")
        
        # Сохранение результатов
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"batch_analysis_{timestamp}.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ Результаты сохранены в batch_analysis_{timestamp}.json")
        input("\nНажмите Enter для продолжения...")
    
    def interactive_game(self):
        """Интерактивная игра с анализом"""
        self.print_header("ИНТЕРАКТИВНАЯ ИГРА")
        
        print("Играйте против Stockfish или анализируйте свои ходы")
        print("Команды:")
        print("  move - сделать ход")
        print("  analyze - проанализировать позицию")
        print("  undo - отменить последний ход")
        print("  reset - начать заново")
        print("  exit - выйти")
        print()
        
        while True:
            print("\nТекущая позиция:")
            print(self.board.unicode(invert_color=True, borders=True))
            print(f"Ход {'белых' if self.board.turn == chess.WHITE else 'чёрных'}")
            
            command = input("\nКоманда: ").strip().lower()
            
            if command == "exit":
                break
                
            elif command == "move":
                move_input = input("Введите ход: ").strip()
                try:
                    move = self.board.parse_san(move_input)
                    self.board.push(move)
                    print(f"✅ Ход {move_input} сделан")
                except:
                    print(f"❌ Неверный ход: {move_input}")
                    
            elif command == "analyze":
                self.analyze_position()
                
            elif command == "undo":
                if len(self.board.move_stack) > 0:
                    self.board.pop()
                    print("✅ Ход отменён")
                else:
                    print("⚠️  Нет ходов для отмены")
                    
            elif command == "reset":
                self.board = chess.Board()
                print("✅ Игра сброшена")
                
            else:
                print("❌ Неизвестная команда")
    
    def main_menu(self):
        """Главное меню программы"""
        while True:
            self.clear_screen()
            print("=" * 70)
            print("🎯 ГЛАВНОЕ МЕНЮ - ПРОДВИНУТЫЙ ШАХМАТНЫЙ АНАЛИЗАТОР")
            print("=" * 70)
            print()
            print("Выберите режим работы:")
            print("1. 🔍 Быстрый анализ текущей позиции")
            print("2. ⚙️  Настроить параметры анализа")
            print("3. 📁 Загрузить новую позицию")
            print("4. 📊 Пакетный анализ нескольких позиций")
            print("5. 🎮 Интерактивная игра с анализом")
            print("6. 📈 Детальная статистика позиции")
            print("7. 💾 Сохранить текущую позицию")
            print("8. 🏆 Сравнение двух ходов")
            print("9. 🚪 Выход")
            print()
            
            choice = input("Ваш выбор (1-9): ").strip()
            
            if choice == "1":
                if self.board:
                    self.analyze_position()
                else:
                    print("⚠️  Сначала загрузите позицию (пункт 3)")
                    input("Нажмите Enter для продолжения...")
                    
            elif choice == "2":
                self.configure_analysis()
                
            elif choice == "3":
                self.load_position()
                
            elif choice == "4":
                self.batch_analysis()
                
            elif choice == "5":
                self.interactive_game()
                
            elif choice == "6":
                if self.board:
                    result = self.engine.analyse(self.board, chess.engine.Limit(time=1.0))
                    self.show_detailed_stats(result[0])
                else:
                    print("⚠️  Сначала загрузите позицию")
                    input("Нажмите Enter для продолжения...")
                    
            elif choice == "7":
                if self.board:
                    fen = self.board.fen()
                    print(f"\nFEN позиции: {fen}")
                    with open("saved_position.fen", "w") as f:
                        f.write(fen)
                    print("✅ Позиция сохранена в saved_position.fen")
                    input("\nНажмите Enter для продолжения...")
                else:
                    print("⚠️  Нет позиции для сохранения")
                    input("Нажмите Enter для продолжения...")
                    
            elif choice == "8":
                self.compare_moves()
                
            elif choice == "9":
                break
                
            else:
                print("❌ Неверный выбор")
                input("Нажмите Enter для продолжения...")
    
    def compare_moves(self):
        """Сравнение двух ходов"""
        self.print_header("СРАВНЕНИЕ ХОДОВ")
        
        if not self.board:
            print("⚠️  Сначала загрузите позицию")
            input("Нажмите Enter для продолжения...")
            return
        
        print("Текущая позиция:")
        print(self.board.unicode(invert_color=True, borders=True))
        print()
        
        print("Введите два хода для сравнения:")
        move1_input = input("Ход 1: ").strip()
        move2_input = input("Ход 2: ").strip()
        
        try:
            move1 = self.board.parse_san(move1_input)
            move2 = self.board.parse_san(move2_input)
            
            # Анализ после первого хода
            board1 = self.board.copy()
            board1.push(move1)
            result1 = self.engine.analyse(board1, chess.engine.Limit(time=1.0))
            score1 = result1[0]["score"].white()
            
            # Анализ после второго хода
            board2 = self.board.copy()
            board2.push(move2)
            result2 = self.engine.analyse(board2, chess.engine.Limit(time=1.0))
            score2 = result2[0]["score"].white()
            
            print("\n📊 РЕЗУЛЬТАТЫ СРАВНЕНИЯ:")
            print("-" * 40)
            
            def format_score(score):
                if score.is_mate():
                    return f"Мат в {abs(score.mate())}"
                else:
                    return f"{score.score()/100.0:+.2f}"
            
            print(f"Ход {move1_input}: {format_score(score1)}")
            print(f"Ход {move2_input}: {format_score(score2)}")
            print()
            
            if score1.is_mate() and score2.is_mate():
                if score1.mate() > 0 and score2.mate() > 0:
                    if score1.mate() < score2.mate():
                        print(f"✅ {move1_input} быстрее ведёт к мату!")
                    else:
                        print(f"✅ {move2_input} быстрее ведёт к мату!")
                elif score1.mate() > 0:
                    print(f"✅ {move1_input} ведёт к мату, а {move2_input} - нет!")
                elif score2.mate() > 0:
                    print(f"✅ {move2_input} ведёт к мату, а {move1_input} - нет!")
                else:
                    if score1.mate() > score2.mate():
                        print(f"✅ {move1_input} отдаляет мат дальше!")
                    else:
                        print(f"✅ {move2_input} отдаляет мат дальше!")
            elif not score1.is_mate() and not score2.is_mate():
                eval1 = score1.score()/100.0
                eval2 = score2.score()/100.0
                diff = eval1 - eval2
                
                if abs(diff) < 0.1:
                    print("🤝 Ходы примерно равны по силе")
                elif diff > 0:
                    print(f"✅ {move1_input} лучше на {diff:.2f} пешки")
                else:
                    print(f"✅ {move2_input} лучше на {-diff:.2f} пешки")
            
            print("-" * 40)
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        input("\nНажмите Enter для продолжения...")
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self.engine:
            try:
                self.engine.quit()
                print("✅ Движок закрыт")
            except:
                pass
    
    def run(self):
        """Основной метод запуска"""
        try:
            # Загрузка движка
            if not self.load_stockfish():
                input("\nНажмите Enter для выхода...")
                return
            
            # Загрузка позиции
            if not self.load_position():
                input("\nНажмите Enter для выхода...")
                return
            
            # Настройка анализа
            self.configure_analysis()
            
            # Главное меню
            self.main_menu()
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Программа прервана пользователем")
        except Exception as e:
            print(f"\n❌ Критическая ошибка: {e}")
        finally:
            self.cleanup()
            print("\n👋 Программа завершена")

# ============================================
# ЗАПУСК ПРОГРАММЫ
# ============================================

if __name__ == "__main__":
    analyzer = ChessAnalyzer()
    analyzer.run()