# ============================================
# ШАХМАТНЫЙ АНАЛИЗАТОР - ШАГ 3 (УЛУЧШЕННЫЙ)
# Распознавание фигур с определением цвета
# ============================================

import cv2
import numpy as np
import os

print("=" * 50)
print("ШАГ 3: РАСПОЗНАВАНИЕ ФИГУР (УЛУЧШЕННАЯ ВЕРСИЯ)")
print("=" * 50)
print()

# 1. Проверяем наличие папки с клетками
if not os.path.exists("cells"):
    print("❌ Папка 'cells' не найдена!")
    print("   Сначала выполните Шаг 2")
    input("Нажмите Enter для выхода...")
    exit()

print("📁 Загружаем клетки из папки 'cells/'...")
print()

# 2. Функция для определения цвета клетки (светлая/тёмная)
def get_cell_color(cell_image):
    """Определяет, светлая клетка или тёмная"""
    gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
    avg_color = np.mean(gray)
    return "light" if avg_color > 127 else "dark"

# 3. Функция для определения: пустая клетка или нет
def is_cell_empty(cell_image, cell_color):
    """Определяет, пустая ли клетка"""
    gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Разные пороги для светлых и тёмных клеток
    if cell_color == "light":
        # На светлой клетке фигуры тёмные
        contrast_pixels = np.sum(blurred < 80)
    else:
        # На тёмной клетке фигуры светлые
        contrast_pixels = np.sum(blurred > 180)
    
    total_pixels = gray.shape[0] * gray.shape[1]
    contrast_ratio = contrast_pixels / total_pixels
    
    # Дополнительная проверка: вычисляем контрастность
    min_val = np.min(blurred)
    max_val = np.max(blurred)
    contrast = max_val - min_val
    
    # Клетка считается пустой если:
    # 1. Мало контрастных пикселей И
    # 2. Низкий общий контраст
    return contrast_ratio < 0.15 and contrast < 100

