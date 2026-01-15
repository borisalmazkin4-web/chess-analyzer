import cv2
import numpy as np
import os

print("ШАГ 1: Загрузка изображения")
print("=" * 40)

# --------------------------------------------------
# НАДЁЖНАЯ ЗАГРУЗКА ФАЙЛА (НЕ ЗАВИСИТ ОТ КАК ЗАПУЩЕН СКРИПТ)
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(BASE_DIR, "chess_board.jpg")

print("Путь к файлу:")
print(IMAGE_PATH)

image = cv2.imread(IMAGE_PATH)

if image is None:
    print("❌ ОШИБКА: файл chess_board.jpg не найден")
    print("Проверь:")
    print("1. Файл лежит рядом с этим .py")
    print("2. Имя файла ТОЧНО chess_board.jpg")
    print("3. Расширение не .png / .jpeg")
    input("Нажмите Enter для выхода...")
    exit()

print("✅ Изображение загружено")
print(f"Размер: {image.shape[1]}x{image.shape[0]}")

# --------------------------------------------------
# ШАГ 2: ПРЕДОБРАБОТКА
# --------------------------------------------------

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blur = cv2.GaussianBlur(gray, (5, 5), 0)
edges = cv2.Canny(blur, 50, 150)

cv2.imshow("Границы", edges)
cv2.waitKey(0)

# --------------------------------------------------
# ШАГ 3: ПОИСК КОНТУРА ДОСКИ
# --------------------------------------------------

contours, _ = cv2.findContours(
    edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
)

board_contour = None
max_area = 0

for cnt in contours:
    area = cv2.contourArea(cnt)
    if area > max_area:
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

        if len(approx) == 4:
            board_contour = approx
            max_area = area

if board_contour is None:
    print("❌ Не удалось найти контур доски")
    input("Нажмите Enter для выхода...")
    exit()

print("✅ Контур доски найден")

debug = image.copy()
cv2.drawContours(debug, [board_contour], -1, (0, 255, 0), 3)
cv2.imshow("Найденная доска", debug)
cv2.waitKey(0)

# --------------------------------------------------
# ШАГ 4: ВЫРАВНИВАНИЕ ПЕРСПЕКТИВЫ
# --------------------------------------------------

pts = board_contour.reshape(4, 2)

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]     # top-left
    rect[2] = pts[np.argmax(s)]     # bottom-right

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right
    rect[3] = pts[np.argmax(diff)]  # bottom-left

    return rect

rect = order_points(pts)

BOARD_SIZE = 800

dst = np.array([
    [0, 0],
    [BOARD_SIZE, 0],
    [BOARD_SIZE, BOARD_SIZE],
    [0, BOARD_SIZE]
], dtype="float32")

M = cv2.getPerspectiveTransform(rect, dst)
warped = cv2.warpPerspective(image, M, (BOARD_SIZE, BOARD_SIZE))

cv2.imshow("Выровненная доска", warped)
cv2.waitKey(0)

# --------------------------------------------------
# ШАГ 5: СЕТКА 8x8
# --------------------------------------------------

cell = BOARD_SIZE // 8
grid = warped.copy()

for row in range(8):
    for col in range(8):
        x1 = col * cell
        y1 = row * cell
        x2 = x1 + cell
        y2 = y1 + cell

        cv2.rectangle(grid, (x1, y1), (x2, y2), (0, 255, 0), 1)

cv2.imshow("Сетка 8x8", grid)
cv2.waitKey(0)

# --------------------------------------------------
# ШАГ 6: СОХРАНЕНИЕ
# --------------------------------------------------

cv2.imwrite(os.path.join(BASE_DIR, "board_warped.jpg"), warped)
cv2.imwrite(os.path.join(BASE_DIR, "board_grid.jpg"), grid)

print("✅ Готово!")
print("Файлы сохранены:")
print("- board_warped.jpg")
print("- board_grid.jpg")

print("=" * 40)
input("Нажмите Enter для выхода...")
cv2.destroyAllWindows()
