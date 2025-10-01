#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用样式定义
"""

# 主要颜色定义
COLORS = {
    'primary': '#007AFF',
    'primary_hover': '#0056CC', 
    'primary_pressed': '#004999',
    'background': '#ffffff',
    'background_alt': '#f6f8fa',
    'text': '#1a1a1a',
    'text_secondary': '#656d76',
    'border': '#d0d7de',
    'border_focus': '#0969da',
    'success': '#2da44e',
    'warning': '#ffd666',
    'warning_bg': '#4CAF50',
    'error': '#da3633',
    'disabled': '#f5f5f5',
    'disabled_text': '#a8a8a8',
}

# 应用主样式
APP_STYLE = f"""
/* 全局字体设置 */
* {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
}}

/* 主窗口背景 */
QMainWindow {{
    background-color: {COLORS['background']};
    color: {COLORS['text']};
}}

/* 标签页样式 */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['background']};
}}

QTabWidget::tab-bar {{
    left: 10px;
}}

QTabBar::tab {{
    background-color: {COLORS['background_alt']};
    color: {COLORS['text']};
    padding: 12px 24px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    border: 1px solid {COLORS['border']};
    border-bottom: none;
    font-size: 13px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['background']};
    color: {COLORS['primary']};
    border-color: {COLORS['border']};
    border-bottom: 1px solid {COLORS['background']};
    font-weight: 600;
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS['background']};
    color: {COLORS['text']};
}}

/* 组框样式 - 极简设计 */
QGroupBox {{
    font-size: 14px;
    font-weight: 600;
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 20px;
    background-color: {COLORS['background']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    background-color: {COLORS['background']};
    color: {COLORS['text']};
}}

/* 按钮样式 - 苹果风格 */
QPushButton {{
    background-color: {COLORS['primary']};
    border: none;
    color: {COLORS['background']};
    padding: 12px 24px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    min-height: 16px;
}}

QPushButton:hover {{
    background-color: {COLORS['primary_hover']};
}}

QPushButton:pressed {{
    background-color: {COLORS['primary_pressed']};
}}

QPushButton:disabled {{
    background-color: {COLORS['disabled']};
    color: {COLORS['disabled_text']};
    border: 1px solid {COLORS['border']};
}}

/* 特殊按钮样式 */
QPushButton#browse_btn {{
    background-color: {COLORS['background']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    padding: 8px 16px;
    font-size: 12px;
}}

QPushButton#browse_btn:hover {{
    background-color: {COLORS['background_alt']};
    border-color: {COLORS['border']};
}}

QPushButton#secondary_btn {{
    background-color: {COLORS['background_alt']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
}}

QPushButton#secondary_btn:hover {{
    background-color: {COLORS['background']};
    border-color: {COLORS['primary']};
}}

QPushButton#danger_btn {{
    background-color: {COLORS['error']};
    color: {COLORS['background']};
}}

QPushButton#danger_btn:hover {{
    background-color: #b91c1c;
}}

/* 输入框样式 - 简洁高级 */
QLineEdit {{
    background-color: {COLORS['background']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 12px 16px;
    font-size: 13px;
    color: {COLORS['text']};
}}

QLineEdit:focus {{
    border-color: {COLORS['border_focus']};
    outline: none;
}}

QLineEdit::placeholder {{
    color: {COLORS['text_secondary']};
}}

/* 复选框样式 */
QCheckBox {{
    font-size: 13px;
    color: {COLORS['text']};
    spacing: 8px;
    font-weight: 500;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    background-color: {COLORS['background']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTkuNSAzLjVMNC41IDguNSAyLjUgNi41IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjEuNSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS['primary']};
}}

/* 数字输入框样式 */
QSpinBox {{
    background-color: {COLORS['background']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    color: {COLORS['text']};
    font-weight: 500;
}}

QSpinBox:focus {{
    border-color: {COLORS['border_focus']};
    outline: none;
}}

QSpinBox::up-button, QSpinBox::down-button {{
    border: none;
    background: transparent;
    width: 16px;
}}

QSpinBox::up-arrow, QSpinBox::down-arrow {{
    width: 8px;
    height: 8px;
}}

/* 标签样式 */
QLabel {{
    color: {COLORS['text']};
    font-size: 13px;
    font-weight: 500;
}}

/* 进度条样式 - 极简设计 */
QProgressBar {{
    border: none;
    border-radius: 4px;
    background-color: {COLORS['background_alt']};
    text-align: center;
    font-size: 12px;
    font-weight: 500;
    color: {COLORS['text']};
    height: 8px;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 {COLORS['success']}, stop: 1 #218c3d);
    border-radius: 4px;
}}

/* 当前文件进度条 */
QProgressBar#current_progress {{
    background-color: {COLORS['background_alt']};
    height: 6px;
}}

