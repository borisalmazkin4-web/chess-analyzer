#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ШАХМАТНЫЙ АНАЛИЗАТОР - МОДУЛЬ ДВИЖКА
Обработка шахматной логики, анализа и изображений
"""

import chess
import chess.engine
import chess.svg
import chess.pgn
from io import BytesIO
import os
import tempfile
import json
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChessEngine:
    """Класс для работы с шахматным движком Stockfish"""
    
    def __init__(self, engine_path: str = "stockfish.exe"):
        """
        Инициализация шахматного движка
        
        Args:
            engine_path: Путь к исполняемому файлу Stockfish
        """
        self.engine_path = engine_path
        self.engine = None
        self.is_engine_loaded = False
        
        # Настройки по умолчанию
        self.default_settings = {
            'analysis_time': 2.0,      # Время анализа в секундах
            'skill_level': 20,         # Уровень сложности (0-20)
            'multipv': 3,              # Количество вариантов
            'threads': 2,              # Количество потоков
            'hash_size': 256,          # Размер хэша в MB
            'show_arrows': True,       # Показывать стрелки на доске
            'show_evaluation_bar': True, # Показывать шкалу оценки
        }
        
        # Загружаем движок
        self.load_engine()
    
    def load_engine(self) -> bool:
        """
        Загрузка шахматного движка Stockfish
        
        Returns:
            bool: True если движок успешно загружен, False в противном случае
        """
        try:
            if not os.path.exists(self.engine_path):
                logger.error(f"Файл Stockfish не найден: {self.engine_path}")
                # Пробуем найти в других местах
                possible_paths = [
                    "./stockfish",
                    "./stockfish.exe",
                    "/usr/local/bin/stockfish",
                    "/usr/bin/stockfish",
                    "/usr/games/stockfish",
                    "C:\\stockfish\\stockfish.exe",
                    "D:\\stockfish\\stockfish.exe",
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        self.engine_path = path
                        logger.info(f"Найден Stockfish по пути: {path}")
                        break
                else:
                    logger.error("Stockfish не найден ни по одному из путей")
                    return False
            
            # Проверяем права доступа
            if not os.access(self.engine_path, os.X_OK):
                logger.error(f"Нет прав на выполнение файла: {self.engine_path}")
                # Пытаемся дать права (для Linux/Mac)
                if os.name != 'nt':  # Не Windows
                    os.chmod(self.engine_path, 0o755)
            
            # Запускаем движок
            logger.info(f"Запускаю Stockfish: {self.engine_path}")
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            
            # Получаем информацию о движке
            engine_info = self.engine.id
            logger.info(f"Движок загружен: {engine_info['name']} от {engine_info['author']}")
            
            # Настраиваем параметры по умолчанию
            self.configure_engine(self.default_settings)
            
            self.is_engine_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Ошибка загрузки Stockfish: {e}")
            self.is_engine_loaded = False
            return False
    
    def configure_engine(self, settings: Dict) -> None:
        """
        Настройка параметров движка
        
        Args:
            settings: Словарь с настройками
        """
        if not self.is_engine_loaded:
            return
        
        try:
            # Устанавливаем параметры
            config = {}
            
            if 'skill_level' in settings:
                config['Skill Level'] = max(0, min(settings['skill_level'], 20))
            
            if 'threads' in settings:
                config['Threads'] = max(1, min(settings['threads'], 128))
            
            if 'hash_size' in settings:
                config['Hash'] = max(1, min(settings['hash_size'], 1048576))  # до 1 TB
            
            # Применяем конфигурацию
            if config:
                self.engine.configure(config)
                logger.info(f"Движок сконфигурирован: {config}")
                
        except Exception as e:
            logger.error(f"Ошибка конфигурации движка: {e}")
    
    def analyze_position(self, board: chess.Board, 
                        analysis_time: float = None,
                        multipv: int = None,
                        skill_level: int = None) -> Optional[List[Dict]]:
        """
        Анализ шахматной позиции
        
        Args:
            board: Шахматная доска для анализа
            analysis_time: Время анализа в секундах
            multipv: Количество вариантов для анализа
            skill_level: Уровень сложности (0-20)
        
        Returns:
            List[Dict] или None: Результаты анализа или None при ошибке
        """
        if not self.is_engine_loaded:
            logger.error("Движок не загружен")
            return None
        
        # Используем настройки по умолчанию, если не указаны
        if analysis_time is None:
            analysis_time = self.default_settings['analysis_time']
        if multipv is None:
            multipv = self.default_settings['multipv']
        if skill_level is None:
            skill_level = self.default_settings['skill_level']
        
        try:
            # Настраиваем уровень сложности
            if skill_level != self.default_settings['skill_level']:
                self.engine.configure({"Skill Level": skill_level})
            
            # Выполняем анализ
            if multipv > 1:
                result = self.engine.analyse(
                    board,
                    chess.engine.Limit(time=analysis_time),
                    multipv=multipv
                )
                # multipv возвращает список результатов
                analysis_results = result
            else:
                result = self.engine.analyse(
                    board,
                    chess.engine.Limit(time=analysis_time)
                )
                # Одиночный анализ возвращает один результат
                analysis_results = [result]
            
            # Форматируем результаты
            formatted_results = []
            for i, res in enumerate(analysis_results):
                formatted_result = {
                    'rank': i + 1,
                    'best_move': res['pv'][0] if res['pv'] else None,
                    'score': res['score'],
                    'depth': res.get('depth', 0),
                    'nodes': res.get('nodes', 0),
                    'time': res.get('time', analysis_time),
                    'pv': res.get('pv', []),
                    'score_formatted': self.format_score(res['score']),
                    'variation': self.get_variation(board, res['pv']) if res['pv'] else []
                }
                formatted_results.append(formatted_result)
            
            logger.info(f"Анализ завершён: {len(formatted_results)} вариантов, время {analysis_time}с")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Ошибка анализа позиции: {e}")
            return None
    
    def format_score(self, score: chess.engine.PovScore) -> str:
        """
        Форматирование оценки позиции
        
        Args:
            score: Оценка от движка
        
        Returns:
            str: Отформатированная оценка
        """
        white_score = score.white()
        
        if white_score.is_mate():
            mate_in = white_score.mate()
            if mate_in > 0:
                return f"Мат белым в {mate_in}"
            else:
                return f"Мат чёрным в {abs(mate_in)}"
        else:
            eval_score = white_score.score() / 100.0
            return f"{eval_score:+.2f}"
    
    def get_variation(self, board: chess.Board, pv: List[chess.Move], max_moves: int = 6) -> List[str]:
        """
        Получение варианта продолжения
        
        Args:
            board: Исходная доска
            pv: Вариант продолжения (list ходов)
            max_moves: Максимальное количество ходов для показа
        
        Returns:
            List[str]: Список ходов в SAN нотации
        """
        variation = []
        temp_board = board.copy()
        
        for i, move in enumerate(pv[:max_moves]):
            try:
                san_move = temp_board.san(move)
                variation.append(san_move)
                temp_board.push(move)
            except:
                # Если не удалось конвертировать в SAN, используем UCI
                variation.append(str(move))
                try:
                    temp_board.push(move)
                except:
                    break
        
        return variation
    
    def get_evaluation_description(self, score: chess.engine.PovScore) -> str:
        """
        Получение текстового описания оценки
        
        Args:
            score: Оценка позиции
        
        Returns:
            str: Текстовое описание
        """
        white_score = score.white()
        
        if white_score.is_mate():
            mate_in = white_score.mate()
            if mate_in > 0:
                return "⚡ Решающее преимущество белых!"
            else:
                return "⚡ Решающее преимущество чёрных!"
        
        eval_score = white_score.score() / 100.0
        
        if eval_score > 3.0:
            return "🏆 Решающее преимущество белых"
        elif eval_score > 1.0:
            return "⭐ Большое преимущество белых"
        elif eval_score > 0.5:
            return "↑ Преимущество белых"
        elif eval_score > 0.2:
            return "↗ Небольшое преимущество белых"
        elif eval_score > -0.2:
            return "↔ Равная позиция"
        elif eval_score > -0.5:
            return "↘ Небольшое преимущество чёрных"
        elif eval_score > -1.0:
            return "↓ Преимущество чёрных"
        elif eval_score > -3.0:
            return "⭐ Большое преимущество чёрных"
        else:
            return "🏆 Решающее преимущество чёрных"
    
    def generate_board_image(self, board: chess.Board, 
                           highlight_move: chess.Move = None,
                           last_move: chess.Move = None,
                           orientation: bool = True) -> Optional[BytesIO]:
        """
        Генерация изображения шахматной доски
        
        Args:
            board: Шахматная доска
            highlight_move: Ход для подсветки
            last_move: Последний сделанный ход
            orientation: Ориентация доски (True - белые снизу)
        
        Returns:
            BytesIO или None: Изображение в формате BytesIO
        """
        try:
            # Создаём SVG доски
            arrows = []
            squares = {}
            
            # Добавляем подсветку для рекомендуемого хода
            if highlight_move:
                arrows.append((highlight_move.from_square, highlight_move.to_square))
            
            # Подсвечиваем последний ход
            if last_move:
                squares[last_move.from_square] = "#ffec8b"  # Светло-жёлтый
                squares[last_move.to_square] = "#ffec8b"
            
            # Генерируем SVG
            svg_content = chess.svg.board(
                board=board,
                arrows=arrows,
                squares=squares,
                orientation=chess.WHITE if orientation else chess.BLACK,
                size=400
            )
            
            # Конвертируем SVG в PNG (используем cairosvg если установлен)
            try:
                import cairosvg
                png_data = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'))
                return BytesIO(png_data)
                
            except ImportError:
                # Если cairosvg не установлен, возвращаем SVG
                logger.warning("cairosvg не установлен, возвращаю SVG")
                return BytesIO(svg_content.encode('utf-8'))
                
        except Exception as e:
            logger.error(f"Ошибка генерации изображения: {e}")
            return None
    
    def save_analysis_to_file(self, board: chess.Board, 
                            analysis_results: List[Dict],
                            filename: str = None) -> str:
        """
        Сохранение анализа в файл
        
        Args:
            board: Анализируемая доска
            analysis_results: Результаты анализа
            filename: Имя файла (если None - генерируется автоматически)
        
        Returns:
            str: Путь к сохранённому файлу
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chess_analysis_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # Заголовок
                f.write("=" * 60 + "\n")
                f.write("АНАЛИЗ ШАХМАТНОЙ ПОЗИЦИИ\n")
                f.write("=" * 60 + "\n\n")
                
                # Информация о позиции
                f.write(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"FEN: {board.fen()}\n\n")
                
                # Лучший ход
                if analysis_results:
                    best_result = analysis_results[0]
                    best_move = best_result['best_move']
                    if best_move:
                        f.write(f"ЛУЧШИЙ ХОД: {board.san(best_move)}\n")
                        f.write(f"ОЦЕНКА: {best_result['score_formatted']}\n")
                        f.write(f"ОПИСАНИЕ: {self.get_evaluation_description(best_result['score'])}\n\n")
                
                # Все варианты
                f.write("ВАРИАНТЫ ПРОДОЛЖЕНИЯ:\n")
                f.write("-" * 60 + "\n")
                
                for result in analysis_results:
                    move = result['best_move']
                    if move:
                        f.write(f"\n{result['rank']}. {board.san(move):8} | {result['score_formatted']:12}\n")
                        
                        if result['variation']:
                            variation_text = " → ".join(result['variation'])
                            f.write(f"   Вариант: {variation_text}\n")
                
                # Статистика анализа
                if analysis_results:
                    f.write("\n" + "=" * 60 + "\n")
                    f.write("СТАТИСТИКА АНАЛИЗА:\n")
                    f.write("-" * 60 + "\n")
                    
                    depth = analysis_results[0].get('depth', 0)
                    nodes = analysis_results[0].get('nodes', 0)
                    time = analysis_results[0].get('time', 0)
                    
                    f.write(f"Глубина анализа: {depth}\n")
                    f.write(f"Узлов рассмотрено: {nodes:,}\n")
                    f.write(f"Время анализа: {time:.2f} сек\n")
                    if time > 0:
                        f.write(f"Скорость анализа: {nodes/time/1000:.0f} тыс.узлов/сек\n")
                    
                    f.write(f"Количество вариантов: {len(analysis_results)}\n")
                
                # Доска в текстовом виде
                f.write("\n" + "=" * 60 + "\n")
                f.write("ПОЗИЦИЯ НА ДОСКЕ:\n")
                f.write("-" * 60 + "\n")
                f.write(self.board_to_text(board) + "\n")
            
            logger.info(f"Анализ сохранён в файл: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Ошибка сохранения анализа: {e}")
            return None
    
    def board_to_text(self, board: chess.Board) -> str:
        """
        Конвертация доски в текстовое представление
        
        Args:
            board: Шахматная доска
        
        Returns:
            str: Текстовое представление доски
        """
        piece_symbols = {
            'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
            'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙',
            None: '·'
        }
        
        result = []
        result.append("    a b c d e f g h")
        result.append("  +-----------------+")
        
        for i in range(7, -1, -1):
            row = []
            for j in range(8):
                piece = board.piece_at(chess.square(j, i))
                row.append(piece_symbols.get(piece, '·'))
            result.append(f"{i+1} | {' '.join(row)} | {i+1}")
        
        result.append("  +-----------------+")
        result.append("    a b c d e f g h")
        
        return "\n".join(result)
    
    def get_game_status(self, board: chess.Board) -> Dict:
        """
        Получение статуса игры
        
        Args:
            board: Шахматная доска
        
        Returns:
            Dict: Информация о статусе игры
        """
        status = {
            'is_checkmate': board.is_checkmate(),
            'is_stalemate': board.is_stalemate(),
            'is_insufficient_material': board.is_insufficient_material(),
            'is_check': board.is_check(),
            'is_game_over': board.is_game_over(),
            'turn': 'white' if board.turn == chess.WHITE else 'black',
            'fullmove_number': board.fullmove_number,
            'halfmove_clock': board.halfmove_clock,
            'legal_moves_count': board.legal_moves.count(),
            'material_balance': self.calculate_material_balance(board)
        }
        
        # Определяем текст статуса
        if status['is_checkmate']:
            status['status_text'] = "ШАХ И МАТ!"
        elif status['is_stalemate']:
            status['status_text'] = "ПАТ"
        elif status['is_insufficient_material']:
            status['status_text'] = "НЕДОСТАТОК МАТЕРИАЛА"
        elif status['is_check']:
            status['status_text'] = "ШАХ"
        else:
            status['status_text'] = "ИГРА ИДЁТ"
        
        return status
    
    def calculate_material_balance(self, board: chess.Board) -> str:
        """
        Расчёт материального баланса
        
        Args:
            board: Шахматная доска
        
        Returns:
            str: Строка с материальным балансом
        """
        piece_values = {
            'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0,
            'p': -1, 'n': -3, 'b': -3, 'r': -5, 'q': -9, 'k': 0
        }
        
        total = 0
        board_fen = board.board_fen()
        
        for char in board_fen:
            if char in piece_values:
                total += piece_values[char]
        
        return f"{'+' if total > 0 else ''}{total:.1f}"
    
    def cleanup(self) -> None:
        """Очистка ресурсов движка"""
        if self.engine:
            try:
                self.engine.quit()
                logger.info("Движок остановлен")
            except Exception as e:
                logger.error(f"Ошибка остановки движка: {e}")
            finally:
                self.engine = None
                self.is_engine_loaded = False

