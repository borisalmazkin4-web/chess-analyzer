print("=" * 50)
print("ПРОВЕРКА УСТАНОВКИ БИБЛИОТЕК")
print("=" * 50)
print()

# 1. Проверяем Python
import sys
print(f"1. Python версия: {sys.version[:6]}")
print()

# 2. Проверяем OpenCV
try:
    import cv2
    print(f"2. ✅ OpenCV установлена, версия: {cv2.__version__}")
except:
    print("2. ❌ OpenCV НЕ установлена")
    print("   Команда для установки: pip install opencv-python")
print()

# 3. Проверяем python-chess
try:
    import chess
    print("3. ✅ Python-chess установлена")
except:
    print("3. ❌ Python-chess НЕ установлена")
    print("   Команда для установки: pip install python-chess")
print()

# 4. Проверяем NumPy
try:
    import numpy as np
    print(f"4. ✅ NumPy установлена, версия: {np.__version__}")
except:
    print("4. ❌ NumPy НЕ установлена")
    print("   Команда для установки: pip install numpy")
print()

print("=" * 50)
print("ЕСЛИ ВСЕ 4 ПУНКТА С ГАЛОЧКАМИ ✅ — ВСЁ УСТАНОВЛЕНО!")
print("ЕСЛИ ЕСТЬ КРЕСТИКИ ❌ — УСТАНОВИТЕ ЭТИ БИБЛИОТЕКИ")
print("=" * 50)

input("\nНажмите Enter для выхода...")