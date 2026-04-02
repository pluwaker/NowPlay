#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для минификации HTML файлов
Удаляет лишние пробелы, переносы строк, комментарии
"""
import re
import os
import sys
from pathlib import Path

def minify_html(html_content):
    """Минифицирует HTML контент"""
    # Удаляем HTML комментарии (но оставляем <!--! для важных)
    html_content = re.sub(r'<!--(?!<!)(?:(?!-->).)*-->', '', html_content, flags=re.DOTALL)
    
    # Удаляем лишние пробелы между тегами
    html_content = re.sub(r'>\s+<', '><', html_content)
    
    # Удаляем пробелы в начале и конце строк (кроме содержимого тегов)
    # Сохраняем содержимое <script> и <style> для дальнейшей обработки
    script_blocks = []
    style_blocks = []
    
    # Извлекаем блоки <style>
    style_pattern = r'<style[^>]*>(.*?)</style>'
    def style_replace(match):
        style_blocks.append(match.group(0))
        return f'<STYLE_BLOCK_{len(style_blocks)-1}>'
    html_content = re.sub(style_pattern, style_replace, html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Извлекаем блоки <script>
    script_pattern = r'<script[^>]*>(.*?)</script>'
    def script_replace(match):
        script_blocks.append(match.group(0))
        return f'<SCRIPT_BLOCK_{len(script_blocks)-1}>'
    html_content = re.sub(script_pattern, script_replace, html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Минифицируем основной HTML
    html_content = re.sub(r'\s+', ' ', html_content)  # Заменяем множественные пробелы на один
    html_content = re.sub(r'>\s+<', '><', html_content)  # Убираем пробелы между тегами
    html_content = html_content.strip()
    
    # Минифицируем CSS в блоках <style>
    for i, style_block in enumerate(style_blocks):
        # Извлекаем содержимое style
        css_content = re.search(r'<style[^>]*>(.*?)</style>', style_block, re.DOTALL | re.IGNORECASE)
        if css_content:
            css = css_content.group(1)
            # Минифицируем CSS
            css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)  # Удаляем комментарии
            css = re.sub(r'\s+', ' ', css)  # Заменяем множественные пробелы
            css = re.sub(r';\s*}', '}', css)  # Удаляем пробелы перед }
            css = re.sub(r'{\s+', '{', css)  # Удаляем пробелы после {
            css = re.sub(r':\s+', ':', css)  # Удаляем пробелы после :
            css = re.sub(r';\s+', ';', css)  # Удаляем пробелы после ;
            css = css.strip()
            # Восстанавливаем блок
            style_tag = re.search(r'<style[^>]*>', style_block, re.IGNORECASE)
            style_blocks[i] = f'{style_tag.group(0)}{css}</style>'
        placeholder = f'<STYLE_BLOCK_{i}>'
        html_content = html_content.replace(placeholder, style_blocks[i])
    
    # Минифицируем JavaScript в блоках <script>
    for i, script_block in enumerate(script_blocks):
        # Извлекаем содержимое script
        js_content = re.search(r'<script[^>]*>(.*?)</script>', script_block, re.DOTALL | re.IGNORECASE)
        if js_content:
            js = js_content.group(1)
            # Простая минификация JS (безопасная)
            js = re.sub(r'/\*.*?\*/', '', js, flags=re.DOTALL)  # Удаляем многострочные комментарии
            js = re.sub(r'//.*?$', '', js, flags=re.MULTILINE)  # Удаляем однострочные комментарии
            js = re.sub(r'\s+', ' ', js)  # Заменяем множественные пробелы
            js = re.sub(r';\s*}', '}', js)  # Удаляем пробелы перед }
            js = re.sub(r'{\s+', '{', js)  # Удаляем пробелы после {
            js = js.strip()
            # Восстанавливаем блок
            script_tag = re.search(r'<script[^>]*>', script_block, re.IGNORECASE)
            script_blocks[i] = f'{script_tag.group(0)}{js}</script>'
        placeholder = f'<SCRIPT_BLOCK_{i}>'
        html_content = html_content.replace(placeholder, script_blocks[i])
    
    return html_content

def process_html_file(file_path):
    """Обрабатывает один HTML файл"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        original_size = len(original_content.encode('utf-8'))
        
        # Минифицируем
        minified_content = minify_html(original_content)
        minified_size = len(minified_content.encode('utf-8'))
        
        # Сохраняем минифицированную версию
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(minified_content)
        
        savings = original_size - minified_size
        savings_percent = (savings / original_size * 100) if original_size > 0 else 0
        
        print(f"{file_path.name}: {original_size:,} -> {minified_size:,} байт "
              f"(-{savings:,} байт, -{savings_percent:.1f}%)")
        
        return savings
        
    except Exception as e:
        print(f"Ошибка при обработке {file_path.name}: {e}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    """Основная функция"""
    # Путь к папке с HTML файлами
    script_dir = Path(__file__).parent.absolute()
    html_dir = script_dir / "now_server"
    
    if not html_dir.exists():
        print("Ошибка: папка now_server не найдена")
        print(f"Искали в: {html_dir}")
        return
    
    # Находим все HTML файлы
    html_files = list(html_dir.glob("*.html"))
    
    if not html_files:
        print("Ошибка: HTML файлы не найдены")
        return
    
    print(f"Найдено {len(html_files)} HTML файлов")
    print("-" * 60)
    
    total_savings = 0
    total_original = 0
    
    for html_file in html_files:
        original_size = html_file.stat().st_size
        total_original += original_size
        savings = process_html_file(html_file)
        total_savings += savings
    
    print("-" * 60)
    if total_original > 0:
        percent = total_savings / total_original * 100
        print(f"Итого: {total_original:,} -> {total_original - total_savings:,} байт")
        print(f"Экономия: -{total_savings:,} байт (-{percent:.1f}%)")

if __name__ == "__main__":
    main()

