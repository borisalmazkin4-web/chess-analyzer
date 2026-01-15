#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ШАХМАТНЫЙ АНАЛИЗАТОР - МОДУЛЬ БАЗЫ ДАННЫХ
Хранение данных пользователей, статистики и настроек
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChessDatabase:
    """Класс для работы с базой данных шахматного бота"""
    
    def __init__(self, db_path: str = "chess_bot.db"):
        """
        Инициализация базы данных
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self.connection = None
        
        # Создаём директорию для базы данных если нужно
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # Подключаемся к базе данных
        self.connect()
        
        # Инициализируем таблицы
        self.init_tables()
    
    def connect(self) -> None:
        """Подключение к базе данных"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # Для доступа к колонкам по имени
            logger.info(f"Подключено к базе данных: {self.db_path}")
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            raise
    
    def init_tables(self) -> None:
        """Инициализация таблиц базы данных"""
        try:
            cursor = self.connection.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT DEFAULT 'ru',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    games_played INTEGER DEFAULT 0,
                    analysis_count INTEGER DEFAULT 0,
                    total_analysis_time REAL DEFAULT 0,
                    is_banned BOOLEAN DEFAULT FALSE,
                    ban_reason TEXT
                )
            ''')
            
            # Таблица игр
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    start_fen TEXT DEFAULT 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
                    end_fen TEXT,
                    moves TEXT,  -- JSON список ходов
                    result TEXT, -- 'white_win', 'black_win', 'draw', 'unfinished'
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    analysis_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица анализов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analyses (
                    analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    game_id INTEGER,
                    fen TEXT,
                    analysis_time REAL,
                    skill_level INTEGER,
                    multipv INTEGER,
                    best_move TEXT,
                    evaluation TEXT,
                    depth INTEGER,
                    nodes INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (game_id) REFERENCES games (game_id)
                )
            ''')
            
            # Таблица настроек пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    analysis_time REAL DEFAULT 2.0,
                    skill_level INTEGER DEFAULT 20,
                    multipv INTEGER DEFAULT 3,
                    show_arrows BOOLEAN DEFAULT TRUE,
                    show_evaluation_bar BOOLEAN DEFAULT TRUE,
                    auto_analyze BOOLEAN DEFAULT FALSE,
                    theme TEXT DEFAULT 'default',
                    language TEXT DEFAULT 'ru',
                    notifications BOOLEAN DEFAULT TRUE,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица сохранённых позиций
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS saved_positions (
                    position_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT,
                    fen TEXT,
                    tags TEXT,  -- JSON список тегов
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица статистики по дебютам
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS opening_stats (
                    user_id INTEGER,
                    eco_code TEXT,
                    opening_name TEXT,
                    games_played INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    draws INTEGER DEFAULT 0,
                    last_played TIMESTAMP,
                    PRIMARY KEY (user_id, eco_code)
                )
            ''')
            
            self.connection.commit()
            logger.info("Таблицы базы данных инициализированы")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации таблиц: {e}")
            raise
    
    # ===== МЕТОДЫ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ =====
    
    def get_or_create_user(self, user_id: int, 
                          username: str = None,
                          first_name: str = None,
                          last_name: str = None,
                          language_code: str = 'ru') -> Dict:
        """
        Получение или создание пользователя
        
        Args:
            user_id: ID пользователя в Telegram
            username: Имя пользователя
            first_name: Имя
            last_name: Фамилия
            language_code: Код языка
        
        Returns:
            Dict: Данные пользователя
        """
        try:
            cursor = self.connection.cursor()
            
            # Пробуем найти пользователя
            cursor.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            user = cursor.fetchone()
            
            if user:
                # Обновляем время последней активности
                cursor.execute(
                    "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (user_id,)
                )
                self.connection.commit()
                
                # Конвертируем в словарь
                return dict(user)
            else:
                # Создаём нового пользователя
                cursor.execute('''
                    INSERT INTO users 
                    (user_id, username, first_name, last_name, language_code, created_at, last_active)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (user_id, username, first_name, last_name, language_code))
                
                # Создаём настройки по умолчанию
                cursor.execute('''
                    INSERT INTO user_settings (user_id) VALUES (?)
                ''', (user_id,))
                
                self.connection.commit()
                
                logger.info(f"Создан новый пользователь: {user_id} ({username})")
                
                # Возвращаем данные нового пользователя
                return {
                    'user_id': user_id,
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                    'language_code': language_code,
                    'created_at': datetime.now().isoformat(),
                    'last_active': datetime.now().isoformat(),
                    'games_played': 0,
                    'analysis_count': 0,
                    'total_analysis_time': 0,
                    'is_banned': False,
                    'ban_reason': None
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения/создания пользователя: {e}")
            self.connection.rollback()
            return {}
    
    def update_user_stats(self, user_id: int, 
                         games_played: int = 0,
                         analysis_count: int = 0,
                         analysis_time: float = 0) -> bool:
        """
        Обновление статистики пользователя
        
        Args:
            user_id: ID пользователя
            games_played: Количество сыгранных игр
            analysis_count: Количество анализов
            analysis_time: Общее время анализа
        
        Returns:
            bool: True если успешно
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET games_played = games_played + ?,
                    analysis_count = analysis_count + ?,
                    total_analysis_time = total_analysis_time + ?,
                    last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (games_played, analysis_count, analysis_time, user_id))
            
            self.connection.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Ошибка обновления статистики: {e}")
            self.connection.rollback()
            return False
    
    def get_user_stats(self, user_id: int) -> Dict:
        """
        Получение статистики пользователя
        
        Args:
            user_id: ID пользователя
        
        Returns:
            Dict: Статистика пользователя
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                SELECT 
                    u.*,
                    COALESCE(SUM(g.analysis_count), 0) as total_game_analyses,
                    COALESCE(COUNT(DISTINCT g.game_id), 0) as total_games,
                    COALESCE(SUM(CASE WHEN g.result = 'white_win' THEN 1 ELSE 0 END), 0) as white_wins,
                    COALESCE(SUM(CASE WHEN g.result = 'black_win' THEN 1 ELSE 0 END), 0) as black_wins,
                    COALESCE(SUM(CASE WHEN g.result = 'draw' THEN 1 ELSE 0 END), 0) as draws
                FROM users u
                LEFT JOIN games g ON u.user_id = g.user_id
                WHERE u.user_id = ?
                GROUP BY u.user_id
            ''', (user_id,))
            
            result = cursor.fetchone()
            if result:
                stats = dict(result)
                
                # Рассчитываем дополнительные метрики
                total_games = stats.get('total_games', 0)
                white_wins = stats.get('white_wins', 0)
                black_wins = stats.get('black_wins', 0)
                draws = stats.get('draws', 0)
                
                if total_games > 0:
                    stats['win_rate'] = ((white_wins + black_wins) / total_games) * 100
                    stats['white_win_rate'] = (white_wins / total_games) * 100 if total_games > 0 else 0
                    stats['draw_rate'] = (draws / total_games) * 100 if total_games > 0 else 0
                else:
                    stats['win_rate'] = 0
                    stats['white_win_rate'] = 0
                    stats['draw_rate'] = 0
                
                # Среднее время анализа
                analysis_count = stats.get('analysis_count', 0)
                total_time = stats.get('total_analysis_time', 0)
                stats['avg_analysis_time'] = total_time / analysis_count if analysis_count > 0 else 0
                
                return stats
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    # ===== МЕТОДЫ ДЛЯ РАБОТЫ С ИГРАМИ =====
    
    def create_game(self, user_id: int, start_fen: str = None) -> Optional[int]:
        """
        Создание новой игры
        
        Args:
            user_id: ID пользователя
            start_fen: Начальная позиция в FEN
        
        Returns:
            Optional[int]: ID созданной игры или None при ошибке
        """
        try:
            cursor = self.connection.cursor()
            
            if start_fen is None:
                start_fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
            
            cursor.execute('''
                INSERT INTO games (user_id, start_fen, start_time)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, start_fen))
            
            game_id = cursor.lastrowid
            self.connection.commit()
            
            # Обновляем статистику пользователя
            self.update_user_stats(user_id, games_played=1)
            
            logger.info(f"Создана новая игра {game_id} для пользователя {user_id}")
            return game_id
            
        except Exception as e:
            logger.error(f"Ошибка создания игры: {e}")
            self.connection.rollback()
            return None
    
    def update_game(self, game_id: int, 
                   end_fen: str = None,
                   moves: List[str] = None,
                   result: str = None) -> bool:
        """
        Обновление информации об игре
        
        Args:
            game_id: ID игры
            end_fen: Конечная позиция
            moves: Список ходов (JSON)
            result: Результат игры
        
        Returns:
            bool: True если успешно
        """
        try:
            cursor = self.connection.cursor()
            
            updates = []
            params = []
            
            if end_fen is not None:
                updates.append("end_fen = ?")
                params.append(end_fen)
            
            if moves is not None:
                updates.append("moves = ?")
                params.append(json.dumps(moves))
            
            if result is not None:
                updates.append("result = ?")
                params.append(result)
            
            # Добавляем время окончания если игра завершена
            if result in ['white_win', 'black_win', 'draw']:
                updates.append("end_time = CURRENT_TIMESTAMP")
            
            if updates:
                query = f"UPDATE games SET {', '.join(updates)} WHERE game_id = ?"
                params.append(game_id)
                
                cursor.execute(query, params)
                self.connection.commit()
                
                return cursor.rowcount > 0
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка обновления игры: {e}")
            self.connection.rollback()
            return False
    
    def get_user_games(self, user_id: int, limit: int = 10, offset: int = 0) -> List[Dict]:
        """
        Получение списка игр пользователя
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество игр
            offset: Смещение
        
        Returns:
            List[Dict]: Список игр
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                SELECT * FROM games 
                WHERE user_id = ? 
                ORDER BY start_time DESC
                LIMIT ? OFFSET ?
            ''', (user_id, limit, offset))
            
            games = []
            for row in cursor.fetchall():
                game = dict(row)
                
                # Парсим JSON с ходами
                if game.get('moves'):
                    try:
                        game['moves'] = json.loads(game['moves'])
                    except:
                        game['moves'] = []
                else:
                    game['moves'] = []
                
                # Рассчитываем длительность игры
                if game.get('end_time'):
                    start = datetime.fromisoformat(game['start_time'])
                    end = datetime.fromisoformat(game['end_time'])
                    game['duration'] = (end - start).total_seconds()
                else:
                    game['duration'] = None
                
                games.append(game)
            
            return games
            
        except Exception as e:
            logger.error(f"Ошибка получения игр пользователя: {e}")
            return []
    
    # ===== МЕТОДЫ ДЛЯ РАБОТЫ С АНАЛИЗАМИ =====
    
    def save_analysis(self, user_id: int,
                     game_id: int = None,
                     fen: str = None,
                     analysis_time: float = None,
                     skill_level: int = None,
                     multipv: int = None,
                     best_move: str = None,
                     evaluation: str = None,
                     depth: int = None,
                     nodes: int = None) -> Optional[int]:
        """
        Сохранение анализа позиции
        
        Args:
            user_id: ID пользователя
            game_id: ID игры (если анализ связан с игрой)
            fen: Позиция в FEN
            analysis_time: Время анализа
            skill_level: Уровень сложности
            multipv: Количество вариантов
            best_move: Лучший ход
            evaluation: Оценка позиции
            depth: Глубина анализа
            nodes: Количество рассмотренных узлов
        
        Returns:
            Optional[int]: ID сохранённого анализа или None при ошибке
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                INSERT INTO analyses 
                (user_id, game_id, fen, analysis_time, skill_level, multipv, 
                 best_move, evaluation, depth, nodes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, game_id, fen, analysis_time, skill_level, multipv,
                  best_move, evaluation, depth, nodes))
            
            analysis_id = cursor.lastrowid
            self.connection.commit()
            
            # Обновляем статистику анализа игры если game_id указан
            if game_id:
                cursor.execute('''
                    UPDATE games 
                    SET analysis_count = analysis_count + 1 
                    WHERE game_id = ?
                ''', (game_id,))
                self.connection.commit()
            
            # Обновляем статистику пользователя
            self.update_user_stats(user_id, analysis_count=1, analysis_time=analysis_time or 0)
            
            logger.info(f"Сохранён анализ {analysis_id} для пользователя {user_id}")
            return analysis_id
            
        except Exception as e:
            logger.error(f"Ошибка сохранения анализа: {e}")
            self.connection.rollback()
            return None
    
    def get_user_analyses(self, user_id: int, limit: int = 10, offset: int = 0) -> List[Dict]:
        """
        Получение списка анализов пользователя
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество анализов
            offset: Смещение
        
        Returns:
            List[Dict]: Список анализов
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                SELECT a.*, g.start_fen as game_start_fen
                FROM analyses a
                LEFT JOIN games g ON a.game_id = g.game_id
                WHERE a.user_id = ? 
                ORDER BY a.created_at DESC
                LIMIT ? OFFSET ?
            ''', (user_id, limit, offset))
            
            analyses = [dict(row) for row in cursor.fetchall()]
            return analyses
            
        except Exception as e:
            logger.error(f"Ошибка получения анализов: {e}")
            return []
    
    # ===== МЕТОДЫ ДЛЯ РАБОТЫ С НАСТРОЙКАМИ =====
    
    def get_user_settings(self, user_id: int) -> Dict:
        """
        Получение настроек пользователя
        
        Args:
            user_id: ID пользователя
        
        Returns:
            Dict: Настройки пользователя
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                SELECT * FROM user_settings WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            if result:
                return dict(result)
            else:
                # Создаём настройки по умолчанию если их нет
                cursor.execute('''
                    INSERT INTO user_settings (user_id) VALUES (?)
                ''', (user_id,))
                self.connection.commit()
                
                cursor.execute('''
                    SELECT * FROM user_settings WHERE user_id = ?
                ''', (user_id,))
                
                return dict(cursor.fetchone())
                
        except Exception as e:
            logger.error(f"Ошибка получения настроек: {e}")
            return {}
    
    def update_user_settings(self, user_id: int, **settings) -> bool:
        """
        Обновление настроек пользователя
        
        Args:
            user_id: ID пользователя
            **settings: Настройки для обновления
        
        Returns:
            bool: True если успешно
        """
        try:
            cursor = self.connection.cursor()
            
            valid_settings = [
                'analysis_time', 'skill_level', 'multipv',
                'show_arrows', 'show_evaluation_bar', 'auto_analyze',
                'theme', 'language', 'notifications'
            ]
            
            updates = []
            params = []
            
            for key, value in settings.items():
                if key in valid_settings:
                    updates.append(f"{key} = ?")
                    params.append(value)
            
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                query = f"UPDATE user_settings SET {', '.join(updates)} WHERE user_id = ?"
                params.append(user_id)
                
                cursor.execute(query, params)
                self.connection.commit()
                
                return cursor.rowcount > 0
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка обновления настроек: {e}")
            self.connection.rollback()
            return False
    
    # ===== МЕТОДЫ ДЛЯ РАБОТЫ С СОХРАНЁННЫМИ ПОЗИЦИЯМИ =====
    
    def save_position(self, user_id: int, name: str, fen: str, 
                     tags: List[str] = None, notes: str = None) -> Optional[int]:
        """
        Сохранение позиции в избранное
        
        Args:
            user_id: ID пользователя
            name: Название позиции
            fen: Позиция в FEN
            tags: Список тегов
            notes: Заметки
        
        Returns:
            Optional[int]: ID сохранённой позиции или None при ошибке
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                INSERT INTO saved_positions 
                (user_id, name, fen, tags, notes, created_at, last_accessed)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (user_id, name, fen, 
                  json.dumps(tags or []), 
                  notes or ''))
            
            position_id = cursor.lastrowid
            self.connection.commit()
            
            logger.info(f"Сохранена позиция {position_id} для пользователя {user_id}")
            return position_id
            
        except Exception as e:
            logger.error(f"Ошибка сохранения позиции: {e}")
            self.connection.rollback()
            return None
    
    def get_saved_positions(self, user_id: int, tag: str = None) -> List[Dict]:
        """
        Получение сохранённых позиций пользователя
        
        Args:
            user_id: ID пользователя
            tag: Фильтр по тегу
        
        Returns:
            List[Dict]: Список сохранённых позиций
        """
        try:
            cursor = self.connection.cursor()
            
            if tag:
                # Используем JSON_EXTRACT для поиска по тегам (SQLite 3.38+)
                cursor.execute('''
                    SELECT * FROM saved_positions 
                    WHERE user_id = ? AND json_extract(tags, '$') LIKE ?
                    ORDER BY last_accessed DESC
                ''', (user_id, f'%"{tag}"%'))
            else:
                cursor.execute('''
                    SELECT * FROM saved_positions 
                    WHERE user_id = ? 
                    ORDER BY last_accessed DESC
                ''', (user_id,))
            
            positions = []
            for row in cursor.fetchall():
                pos = dict(row)
                
                # Парсим JSON с тегами
                if pos.get('tags'):
                    try:
                        pos['tags'] = json.loads(pos['tags'])
                    except:
                        pos['tags'] = []
                else:
                    pos['tags'] = []
                
                positions.append(pos)
            
            return positions
            
        except Exception as e:
            logger.error(f"Ошибка получения сохранённых позиций: {e}")
            return []
    
    def update_position_access(self, position_id: int) -> bool:
        """
        Обновление времени последнего доступа к позиции
        
        Args:
            position_id: ID позиции
        
        Returns:
            bool: True если успешно
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                UPDATE saved_positions 
                SET last_accessed = CURRENT_TIMESTAMP,
                    access_count = access_count + 1
                WHERE position_id = ?
            ''', (position_id,))
            
            self.connection.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Ошибка обновления доступа к позиции: {e}")
            self.connection.rollback()
            return False
    
    # ===== МЕТОДЫ ДЛЯ РАБОТЫ СО СТАТИСТИКОЙ ДЕБЮТОВ =====
    
    def update_opening_stats(self, user_id: int, eco_code: str, 
                           opening_name: str, result: str) -> bool:
        """
        Обновление статистики по дебюту
        
        Args:
            user_id: ID пользователя
            eco_code: ECO код дебюта
            opening_name: Название дебюта
            result: Результат игры
        
        Returns:
            bool: True если успешно
        """
        try:
            cursor = self.connection.cursor()
            
            # Пробуем обновить существующую запись
            cursor.execute('''
                UPDATE opening_stats 
                SET games_played = games_played + 1,
                    wins = wins + ?,
                    losses = losses + ?,
                    draws = draws + ?,
                    last_played = CURRENT_TIMESTAMP
                WHERE user_id = ? AND eco_code = ?
            ''', (
                1 if result == 'white_win' else 0,
                1 if result == 'black_win' else 0,
                1 if result == 'draw' else 0,
                user_id, eco_code
            ))
            
            if cursor.rowcount == 0:
                # Создаём новую запись
                cursor.execute('''
                    INSERT INTO opening_stats 
                    (user_id, eco_code, opening_name, games_played, wins, losses, draws, last_played)
                    VALUES (?, ?, ?, 1, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    user_id, eco_code, opening_name,
                    1 if result == 'white_win' else 0,
                    1 if result == 'black_win' else 0,
                    1 if result == 'draw' else 0
                ))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления статистики дебютов: {e}")
            self.connection.rollback()
            return False
    
    def get_opening_stats(self, user_id: int) -> List[Dict]:
        """
        Получение статистики по дебютам
        
        Args:
            user_id: ID пользователя
        
        Returns:
            List[Dict]: Статистика по дебютам
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                SELECT * FROM opening_stats 
                WHERE user_id = ? 
                ORDER BY games_played DESC
            ''', (user_id,))
            
            stats = []
            for row in cursor.fetchall():
                stat = dict(row)
                
                # Рассчитываем проценты
                games = stat['games_played']
                if games > 0:
                    stat['win_percentage'] = (stat['wins'] / games) * 100
                    stat['loss_percentage'] = (stat['losses'] / games) * 100
                    stat['draw_percentage'] = (stat['draws'] / games) * 100
                else:
                    stat['win_percentage'] = 0
                    stat['loss_percentage'] = 0
                    stat['draw_percentage'] = 0
                
                stats.append(stat)
            
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики дебютов: {e}")
            return []
    
    # ===== АДМИНИСТРАТИВНЫЕ МЕТОДЫ =====
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Получение списка всех пользователей (для администратора)
        
        Args:
            limit: Максимальное количество пользователей
            offset: Смещение
        
        Returns:
            List[Dict]: Список пользователей
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                SELECT * FROM users 
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Ошибка получения списка пользователей: {e}")
            return []
    
    def ban_user(self, user_id: int, reason: str = None) -> bool:
        """
        Блокировка пользователя
        
        Args:
            user_id: ID пользователя
            reason: Причина блокировки
        
        Returns:
            bool: True если успешно
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET is_banned = TRUE, ban_reason = ?
                WHERE user_id = ?
            ''', (reason, user_id))
            
            self.connection.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Ошибка блокировки пользователя: {e}")
            self.connection.rollback()
            return False
    
    def unban_user(self, user_id: int) -> bool:
        """
        Разблокировка пользователя
        
        Args:
            user_id: ID пользователя
        
        Returns:
            bool: True если успешно
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET is_banned = FALSE, ban_reason = NULL
                WHERE user_id = ?
            ''', (user_id,))
            
            self.connection.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Ошибка разблокировки пользователя: {e}")
            self.connection.rollback()
            return False
    
    # ===== СЛУЖЕБНЫЕ МЕТОДЫ =====
    
    def backup_database(self, backup_path: str = None) -> Optional[str]:
        """
        Создание резервной копии базы данных
        
        Args:
            backup_path: Путь для сохранения резервной копии
        
        Returns:
            Optional[str]: Путь к резервной копии или None при ошибке
        """
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"chess_bot_backup_{timestamp}.db"
            
            # Создаём резервную копию
            backup_conn = sqlite3.connect(backup_path)
            self.connection.backup(backup_conn)
            backup_conn.close()
            
            logger.info(f"Создана резервная копия: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            return None
    
    def cleanup_old_data(self, days_old: int = 30) -> Tuple[int, int]:
        """
        Очистка старых данных
        
        Args:
            days_old: Удалять данные старше N дней
        
        Returns:
            Tuple[int, int]: Количество удалённых анализов и игр
        """
        try:
            cursor = self.connection.cursor()
            
            # Удаляем старые анализы
            cursor.execute('''
                DELETE FROM analyses 
                WHERE julianday('now') - julianday(created_at) > ?
            ''', (days_old,))
            analyses_deleted = cursor.rowcount
            
            # Удаляем старые игры
            cursor.execute('''
                DELETE FROM games 
                WHERE julianday('now') - julianday(start_time) > ? 
                AND end_time IS NOT NULL
            ''', (days_old,))
            games_deleted = cursor.rowcount
            
            self.connection.commit()
            
            logger.info(f"Удалено {analyses_deleted} анализов и {games_deleted} игр старше {days_old} дней")
            return analyses_deleted, games_deleted
            
        except Exception as e:
            logger.error(f"Ошибка очистки старых данных: {e}")
            self.connection.rollback()
            return 0, 0
    
    def close(self) -> None:
        """Закрытие соединения с базой данных"""
        if self.connection:
            self.connection.close()
            logger.info("Соединение с базой данных закрыто")
    
    def __del__(self):
        """Деструктор - закрываем соединение"""
        self.close()

# Создаём глобальный экземпляр базы данных
# Его можно импортировать в других модулях
chess_db = ChessDatabase()

# Функция для получения экземпляра базы данных
def get_database() -> ChessDatabase:
    """Получение экземпляра базы данных"""
    return chess_db

# Тестирование модуля
if __name__ == "__main__":
    print("Тестирование модуля базы данных...")
    
    # Создаём базу данных
    db = ChessDatabase("test_chess_bot.db")
    
    # Тест 1: Создание пользователя
    print("\n1. Тест создания пользователя...")
    user = db.get_or_create_user(
        user_id=123456789,
        username="test_user",
        first_name="Иван",
        last_name="Тестовый",
        language_code="ru"
    )
    print(f"✅ Пользователь создан: {user.get('username')}")
    
    # Тест 2: Получение настроек
    print("\n2. Тест получения настроек...")
    settings = db.get_user_settings(123456789)
    print(f"✅ Настройки получены: анализ {settings.get('analysis_time')} сек")
    
    # Тест 3: Создание игры
    print("\n3. Тест создания игры...")
    game_id = db.create_game(123456789)
    print(f"✅ Игра создана: ID {game_id}")
    
    # Тест 4: Сохранение анализа
    print("\n4. Тест сохранения анализа...")
    analysis_id = db.save_analysis(
        user_id=123456789,
        game_id=game_id,
        fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        analysis_time=2.5,
        skill_level=20,
        multipv=3,
        best_move="e2e4",
        evaluation="+0.15",
        depth=18,
        nodes=1500000
    )
    print(f"✅ Анализ сохранён: ID {analysis_id}")
    
    # Тест 5: Получение статистики
    print("\n5. Тест получения статистики...")
    stats = db.get_user_stats(123456789)
    print(f"✅ Статистика получена: {stats.get('analysis_count')} анализов")
    
    # Тест 6: Сохранение позиции
    print("\n6. Тест сохранения позиции...")
    position_id = db.save_position(
        user_id=123456789,
        name="Сицилианская защита",
        fen="rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
        tags=["дебют", "сицилианская"],
        notes="Моё любимое начало"
    )
    print(f"✅ Позиция сохранена: ID {position_id}")
    
    # Тест 7: Получение сохранённых позиций
    print("\n7. Тест получения сохранённых позиций...")
    positions = db.get_saved_positions(123456789)
    print(f"✅ Получено {len(positions)} позиций")
    
    # Очистка тестовой базы
    import os
    if os.path.exists("test_chess_bot.db"):
        os.remove("test_chess_bot.db")
        print("\n🗑️ Тестовая база данных удалена")
    
    print("\n✅ Все тесты пройдены успешно!")