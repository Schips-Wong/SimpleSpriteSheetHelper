import sys
import os
import json
from PIL import Image, ImageDraw
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QGroupBox, QMessageBox,
    QCheckBox, QSpinBox, QScrollArea, QAction, QMenu, QToolBar, QProgressBar,
    QSlider, QComboBox
)
from PyQt5.QtGui import (
    QPixmap, QImage, QPainter, QPen, QColor, QBrush, QCursor,
    QMouseEvent, QPaintEvent, QKeyEvent, QIcon
)
from PyQt5.QtCore import Qt, QPoint, QRect, QThread, pyqtSignal, QObject, QSize, QTranslator, QCoreApplication


class SpriteDetector(QObject):
    """精灵检测类，用于自动识别精灵图中的精灵"""

    progress_updated = pyqtSignal(int)
    detection_finished = pyqtSignal(list)

    def __init__(self, image_path, bg_color=None, threshold=50, detection_areas=None):
        super().__init__()
        self.image_path = image_path
        self.bg_color = bg_color
        self.threshold = threshold
        self.detection_areas = detection_areas or []  # 检测范围列表
        self.sprite_rects = []

    def detect_sprites(self):
        """检测精灵图中的所有精灵"""
        try:
            with Image.open(self.image_path) as img:
                # 转换为RGBA模式
                img = img.convert('RGBA')
                pixels = img.load()
                width, height = img.size

                # 如果没有指定背景颜色，则自动检测
                if not self.bg_color:
                    self.bg_color = self._detect_background_color(img)

                # 创建一个标记矩阵，用于记录已经访问过的像素
                visited = [[False for _ in range(width)] for _ in range(height)]

                # 如果没有指定检测范围，则检测整个图像
                if not self.detection_areas:
                    self.detection_areas = [(0, 0, width, height)]

                # 遍历所有检测范围
                for area in self.detection_areas:
                    area_x, area_y, area_width, area_height = area
                    area_end_x = area_x + area_width
                    area_end_y = area_y + area_height

                    # 遍历检测范围内的所有像素，寻找精灵
                    for y in range(area_y, area_end_y):
                        for x in range(area_x, area_end_x):
                            if not visited[y][x]:
                                pixel_color = pixels[x, y]
                                # 如果当前像素不是背景色，且是不透明的，则检测精灵
                                if pixel_color[3] > 128 and not self._is_background(pixel_color):
                                    # 使用BFS找到整个精灵区域
                                    rect = self._find_sprite_region(img, x, y, visited)
                                    if rect:
                                        self.sprite_rects.append(rect)
                        # 更新进度
                        progress = int((y / height) * 100)
                        self.progress_updated.emit(progress)

            # 发送检测完成信号
            self.detection_finished.emit(self.sprite_rects)
        except Exception as e:
            QMessageBox.critical(None, "错误", f"检测精灵失败：{str(e)}")

    def _detect_background_color(self, img):
        """自动检测背景颜色"""
        # 采样四个角落的像素，取出现最多的颜色作为背景色
        width, height = img.size
        corners = [
            img.getpixel((0, 0)),
            img.getpixel((width-1, 0)),
            img.getpixel((0, height-1)),
            img.getpixel((width-1, height-1))
        ]

        # 统计每个颜色出现的次数
        color_counts = {}
        for color in corners:
            if color in color_counts:
                color_counts[color] += 1
            else:
                color_counts[color] = 1

        # 返回出现次数最多的颜色
        return max(color_counts, key=color_counts.get)

    def _is_background(self, pixel_color):
        """判断像素是否为背景色"""
        if pixel_color[3] < 128:  # 透明像素
            return True

        # 计算与背景色的欧氏距离
        distance = sum(
            (a - b) ** 2 for a, b in zip(pixel_color[:3], self.bg_color[:3])
        ) ** 0.5

        return distance < self.threshold

    def _find_sprite_region(self, img, start_x, start_y, visited):
        """使用BFS找到精灵区域"""
        width, height = img.size
        pixels = img.load()

        # 初始化BFS队列
        queue = [(start_x, start_y)]
        visited[start_y][start_x] = True

        # 初始化精灵区域的边界
        min_x, min_y = start_x, start_y
        max_x, max_y = start_x, start_y

        # BFS遍历
        while queue:
            x, y = queue.pop(0)

            # 更新精灵区域边界
            if x < min_x: min_x = x
            if x > max_x: max_x = x
            if y < min_y: min_y = y
            if y > max_y: max_y = y

            # 检查八个方向的相邻像素
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue

                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
                        pixel_color = pixels[nx, ny]
                        if pixel_color[3] > 128 and not self._is_background(pixel_color):
                            visited[ny][nx] = True
                            queue.append((nx, ny))

        # 计算精灵区域的宽度和高度
        sprite_width = max_x - min_x + 1
        sprite_height = max_y - min_y + 1

        # 过滤掉太小的区域（可能是噪点）
        if sprite_width < 5 or sprite_height < 5:
            return None

        return (min_x, min_y, sprite_width, sprite_height)