QProgressBar#current_progress::chunk {{
    background-color: {COLORS['success']};
    border-radius: 3px;
}}

/* 文本编辑器样式 */
QTextEdit {{
    background-color: {COLORS['background_alt']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 16px;
    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
    font-size: 12px;
    color: {COLORS['text']};
    line-height: 1.5;
}}

/* 表格样式 */
QTableWidget, QTableView {{
    background-color: {COLORS['background']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    gridline-color: {COLORS['border']};
    selection-background-color: rgba(0, 122, 255, 0.1);
    selection-color: {COLORS['text']};
    font-size: 13px;
    show-decoration-selected: 0;
    outline: none;
}}

QTableWidget::item {{
    padding: 8px 12px;
    border: none;
    outline: none;
}}

QTableWidget::item:selected {{
    background-color: rgba(0, 122, 255, 0.1);
    color: {COLORS['text']};
    border: none;
    outline: none;
}}

QHeaderView::section {{
    background-color: {COLORS['background_alt']};
    color: {COLORS['text']};
    padding: 10px 12px;
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    font-weight: 600;
    font-size: 13px;
}}

/* 滚动条样式 */
QScrollBar:vertical {{
    background: {COLORS['background_alt']};
    width: 12px;
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    border-radius: 6px;
    min-height: 20px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['text_secondary']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    border: none;
    background: none;
    height: 0px;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

/* 状态栏样式 */
QStatusBar {{
    background-color: {COLORS['background_alt']};
    color: {COLORS['text_secondary']};
    border-top: 1px solid {COLORS['border']};
    font-size: 12px;
}}
"""

# 深色主题样式（保留原字幕重命名工具的深色风格作为可选主题）
DARK_STYLE = """
QMainWindow { 
    background: #0f1115; 
    color: #e4e6eb; 
}

QTabWidget::pane {
    border: 1px solid #2b2f3a;
    border-radius: 8px;
    background-color: #151822;
}

QTabBar::tab {
    background-color: #1a1f2b;
    color: #cfd3dc;
    padding: 12px 24px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    border: 1px solid #2b2f3a;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #151822;
    color: #e4e6eb;
    border-color: #2b2f3a;
    border-bottom: 1px solid #151822;
}

QLineEdit, QTableWidget, QTableView { 
    background: #151822; 
    color: #e4e6eb; 
    border: 1px solid #2b2f3a; 
    border-radius: 8px; 
    padding: 6px; 
}

QPushButton { 
    background: #1f2430; 
    color: #e4e6eb; 
    border: 1px solid #343a46; 
    border-radius: 8px; 
    padding: 8px 12px; 
}

QPushButton:hover { 
    background: #2a3140; 
}

QPushButton:disabled { 
    color: #888; 
    border-color: #2b2f3a; 
}

QHeaderView::section { 
    background: #1a1f2b; 
    color: #cfd3dc; 
    padding: 6px; 
    border: 0; 
}

QCheckBox { 
    color: #cfd3dc; 
}

QGroupBox {
    color: #e4e6eb;
    border: 1px solid #2b2f3a;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 20px;
    background-color: #151822;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    background-color: #151822;
    color: #e4e6eb;
}
"""