# Создаём глобальный экземпляр движка
# Его можно импортировать в других модулях
chess_engine = ChessEngine()

# Функция для получения экземпляра движка
def get_engine() -> ChessEngine:
    """Получение экземпляра шахматного движка"""
    return chess_engine

# Тестирование модуля
if __name__ == "__main__":
    print("Тестирование модуля шахматного движка...")
    
    # Создаём движок
    engine = ChessEngine()
    
    if engine.is_engine_loaded:
        print("✅ Движок успешно загружен")
        
        # Тестовая позиция
        board = chess.Board()
        
        # Анализ начальной позиции
        print("🔍 Анализирую начальную позицию...")
        results = engine.analyze_position(board, analysis_time=1.0)
        
        if results:
            print(f"✅ Получено {len(results)} вариантов")
            
            # Показываем лучший ход
            best_result = results[0]
            best_move = best_result['best_move']
            
            if best_move:
                print(f"🎯 Лучший ход: {board.san(best_move)}")
                print(f"📊 Оценка: {best_result['score_formatted']}")
                print(f"📝 Описание: {engine.get_evaluation_description(best_result['score'])}")
            
            # Генерация изображения
            print("🎨 Генерирую изображение доски...")
            image_data = engine.generate_board_image(board, highlight_move=best_move)
            
            if image_data:
                # Сохраняем изображение для проверки
                with open("test_board.png", "wb") as f:
                    f.write(image_data.getvalue())
                print("✅ Изображение сохранено как test_board.png")
        
        # Очистка
        engine.cleanup()
    else:
        print("❌ Не удалось загрузить движок")
    
    print("Тестирование завершено.")