class SpriteCanvas(QLabel):
    """精灵图画布，用于显示和编辑精灵区域"""

    # 调整大小的方向常量
    NONE = 0
    LEFT = 1
    RIGHT = 2
    TOP = 4
    BOTTOM = 8
    TOP_LEFT = 5
    TOP_RIGHT = 6
    BOTTOM_LEFT = 9
    BOTTOM_RIGHT = 10

    rect_selected = pyqtSignal(int)
    rect_updated = pyqtSignal()
    scale_changed = pyqtSignal(float)  # 缩放变化信号
    detection_area_selected = pyqtSignal(list)  # 检测范围选择信号

    def __init__(self):
        super().__init__()
        # 设置对齐方式为左上角对齐
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        # 设置鼠标跟踪
        self.setMouseTracking(True)
        # 设置焦点策略，以便接收键盘事件
        self.setFocusPolicy(Qt.StrongFocus)
        self.image_path = None
        self.pixmap = None
        self.original_pixmap = None
        self.sprite_rects = []
        self.detection_areas = []  # 检测范围列表
        self.selected_rect_index = -1
        self.selected_area_index = -1  # 选中的检测范围索引
        self.hover_rect_index = -1
        self.hover_area_index = -1  # 悬停的检测范围索引
        self.scale_factor = 1.0
        # 添加选框相关变量
        self.is_drawing = False
        self.start_pos = QPoint()
        self.current_rect = QRect()
        self.drawing_mode = False  # 是否处于绘制模式
        self.drawing_area_mode = False  # 是否处于绘制检测范围模式

        # 调整大小相关变量
        self.is_resizing = False
        self.is_dragging = False  # 是否处于拖拽模式
        self.resize_direction = self.NONE
        self.resize_start_pos = QPoint()
        self.drag_start_pos = QPoint()  # 拖拽开始位置
        self.original_rect = QRect()
        self.handle_size = 8  # 调整大小的控制点大小
        
        # 拖拽重排序相关变量
        self.is_reordering = False  # 是否处于拖拽重排序模式
        self.reorder_start_index = -1  # 开始拖拽的精灵索引
        self.reorder_drag_pos = QPoint()  # 拖拽起始位置
        # Shift+点击交换相关变量
        self.is_shift_pressed = False  # Shift键是否按下
        self.swap_start_index = -1  # 第一个选中的交换对象索引
        
        # 撤销功能相关变量
        self.undo_stack = []  # 撤销栈，保存检测区域移动前的状态

    def set_scale(self, scale):
        """设置缩放比例"""
        self.scale_factor = scale
        if self.original_pixmap:
            scaled_pixmap = self.original_pixmap.scaled(
                int(self.original_pixmap.width() * scale),
                int(self.original_pixmap.height() * scale),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
            self.update()

    def set_image(self, image_path):
        """设置显示的图片"""
        self.image_path = image_path
        self.original_pixmap = QPixmap(image_path)
        self.set_scale(self.scale_factor)
        self.sprite_rects = []
        self.detection_areas = []  # 清空检测范围
        self.selected_rect_index = -1
        self.selected_area_index = -1
        self.hover_rect_index = -1
        self.hover_area_index = -1

    def set_sprite_rects(self, rects):
        """设置精灵区域列表"""
        self.sprite_rects = rects
        self.selected_rect_index = -1
        self.hover_rect_index = -1
        self.update()

    def set_drawing_mode(self, mode):
        """设置绘制模式"""
        self.drawing_mode = mode
        self.drawing_area_mode = False
        if mode:
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
            self.hover_rect_index = -1
        self.update()

    def set_drawing_area_mode(self, mode):
        """设置绘制检测范围模式"""
        self.drawing_area_mode = mode
        self.drawing_mode = False
        if mode:
            # 使用更明显的十字光标
            self.setCursor(Qt.SizeAllCursor)  # 使用四向箭头光标，比CrossCursor更明显
        else:
            self.setCursor(Qt.ArrowCursor)
            self.hover_area_index = -1
        self.update()

    def paintEvent(self, event):
        """绘制事件，用于绘制精灵区域框、检测范围框、控制点和正在创建的选框"""
        super().paintEvent(event)
        if not self.original_pixmap:
            return

        painter = QPainter(self)

        # 绘制精灵区域框
        for i, rect in enumerate(self.sprite_rects):
            x, y, width, height = rect

            # 使用当前缩放因子计算绘制坐标
            scaled_x = int(x * self.scale_factor)
            scaled_y = int(y * self.scale_factor)
            scaled_width = int(width * self.scale_factor)
            scaled_height = int(height * self.scale_factor)

            # 创建绘制的矩形
            draw_rect = QRect(scaled_x, scaled_y, scaled_width, scaled_height)

            # 设置画笔样式
            if i == self.swap_start_index:
                # 第一个选中的交换对象，使用特殊样式
                pen = QPen(QColor(0, 0, 255), 3, Qt.DashLine)
                brush = QBrush(QColor(0, 0, 255, 30))
            elif i == self.selected_rect_index:
                pen = QPen(QColor(255, 0, 0), 2, Qt.SolidLine)
                brush = QBrush(QColor(255, 0, 0, 30))
            elif i == self.hover_rect_index and not self.drawing_mode:
                pen = QPen(QColor(255, 255, 0), 2, Qt.SolidLine)
                brush = QBrush(QColor(255, 255, 0, 30))
            else:
                pen = QPen(QColor(0, 255, 0), 1, Qt.SolidLine)
                brush = QBrush(QColor(0, 255, 0, 30))

            painter.setPen(pen)
            painter.setBrush(brush)
            painter.drawRect(draw_rect)

            # 绘制矩形索引
            painter.drawText(scaled_x + 5, scaled_y + 15, str(i+1))

            # 如果是选中的选框，绘制调整大小的控制点
            if i == self.selected_rect_index:
                self.draw_handles(painter, rect)
            # 如果是第一个选中的交换对象，绘制特殊的交换控制点
            elif i == self.swap_start_index:
                # 绘制四个角的交换标记
                marker_size = 12
                # 左上角
                painter.drawLine(scaled_x, scaled_y, scaled_x + marker_size, scaled_y + marker_size)
                painter.drawLine(scaled_x, scaled_y + marker_size, scaled_x + marker_size, scaled_y)
                # 右上角
                painter.drawLine(scaled_x + scaled_width, scaled_y, scaled_x + scaled_width - marker_size, scaled_y + marker_size)
                painter.drawLine(scaled_x + scaled_width, scaled_y + marker_size, scaled_x + scaled_width - marker_size, scaled_y)
                # 左下角
                painter.drawLine(scaled_x, scaled_y + scaled_height, scaled_x + marker_size, scaled_y + scaled_height - marker_size)
                painter.drawLine(scaled_x, scaled_y + scaled_height - marker_size, scaled_x + marker_size, scaled_y + scaled_height)
                # 右下角
                painter.drawLine(scaled_x + scaled_width, scaled_y + scaled_height, scaled_x + scaled_width - marker_size, scaled_y + scaled_height - marker_size)
                painter.drawLine(scaled_x + scaled_width, scaled_y + scaled_height - marker_size, scaled_x + scaled_width - marker_size, scaled_y + scaled_height)

        # 绘制检测范围框
        for i, rect in enumerate(self.detection_areas):
            x, y, width, height = rect

            # 使用当前缩放因子计算绘制坐标
            scaled_x = int(x * self.scale_factor)
            scaled_y = int(y * self.scale_factor)
            scaled_width = int(width * self.scale_factor)
            scaled_height = int(height * self.scale_factor)

            # 创建绘制的矩形
            draw_rect = QRect(scaled_x, scaled_y, scaled_width, scaled_height)

            # 设置画笔样式
            if i == self.selected_area_index:
                pen = QPen(QColor(255, 255, 0), 2, Qt.DashLine)
                brush = QBrush(QColor(255, 255, 0, 20))
            elif i == self.hover_area_index and not self.drawing_area_mode:
                pen = QPen(QColor(0, 255, 255), 2, Qt.DashLine)
                brush = QBrush(QColor(0, 255, 255, 20))
            else:
                pen = QPen(QColor(255, 0, 255), 1, Qt.DashLine)
                brush = QBrush(QColor(255, 0, 255, 20))

            painter.setPen(pen)
            painter.setBrush(brush)
            painter.drawRect(draw_rect)

            # 绘制检测范围索引
            painter.drawText(scaled_x + 5, scaled_y + 15, f"A{i+1}")

            # 如果是选中的检测范围，绘制调整大小的控制点
            if i == self.selected_area_index:
                self.draw_handles(painter, rect)

        # 绘制正在创建的选框
        if (self.drawing_mode or self.drawing_area_mode) and self.is_drawing:
            # 使用更明显的样式绘制正在创建的选框
            pen = QPen(QColor(255, 0, 255), 3, Qt.DashLine)  # 更粗的线条，更鲜艳的颜色
            brush = QBrush(QColor(255, 0, 255, 20))
            painter.setPen(pen)
            painter.setBrush(brush)
            painter.drawRect(self.current_rect)
            
            # 绘制十字线，增强视觉效果
            if self.drawing_area_mode:
                # 绘制水平线
                painter.drawLine(
                    self.current_rect.left(), self.current_rect.center().y(),
                    self.current_rect.right(), self.current_rect.center().y()
                )
                # 绘制垂直线
                painter.drawLine(
                    self.current_rect.center().x(), self.current_rect.top(),
                    self.current_rect.center().x(), self.current_rect.bottom()
                )

    def mouseMoveEvent(self, event):
        """鼠标移动事件，用于检测鼠标悬停的边框、绘制选框或调整选框大小"""
        mouse_pos = event.pos()

        if self.is_resizing:
            # 调整选框大小
            self.resize_rect(mouse_pos)
        elif self.is_dragging:
            # 拖拽移动选框
            self.drag_rect(mouse_pos)
        elif (self.drawing_mode or self.drawing_area_mode) and self.is_drawing:
            # 绘制模式下，更新正在创建的选框
            self.current_rect = QRect(self.start_pos, mouse_pos).normalized()
            self.update()
        elif not self.drawing_mode and not self.drawing_area_mode:
            # 非绘制模式下
            if self.selected_area_index != -1:
                # 如果有选中的检测范围，检测是否在调整大小的控制点上
                direction = self.get_resize_direction(mouse_pos, self.detection_areas[self.selected_area_index])
                if direction != self.NONE:
                    self.resize_direction = direction
                    self.set_cursor_by_direction(direction)
                    return

            if self.selected_rect_index != -1:
                # 如果有选中的选框，检测是否在调整大小的控制点上
                direction = self.get_resize_direction(mouse_pos, self.sprite_rects[self.selected_rect_index])
                if direction != self.NONE:
                    self.resize_direction = direction
                    self.set_cursor_by_direction(direction)
                    return

            # 检测鼠标是否在某个精灵区域内
            hover_rect_index = -1
            for i, rect in enumerate(self.sprite_rects):
                x, y, width, height = rect
                scaled_x = int(x * self.scale_factor)
                scaled_y = int(y * self.scale_factor)
                scaled_width = int(width * self.scale_factor)
                scaled_height = int(height * self.scale_factor)

                draw_rect = QRect(scaled_x, scaled_y, scaled_width, scaled_height)
                if draw_rect.contains(mouse_pos):
                    hover_rect_index = i
                    break

            # 检测鼠标是否在某个检测范围内
            hover_area_index = -1
            if hover_rect_index == -1:  # 只有不在精灵区域内时才检测检测范围
                for i, rect in enumerate(self.detection_areas):
                    x, y, width, height = rect
                    scaled_x = int(x * self.scale_factor)
                    scaled_y = int(y * self.scale_factor)
                    scaled_width = int(width * self.scale_factor)
                    scaled_height = int(height * self.scale_factor)

                    draw_rect = QRect(scaled_x, scaled_y, scaled_width, scaled_height)
                    if draw_rect.contains(mouse_pos):
                        hover_area_index = i
                        break

            # 更新悬停状态
            if hover_area_index != self.hover_area_index:
                self.hover_area_index = hover_area_index
                self.update()

            if hover_rect_index != self.hover_rect_index:
                self.hover_rect_index = hover_rect_index
                self.update()

            # 设置鼠标指针样式
            if hover_area_index != -1:
                self.setCursor(Qt.PointingHandCursor)
            elif hover_rect_index != -1:
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

            self.resize_direction = self.NONE

    def mousePressEvent(self, event):
        """鼠标点击事件，用于选中边框、开始绘制选框或开始调整选框大小"""
        if event.button() == Qt.LeftButton:
            if self.drawing_mode or self.drawing_area_mode:
                # 绘制模式下，开始创建选框
                self.is_drawing = True
                self.start_pos = event.pos()
                self.current_rect = QRect(self.start_pos, self.start_pos)
                self.update()
            else:
                # 非绘制模式下，先检测是否点击了精灵区域
                clicked_rect_index = -1
                for i, rect in enumerate(self.sprite_rects):
                    x, y, width, height = rect
                    scaled_x = int(x * self.scale_factor)
                    scaled_y = int(y * self.scale_factor)
                    scaled_width = int(width * self.scale_factor)
                    scaled_height = int(height * self.scale_factor)

                    draw_rect = QRect(scaled_x, scaled_y, scaled_width, scaled_height)
                    if draw_rect.contains(event.pos()):
                        clicked_rect_index = i
                        break

                if clicked_rect_index != -1:
                    # 检查是否按下了Shift键（用于交换）
                    if event.modifiers() & Qt.ShiftModifier:
                        if self.swap_start_index == -1:
                            # 第一次点击，记录起始索引
                            self.swap_start_index = clicked_rect_index
                            self.selected_rect_index = -1  # 取消普通选中
                            self.update()
                        elif self.swap_start_index != clicked_rect_index:
                            # 第二次点击，交换两个精灵
                            # 保存当前精灵区域状态到撤销栈
                            self.undo_stack.append((self.sprite_rects.copy(), self.detection_areas.copy()))
                            # 交换精灵位置
                            self.sprite_rects[self.swap_start_index], self.sprite_rects[clicked_rect_index] = \
                                self.sprite_rects[clicked_rect_index], self.sprite_rects[self.swap_start_index]
                            
                            # 更新选中索引
                            self.selected_rect_index = clicked_rect_index
                            # 重置交换状态
                            self.swap_start_index = -1
                            # 发射更新信号
                            self.rect_updated.emit()
                            self.rect_selected.emit(self.selected_rect_index)
                            self.update()
                        else:
                            # 点击了同一个精灵，取消选中
                            self.swap_start_index = -1
                            self.selected_rect_index = clicked_rect_index
                            self.update()
                            self.rect_selected.emit(self.selected_rect_index)
                    else:
                        # 普通点击选择
                        self.swap_start_index = -1  # 重置交换状态
                        # 选中精灵区域
                        self.selected_rect_index = clicked_rect_index
                        self.selected_area_index = -1
                        self.hover_area_index = -1
                        
                        # 检查是否在调整大小的控制点上
                        rect = self.sprite_rects[self.selected_rect_index]
                        direction = self.get_resize_direction(event.pos(), rect)
                        if direction != self.NONE:
                            # 开始调整大小
                            self.is_resizing = True
                            self.resize_direction = direction
                            self.resize_start_pos = event.pos()
                            # 保存当前精灵区域状态到撤销栈
                            self.undo_stack.append((self.sprite_rects.copy(), self.detection_areas.copy()))
                            self.original_rect = QRect(
                                int(rect[0] * self.scale_factor),
                                int(rect[1] * self.scale_factor),
                                int(rect[2] * self.scale_factor),
                                int(rect[3] * self.scale_factor)
                            )
                        else:
                            # 开始拖拽移动
                            self.is_dragging = True
                            self.drag_start_pos = event.pos()
                            # 保存当前精灵区域状态到撤销栈
                            self.undo_stack.append((self.sprite_rects.copy(), self.detection_areas.copy()))
                            self.original_rect = QRect(
                                int(rect[0] * self.scale_factor),
                                int(rect[1] * self.scale_factor),
                                int(rect[2] * self.scale_factor),
                                int(rect[3] * self.scale_factor)
                            )
                    
                    self.update()
                    self.rect_selected.emit(self.selected_rect_index)
                    # 发射检测范围选择信号，表示没有选中检测范围
                    self.detection_area_selected.emit([])
                    return

                # 检测是否点击了检测范围
                clicked_area_index = -1
                for i, rect in enumerate(self.detection_areas):
                    x, y, width, height = rect
                    scaled_x = int(x * self.scale_factor)
                    scaled_y = int(y * self.scale_factor)
                    scaled_width = int(width * self.scale_factor)
                    scaled_height = int(height * self.scale_factor)

                    draw_rect = QRect(scaled_x, scaled_y, scaled_width, scaled_height)
                    if draw_rect.contains(event.pos()):
                        clicked_area_index = i
                        break

                if clicked_area_index != -1:
                    # 选中检测范围
                    self.selected_area_index = clicked_area_index
                    self.selected_rect_index = -1
                    self.hover_rect_index = -1
                    
                    # 检查是否在调整大小的控制点上
                    rect = self.detection_areas[self.selected_area_index]
                    direction = self.get_resize_direction(event.pos(), rect)
                    if direction != self.NONE:
                        # 开始调整大小
                        self.is_resizing = True
                        self.resize_direction = direction
                        self.resize_start_pos = event.pos()
                        # 保存当前检测区域状态到撤销栈
                        self.undo_stack.append(self.detection_areas.copy())
                        self.original_rect = QRect(
                            int(rect[0] * self.scale_factor),
                            int(rect[1] * self.scale_factor),
                            int(rect[2] * self.scale_factor),
                            int(rect[3] * self.scale_factor)
                        )
                    else:
                        # 开始拖拽移动
                        self.is_dragging = True
                        self.drag_start_pos = event.pos()
                        # 保存当前检测区域状态到撤销栈
                        self.undo_stack.append(self.detection_areas.copy())
                        self.original_rect = QRect(
                            int(rect[0] * self.scale_factor),
                            int(rect[1] * self.scale_factor),
                            int(rect[2] * self.scale_factor),
                            int(rect[3] * self.scale_factor)
                        )
                    
                    self.update()
                    # 发射检测范围选择信号
                    self.detection_area_selected.emit([self.selected_area_index])
                    return

                # 没有选中任何区域，清除选择
                self.selected_rect_index = -1
                self.selected_area_index = -1
                self.rect_selected.emit(-1)
                self.detection_area_selected.emit([])
                self.update()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件，用于完成选框绘制或调整大小"""
        if event.button() == Qt.LeftButton:
            if self.is_resizing:
                # 完成调整大小
                self.is_resizing = False
                self.resize_direction = self.NONE
                self.setCursor(Qt.ArrowCursor)
                self.rect_updated.emit()
            elif self.is_dragging:
                # 完成拖拽移动
                self.is_dragging = False
                self.setCursor(Qt.ArrowCursor)
                self.rect_updated.emit()
            elif self.drawing_mode and self.is_drawing:
                self.is_drawing = False
                # 计算选框的实际坐标（考虑缩放因子）
                if not self.current_rect.isNull() and self.current_rect.width() > 5 and self.current_rect.height() > 5:
                    # 获取选框的左上角和右下角坐标
                    top_left = self.current_rect.topLeft()
                    bottom_right = self.current_rect.bottomRight()

                    # 转换为原始图片坐标
                    orig_x = int(top_left.x() / self.scale_factor)
                    orig_y = int(top_left.y() / self.scale_factor)
                    orig_width = int(self.current_rect.width() / self.scale_factor)
                    orig_height = int(self.current_rect.height() / self.scale_factor)

                    # 添加新的选框
                    self.add_rect((orig_x, orig_y, orig_width, orig_height))

                # 重置当前绘制的选框
                self.current_rect = QRect()
                self.update()
            elif self.drawing_area_mode and self.is_drawing:
                self.is_drawing = False
                # 计算检测范围的实际坐标（考虑缩放因子）
                if not self.current_rect.isNull() and self.current_rect.width() > 5 and self.current_rect.height() > 5:
                    # 获取选框的左上角和右下角坐标
                    top_left = self.current_rect.topLeft()
                    bottom_right = self.current_rect.bottomRight()

                    # 转换为原始图片坐标
                    orig_x = int(top_left.x() / self.scale_factor)
                    orig_y = int(top_left.y() / self.scale_factor)
                    orig_width = int(self.current_rect.width() / self.scale_factor)
                    orig_height = int(self.current_rect.height() / self.scale_factor)

                    # 添加新的检测范围
                    self.add_detection_area((orig_x, orig_y, orig_width, orig_height))

                # 重置当前绘制的选框
                self.current_rect = QRect()
                self.update()

    def drag_rect(self, pos):
        """拖拽移动选框"""
        if not self.is_dragging:
            return

        if self.selected_area_index != -1:
            # 移动检测范围
            self.drag_detection_area(pos)
        elif self.selected_rect_index != -1:
            # 移动精灵区域
            self.drag_sprite_rect(pos)
    
    def reorder_rect(self, pos):
        """拖拽重排序精灵"""
        if not self.is_reordering or self.reorder_start_index == -1:
            return
        
        # 检测鼠标当前位置下的精灵索引
        current_index = -1
        for i, rect in enumerate(self.sprite_rects):
            x, y, width, height = rect
            scaled_x = int(x * self.scale_factor)
            scaled_y = int(y * self.scale_factor)
            scaled_width = int(width * self.scale_factor)
            scaled_height = int(height * self.scale_factor)
            
            draw_rect = QRect(scaled_x, scaled_y, scaled_width, scaled_height)
            if draw_rect.contains(pos):
                current_index = i
                break
        
        # 如果鼠标在另一个精灵上，并且与起始索引不同，就交换它们的位置
        if current_index != -1 and current_index != self.reorder_start_index:
            # 交换精灵位置
            self.sprite_rects[self.reorder_start_index], self.sprite_rects[current_index] = \
                self.sprite_rects[current_index], self.sprite_rects[self.reorder_start_index]
            
            # 更新选中的索引
            self.selected_rect_index = current_index
            self.reorder_start_index = current_index
            
            # 发射更新信号
            self.rect_updated.emit()
            self.rect_selected.emit(self.selected_rect_index)
            self.update()

    def drag_sprite_rect(self, pos):
        """拖拽移动精灵区域"""
        # 计算移动距离
        delta_x = pos.x() - self.drag_start_pos.x()
        delta_y = pos.y() - self.drag_start_pos.y()

        # 计算新的矩形
        new_rect = self.original_rect.translated(delta_x, delta_y)

        # 转换为原始坐标
        orig_x = int(new_rect.x() / self.scale_factor)
        orig_y = int(new_rect.y() / self.scale_factor)
        orig_width = int(new_rect.width() / self.scale_factor)
        orig_height = int(new_rect.height() / self.scale_factor)

        # 确保选框不会移出图片边界
        if self.original_pixmap:
            orig_x = max(0, orig_x)
            orig_y = max(0, orig_y)

        # 更新选框
        self.sprite_rects[self.selected_rect_index] = (orig_x, orig_y, orig_width, orig_height)
        self.update()

    def drag_detection_area(self, pos):
        """拖拽移动检测范围"""
        # 计算移动距离
        delta_x = pos.x() - self.drag_start_pos.x()
        delta_y = pos.y() - self.drag_start_pos.y()

        # 计算新的矩形
        new_rect = self.original_rect.translated(delta_x, delta_y)

        # 转换为原始坐标
        orig_x = int(new_rect.x() / self.scale_factor)
        orig_y = int(new_rect.y() / self.scale_factor)
        orig_width = int(new_rect.width() / self.scale_factor)
        orig_height = int(new_rect.height() / self.scale_factor)

        # 确保选框不会移出图片边界
        if self.original_pixmap:
            orig_x = max(0, orig_x)
            orig_y = max(0, orig_y)

        # 更新检测范围
        self.detection_areas[self.selected_area_index] = (orig_x, orig_y, orig_width, orig_height)
        self.update()



    def resize_rect(self, pos):
        """调整选框大小"""
        if not self.is_resizing:
            return

        if self.selected_area_index != -1:
            # 调整检测范围大小
            self.resize_detection_area(pos)
        elif self.selected_rect_index != -1:
            # 调整精灵区域大小
            self.resize_sprite_rect(pos)

    def resize_sprite_rect(self, pos):
        """调整精灵区域大小"""
        # 计算新的矩形
        new_rect = QRect(self.original_rect)

        if self.resize_direction & self.LEFT:
            new_rect.setLeft(pos.x())
        elif self.resize_direction & self.RIGHT:
            new_rect.setRight(pos.x())

        if self.resize_direction & self.TOP:
            new_rect.setTop(pos.y())
        elif self.resize_direction & self.BOTTOM:
            new_rect.setBottom(pos.y())

        # 确保矩形有效
        new_rect = new_rect.normalized()

        # 确保最小尺寸
        min_size = 10  # 最小尺寸（缩放后）
        if new_rect.width() < min_size:
            if self.resize_direction & self.LEFT:
                new_rect.setLeft(new_rect.right() - min_size)
            else:
                new_rect.setRight(new_rect.left() + min_size)

        if new_rect.height() < min_size:
            if self.resize_direction & self.TOP:
                new_rect.setTop(new_rect.bottom() - min_size)
            else:
                new_rect.setBottom(new_rect.top() + min_size)

        # 转换为原始坐标
        orig_x = int(new_rect.x() / self.scale_factor)
        orig_y = int(new_rect.y() / self.scale_factor)
        orig_width = int(new_rect.width() / self.scale_factor)
        orig_height = int(new_rect.height() / self.scale_factor)

        # 确保选框不会移出图片边界
        if self.original_pixmap:
            orig_width = max(1, orig_width)
            orig_height = max(1, orig_height)

        # 更新选框
        self.sprite_rects[self.selected_rect_index] = (orig_x, orig_y, orig_width, orig_height)
        self.update()

    def resize_detection_area(self, pos):
        """调整检测范围大小"""
        # 计算新的矩形
        new_rect = QRect(self.original_rect)

        if self.resize_direction & self.LEFT:
            new_rect.setLeft(pos.x())
        elif self.resize_direction & self.RIGHT:
            new_rect.setRight(pos.x())

        if self.resize_direction & self.TOP:
            new_rect.setTop(pos.y())
        elif self.resize_direction & self.BOTTOM:
            new_rect.setBottom(pos.y())

        # 确保矩形有效
        new_rect = new_rect.normalized()

        # 确保最小尺寸
        min_size = 10  # 最小尺寸（缩放后）
        if new_rect.width() < min_size:
            if self.resize_direction & self.LEFT:
                new_rect.setLeft(new_rect.right() - min_size)
            else:
                new_rect.setRight(new_rect.left() + min_size)

        if new_rect.height() < min_size:
            if self.resize_direction & self.TOP:
                new_rect.setTop(new_rect.bottom() - min_size)
            else:
                new_rect.setBottom(new_rect.top() + min_size)

        # 转换为原始坐标
        orig_x = int(new_rect.x() / self.scale_factor)
        orig_y = int(new_rect.y() / self.scale_factor)
        orig_width = int(new_rect.width() / self.scale_factor)
        orig_height = int(new_rect.height() / self.scale_factor)

        # 更新检测范围
        self.detection_areas[self.selected_area_index] = (orig_x, orig_y, orig_width, orig_height)
        self.update()

    def remove_selected_rect(self):
        """删除选中的精灵区域"""
        if self.selected_rect_index != -1:
            del self.sprite_rects[self.selected_rect_index]
            self.selected_rect_index = -1
            self.hover_rect_index = -1
            self.rect_updated.emit()
            self.update()

    def remove_selected_detection_area(self):
        """删除选中的检测范围"""
        if self.selected_area_index != -1:
            del self.detection_areas[self.selected_area_index]
            self.selected_area_index = -1
            self.hover_area_index = -1
            self.update()

    def add_rect(self, rect):
        """添加新的精灵区域"""
        self.sprite_rects.append(rect)
        self.rect_updated.emit()
        self.update()

    def add_detection_area(self, rect):
        """添加新的检测范围"""
        self.detection_areas.append(rect)
        self.update()

    def get_detection_areas(self):
        """获取所有检测范围"""
        return self.detection_areas

    def get_resize_direction(self, pos, rect):
        """检测鼠标是否在选框的调整大小控制点上"""
        # 将原始坐标转换为缩放后的坐标
        x, y, width, height = rect
        scaled_x = int(x * self.scale_factor)
        scaled_y = int(y * self.scale_factor)
        scaled_width = int(width * self.scale_factor)
        scaled_height = int(height * self.scale_factor)

        draw_rect = QRect(scaled_x, scaled_y, scaled_width, scaled_height)

        # 计算各边的热区
        margin = self.handle_size
        left_margin = QRect(scaled_x - margin, scaled_y, margin * 2, scaled_height)
        right_margin = QRect(scaled_x + scaled_width - margin, scaled_y, margin * 2, scaled_height)
        top_margin = QRect(scaled_x, scaled_y - margin, scaled_width, margin * 2)
        bottom_margin = QRect(scaled_x, scaled_y + scaled_height - margin, scaled_width, margin * 2)

        direction = self.NONE

        if left_margin.contains(pos):
            direction |= self.LEFT
        elif right_margin.contains(pos):
            direction |= self.RIGHT

        if top_margin.contains(pos):
            direction |= self.TOP
        elif bottom_margin.contains(pos):
            direction |= self.BOTTOM

        return direction

    def set_cursor_by_direction(self, direction):
        """根据调整方向设置鼠标指针"""
        if direction == self.NONE:
            self.setCursor(Qt.ArrowCursor)
        elif direction == self.LEFT or direction == self.RIGHT:
            self.setCursor(Qt.SizeHorCursor)
        elif direction == self.TOP or direction == self.BOTTOM:
            self.setCursor(Qt.SizeVerCursor)
        elif direction in (self.TOP_LEFT, self.BOTTOM_RIGHT):
            self.setCursor(Qt.SizeFDiagCursor)
        elif direction in (self.TOP_RIGHT, self.BOTTOM_LEFT):
            self.setCursor(Qt.SizeBDiagCursor)

    def draw_handles(self, painter, rect):
        """绘制调整大小的控制点"""
        x, y, width, height = rect
        scaled_x = int(x * self.scale_factor)
        scaled_y = int(y * self.scale_factor)
        scaled_width = int(width * self.scale_factor)
        scaled_height = int(height * self.scale_factor)

        # 控制点的位置
        handle_positions = [
            QPoint(scaled_x, scaled_y),  # 左上角
            QPoint(scaled_x + scaled_width // 2, scaled_y),  # 上中
            QPoint(scaled_x + scaled_width, scaled_y),  # 右上角
            QPoint(scaled_x, scaled_y + scaled_height // 2),  # 左中
            QPoint(scaled_x + scaled_width, scaled_y + scaled_height // 2),  # 右中
            QPoint(scaled_x, scaled_y + scaled_height),  # 左下角
            QPoint(scaled_x + scaled_width // 2, scaled_y + scaled_height),  # 下中
            QPoint(scaled_x + scaled_width, scaled_y + scaled_height)  # 右下角
        ]

        # 绘制控制点
        for pos in handle_positions:
            # 绘制填充矩形
            painter.fillRect(
                pos.x() - self.handle_size // 2,
                pos.y() - self.handle_size // 2,
                self.handle_size,
                self.handle_size,
                QBrush(QColor(255, 255, 255))
            )
            # 绘制边框（先保存当前画笔，设置新画笔，绘制后恢复）
            old_pen = painter.pen()
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.drawRect(
                pos.x() - self.handle_size // 2 - 1,
                pos.y() - self.handle_size // 2 - 1,
                self.handle_size + 1,
                self.handle_size + 1
            )
            painter.setPen(old_pen)

    def resizeEvent(self, event):
        """窗口大小变化时，保持当前缩放比例"""
        pass

    def wheelEvent(self, event):
        """处理鼠标滚轮事件，实现Ctrl+滚轮缩放"""
        # 检查是否按下了Ctrl键
        if event.modifiers() & Qt.ControlModifier:
            # 获取滚轮的角度变化
            delta = event.angleDelta().y()

            # 计算缩放因子变化
            if delta > 0:
                # 滚轮向上，放大
                new_scale = min(5.0, self.scale_factor + 0.1)
            else:
                # 滚轮向下，缩小
                new_scale = max(0.1, self.scale_factor - 0.1)

            # 更新缩放因子
            self.scale_factor = new_scale

            # 更新画布
            if self.original_pixmap:
                scaled_pixmap = self.original_pixmap.scaled(
                    int(self.original_pixmap.width() * new_scale),
                    int(self.original_pixmap.height() * new_scale),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.setPixmap(scaled_pixmap)
                self.update()

            # 发射缩放变化信号
            self.scale_changed.emit(new_scale)
    
    def keyPressEvent(self, event):
        """处理键盘按下事件"""
        if event.key() == Qt.Key_Shift:
            self.is_shift_pressed = True
    
    def keyReleaseEvent(self, event):
        """处理键盘释放事件"""
        if event.key() == Qt.Key_Shift:
            self.is_shift_pressed = False
            # 释放Shift键时，重置交换状态
            self.swap_start_index = -1
            self.update()

    def get_selected_rect(self):
        """获取选中的矩形"""
        if self.selected_rect_index != -1:
            return self.sprite_rects[self.selected_rect_index]
        return None
    
    def keyPressEvent(self, event):
        """键盘事件处理"""
        # 处理Ctrl+Z撤销操作
        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Z:
            self.undo_last_action()
    
    def undo_last_action(self):
        """撤销最后一次操作，包括精灵区域和检测区域的移动或调整大小"""
        if self.undo_stack:
            # 恢复上一个状态
            last_state = self.undo_stack.pop()
            
            # 检查状态类型，兼容旧的只包含检测区域的状态
            if isinstance(last_state, tuple):
                # 新状态格式：(sprite_rects, detection_areas)
                self.sprite_rects, self.detection_areas = last_state
            else:
                # 旧状态格式：只包含detection_areas
                self.detection_areas = last_state
            
            self.update()
            self.rect_updated.emit()


class SpriteSplitterGUI(QMainWindow):
    """智能精灵图切分工具的图形界面"""

    def __init__(self):
        super().__init__()
        # 初始化语言字典
        self.language_dict = self.load_language_dict()
        self.current_language = 'zh_CN'  # 默认中文
        self.init_ui()
        self.image_path = None
        self.sprite_detector = None
        self.detection_thread = None

    def load_language_dict(self):
        """从JSON文件加载语言字典"""
        language_file = os.path.join("translations", "languages_SpriteSheet2Sprite.json")
        try:
            with open(language_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"无法加载语言文件: {e}")
            # 如果加载失败，返回默认的语言字典
            return {
                'zh_CN': {
                    'window_title': '智能精灵图切分工具',
                    'language': '语言:',
                    'sprite_preview': '精灵预览',
                    'select_image': '选择图片',
                    'detect_sprites': '检测精灵',
                    'add_rect': '添加选框',
                    'remove_rect': '删除选中边框',
                    'start_split': '导出分割结果',
                    'control_options': '控制选项',
                    'auto_detection_threshold': '自动检测阈值:',
                    'image_path': '图片路径:',
                    'no_image_selected': '未选择图片',
                    'output_directory': '输出目录:',
                    'browse': '浏览',
                    'sprite_count': '精灵数量:',
                    'scale': '缩放比例:',
                    'select_sprite_image': '选择精灵图',
                    'select_output_directory': '选择输出目录',
                    'warning': '警告',
                    'please_select_image_first': '请先选择图片',
                    'success': '成功',
                    'detection_completed': '检测完成！共检测到 {0} 个精灵',
                    'no_sprite_regions_detected': '没有检测到精灵区域',
                    'splitting_completed': '分割完成！共生成 {0} 个精灵图片',
                    'error': '错误',
                    'splitting_failed': '分割失败：{0}',
                    'transparent_background': '透明化背景',
                    'export_by_detection_area': '按检测区域为组导出（序号重新编号）',
                    'add_detection_area': '添加检测范围',
                    'remove_detection_area': '删除选中检测范围',
                    'clear_detection_areas': '清除所有检测范围',
                    'operation_tip': '按住 Shift 键 + 依次点击两次精灵可交换序号'
                },
                'en_US': {
                    'window_title': 'Smart Sprite Splitter',
                    'language': 'Language:',
                    'sprite_preview': 'Sprite Preview',
                    'select_image': 'Select Image',
                    'detect_sprites': 'Detect Sprites',
                    'add_rect': 'Add Rectangle',
                    'remove_rect': 'Delete Selected Rectangle',
                    'start_split': 'Start Splitting',
                    'control_options': 'Control Options',
                    'auto_detection_threshold': 'Auto Detection Threshold:',
                    'image_path': 'Image Path:',
                    'no_image_selected': 'No Image Selected',
                    'output_directory': 'Output Directory:',
                    'browse': 'Browse',
                    'sprite_count': 'Sprite Count:',
                    'scale': 'Scale:',
                    'select_sprite_image': 'Select Sprite Image',
                    'select_output_directory': 'Select Output Directory',
                    'warning': 'Warning',
                    'please_select_image_first': 'Please select an image first',
                    'success': 'Success',
                    'detection_completed': 'Detection completed! Found {0} sprites',
                    'no_sprite_regions_detected': 'No sprite regions detected',
                    'splitting_completed': 'Splitting completed! Generated {0} sprite images',
                    'error': 'Error',
                    'splitting_failed': 'Splitting failed: {0}',
                    'transparent_background': 'Transparent Background',
                    'export_by_detection_area': 'Export by Detection Area (Renumber sequentially)',
                    'add_detection_area': 'Add Detection Area',
                    'remove_detection_area': 'Delete Selected Detection Area',
                    'clear_detection_areas': 'Clear All Detection Areas',
                    'operation_tip': 'Hold Shift key + click twice on sprites\nTo swap sprite indexes'
                }
            }

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(self.language_dict[self.current_language]['window_title'])
        self.setGeometry(100, 100, 1000, 700)

        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局 - 水平布局，左侧图片区，右侧按钮控制区
        main_layout = QHBoxLayout(central_widget)

        # 左侧：图片预览区域（占据3/4宽度）
        left_layout = QVBoxLayout()
        main_layout.addLayout(left_layout, 3)

        # 预览区域
        self.preview_group = QGroupBox(self.language_dict[self.current_language]['sprite_preview'])
        preview_layout = QVBoxLayout(self.preview_group)

        # 滚动区域，用于显示大图片
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # 精灵画布
        self.canvas = SpriteCanvas()
        scroll_area.setWidget(self.canvas)
        preview_layout.addWidget(scroll_area)

        left_layout.addWidget(self.preview_group, 1)

        # 右侧：按钮和控制区域（占据1/4宽度）
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 1)

        # 语言选择布局
        language_layout = QHBoxLayout()
        language_layout.addStretch()
        self.language_label = QLabel(self.language_dict[self.current_language]['language'])
        language_layout.addWidget(self.language_label)
        self.language_combo = QComboBox()
        self.language_combo.addItem("中文", "zh_CN")
        self.language_combo.addItem("English", "en_US")
        self.language_combo.currentIndexChanged.connect(self.switch_language)
        language_layout.addWidget(self.language_combo)
        right_layout.addLayout(language_layout)

        # 主要功能按钮区域 - 垂直布局
        main_buttons_layout = QVBoxLayout()

        # 选择图片按钮
        self.select_image_btn = QPushButton(self.language_dict[self.current_language]['select_image'])
        self.select_image_btn.clicked.connect(self.select_image)
        self.nobody_label_1 = QLabel("")
        main_buttons_layout.addWidget(self.select_image_btn)
        main_buttons_layout.addWidget(self.nobody_label_1)


        # 检测范围管理按钮
        self.add_detection_area_btn = QPushButton(self.language_dict[self.current_language]['add_detection_area'])
        self.add_detection_area_btn.clicked.connect(self.toggle_drawing_area_mode)
        self.add_detection_area_btn.setCheckable(True)  # 可切换状态
        self.add_detection_area_btn.setEnabled(False)  # 初始禁用
        main_buttons_layout.addWidget(self.add_detection_area_btn)

        self.remove_detection_area_btn = QPushButton(self.language_dict[self.current_language]['remove_detection_area'])
        self.remove_detection_area_btn.clicked.connect(self.remove_selected_detection_area)
        self.remove_detection_area_btn.setEnabled(False)  # 初始禁用
        main_buttons_layout.addWidget(self.remove_detection_area_btn)

        self.clear_detection_areas_btn = QPushButton(self.language_dict[self.current_language]['clear_detection_areas'])
        self.clear_detection_areas_btn.clicked.connect(self.clear_detection_areas)
        main_buttons_layout.addWidget(self.clear_detection_areas_btn)

        self.nobody_label_2 = QLabel("")
        main_buttons_layout.addWidget(self.nobody_label_2)

        self.detect_sprites_btn = QPushButton(self.language_dict[self.current_language]['detect_sprites'])
        self.detect_sprites_btn.clicked.connect(self.detect_sprites)
        main_buttons_layout.addWidget(self.detect_sprites_btn)

        self.add_rect_btn = QPushButton(self.language_dict[self.current_language]['add_rect'])
        self.add_rect_btn.clicked.connect(self.toggle_drawing_mode)
        self.add_rect_btn.setCheckable(True)  # 可切换状态
        main_buttons_layout.addWidget(self.add_rect_btn)

        self.remove_rect_btn = QPushButton(self.language_dict[self.current_language]['remove_rect'])
        self.remove_rect_btn.clicked.connect(self.remove_selected_rect)
        self.remove_rect_btn.setEnabled(False)  # 初始禁用
        main_buttons_layout.addWidget(self.remove_rect_btn)

        self.clear_all_rects_btn = QPushButton(self.language_dict[self.current_language]['clear_all_rects'])
        self.clear_all_rects_btn.clicked.connect(self.clear_all_rects)
        main_buttons_layout.addWidget(self.clear_all_rects_btn)

        # 添加操作提示标签
        self.operation_tip_label = QLabel(self.language_dict[self.current_language]['operation_tip'])
        self.operation_tip_label.setStyleSheet("color: #666; background-color: #f5f5f5; padding: 8px; border-radius: 4px;")
        self.operation_tip_label.setWordWrap(True)
        main_buttons_layout.addWidget(self.operation_tip_label)

        self.nobody_label_3 = QLabel("")
        main_buttons_layout.addWidget(self.nobody_label_3)

        self.start_split_btn = QPushButton(self.language_dict[self.current_language]['start_split'])
        self.start_split_btn.clicked.connect(self.start_split)
        main_buttons_layout.addWidget(self.start_split_btn)


        # 控制区域
        self.control_group = QGroupBox(self.language_dict[self.current_language]['control_options'])
        control_layout = QVBoxLayout(self.control_group)

        # 检测阈值
        threshold_layout = QHBoxLayout()
        self.threshold_label = QLabel(self.language_dict[self.current_language]['auto_detection_threshold'])
        threshold_layout.addWidget(self.threshold_label)
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(10, 200)
        self.threshold_spin.setValue(50)
        threshold_layout.addWidget(self.threshold_spin)
        control_layout.addLayout(threshold_layout)

        # 图片路径显示
        path_layout = QHBoxLayout()
        self.image_path_label_text = QLabel(self.language_dict[self.current_language]['image_path'])
        path_layout.addWidget(self.image_path_label_text)
        self.image_path_label = QLabel(self.language_dict[self.current_language]['no_image_selected'])
        self.image_path_label.setWordWrap(True)
        path_layout.addWidget(self.image_path_label)
        control_layout.addLayout(path_layout)

        # 输出目录
        output_layout = QHBoxLayout()
        self.output_dir_label = QLabel(self.language_dict[self.current_language]['output_directory'])
        output_layout.addWidget(self.output_dir_label)
        self.output_dir_edit = QLineEdit("output")
        output_layout.addWidget(self.output_dir_edit)

        self.browse_btn = QPushButton(self.language_dict[self.current_language]['browse'])
        self.browse_btn.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(self.browse_btn)
        control_layout.addLayout(output_layout)

        # 精灵区域列表
        rects_layout = QHBoxLayout()
        self.rect_count_label_text = QLabel(self.language_dict[self.current_language]['sprite_count'])
        rects_layout.addWidget(self.rect_count_label_text)
        self.rect_count_label = QLabel("0")
        rects_layout.addWidget(self.rect_count_label)
        control_layout.addLayout(rects_layout)

        # 缩放控制
        scale_layout = QHBoxLayout()
        self.scale_label_text = QLabel(self.language_dict[self.current_language]['scale'])
        scale_layout.addWidget(self.scale_label_text)

        # 缩放滑动条
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(10, 500)
        self.scale_slider.setValue(100)
        self.scale_slider.setTickPosition(QSlider.TicksBelow)
        self.scale_slider.setTickInterval(50)
        scale_layout.addWidget(self.scale_slider)

        # 缩放比例显示
        self.scale_label = QLabel("100%")
        scale_layout.addWidget(self.scale_label)

        control_layout.addLayout(scale_layout)

        # 透明化背景选项
        transparent_layout = QHBoxLayout()
        self.transparent_checkbox = QCheckBox(self.language_dict[self.current_language]['transparent_background'])
        self.transparent_checkbox.setChecked(True)
        transparent_layout.addWidget(self.transparent_checkbox)
        control_layout.addLayout(transparent_layout)

        # 按检测区域为组导出选项
        export_by_area_layout = QHBoxLayout()
        self.export_by_area_checkbox = QCheckBox(self.language_dict[self.current_language]['export_by_detection_area'])
        self.export_by_area_checkbox.setChecked(False)
        export_by_area_layout.addWidget(self.export_by_area_checkbox)
        control_layout.addLayout(export_by_area_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
            
        # 将按钮布局和控制区域添加到右侧布局
        right_layout.addLayout(main_buttons_layout)
        right_layout.addWidget(self.control_group)
        right_layout.addStretch()  # 底部拉伸，使控件顶部对齐

        # 连接信号槽
        self.scale_slider.valueChanged.connect(self.on_scale_changed)
        self.canvas.rect_selected.connect(self.on_rect_selected)
        self.canvas.rect_updated.connect(self.on_rect_updated)
        self.canvas.scale_changed.connect(self.on_canvas_scale_changed)
        self.canvas.detection_area_selected.connect(self.on_detection_area_selected)

    def select_image(self):
        """选择图片文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, self.language_dict[self.current_language]['select_sprite_image'], ".", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if file_path:
            self.image_path = file_path
            self.image_path_label.setText(file_path)
            self.canvas.set_image(file_path)
            self.add_detection_area_btn.setEnabled(True)

    def browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, self.language_dict[self.current_language]['select_output_directory'], ".", QFileDialog.ShowDirsOnly
        )

        if dir_path:
            self.output_dir_edit.setText(dir_path)

    def detect_sprites(self):
        """开始检测精灵"""
        if not self.image_path:
            QMessageBox.warning(self, self.language_dict[self.current_language]['warning'],
                                self.language_dict[self.current_language]['please_select_image_first'])
            return

        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 获取检测范围
        detection_areas = self.canvas.get_detection_areas()

        # 创建精灵检测器
        self.sprite_detector = SpriteDetector(self.image_path, threshold=self.threshold_spin.value(), detection_areas=detection_areas)
        self.sprite_detector.progress_updated.connect(self.update_progress)
        self.sprite_detector.detection_finished.connect(self.on_detection_finished)

        # 在新线程中执行检测，避免阻塞UI
        self.detection_thread = QThread()
        self.sprite_detector.moveToThread(self.detection_thread)
        self.detection_thread.started.connect(self.sprite_detector.detect_sprites)
        self.detection_thread.start()

    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)

    def on_detection_finished(self, rects):
        """检测完成处理"""
        self.progress_bar.setVisible(False)
        
        # 对检测到的精灵区域进行排序：从上到下，从左到右
        if rects:
            # 1. 先按精灵中心点的Y坐标进行初步排序，确定大致的上下顺序
            rects.sort(key=lambda rect: rect[1] + rect[3]/2)
            
            # 2. 计算每个精灵的高度和中心点
            heights = [rect[3] for rect in rects]
            avg_height = sum(heights) / len(heights)
            
            # 3. 更智能的容差计算：使用平均高度的70%，容差更大
            tolerance = avg_height * 0.7
            
            # 4. 使用更精确的行分组算法：排序后相邻分组
            rows = []
            current_row = []
            
            for rect in rects:
                rect_center_y = rect[1] + rect[3]/2
                
                if not current_row:
                    # 第一行的第一个精灵
                    current_row.append(rect)
                else:
                    # 计算当前行的平均中心Y坐标
                    row_center_y = sum(r[1] + r[3]/2 for r in current_row) / len(current_row)
                    
                    # 如果当前精灵的中心Y坐标与行平均中心Y坐标的差在容差范围内，则加入当前行
                    if abs(rect_center_y - row_center_y) <= tolerance:
                        current_row.append(rect)
                    else:
                        # 否则创建新行
                        rows.append(current_row)
                        current_row = [rect]
            
            # 处理最后一行
            if current_row:
                rows.append(current_row)
            
            # 5. 对每一行内的精灵按中心点X坐标排序，实现从左到右
            sorted_rects = []
            for row in rows:
                # 同一行内按中心点X坐标排序
                row.sort(key=lambda rect: rect[0] + rect[2]/2)
                sorted_rects.extend(row)
            
            rects = sorted_rects
        
        self.canvas.set_sprite_rects(rects)
        self.rect_count_label.setText(str(len(rects)))
        self.detection_thread.quit()
        self.detection_thread.wait()

        QMessageBox.information(self, self.language_dict[self.current_language]['success'],
                               self.language_dict[self.current_language]['detection_completed'].format(len(rects)))



    def start_split(self):
        """导出分割结果精灵"""
        if not self.image_path:
            QMessageBox.warning(self, self.language_dict[self.current_language]['warning'],
                                self.language_dict[self.current_language]['please_select_image_first'])
            return

        sprite_rects = self.canvas.sprite_rects
        if not sprite_rects:
            QMessageBox.warning(self, self.language_dict[self.current_language]['warning'],
                                self.language_dict[self.current_language]['no_sprite_regions_detected'])
            return

        try:
            with Image.open(self.image_path) as img:
                # 创建输出目录
                output_dir = self.output_dir_edit.text()
                os.makedirs(output_dir, exist_ok=True)

                # 检测背景颜色（如果需要透明化背景）
                bg_color = None
                if self.transparent_checkbox.isChecked():
                    # 转换为RGBA模式以便处理
                    img = img.convert('RGBA')
                    bg_color = self._detect_background_color(img)
                else:
                    # 确保图像是RGBA模式，以便后续处理
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')

                # 获取检测区域
                detection_areas = self.canvas.get_detection_areas()
                
                # 分割精灵
                base_name = os.path.splitext(os.path.basename(self.image_path))[0]
                
                # 检查是否按检测区域为组导出
                export_by_area = self.export_by_area_checkbox.isChecked()
                
                # 为每个检测区域创建子文件夹（如果需要）
                area_counters = {}
                if export_by_area and detection_areas:
                    for i, area in enumerate(detection_areas):
                        area_folder = os.path.join(output_dir, f"A{i+1}")
                        os.makedirs(area_folder, exist_ok=True)
                        area_counters[i] = 0
                
                # 遍历所有精灵
                for i, rect in enumerate(sprite_rects):
                    x, y, width, height = rect
                    sprite = img.crop((x, y, x + width, y + height))
                    
                    # 如果需要透明化背景，处理精灵图像
                    if bg_color:
                        sprite = self._make_background_transparent(sprite, bg_color)
                    
                    # 确定输出路径
                    if export_by_area and detection_areas:
                        # 确定精灵所属的检测区域
                        area_index = -1
                        # 计算精灵中心点
                        sprite_center_x = x + width / 2
                        sprite_center_y = y + height / 2
                        
                        # 检查精灵中心点是否在某个检测区域内
                        for j, area in enumerate(detection_areas):
                            area_x, area_y, area_width, area_height = area
                            if area_x <= sprite_center_x < area_x + area_width and area_y <= sprite_center_y < area_y + area_height:
                                area_index = j
                                break
                        
                        if area_index != -1:
                            # 精灵属于某个检测区域，保存到对应的子文件夹
                            area_folder = os.path.join(output_dir, f"A{area_index+1}")
                            area_counters[area_index] += 1
                            counter = area_counters[area_index]
                            output_path = os.path.join(area_folder, f"{base_name}_{counter:04d}.png")
                        else:
                            # 精灵不属于任何检测区域，直接保存到输出目录
                            output_path = os.path.join(output_dir, f"{base_name}_{i+1:04d}.png")
                    else:
                        # 不按检测区域导出，直接按序号逐一导出
                        output_path = os.path.join(output_dir, f"{base_name}_{i+1:04d}.png")
                    
                    sprite.save(output_path)

            QMessageBox.information(self, self.language_dict[self.current_language]['success'],
                               self.language_dict[self.current_language]['splitting_completed'].format(len(sprite_rects)))
        except Exception as e:
            QMessageBox.critical(self, self.language_dict[self.current_language]['error'],
                               self.language_dict[self.current_language]['splitting_failed'].format(str(e)))

    def _detect_background_color(self, img):
        """自动检测背景颜色"""
        # 采样四个角落的像素，取出现最多的颜色作为背景色
        width, height = img.size
        corners = [
            img.getpixel((0, 0)),
            img.getpixel((width-1, 0)),
            img.getpixel((0, height-1)),
            img.getpixel((width-1, height-1))
        ]

        # 统计每个颜色出现的次数
        color_counts = {}
        for color in corners:
            if color in color_counts:
                color_counts[color] += 1
            else:
                color_counts[color] = 1

        # 返回出现次数最多的颜色
        return max(color_counts, key=color_counts.get)

    def _make_background_transparent(self, img, bg_color, threshold=50):
        """将背景颜色转换为透明"""
        # 确保图像是RGBA模式
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        pixels = img.load()
        width, height = img.size
        
        # 遍历所有像素
        for y in range(height):
            for x in range(width):
                pixel_color = pixels[x, y]
                # 如果当前像素与背景颜色相似，设置为透明
                if self._is_similar_color(pixel_color, bg_color, threshold):
                    pixels[x, y] = (0, 0, 0, 0)  # 设置为透明
        
        return img
    
    def _is_similar_color(self, color1, color2, threshold):
        """判断两种颜色是否相似"""
        # 计算RGB三个通道的欧氏距离
        distance = sum(
            (a - b) ** 2 for a, b in zip(color1[:3], color2[:3])
        ) ** 0.5
        
        return distance < threshold

    def on_rect_selected(self, index):
        """处理矩形选中信号"""
        # 启用或禁用删除按钮
        self.remove_rect_btn.setEnabled(index != -1)

    def on_rect_updated(self):
        """处理矩形更新信号"""
        # 更新精灵数量显示
        self.rect_count_label.setText(str(len(self.canvas.sprite_rects)))
        # 如果没有选中的矩形，禁用删除按钮
        if self.canvas.selected_rect_index == -1:
            self.remove_rect_btn.setEnabled(False)

    def on_detection_area_selected(self, indexes):
        """处理检测范围选择信号"""
        # 启用或禁用删除检测范围按钮
        self.remove_detection_area_btn.setEnabled(len(indexes) > 0)

    def toggle_drawing_mode(self, checked):
        """切换绘制模式"""
        self.canvas.set_drawing_mode(checked)
        # 如果进入绘制模式，取消当前选中的边框
        if checked:
            self.canvas.selected_rect_index = -1
            self.canvas.hover_rect_index = -1
            self.canvas.rect_selected.emit(-1)
            self.canvas.update()

    def toggle_drawing_area_mode(self, checked):
        """切换绘制检测范围模式"""
        self.canvas.set_drawing_area_mode(checked)
        # 如果进入绘制模式，取消当前选中的边框
        if checked:
            self.canvas.selected_rect_index = -1
            self.canvas.selected_area_index = -1
            self.canvas.hover_rect_index = -1
            self.canvas.hover_area_index = -1
            self.canvas.rect_selected.emit(-1)
            self.canvas.update()
            self.remove_rect_btn.setEnabled(False)
            self.remove_detection_area_btn.setEnabled(False)

    def remove_selected_rect(self):
        """删除选中的边框"""
        self.canvas.remove_selected_rect()

    def clear_all_rects(self):
        """清除所有边框"""
        self.canvas.sprite_rects = []
        self.canvas.selected_rect_index = -1
        self.canvas.hover_rect_index = -1
        self.canvas.rect_selected.emit(-1)
        self.canvas.update()
        self.rect_count_label.setText("0")
        self.remove_rect_btn.setEnabled(False)

    def remove_selected_detection_area(self):
        """删除选中的检测范围"""
        self.canvas.remove_selected_detection_area()
        self.remove_detection_area_btn.setEnabled(False)

    def clear_detection_areas(self):
        """清除所有检测范围"""
        self.canvas.detection_areas = []
        self.canvas.selected_area_index = -1
        self.canvas.hover_area_index = -1
        self.canvas.update()
        self.remove_detection_area_btn.setEnabled(False)

    def on_canvas_scale_changed(self, scale):
        """处理画布缩放变化信号，更新UI控件"""
        # 将缩放因子转换为百分比
        scale_percent = int(scale * 100)
        # 更新缩放滑块和标签
        self.scale_slider.setValue(scale_percent)
        self.scale_label.setText(f"{scale_percent}%")

    def on_scale_changed(self, value):
        """处理缩放比例变化"""
        # 将百分比转换为缩放因子
        scale = value / 100.0
        # 更新缩放标签
        self.scale_label.setText(f"{value}%")
        # 更新画布缩放
        self.canvas.set_scale(scale)

    def switch_language(self):
        """切换语言"""
        language = self.language_combo.currentData()
        if language == self.current_language:
            return

        self.current_language = language

        # 重新翻译界面
        self.retranslate_ui()

    def retranslate_ui(self):
        """重新翻译界面"""
        lang = self.current_language

        # 更新窗口标题
        self.setWindowTitle(self.language_dict[lang]['window_title'])

        # 更新语言标签
        self.language_label.setText(self.language_dict[lang]['language'])

        # 更新分组框标题
        self.preview_group.setTitle(self.language_dict[lang]['sprite_preview'])
        self.control_group.setTitle(self.language_dict[lang]['control_options'])

        # 更新按钮文本
        self.select_image_btn.setText(self.language_dict[lang]['select_image'])
        self.detect_sprites_btn.setText(self.language_dict[lang]['detect_sprites'])
        self.add_rect_btn.setText(self.language_dict[lang]['add_rect'])
        self.remove_rect_btn.setText(self.language_dict[lang]['remove_rect'])
        self.add_detection_area_btn.setText(self.language_dict[lang]['add_detection_area'])
        self.remove_detection_area_btn.setText(self.language_dict[lang]['remove_detection_area'])
        self.clear_detection_areas_btn.setText(self.language_dict[lang]['clear_detection_areas'])
        self.start_split_btn.setText(self.language_dict[lang]['start_split'])
        self.browse_btn.setText(self.language_dict[lang]['browse'])

        # 更新控制选项中的标签
        self.threshold_label.setText(self.language_dict[lang]['auto_detection_threshold'])
        self.image_path_label_text.setText(self.language_dict[lang]['image_path'])
        if not self.image_path:
            self.image_path_label.setText(self.language_dict[lang]['no_image_selected'])
        self.output_dir_label.setText(self.language_dict[lang]['output_directory'])
        self.rect_count_label_text.setText(self.language_dict[lang]['sprite_count'])
        self.scale_label_text.setText(self.language_dict[lang]['scale'])
        self.transparent_checkbox.setText(self.language_dict[lang]['transparent_background'])
        self.export_by_area_checkbox.setText(self.language_dict[lang]['export_by_detection_area'])
        
        # 更新操作提示标签
        self.operation_tip_label.setText(f"\n{self.language_dict[lang]['operation_tip']}")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpriteSplitterGUI()
    window.show()
    sys.exit(app.exec_())
