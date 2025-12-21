import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QListWidget, QFileDialog, QSpinBox, 
    QGroupBox, QMessageBox, QGridLayout, QScrollArea,
    QSplitter, QSlider, QCheckBox, QComboBox
)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QCursor
from PyQt5.QtCore import Qt, QPoint, QRect
from PIL import Image


class SpriteAlignerGUI(QMainWindow):
    """精灵图对齐工具的图形界面"""
    
    def __init__(self):
        super().__init__()
        # 先初始化所有属性
        self.image_files = []  # 存储导入的图片文件路径
        self.selected_index = -1  # 当前选中的图片索引
        self.images_data = []  # 存储图片数据和对齐信息
        self.grid_size = 64  # 默认网格大小
        self.show_grid = True  # 是否显示网格
        self.show_center = True  # 是否显示中心点
        self.ref_index = -1  # 参考图索引
        self.show_ref = False  # 是否显示参考图
        self.ref_opacity = 0.5  # 参考图透明度
        self.zoom_factor = 1.0  # 缩放因子，默认100%
        self.min_zoom = 0.1  # 最小缩放比例
        self.max_zoom = 5.0  # 最大缩放比例
        self.current_image_visible = True  # 当前图片是否可见
        # 然后调用init_ui
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("精灵图对齐工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置快捷键
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        
        # 应用到当前图片：F5
        self.shortcut_apply = QShortcut(QKeySequence("F5"), self)
        self.shortcut_apply.activated.connect(self.apply_auto_align)
        
        # 批量应用到所有图片：Ctrl + F5
        self.shortcut_batch_apply = QShortcut(QKeySequence("Ctrl+F5"), self)
        self.shortcut_batch_apply.activated.connect(self.batch_apply_auto_align)
        
        # 删除图片：Delete
        self.shortcut_delete = QShortcut(QKeySequence("Delete"), self)
        self.shortcut_delete.activated.connect(self.delete_selected_image)
        
        # 显示网格：Ctrl+'（单引号）
        self.shortcut_toggle_grid = QShortcut(QKeySequence("Ctrl+'"), self)
        self.shortcut_toggle_grid.activated.connect(self.toggle_grid_by_shortcut)
        
        # 拼接并保存精灵图：Ctrl + S
        self.shortcut_stitch_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_stitch_save.activated.connect(self.stitch_and_save_sprites)
        
        # 上移：Q
        self.shortcut_move_up = QShortcut(QKeySequence("Q"), self)
        self.shortcut_move_up.activated.connect(self.move_selected_up)
        
        # 下移：E
        self.shortcut_move_down = QShortcut(QKeySequence("E"), self)
        self.shortcut_move_down.activated.connect(self.move_selected_down)
        
        # 设为参考图：F
        self.shortcut_set_reference = QShortcut(QKeySequence("F"), self)
        self.shortcut_set_reference.activated.connect(self.set_selected_as_reference)
        
        # 选择上一张图片：A 或 W
        self.shortcut_prev_image = QShortcut(QKeySequence("A"), self)
        self.shortcut_prev_image.activated.connect(self.select_previous_image)
        self.shortcut_prev_image_w = QShortcut(QKeySequence("W"), self)
        self.shortcut_prev_image_w.activated.connect(self.select_previous_image)
        
        # 选择下一张图片：D 或 S
        self.shortcut_next_image = QShortcut(QKeySequence("D"), self)
        self.shortcut_next_image.activated.connect(self.select_next_image)
        self.shortcut_next_image_s = QShortcut(QKeySequence("S"), self)
        self.shortcut_next_image_s.activated.connect(self.select_next_image)
        
        # 切换参考图可视：C
        self.shortcut_toggle_ref = QShortcut(QKeySequence("C"), self)
        self.shortcut_toggle_ref.activated.connect(self.toggle_reference_by_shortcut)
        
        # Alt + W/A/S/D 调整XY偏移量
        # Alt + W: Y偏移量减少
        self.shortcut_alt_w = QShortcut(QKeySequence("Alt+W"), self)
        self.shortcut_alt_w.activated.connect(lambda: self.adjust_offset(0, -1))
        
        # Alt + S: Y偏移量增加
        self.shortcut_alt_s = QShortcut(QKeySequence("Alt+S"), self)
        self.shortcut_alt_s.activated.connect(lambda: self.adjust_offset(0, 1))
        
        # Alt + A: X偏移量减少
        self.shortcut_alt_a = QShortcut(QKeySequence("Alt+A"), self)
        self.shortcut_alt_a.activated.connect(lambda: self.adjust_offset(-1, 0))
        
        # Alt + D: X偏移量增加
        self.shortcut_alt_d = QShortcut(QKeySequence("Alt+D"), self)
        self.shortcut_alt_d.activated.connect(lambda: self.adjust_offset(1, 0))
        
        # 切换当前图片显示：H
        self.shortcut_toggle_current_image = QShortcut(QKeySequence("H"), self)
        self.shortcut_toggle_current_image.activated.connect(self.toggle_current_image_by_shortcut)
        
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部控制区域
        control_group = QGroupBox("控制选项")
        control_layout = QGridLayout(control_group)
        # 限制控制选项区域的最大高度
        control_group.setMaximumHeight(180)
        
        # 导入图片按钮
        self.import_btn = QPushButton("导入分割图片")
        self.import_btn.clicked.connect(self.import_images)
        control_layout.addWidget(self.import_btn, 0, 0)
        
        # 网格大小设置
        control_layout.addWidget(QLabel("网格大小:"), 0, 1)
        self.grid_spin = QSpinBox()
        self.grid_spin.setRange(8, 256)
        self.grid_spin.setValue(64)
        self.grid_spin.valueChanged.connect(self.update_grid_size)
        control_layout.addWidget(self.grid_spin, 0, 2)
        
        # 显示选项
        self.grid_check = QCheckBox("显示网格 (Ctrl+')")
        self.grid_check.setChecked(True)
        self.grid_check.stateChanged.connect(self.toggle_grid)
        control_layout.addWidget(self.grid_check, 0, 3)
        
        self.center_check = QCheckBox("显示中心点")
        self.center_check.setChecked(True)
        self.center_check.stateChanged.connect(self.toggle_center)
        control_layout.addWidget(self.center_check, 0, 4)
        
        # 当前图片显示选项
        self.current_image_check = QCheckBox("显示当前图片 (H)")
        self.current_image_check.setChecked(True)
        self.current_image_check.stateChanged.connect(self.toggle_current_image)
        control_layout.addWidget(self.current_image_check, 0, 5)
        
        # 参考图选项
        control_layout.addWidget(QLabel("参考图:"), 1, 0)
        self.ref_combo = QComboBox()
        self.ref_combo.setEnabled(False)
        self.ref_combo.currentIndexChanged.connect(self.set_reference_image)
        control_layout.addWidget(self.ref_combo, 1, 1, 1, 2)
        
        self.ref_check = QCheckBox("显示参考图 (C)")
        self.ref_check.setChecked(False)
        self.ref_check.stateChanged.connect(self.toggle_reference)
        self.ref_check.setEnabled(False)
        control_layout.addWidget(self.ref_check, 1, 3)
        
        # 参考图透明度
        control_layout.addWidget(QLabel("参考图透明度:"), 2, 0)
        self.ref_opacity_slider = QSlider(Qt.Horizontal)
        self.ref_opacity_slider.setRange(10, 100)
        self.ref_opacity_slider.setValue(50)
        self.ref_opacity_slider.setEnabled(False)
        self.ref_opacity_slider.valueChanged.connect(self.update_ref_opacity)
        control_layout.addWidget(self.ref_opacity_slider, 2, 1, 1, 3)
        
        self.ref_opacity_label = QLabel("50%")
        control_layout.addWidget(self.ref_opacity_label, 2, 4)
        
        # 工作区缩放控制
        control_layout.addWidget(QLabel("工作区缩放:"), 3, 0)
        zoom_layout = QHBoxLayout()
        
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_out_btn.setEnabled(False)
        zoom_layout.addWidget(self.zoom_out_btn)
        
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(int(self.min_zoom * 100), int(self.max_zoom * 100))
        self.zoom_slider.setValue(int(self.zoom_factor * 100))
        self.zoom_slider.setEnabled(False)
        self.zoom_slider.valueChanged.connect(self.update_zoom)
        zoom_layout.addWidget(self.zoom_slider, 1)
        
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_in_btn.setEnabled(False)
        zoom_layout.addWidget(self.zoom_in_btn)
        
        self.reset_zoom_btn = QPushButton("重置缩放")
        self.reset_zoom_btn.clicked.connect(self.reset_zoom)
        self.reset_zoom_btn.setEnabled(False)
        zoom_layout.addWidget(self.reset_zoom_btn)
        
        self.zoom_label = QLabel("100%")
        zoom_layout.addWidget(self.zoom_label)
        
        control_layout.addLayout(zoom_layout, 3, 1, 1, 4)
        
        # 中间工作区域
        work_layout = QHBoxLayout()
        
        # 左侧图片列表
        list_group = QGroupBox("图片列表")
        list_layout = QVBoxLayout(list_group)
        
        self.image_list = QListWidget()
        self.image_list.itemClicked.connect(self.select_image)
        # 添加键盘选择支持
        self.image_list.currentItemChanged.connect(self.on_current_item_changed)
        self.image_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.image_list.customContextMenuRequested.connect(self.show_image_context_menu)
        # 启用拖拽功能
        self.image_list.setDragDropMode(QListWidget.InternalMove)
        self.image_list.setDefaultDropAction(Qt.MoveAction)
        self.image_list.setSelectionMode(QListWidget.SingleSelection)
        self.image_list.model().rowsMoved.connect(self.on_rows_moved)
        list_layout.addWidget(self.image_list)
        
        # 添加图片排序控制按钮
        order_layout = QHBoxLayout()
        
        self.move_up_btn = QPushButton("上移 (Q)")
        self.move_up_btn.clicked.connect(self.move_selected_up)
        self.move_up_btn.setEnabled(False)
        order_layout.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("下移 (E)")
        self.move_down_btn.clicked.connect(self.move_selected_down)
        self.move_down_btn.setEnabled(False)
        order_layout.addWidget(self.move_down_btn)
        
        self.set_ref_btn = QPushButton("设为参考图 (F)")
        self.set_ref_btn.clicked.connect(self.set_selected_as_reference)
        self.set_ref_btn.setEnabled(False)
        order_layout.addWidget(self.set_ref_btn)
        
        self.delete_btn = QPushButton("删除图片 (Delete)")
        self.delete_btn.clicked.connect(self.delete_selected_image)
        self.delete_btn.setEnabled(False)
        order_layout.addWidget(self.delete_btn)
        
        list_layout.addLayout(order_layout)
        
        # 右侧对齐控制
        align_group = QGroupBox("对齐控制")
        align_layout = QVBoxLayout(align_group)
        
        # X坐标控制
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X偏移:"))
        self.x_spin = QSpinBox()
        self.x_spin.setRange(-500, 500)
        self.x_spin.setValue(0)
        self.x_spin.valueChanged.connect(self.update_offset)
        x_layout.addWidget(self.x_spin)
        align_layout.addLayout(x_layout)
        
        # Y坐标控制
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Y偏移:"))
        self.y_spin = QSpinBox()
        self.y_spin.setRange(-500, 500)
        self.y_spin.setValue(0)
        self.y_spin.valueChanged.connect(self.update_offset)
        y_layout.addWidget(self.y_spin)
        align_layout.addLayout(y_layout)
        
        # 重置偏移按钮
        self.reset_btn = QPushButton("重置偏移")
        self.reset_btn.clicked.connect(self.reset_offset)
        align_layout.addWidget(self.reset_btn)
        
        # 自动对齐选项
        auto_layout = QVBoxLayout()
        
        # 创建水平布局来容纳标签和下拉框
        auto_label_layout = QHBoxLayout()
        auto_label_layout.addWidget(QLabel("自动对齐:"))
        self.auto_align_combo = QComboBox()
        self.auto_align_combo.addItems(["无", "左对齐", "右对齐", "上对齐", "下对齐", "中心对齐"])
        auto_label_layout.addWidget(self.auto_align_combo)
        auto_label_layout.addStretch()  # 添加拉伸空间，将组件靠左对齐
        
        # 添加到垂直布局中
        auto_layout.addLayout(auto_label_layout)
        
        # 单个对齐按钮
        self.auto_align_btn = QPushButton("应用到当前图片 (F5)")
        self.auto_align_btn.clicked.connect(self.apply_auto_align)
        
        # 批量对齐按钮
        self.batch_align_btn = QPushButton("批量应用到所有图片 (Ctrl+F5)")
        self.batch_align_btn.clicked.connect(self.batch_apply_auto_align)
        
        auto_layout.addWidget(self.auto_align_btn)
        auto_layout.addWidget(self.batch_align_btn)
        align_layout.addLayout(auto_layout)
        
        # 中间工作区预览
        preview_group = QGroupBox("工作区")
        preview_layout = QVBoxLayout(preview_group)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.workspace_label = QLabel()
        self.workspace_label.setAlignment(Qt.AlignCenter)
        self.workspace_label.setMinimumSize(600, 600)
        self.workspace_label.setStyleSheet("border: 1px solid #ccc")
        self.workspace_label.mousePressEvent = self.workspace_click
        self.workspace_label.mouseMoveEvent = self.workspace_drag
        self.workspace_label.mouseReleaseEvent = self.workspace_release
        self.workspace_label.wheelEvent = self.workspace_wheel_event  # 添加鼠标滚轮事件处理
        
        scroll_area.setWidget(self.workspace_label)
        preview_layout.addWidget(scroll_area)
        
        # 使用QSplitter来分割区域
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(list_group)
        splitter.addWidget(preview_group)
        splitter.addWidget(align_group)
        
        # 设置初始大小
        splitter.setSizes([200, 600, 200])
        
        # 设置拉伸因子，让工作区获得更多空间
        # 参数：索引，拉伸因子
        splitter.setStretchFactor(0, 1)  # 左侧图片列表
        splitter.setStretchFactor(1, 4)  # 中间工作区（更大的拉伸因子，横向占比更多）
        splitter.setStretchFactor(2, 1)  # 右侧对齐控制
        
        work_layout.addWidget(splitter)
        
        # 底部拼接控制
        stitch_group = QGroupBox("拼接设置")
        stitch_layout = QGridLayout(stitch_group)
        # 限制拼接设置区域的高度
        stitch_group.setMaximumHeight(120)
        
        # 行列数设置
        stitch_layout.addWidget(QLabel("列数:"), 0, 0)
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 100)
        self.cols_spin.setValue(10)
        stitch_layout.addWidget(self.cols_spin, 0, 1)
        
        stitch_layout.addWidget(QLabel("行数:"), 0, 2)
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 100)
        self.rows_spin.setValue(10)
        stitch_layout.addWidget(self.rows_spin, 0, 3)
        
        # 间距设置
        stitch_layout.addWidget(QLabel("水平间距:"), 1, 0)
        self.h_spacing_spin = QSpinBox()
        self.h_spacing_spin.setRange(0, 100)
        self.h_spacing_spin.setValue(0)
        stitch_layout.addWidget(self.h_spacing_spin, 1, 1)
        
        stitch_layout.addWidget(QLabel("垂直间距:"), 1, 2)
        self.v_spacing_spin = QSpinBox()
        self.v_spacing_spin.setRange(0, 100)
        self.v_spacing_spin.setValue(0)
        stitch_layout.addWidget(self.v_spacing_spin, 1, 3)
        
        # 底部按钮区域
        button_layout = QHBoxLayout()
        
        self.stitch_save_btn = QPushButton("拼接并保存精灵图 (Ctrl+S)")
        self.stitch_save_btn.clicked.connect(self.stitch_and_save_sprites)
        self.stitch_save_btn.setEnabled(False)
        button_layout.addWidget(self.stitch_save_btn)
        
        # 添加到主布局
        main_layout.addWidget(control_group)
        main_layout.addLayout(work_layout)
        main_layout.addWidget(stitch_group)
        main_layout.addLayout(button_layout)
        
        # 设置垂直拉伸因子，让工作区获得更多垂直空间
        # 参数：索引，拉伸因子
        main_layout.setStretch(0, 1)  # 顶部控制选项
        main_layout.setStretch(1, 3)  # 中间工作区域（更大的拉伸因子）
        main_layout.setStretch(2, 1)  # 底部拼接设置
        main_layout.setStretch(3, 1)  # 底部按钮区域
        
        # 设置中心部件
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # 初始化变量
        self.dragging = False
        self.last_pos = QPoint()
        self.workspace_pixmap = None
        self.stitch_result = None
    
    def import_images(self):
        """导入分割后的小图片"""
        # 打开文件选择对话框，允许选择多个图片文件
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择分割后的小图片", ".", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_paths:
            # 清空之前的数据
            self.image_files = []
            self.images_data = []
            self.image_list.clear()
            self.ref_combo.clear()
            
            # 添加图片文件
            for file_path in file_paths:
                self.image_files.append(file_path)
                # 为每个图片创建数据结构：(文件名, 偏移量x, 偏移量y, 原始图片尺寸)
                with Image.open(file_path) as img:
                    width, height = img.size
                    self.images_data.append({
                        'file_path': file_path,
                        'offset_x': 0,
                        'offset_y': 0,
                        'width': width,
                        'height': height
                    })
                # 添加到列表
                filename = os.path.basename(file_path)
                self.image_list.addItem(filename)
                self.ref_combo.addItem(filename)
            
            QMessageBox.information(self, "成功", f"成功导入 {len(file_paths)} 张图片")
            self.stitch_save_btn.setEnabled(True)
            
            # 启用相关控件
            if len(file_paths) > 0:
                self.ref_combo.setEnabled(True)
                self.ref_check.setEnabled(True)
                self.ref_opacity_slider.setEnabled(True)
                # 启用缩放控件
                self.zoom_slider.setEnabled(True)
                self.zoom_in_btn.setEnabled(True)
                self.zoom_out_btn.setEnabled(True)
                self.reset_zoom_btn.setEnabled(True)
            
            # 自动选择第一张图片
            if self.image_list.count() > 0:
                self.image_list.setCurrentRow(0)
                self.select_image(self.image_list.item(0))
            
            # 默认选择第一张图片作为参考图
            if self.ref_combo.count() > 0:
                self.ref_combo.setCurrentIndex(0)
                self.ref_index = 0
    
    def select_image(self, item):
        """选择列表中的图片"""
        self.selected_index = self.image_list.row(item)
        self.update_workspace()
        
        # 更新偏移量控件
        if 0 <= self.selected_index < len(self.images_data):
            self.x_spin.setValue(self.images_data[self.selected_index]['offset_x'])
            self.y_spin.setValue(self.images_data[self.selected_index]['offset_y'])
        
        # 启用/禁用相关按钮
        self.set_ref_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        
        # 更新上移/下移按钮状态
        total_items = self.image_list.count()
        self.move_up_btn.setEnabled(self.selected_index > 0)
        self.move_down_btn.setEnabled(self.selected_index < total_items - 1)
    
    def on_current_item_changed(self, current, previous):
        """处理当前选中项目改变事件（用于键盘选择）"""
        if current:
            self.select_image(current)
    
    def show_image_context_menu(self, pos):
        """显示图片列表的上下文菜单"""
        from PyQt5.QtWidgets import QMenu
        
        # 获取当前选中的项目
        item = self.image_list.itemAt(pos)
        if item:
            menu = QMenu()
            set_ref_action = menu.addAction("设为参考图")
            delete_action = menu.addAction("删除图片")
            action = menu.exec_(self.image_list.mapToGlobal(pos))
            
            if action == set_ref_action:
                self.set_selected_as_reference()
            elif action == delete_action:
                self.delete_selected_image()
    
    def set_selected_as_reference(self):
        """将选中的图片设为参考图"""
        if self.selected_index >= 0 and self.selected_index < len(self.images_data):
            self.ref_index = self.selected_index
            # 更新参考图下拉框
            self.ref_combo.setCurrentIndex(self.selected_index)
            QMessageBox.information(self, "成功", f"已将 '{os.path.basename(self.images_data[self.selected_index]['file_path'])}' 设为参考图")
            self.update_workspace()
    
    def delete_selected_image(self):
        """删除选中的图片"""
        if self.selected_index < 0 or self.selected_index >= len(self.images_data):
            return
        
        # 获取要删除的图片信息
        img_data = self.images_data[self.selected_index]
        img_name = os.path.basename(img_data['file_path'])
        
        # 显示确认对话框
        reply = QMessageBox.question(
            self, "确认移除", f"确定要移除图片 '{img_name}' 吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除图片
            # 1. 从图片列表中删除
            self.image_list.takeItem(self.selected_index)
            
            # 2. 从数据列表中删除
            del self.images_data[self.selected_index]
            
            # 3. 更新参考图下拉框
            self.update_ref_combo_order()
            
            # 4. 检查是否删除的是参考图
            if self.ref_index == self.selected_index:
                self.ref_index = -1
                self.show_ref = False
                self.ref_check.setChecked(False)
            elif self.ref_index > self.selected_index:
                # 如果参考图索引大于删除的索引，需要递减
                self.ref_index -= 1
            
            # 5. 更新当前选中索引
            total_items = self.image_list.count()
            if total_items > 0:
                # 如果还有图片，选择新的图片
                new_index = min(self.selected_index, total_items - 1)
                self.image_list.setCurrentRow(new_index)
                self.select_image(self.image_list.item(new_index))
            else:
                # 如果没有图片了，重置状态
                self.selected_index = -1
                self.workspace_label.clear()
                self.workspace_label.setText("请导入图片")
                # 禁用相关按钮
                self.set_ref_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
                self.move_up_btn.setEnabled(False)
                self.move_down_btn.setEnabled(False)
                self.stitch_save_btn.setEnabled(False)
                # 禁用缩放控件
                self.zoom_slider.setEnabled(False)
                self.zoom_in_btn.setEnabled(False)
                self.zoom_out_btn.setEnabled(False)
                self.reset_zoom_btn.setEnabled(False)
                # 禁用参考图控件
                self.ref_combo.setEnabled(False)
                self.ref_check.setEnabled(False)
                self.ref_opacity_slider.setEnabled(False)
            
            # 6. 更新工作区显示
            self.update_workspace()
            
            # 7. 显示删除成功消息
            #QMessageBox.information(self, "成功", f"成功移除图片 '{img_name}'")
    
    def move_selected_up(self):
        """将选中的图片上移一位"""
        current_row = self.image_list.currentRow()
        if current_row > 0:
            # 获取当前选中的项目
            item = self.image_list.takeItem(current_row)
            # 插入到上一行
            self.image_list.insertItem(current_row - 1, item)
            # 重新选择项目
            self.image_list.setCurrentRow(current_row - 1)
            # 更新数据列表
            self.update_images_data_order()
            # 更新选择
            self.select_image(item)
    
    def move_selected_down(self):
        """将选中的图片下移一位"""
        current_row = self.image_list.currentRow()
        if current_row < self.image_list.count() - 1:
            # 获取当前选中的项目
            item = self.image_list.takeItem(current_row)
            # 插入到下一行
            self.image_list.insertItem(current_row + 1, item)
            # 重新选择项目
            self.image_list.setCurrentRow(current_row + 1)
            # 更新数据列表
            self.update_images_data_order()
            # 更新选择
            self.select_image(item)
    
    def on_rows_moved(self, parent, start, end, destination, row):
        """处理拖拽移动行事件"""
        # 更新数据列表顺序
        self.update_images_data_order()
        # 更新选择
        self.select_image(self.image_list.currentItem())
    
    def update_images_data_order(self):
        """根据图片列表的顺序更新images_data列表"""
        new_order = []
        for i in range(self.image_list.count()):
            # 获取项目文本
            item_text = self.image_list.item(i).text()
            # 找到对应的图片数据
            for img_data in self.images_data:
                if os.path.basename(img_data['file_path']) == item_text:
                    new_order.append(img_data)
                    break
        # 更新images_data列表
        self.images_data = new_order
        # 更新参考图下拉框
        self.update_ref_combo_order()
    
    def update_ref_combo_order(self):
        """更新参考图下拉框的顺序"""
        # 保存当前选中的索引
        current_index = self.ref_combo.currentIndex()
        current_text = self.ref_combo.currentText() if current_index >= 0 else ""
        
        # 清空下拉框
        self.ref_combo.clear()
        
        # 重新添加项目
        for img_data in self.images_data:
            self.ref_combo.addItem(os.path.basename(img_data['file_path']))
        
        # 恢复选中状态
        if current_text:
            new_index = self.ref_combo.findText(current_text)
            if new_index >= 0:
                self.ref_combo.setCurrentIndex(new_index)
                self.ref_index = new_index
    
    def update_workspace(self):
        """更新工作区显示"""
        if self.selected_index < 0 or self.selected_index >= len(self.images_data):
            return
        
        # 获取当前选中的图片数据
        img_data = self.images_data[self.selected_index]
        file_path = img_data['file_path']
        offset_x = img_data['offset_x']
        offset_y = img_data['offset_y']
        
        # 加载图片
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            QMessageBox.warning(self, "警告", f"无法加载图片: {file_path}")
            return
        
        # 创建工作区画布
        workspace_size = 600
        self.workspace_pixmap = QPixmap(workspace_size, workspace_size)
        self.workspace_pixmap.fill(QColor(240, 240, 240))
        
        # 获取中心坐标
        center_x = workspace_size // 2
        center_y = workspace_size // 2
        
        # 绘制网格（应用缩放）
        if self.show_grid:
            painter = QPainter(self.workspace_pixmap)
            pen = QPen(QColor(200, 200, 200), 1, Qt.DotLine)
            painter.setPen(pen)
            
            # 计算缩放后的网格间距
            scaled_grid_size = int(self.grid_size * self.zoom_factor)
            
            # 绘制水平网格线
            for y in range(0, workspace_size, scaled_grid_size):
                painter.drawLine(0, y, workspace_size, y)
            
            # 绘制垂直网格线
            for x in range(0, workspace_size, scaled_grid_size):
                painter.drawLine(x, 0, x, workspace_size)
            
            painter.end()
        
        # 绘制中心点（应用缩放）
        if self.show_center:
            painter = QPainter(self.workspace_pixmap)
            
            # 绘制中心十字线
            pen = QPen(QColor(255, 0, 0), 2, Qt.SolidLine)
            painter.setPen(pen)
            # 垂直线
            painter.drawLine(center_x, 0, center_x, workspace_size)
            # 水平线
            painter.drawLine(0, center_y, workspace_size, center_y)
            
            # 绘制中心点（应用缩放）
            pen = QPen(QColor(255, 0, 0), int(4 * self.zoom_factor), Qt.SolidLine)
            painter.setPen(pen)
            radius = int(5 * self.zoom_factor)
            painter.drawEllipse(QPoint(center_x, center_y), radius, radius)
            
            painter.end()
        
        # 计算当前图片位置和缩放后的尺寸（考虑偏移量和缩放）
        img_width = pixmap.width()
        img_height = pixmap.height()
        
        # 计算缩放后的尺寸
        scaled_img_width = int(img_width * self.zoom_factor)
        scaled_img_height = int(img_height * self.zoom_factor)
        
        # 计算缩放后的偏移量
        scaled_offset_x = int(offset_x * self.zoom_factor)
        scaled_offset_y = int(offset_y * self.zoom_factor)
        
        # 图片中心点对齐到工作区中心点，加上偏移量
        x = center_x - scaled_img_width // 2 + scaled_offset_x
        y = center_y - scaled_img_height // 2 + scaled_offset_y
        
        # 绘制当前图片（应用缩放）
        if self.current_image_visible:
            painter = QPainter(self.workspace_pixmap)
            scaled_pixmap = pixmap.scaled(scaled_img_width, scaled_img_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(x, y, scaled_pixmap)
            painter.end()
        
        # 绘制参考图（如果启用，应用缩放）
        if self.show_ref and self.ref_index >= 0 and self.ref_index < len(self.images_data):
            ref_data = self.images_data[self.ref_index]
            ref_pixmap = QPixmap(ref_data['file_path'])
            if not ref_pixmap.isNull():
                painter = QPainter(self.workspace_pixmap)
                
                # 设置透明度
                painter.setOpacity(self.ref_opacity)
                
                # 计算参考图位置和缩放后的尺寸
                ref_width = ref_pixmap.width()
                ref_height = ref_pixmap.height()
                ref_offset_x = ref_data['offset_x']
                ref_offset_y = ref_data['offset_y']
                
                # 计算缩放后的尺寸
                scaled_ref_width = int(ref_width * self.zoom_factor)
                scaled_ref_height = int(ref_height * self.zoom_factor)
                
                # 参考图中心点对齐到工作区中心点，加上其自身的偏移量
                # 偏移量也需要应用缩放
                scaled_ref_offset_x = int(ref_offset_x * self.zoom_factor)
                scaled_ref_offset_y = int(ref_offset_y * self.zoom_factor)
                
                ref_x = center_x - scaled_ref_width // 2 + scaled_ref_offset_x
                ref_y = center_y - scaled_ref_height // 2 + scaled_ref_offset_y
                
                # 缩放参考图并绘制
                scaled_ref_pixmap = ref_pixmap.scaled(scaled_ref_width, scaled_ref_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter.drawPixmap(ref_x, ref_y, scaled_ref_pixmap)
                
                painter.end()
        
        # 更新工作区显示
        self.workspace_label.setPixmap(self.workspace_pixmap)
    
    def set_reference_image(self, index):
        """设置参考图"""
        self.ref_index = index
        self.update_workspace()
    
    def toggle_reference(self, state):
        """切换参考图显示"""
        self.show_ref = state == Qt.Checked
        self.update_workspace()
    
    def update_ref_opacity(self, value):
        """更新参考图透明度"""
        self.ref_opacity = value / 100.0
        self.ref_opacity_label.setText(f"{value}%")
        self.update_workspace()
    
    def zoom_in(self):
        """放大工作区图片"""
        new_zoom = min(self.zoom_factor + 0.1, self.max_zoom)
        self.zoom_factor = new_zoom
        self.update_zoom_display()
        self.update_workspace()
    
    def zoom_out(self):
        """缩小工作区图片"""
        new_zoom = max(self.zoom_factor - 0.1, self.min_zoom)
        self.zoom_factor = new_zoom
        self.update_zoom_display()
        self.update_workspace()
    
    def update_zoom(self, value):
        """根据滑块值更新缩放"""
        self.zoom_factor = value / 100.0
        self.update_zoom_display()
        self.update_workspace()
    
    def update_zoom_display(self):
        """更新缩放显示"""
        # 更新滑块值
        self.zoom_slider.setValue(int(self.zoom_factor * 100))
        # 更新缩放比例标签
        self.zoom_label.setText(f"{int(self.zoom_factor * 100)}%")
        # 更新按钮状态
        self.zoom_in_btn.setEnabled(self.zoom_factor < self.max_zoom)
        self.zoom_out_btn.setEnabled(self.zoom_factor > self.min_zoom)
    
    def reset_zoom(self):
        """重置缩放为100%"""
        self.zoom_factor = 1.0
        self.update_zoom_display()
        self.update_workspace()
    
    def update_grid_size(self):
        """更新网格大小"""
        self.grid_size = self.grid_spin.value()
        self.update_workspace()
    
    def toggle_grid(self):
        """切换网格显示"""
        self.show_grid = self.grid_check.isChecked()
        self.update_workspace()
    
    def toggle_grid_by_shortcut(self):
        """通过快捷键切换网格显示"""
        # 切换网格显示状态
        self.show_grid = not self.show_grid
        # 更新复选框状态
        self.grid_check.setChecked(self.show_grid)
        # 更新工作区显示
        self.update_workspace()
    
    def select_previous_image(self):
        """选择上一张图片（A键）"""
        total_items = self.image_list.count()
        if total_items > 0:
            current_index = self.image_list.currentRow()
            new_index = (current_index - 1) % total_items
            self.image_list.setCurrentRow(new_index)
            self.select_image(self.image_list.item(new_index))
    
    def select_next_image(self):
        """选择下一张图片（D键）"""
        total_items = self.image_list.count()
        if total_items > 0:
            current_index = self.image_list.currentRow()
            new_index = (current_index + 1) % total_items
            self.image_list.setCurrentRow(new_index)
            self.select_image(self.image_list.item(new_index))
    
    def toggle_reference_by_shortcut(self):
        """通过快捷键切换参考图可视状态"""
        # 切换参考图显示状态
        self.show_ref = not self.show_ref
        # 更新复选框状态
        self.ref_check.setChecked(self.show_ref)
        # 更新工作区显示
        self.update_workspace()
    
    def toggle_current_image_by_shortcut(self):
        """通过快捷键切换当前图片显示状态"""
        # 切换当前图片显示状态
        self.current_image_visible = not self.current_image_visible
        # 更新复选框状态
        self.current_image_check.setChecked(self.current_image_visible)
        # 更新工作区显示
        self.update_workspace()
    
    def workspace_wheel_event(self, event):
        """处理工作区鼠标滚轮事件，实现缩放功能"""
        # 获取滚轮滚动方向
        delta = event.angleDelta().y()
        
        # 计算新的缩放因子
        zoom_step = 0.1  # 每次滚动的缩放步长
        if delta > 0:
            # 向上滚动，放大
            self.zoom_factor = min(self.zoom_factor + zoom_step, self.max_zoom)
        else:
            # 向下滚动，缩小
            self.zoom_factor = max(self.zoom_factor - zoom_step, self.min_zoom)
        
        # 更新缩放显示和工作区
        self.update_zoom_display()
        self.update_workspace()
    
    def adjust_offset(self, delta_x, delta_y):
        """调整XY偏移量
        
        Args:
            delta_x (int): X偏移量调整值
            delta_y (int): Y偏移量调整值
        """
        if 0 <= self.selected_index < len(self.images_data):
            # 获取当前图片数据
            img_data = self.images_data[self.selected_index]
            
            # 调整偏移量
            img_data['offset_x'] += delta_x
            img_data['offset_y'] += delta_y
            
            # 更新控件值
            self.x_spin.setValue(img_data['offset_x'])
            self.y_spin.setValue(img_data['offset_y'])
            
            # 更新工作区显示
            self.update_workspace()
    
    def toggle_center(self):
        """切换中心点显示"""
        self.show_center = self.center_check.isChecked()
        self.update_workspace()
    
    def toggle_current_image(self, state):
        """切换当前图片显示"""
        self.current_image_visible = state == Qt.Checked
        self.update_workspace()
    
    def update_offset(self):
        """更新偏移量"""
        if 0 <= self.selected_index < len(self.images_data):
            offset_x = self.x_spin.value()
            offset_y = self.y_spin.value()
            self.images_data[self.selected_index]['offset_x'] = offset_x
            self.images_data[self.selected_index]['offset_y'] = offset_y
            self.update_workspace()
    
    def reset_offset(self):
        """重置当前图片的偏移量"""
        if 0 <= self.selected_index < len(self.images_data):
            self.images_data[self.selected_index]['offset_x'] = 0
            self.images_data[self.selected_index]['offset_y'] = 0
            self.x_spin.setValue(0)
            self.y_spin.setValue(0)
            self.update_workspace()
    
    def apply_auto_align(self):
        """应用自动对齐到当前图片"""
        align_type = self.auto_align_combo.currentText()
        if align_type == "无" or self.selected_index < 0:
            return
        
        # 获取当前图片数据
        img_data = self.images_data[self.selected_index]
        img_width = img_data['width']
        img_height = img_data['height']
        
        # 计算偏移量
        offset_x, offset_y = self.calculate_align_offset(img_width, img_height, align_type)
        
        # 更新偏移量
        self.images_data[self.selected_index]['offset_x'] = offset_x
        self.images_data[self.selected_index]['offset_y'] = offset_y
        
        # 更新控件值
        self.x_spin.setValue(offset_x)
        self.y_spin.setValue(offset_y)
        
        # 更新工作区显示
        self.update_workspace()
    
    def batch_apply_auto_align(self):
        """批量应用自动对齐到所有图片"""
        align_type = self.auto_align_combo.currentText()
        if align_type == "无":
            QMessageBox.warning(self, "警告", "请先选择对齐类型")
            return
        
        # 显示确认对话框
        reply = QMessageBox.question(
            self, "确认批量对齐", f"确定要将 '{align_type}' 应用到所有 {len(self.images_data)} 张图片吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 批量应用对齐方案
            for i, img_data in enumerate(self.images_data):
                img_width = img_data['width']
                img_height = img_data['height']
                
                # 计算偏移量
                offset_x, offset_y = self.calculate_align_offset(img_width, img_height, align_type)
                
                # 更新偏移量
                self.images_data[i]['offset_x'] = offset_x
                self.images_data[i]['offset_y'] = offset_y
            
            # 更新当前选中图片的控件值
            if self.selected_index >= 0 and self.selected_index < len(self.images_data):
                current_img = self.images_data[self.selected_index]
                self.x_spin.setValue(current_img['offset_x'])
                self.y_spin.setValue(current_img['offset_y'])
            
            # 更新工作区显示
            self.update_workspace()
            
            # 显示成功消息
            QMessageBox.information(self, "成功", f"已将 '{align_type}' 应用到所有 {len(self.images_data)} 张图片")
    
    def calculate_align_offset(self, img_width, img_height, align_type):
        """计算对齐偏移量"""
        # 重新计算对齐逻辑，确保所有对齐都基于图片中心点
        # 工作区中心点是参考点，图片中心点需要对齐到特定位置
        if align_type == "中心对齐":
            # 图片中心点精确对齐到工作区中心点
            offset_x = 0
            offset_y = 0
        elif align_type == "左对齐":
            # 图片中心点对齐到工作区中心点左侧，距离为图片宽度的一半
            offset_x = -img_width // 2
            offset_y = 0
        elif align_type == "右对齐":
            # 图片中心点对齐到工作区中心点右侧，距离为图片宽度的一半
            offset_x = img_width // 2
            offset_y = 0
        elif align_type == "上对齐" or align_type == "顶部对齐":
            # 图片中心点对齐到工作区中心点上方，距离为图片高度的一半
            offset_x = 0
            offset_y = -img_height // 2
        elif align_type == "下对齐" or align_type == "底部对齐":
            # 图片中心点对齐到工作区中心点下方，距离为图片高度的一半
            offset_x = 0
            offset_y = img_height // 2
        else:
            offset_x = 0
            offset_y = 0
        
        return offset_x, offset_y
    
    def workspace_click(self, event):
        """工作区鼠标点击事件"""
        if self.workspace_pixmap:
            self.dragging = True
            self.last_pos = event.pos()
    
    def workspace_drag(self, event):
        """工作区鼠标拖动事件"""
        if self.dragging and self.workspace_pixmap:
            # 计算拖动偏移量
            delta = event.pos() - self.last_pos
            
            # 更新偏移量
            if 0 <= self.selected_index < len(self.images_data):
                self.images_data[self.selected_index]['offset_x'] += delta.x()
                self.images_data[self.selected_index]['offset_y'] += delta.y()
                
                # 更新控件值
                self.x_spin.setValue(self.images_data[self.selected_index]['offset_x'])
                self.y_spin.setValue(self.images_data[self.selected_index]['offset_y'])
                
                self.update_workspace()
                self.last_pos = event.pos()
    
    def workspace_release(self, event):
        """工作区鼠标释放事件"""
        self.dragging = False
    
    def stitch_sprites(self):
        """将对齐后的精灵图重新拼接成完整的精灵图表"""
        if not self.images_data:
            QMessageBox.warning(self, "警告", "请先导入图片")
            return
        
        try:
            cols = self.cols_spin.value()
            rows = self.rows_spin.value()
            h_spacing = self.h_spacing_spin.value()
            v_spacing = self.v_spacing_spin.value()
            
            # 1. 首先计算所有图片的原始尺寸和最大尺寸
            all_images = []
            max_width = 0
            max_height = 0
            
            for img_data in self.images_data:
                with Image.open(img_data['file_path']) as img:
                    width, height = img.size
                    all_images.append((img_data, width, height))
                    max_width = max(max_width, width)
                    max_height = max(max_height, height)
            
            # 2. 计算每个单元格的基本尺寸（包含间距）
            cell_width = max_width + h_spacing
            cell_height = max_height + v_spacing
            
            # 3. 计算所有图片在拼接图中的实际位置和尺寸
            # 我们需要找到整个拼接图的最小和最大坐标，以确定最终尺寸
            min_x = float('inf')
            min_y = float('inf')
            max_x = 0
            max_y = 0
            
            # 先收集所有图片的位置信息
            image_positions = []
            for i, (img_data, width, height) in enumerate(all_images):
                if i >= cols * rows:
                    break
                
                # 计算当前图片在网格中的行列位置
                row = i // cols
                col = i % cols
                
                # 计算单元格左上角坐标（不考虑偏移）
                cell_x = col * cell_width
                cell_y = row * cell_height
                
                # 计算图片在单元格中的偏移量（考虑用户调整）
                offset_x = img_data['offset_x']
                offset_y = img_data['offset_y']
                
                # 计算图片中心点在单元格中的位置
                # 默认情况下，图片中心点对齐到单元格中心点
                # 然后加上用户调整的偏移量
                center_x = cell_x + max_width // 2 + offset_x
                center_y = cell_y + max_height // 2 + offset_y
                
                # 计算图片左上角和右下角坐标
                img_left = center_x - width // 2
                img_top = center_y - height // 2
                img_right = center_x + width // 2
                img_bottom = center_y + height // 2
                
                # 更新全局坐标范围
                min_x = min(min_x, img_left)
                min_y = min(min_y, img_top)
                max_x = max(max_x, img_right)
                max_y = max(max_y, img_bottom)
                
                # 保存图片位置信息
                image_positions.append({
                    'img_data': img_data,
                    'width': width,
                    'height': height,
                    'left': img_left,
                    'top': img_top
                })
            
            # 4. 计算最终拼接图的尺寸
            # 确保尺寸至少为0
            total_width = max(int(max_x - min_x), 0)
            total_height = max(int(max_y - min_y), 0)
            
            # 5. 创建新的空白图片
            stitch_img = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
            
            # 6. 粘贴所有图片到正确位置
            for pos in image_positions:
                img_data = pos['img_data']
                width = pos['width']
                height = pos['height']
                
                # 计算调整后的粘贴位置（减去min_x和min_y，确保图片在画布内）
                paste_x = int(pos['left'] - min_x)
                paste_y = int(pos['top'] - min_y)
                
                # 打开图片并粘贴
                with Image.open(img_data['file_path']) as img:
                    stitch_img.paste(img, (paste_x, paste_y), img if img.mode == 'RGBA' else None)
            
            return stitch_img
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"拼接失败：{str(e)}")
            return None
    
    def stitch_and_save_sprites(self):
        """拼接并保存精灵图"""
        # 拼接精灵图
        stitch_img = self.stitch_sprites()
        
        if stitch_img:
            try:
                # 显示拼接结果预览
                self.show_stitch_preview(stitch_img)
                
                # 打开文件保存对话框
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "保存拼接结果", ".", "PNG Files (*.png);;All Files (*)"
                )
                
                if file_path:
                    # 保存拼接结果
                    stitch_img.save(file_path, 'PNG')
                    QMessageBox.information(self, "成功", f"拼接结果已保存到：{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败：{str(e)}")
    
    def show_stitch_preview(self, stitch_img):
        """显示拼接结果预览"""
        # 将PIL Image转换为QPixmap
        img = stitch_img.convert('RGBA')
        data = img.tobytes("raw", "RGBA")
        qimage = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)
        
        # 创建预览窗口
        preview_window = QWidget()
        preview_window.setWindowTitle("拼接结果预览")
        preview_window.resize(800, 600)
        
        layout = QVBoxLayout(preview_window)
        label = QLabel()
        label.setPixmap(pixmap.scaled(800, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        label.setAlignment(Qt.AlignCenter)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(label)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        preview_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpriteAlignerGUI()
    window.show()
    sys.exit(app.exec_())