# 4. Функция для определения цвета фигуры
def get_piece_color(cell_image, cell_color):
    """Определяет цвет фигуры (белая/чёрная)"""
    gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
    
    # Разделяем изображение на области
    height, width = gray.shape
    center_region = gray[height//4:3*height//4, width//4:3*width//4]
    
    avg_brightness = np.mean(center_region)
    
    if cell_color == "light":
        # На светлой клетке:
        # - Белая фигура: яркая
        # - Чёрная фигура: тёмная
        if avg_brightness > 160:
            return 'w'  # белая
        elif avg_brightness < 100:
            return 'b'  # чёрная
    else:
        # На тёмной клетке:
        # - Белая фигура: очень яркая
        # - Чёрная фигура: тёмная, но не такая как клетка
        if avg_brightness > 180:
            return 'w'  # белая
        elif avg_brightness < 140:
            return 'b'  # чёрная
    
    return '?'  # неопределён

# 5. Функция для определения типа фигуры (очень упрощённо)
def guess_piece_type(cell_image, piece_color, cell_color):
    """Пытается угадать тип фигуры (очень простой метод)"""
    gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
    
    # Вычисляем "заполненность" клетки
    if cell_color == "light":
        filled_pixels = np.sum(gray < 100)
    else:
        filled_pixels = np.sum(gray > 150)
    
    total_pixels = gray.shape[0] * gray.shape[1]
    fill_ratio = filled_pixels / total_pixels
    
    # Вычисляем форму (отношение высоты к ширине заполненной области)
    # Для этого находим контуры
    if cell_color == "light":
        _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
    else:
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # Берём самый большой контур
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        aspect_ratio = h / w if w > 0 else 0
        
        # Очень грубая классификация:
        if fill_ratio > 0.6:
            if aspect_ratio > 1.2:
                return 'r'  # ладья (высокая)
            else:
                return 'q'  # ферзь (круглая)
        elif fill_ratio > 0.4:
            return 'n'  # конь (средняя заполненность)
        elif fill_ratio > 0.2:
            return 'b'  # слон
        else:
            return 'p'  # пешка
    
    return 'p'  # по умолчанию пешка

# 6. Анализируем все клетки
print("🔍 Анализируем клетки...")
print("   (определяем: пустая, цвет фигуры, тип фигуры)")
print()

# Создаём шахматную доску 8x8
# Будем хранить в формате: 'wp' - белая пешка, 'bk' - чёрный король и т.д.
board = [['.' for _ in range(8)] for _ in range(8)]

# Шахматные обозначения
chess_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
chess_numbers = ['8', '7', '6', '5', '4', '3', '2', '1']

# Счётчики для статистики
empty_count = 0
white_count = 0
black_count = 0

# Анализируем каждую клетку
for row in range(8):
    for col in range(8):
        filename = f"cells/cell_{row}_{col}.jpg"
        
        if os.path.exists(filename):
            # Загружаем клетку
            cell = cv2.imread(filename)
            
            # Определяем цвет клетки
            cell_color = get_cell_color(cell)
            
            # Проверяем, пустая ли клетка
            if is_cell_empty(cell, cell_color):
                board[row][col] = '.'  # пустая
                empty_count += 1
            else:
                # Определяем цвет фигуры
                piece_color = get_piece_color(cell, cell_color)
                
                # Пытаемся определить тип фигуры
                piece_type = guess_piece_type(cell, piece_color, cell_color)
                
                # Формируем обозначение
                if piece_color == 'w':
                    piece_code = piece_type.upper()  # белые - заглавные
                    white_count += 1
                elif piece_color == 'b':
                    piece_code = piece_type.lower()  # чёрные - строчные
                    black_count += 1
                else:
                    piece_code = '?'  # неопределённый цвет
                
                board[row][col] = piece_code
            
            # Выводим информацию для первых 4 клеток
            if row < 2 and col < 2:
                pos = f"{chess_letters[col]}{chess_numbers[row]}"
                cell_type = "пустая" if board[row][col] == '.' else f"фигура: {board[row][col]}"
                print(f"   {pos}: {cell_type} ({cell_color} клетка)")
        else:
            print(f"❌ Файл не найден: {filename}")
            board[row][col] = '?'

print()
print("✅ Анализ завершён!")
print()

# 7. Выводим доску в консоль
print("🎲 РАСПОЗНАННАЯ ДОСКА:")
print("   . - пустая клетка")
print("   K/Q/R/B/N/P - белые фигуры")
print("   k/q/r/b/n/p - чёрные фигуры")
print("   ? - неопределено")
print()

print("    a b c d e f g h")
print("   ┌─┬─┬─┬─┬─┬─┬─┬─┐")
for i in range(8):
    print(f"{8-i}  │", end="")
    for j in range(8):
        print(f"{board[i][j]}│", end="")
    print(f" {8-i}")
    if i < 7:
        print("   ├─┼─┼─┼─┼─┼─┼─┼─┤")
print("   └─┴─┴─┴─┴─┴─┴─┴─┘")
print("    a b c d e f g h")
print()

# 8. Статистика
print("📊 СТАТИСТИКА:")
print(f"   Пустых клеток: {empty_count}")
print(f"   Белых фигур: {white_count}")
print(f"   Чёрных фигур: {black_count}")
print(f"   Всего фигур: {white_count + black_count}")
print()

# 9. Создаём FEN строку
print("📝 Создаём FEN запись...")
fen_rows = []
for row in range(8):
    fen_row = ''
    empty_count_in_row = 0
    
    for col in range(8):
        piece = board[row][col]
        if piece == '.':
            empty_count_in_row += 1
        else:
            if empty_count_in_row > 0:
                fen_row += str(empty_count_in_row)
                empty_count_in_row = 0
            fen_row += piece
    
    if empty_count_in_row > 0:
        fen_row += str(empty_count_in_row)
    
    fen_rows.append(fen_row)

fen_position = '/'.join(fen_rows)

# Для начальной позиции ожидаем:
# rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR
print("🎯 ОЖИДАЕМЫЙ FEN для начальной позиции:")
print("   rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
print()
print("🎯 ПОЛУЧЕННЫЙ FEN:")
print(f"   {fen_position}")
print()

# 10. Создаём визуализацию доски
print("🎨 Создаём цветную визуализацию...")
cell_size = 60
board_size = cell_size * 8
visualization = np.ones((board_size, board_size, 3), dtype=np.uint8) * 200

# Цвета
light_color = (240, 217, 181)
dark_color = (181, 136, 99)
white_piece_color = (255, 255, 255)
black_piece_color = (0, 0, 0)

# Обозначения фигур (Unicode символы)
piece_symbols = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
}

# Рисуем доску
for row in range(8):
    for col in range(8):
        # Цвет клетки
        if (row + col) % 2 == 0:
            color = light_color
            text_color = (0, 0, 0)  # чёрный текст на светлой клетке
        else:
            color = dark_color
            text_color = (255, 255, 255)  # белый текст на тёмной клетке
        
        # Координаты
        x1 = col * cell_size
        y1 = row * cell_size
        x2 = x1 + cell_size
        y2 = y1 + cell_size
        
        # Рисуем клетку
        cv2.rectangle(visualization, (x1, y1), (x2, y2), color, -1)
        
        # Если есть фигура
        piece = board[row][col]
        if piece != '.':
            # Цвет кружка под фигурой
            if piece.isupper():  # белая фигура
                circle_color = (200, 200, 255)  # светло-синий
            else:  # чёрная фигура
                circle_color = (100, 100, 150)  # тёмно-синий
            
            # Центр клетки
            center_x = x1 + cell_size // 2
            center_y = y1 + cell_size // 2
            
            # Рисуем кружок
            cv2.circle(visualization, (center_x, center_y), 22, circle_color, -1)
            cv2.circle(visualization, (center_x, center_y), 22, (0, 0, 0), 2)
            
            # Буква фигуры
            piece_char = piece.upper() if piece != '?' else '?'
            cv2.putText(visualization, piece_char, 
                       (center_x-8, center_y+10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)

# Добавляем координаты
font = cv2.FONT_HERSHEY_SIMPLEX
for i in range(8):
    # Буквы
    cv2.putText(visualization, chess_letters[i], 
                (i*cell_size + cell_size//2 - 10, board_size - 10),
                font, 0.6, (0, 0, 0), 2)
    # Цифры
    cv2.putText(visualization, chess_numbers[i],
                (10, i*cell_size + cell_size//2 + 10),
                font, 0.6, (0, 0, 0), 2)

# Сохраняем
output_file = "step3_advanced_visualization.jpg"
cv2.imwrite(output_file, visualization)
print(f"✅ Визуализация сохранена: {output_file}")
print()

# 11. Показываем результаты
print("👀 Показываю цветную визуализацию:")
print("   • Синие кружки - фигуры")
print("   • Буквы внутри - тип фигуры")
print("   • Заглавные - белые, строчные - чёрные")
print()

cv2.imshow("Распознанная доска (усовершенствованная)", visualization)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 12. Сохраняем результаты в файл
print("💾 Сохраняем результаты в текстовый файл...")
with open("step3_results.txt", "w", encoding="utf-8") as f:
    f.write("=" * 50 + "\n")
    f.write("РЕЗУЛЬТАТЫ РАСПОЗНАВАНИЯ ШАХМАТНОЙ ДОСКИ\n")
    f.write("=" * 50 + "\n\n")
    
    f.write("РАСПОЗНАННАЯ ПОЗИЦИЯ:\n")
    f.write("    a b c d e f g h\n")
    f.write("   ┌─┬─┬─┬─┬─┬─┬─┬─┐\n")
    for i in range(8):
        f.write(f"{8-i}  │")
        for j in range(8):
            f.write(f"{board[i][j]}│")
        f.write(f" {8-i}\n")
        if i < 7:
            f.write("   ├─┼─┼─┼─┼─┼─┼─┼─┤\n")
    f.write("   └─┴─┴─┴─┴─┴─┴─┴─┘\n")
    f.write("    a b c d e f g h\n\n")
    
    f.write(f"FEN: {fen_position}\n\n")
    
    f.write("СТАТИСТИКА:\n")
    f.write(f"  Пустых клеток: {empty_count}\n")
    f.write(f"  Белых фигур: {white_count}\n")
    f.write(f"  Чёрных фигур: {black_count}\n")
    f.write(f"  Всего фигур: {white_count + black_count}\n\n")
    
    f.write("ОБОЗНАЧЕНИЯ:\n")
    f.write("  K/k - Король   Q/q - Ферзь   R/r - Ладья\n")
    f.write("  B/b - Слон     N/n - Конь    P/p - Пешка\n")
    f.write("  . - пустая клетка\n")

print(f"✅ Результаты сохранены: step3_results.txt")
print()

print("✅ ШАГ 3 (УЛУЧШЕННЫЙ) ВЫПОЛНЕН УСПЕШНО!")
print()
print("📋 ИТОГИ:")
print(f"   1. Создано: {output_file} - визуализация")
print(f"   2. Создано: step3_results.txt - текстовый отчёт")
print(f"   3. FEN позиция: {fen_position}")
print()
print("⚠️  ПРИМЕЧАНИЕ: Распознавание типов фигур очень приблизительное!")
print("   Для точного распознавания нужны:")
print("   1. Обучение нейросети")
print("   2. Или шаблонное сопоставление с образцами")
print()
print("➡️  Теперь можно переходить к Шагу 4 (подключение шахматного движка)")

print("=" * 50)
input("Нажмите Enter для завершения...")