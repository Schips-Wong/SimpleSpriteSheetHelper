import sys
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QListWidget, QFileDialog, QSpinBox, 
    QGroupBox, QMessageBox, QGridLayout, QScrollArea,
    QSplitter, QSlider, QCheckBox, QComboBox, QListView, QTreeView,
    QDialog, QListWidgetItem, QProgressBar, QTabWidget, QTextEdit,
    QAbstractItemView, QTreeWidget, QTreeWidgetItem, QLineEdit
)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QCursor
from PyQt5.QtCore import Qt, QPoint, QRect
from PIL import Image


class AdvancedImageFileDialog(QDialog):
    """高级图片文件选择对话框，支持多目录选择"""
    
    def __init__(self, parent=None, language_dict=None, current_language='zh_CN', initial_path=None):
        super().__init__(parent)
        self.selected_directories = []
        self.language_dict = language_dict or self.load_default_language_dict()
        self.current_language = current_language
        self.initial_path = initial_path or "."
        self.setup_ui()
    
    def load_default_language_dict(self):
        """加载默认语言字典"""
        return {
            'zh_CN': {
                'select_image_directories': '选择图片目录',
                'select_containing_images': '选择包含图片的目录:',
                'current_path': '当前路径:',
                'enter_path_or_browse': '输入目录路径或点击浏览...',
                'browse': '浏览',
                'parent_directory': '上级目录',
                'program_directory': '程序目录',
                'directory_tree': '目录树:',
                'directory': '目录',
                'refresh': '刷新',
                'expand_all': '展开全部',
                'collapse_all': '折叠全部',
                'selected_directories': '已选目录:',
                'remove': '移除',
                'clear': '清空',
                'file_type': '文件类型:',
                'images_in_directory': '目录中的图片文件:',
                'selected_directories_count': '已选择 {0} 个目录，共 {1} 个文件',
                'ok': '确定',
                'cancel': '取消',
                'click_to_expand': '点击展开...',
                'no_access_permission': '无访问权限',
                'load_failed': '加载失败: {0}',
                'error': '错误',
                'path_not_exist': '路径不存在或不是目录',
                'select_directory': '选择目录',
                'cannot_navigate': '无法导航到目录: {0}',
                'all_images': '所有图片 (*.png *.jpg *.jpeg *.bmp *.gif)',
                'png_images': 'PNG 图片 (*.png)',
                'jpeg_images': 'JPEG 图片 (*.jpg *.jpeg)',
                'bmp_images': 'BMP 图片 (*.bmp)',
                'gif_images': 'GIF 图片 (*.gif)',
                'include_subdirectories': '包含子目录'
            },
            'en_US': {
                'select_image_directories': 'Select Image Directories',
                'select_containing_images': 'Select directories containing images:',
                'current_path': 'Current Path:',
                'enter_path_or_browse': 'Enter directory path or click browse...',
                'browse': 'Browse',
                'parent_directory': 'Parent Directory',
                'program_directory': 'Program Directory',
                'directory_tree': 'Directory Tree:',
                'directory': 'Directory',
                'refresh': 'Refresh',
                'expand_all': 'Expand All',
                'collapse_all': 'Collapse All',
                'selected_directories': 'Selected Directories:',
                'remove': 'Remove',
                'clear': 'Clear',
                'file_type': 'File Type:',
                'images_in_directory': 'Images in directory:',
                'selected_directories_count': 'Selected {0} directories, total {1} files',
                'ok': 'OK',
                'cancel': 'Cancel',
                'click_to_expand': 'Click to expand...',
                'no_access_permission': 'No access permission',
                'load_failed': 'Load failed: {0}',
                'error': 'Error',
                'path_not_exist': 'Path does not exist or is not a directory',
                'select_directory': 'Select Directory',
                'cannot_navigate': 'Cannot navigate to directory: {0}',
                'all_images': 'All images (*.png *.jpg *.jpeg *.bmp *.gif)',
                'png_images': 'PNG images (*.png)',
                'jpeg_images': 'JPEG images (*.jpg *.jpeg)',
                'bmp_images': 'BMP images (*.bmp)',
                'gif_images': 'GIF images (*.gif)',
                'include_subdirectories': 'Include subdirectories'
            }
        }

    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle(self.language_dict[self.current_language]['select_image_directories'])
        self.setGeometry(200, 100, 1000, 800)
        
        layout = QVBoxLayout(self)
        
        # 目录选择区域
        directory_layout = QVBoxLayout()
        directory_layout.addWidget(QLabel(self.language_dict[self.current_language]['select_containing_images']))
        
        # 地址栏
        address_layout = QHBoxLayout()
        address_layout.addWidget(QLabel(self.language_dict[self.current_language]['current_path']))
        
        self.address_bar = QLineEdit()
        self.address_bar.setPlaceholderText(self.language_dict[self.current_language]['enter_path_or_browse'])
        self.address_bar.textEdited.connect(self.navigate_to_address)
        address_layout.addWidget(self.address_bar)
        
        self.browse_btn = QPushButton(self.language_dict[self.current_language]['browse'])
        self.browse_btn.clicked.connect(self.browse_directory)
        address_layout.addWidget(self.browse_btn)
        
        self.up_btn = QPushButton(self.language_dict[self.current_language]['parent_directory'])
        self.up_btn.clicked.connect(self.navigate_up)
        address_layout.addWidget(self.up_btn)
        
        self.home_btn = QPushButton(self.language_dict[self.current_language]['program_directory'])
        self.home_btn.clicked.connect(self.navigate_to_program_dir)
        address_layout.addWidget(self.home_btn)
        
        directory_layout.addLayout(address_layout)
        
        # 目录浏览和选择区域（使用分割器）
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：目录树区域
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel(self.language_dict[self.current_language]['directory_tree']))
        
        self.directory_tree = QTreeWidget()
        self.directory_tree.setHeaderLabels([self.language_dict[self.current_language]['directory']])
        self.directory_tree.setColumnWidth(0, 300)
        self.directory_tree.setColumnWidth(1, 80)
        self.directory_tree.itemChanged.connect(self.on_item_changed)
        left_layout.addWidget(self.directory_tree)
        
        # 目录操作按钮
        tree_buttons_layout = QHBoxLayout()
        self.refresh_btn = QPushButton(self.language_dict[self.current_language]['refresh'])
        self.refresh_btn.clicked.connect(self.refresh_directory_tree)
        tree_buttons_layout.addWidget(self.refresh_btn)
        
        self.expand_all_btn = QPushButton(self.language_dict[self.current_language]['expand_all'])
        self.expand_all_btn.clicked.connect(self.directory_tree.expandAll)
        tree_buttons_layout.addWidget(self.expand_all_btn)
        
        self.collapse_all_btn = QPushButton(self.language_dict[self.current_language]['collapse_all'])
        self.collapse_all_btn.clicked.connect(self.directory_tree.collapseAll)
        tree_buttons_layout.addWidget(self.collapse_all_btn)
        
        left_layout.addLayout(tree_buttons_layout)
        
        # 右侧：已选目录列表区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel(self.language_dict[self.current_language]['selected_directories']))
        
        self.selected_list = QListWidget()
        right_layout.addWidget(self.selected_list)
        
        # 已选目录操作按钮
        selected_buttons_layout = QHBoxLayout()
        self.remove_btn = QPushButton(self.language_dict[self.current_language]['remove'])
        self.remove_btn.clicked.connect(self.remove_selected)
        selected_buttons_layout.addWidget(self.remove_btn)
        
        self.clear_btn = QPushButton(self.language_dict[self.current_language]['clear'])
        self.clear_btn.clicked.connect(self.clear_selected)
        selected_buttons_layout.addWidget(self.clear_btn)
        
        right_layout.addLayout(selected_buttons_layout)
        
        # 添加分割器部件
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)  # 目录树占2/4
        splitter.setStretchFactor(1, 2)  # 已选列表占2/4
        
        directory_layout.addWidget(splitter)
        layout.addLayout(directory_layout)
        
        # 文件类型过滤器
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel(self.language_dict[self.current_language]['file_type']))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            self.language_dict[self.current_language]['all_images'],
            self.language_dict[self.current_language]['png_images'],
            self.language_dict[self.current_language]['jpeg_images'],
            self.language_dict[self.current_language]['bmp_images'],
            self.language_dict[self.current_language]['gif_images']
        ])
        filter_layout.addWidget(self.filter_combo)
        
        filter_layout.addStretch()
        
        # 包含子目录选项
        self.include_subdirs_check = QCheckBox(self.language_dict[self.current_language]['include_subdirectories'])
        self.include_subdirs_check.setChecked(False)
        filter_layout.addWidget(self.include_subdirs_check)
        
        layout.addLayout(filter_layout)
        
        # 文件预览区域（使用分割器）
        main_splitter = QSplitter(Qt.Vertical)
        
        # 上部：目录浏览区域
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.addLayout(directory_layout)
        
        # 下部：文件预览区域
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.addWidget(QLabel(self.language_dict[self.current_language]['images_in_directory']))
        
        self.file_list = QListWidget()
        bottom_layout.addWidget(self.file_list)
        
        # 文件统计信息
        self.file_info_label = QLabel(self.language_dict[self.current_language]['selected_directories_count'].format(0, 0))
        bottom_layout.addWidget(self.file_info_label)
        
        # 添加分割器部件
        main_splitter.addWidget(top_widget)
        main_splitter.addWidget(bottom_widget)
        main_splitter.setStretchFactor(0, 3)  # 目录浏览区域占3/4
        main_splitter.setStretchFactor(1, 1)  # 文件预览区域占1/4
        
        layout.addWidget(main_splitter)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_btn = QPushButton(self.language_dict[self.current_language]['ok'])
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton(self.language_dict[self.current_language]['cancel'])
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 初始化目录树
        self.populate_directory_tree()
        
        # 默认定位到程序所在位置
        self.navigate_to_program_dir()
    
    def populate_directory_tree(self, initial_path=None):
        """填充目录树（懒加载模式）"""
        self.directory_tree.clear()
        
        # 连接展开事件
        self.directory_tree.itemExpanded.connect(self.on_item_expanded)
        self.directory_tree.itemCollapsed.connect(self.on_item_collapsed)
        
        if initial_path:
            # 使用指定路径作为根节点
            root_item = QTreeWidgetItem(self.directory_tree)
            root_item.setText(0, initial_path)
            root_item.setFlags(root_item.flags() | Qt.ItemIsUserCheckable)
            root_item.setCheckState(0, Qt.Unchecked)
            
            # 添加子目录占位符（懒加载）
            child_item = QTreeWidgetItem(root_item)
            child_item.setText(0, self.language_dict[self.current_language]['click_to_expand'])
            child_item.setFlags(child_item.flags() & ~Qt.ItemIsUserCheckable)
            
            # 展开根节点
            self.directory_tree.expandItem(root_item)
        else:
            # 获取驱动器列表（Windows）
            import string
            drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
            
            for drive in drives:
                drive_item = QTreeWidgetItem(self.directory_tree)
                drive_item.setText(0, drive)
                drive_item.setFlags(drive_item.flags() | Qt.ItemIsUserCheckable)
                drive_item.setCheckState(0, Qt.Unchecked)
                
                # 添加子目录占位符（懒加载）
                child_item = QTreeWidgetItem(drive_item)
                child_item.setText(0, self.language_dict[self.current_language]['click_to_expand'])
                child_item.setFlags(child_item.flags() & ~Qt.ItemIsUserCheckable)
    
    def on_item_expanded(self, item):
        """目录项展开时的处理（懒加载子目录）"""
        # 如果当前项有子项且是占位符，则加载真实子目录
        if item.childCount() == 1 and item.child(0).text(0) == self.language_dict[self.current_language]['click_to_expand']:
            # 移除占位符
            item.removeChild(item.child(0))
            
            # 加载子目录
            self.load_subdirectories(item)
    
    def on_item_collapsed(self, item):
        """目录项折叠时的处理（可选：清理子项以节省内存）"""
        # 可以保留子目录，或者清理以节省内存
        # 这里选择保留，因为重新加载可能耗时
        pass
    
    def load_subdirectories(self, parent_item):
        """加载指定目录的子目录"""
        directory_path = self.get_item_full_path(parent_item)
        
        try:
            # 获取子目录列表
            subdirs = []
            for entry in os.listdir(directory_path):
                entry_path = os.path.join(directory_path, entry)
                if os.path.isdir(entry_path):
                    subdirs.append(entry)
            
            # 按名称排序
            subdirs.sort()
            
            # 添加子目录项
            for subdir in subdirs:
                subdir_path = os.path.join(directory_path, subdir)
                subdir_item = QTreeWidgetItem(parent_item)
                subdir_item.setText(0, subdir)  # 只显示目录名
                subdir_item.setData(0, Qt.UserRole, subdir_path)  # 存储完整路径
                subdir_item.setFlags(subdir_item.flags() | Qt.ItemIsUserCheckable)
                subdir_item.setCheckState(0, Qt.Unchecked)
                
                # 添加子目录占位符（懒加载）
                child_item = QTreeWidgetItem(subdir_item)
                child_item.setText(0, self.language_dict[self.current_language]['click_to_expand'])
                child_item.setFlags(child_item.flags() & ~Qt.ItemIsUserCheckable)
                
        except PermissionError:
            # 无权限访问的目录
            error_item = QTreeWidgetItem(parent_item)
            error_item.setText(0, self.language_dict[self.current_language]['no_access_permission'])
            error_item.setFlags(error_item.flags() & ~Qt.ItemIsUserCheckable)
        except Exception as e:
            # 其他错误
            error_item = QTreeWidgetItem(parent_item)
            error_item.setText(0, self.language_dict[self.current_language]['load_failed'].format(str(e)))
            error_item.setFlags(error_item.flags() & ~Qt.ItemIsUserCheckable)
    
    def get_item_full_path(self, item):
        """获取目录项的完整路径"""
        # 如果项存储了完整路径数据，则使用该数据
        full_path = item.data(0, Qt.UserRole)
        if full_path:
            return full_path
        
        # 否则使用显示的文本（根节点）
        return item.text(0)
    
    def on_item_changed(self, item, column):
        """目录树项状态改变时的处理"""
        if column == 0:  # 只处理第一列
            directory_path = self.get_item_full_path(item)
            
            if item.checkState(0) == Qt.Checked:
                # 添加目录到已选列表
                if directory_path not in self.selected_directories:
                    self.selected_directories.append(directory_path)
                    self.selected_list.addItem(directory_path)
                    self.update_file_list()
            else:
                # 从已选列表中移除目录
                if directory_path in self.selected_directories:
                    self.selected_directories.remove(directory_path)
                    # 从列表控件中移除
                    for i in range(self.selected_list.count()):
                        if self.selected_list.item(i).text() == directory_path:
                            self.selected_list.takeItem(i)
                            break
                    self.update_file_list()
    
    def refresh_directory_tree(self):
        """刷新目录树"""
        self.populate_directory_tree()
    
    def remove_selected(self):
        """移除选中的目录"""
        current_item = self.selected_list.currentItem()
        if current_item:
            directory_path = current_item.text()
            if directory_path in self.selected_directories:
                self.selected_directories.remove(directory_path)
                self.selected_list.takeItem(self.selected_list.row(current_item))
                
                # 更新目录树的勾选状态
                self.update_tree_check_state(directory_path, False)
                self.update_file_list()
    
    def clear_selected(self):
        """清空已选目录"""
        self.selected_directories.clear()
        self.selected_list.clear()
        
        # 更新目录树的勾选状态
        self.update_all_tree_check_states(False)
        self.update_file_list()
    
    def update_tree_check_state(self, directory_path, checked):
        """更新目录树中指定目录的勾选状态"""
        # 遍历所有目录项
        def update_item(item):
            if self.get_item_full_path(item) == directory_path:
                item.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
                return True
            
            # 递归检查子项
            for i in range(item.childCount()):
                if update_item(item.child(i)):
                    return True
            return False
        
        for i in range(self.directory_tree.topLevelItemCount()):
            if update_item(self.directory_tree.topLevelItem(i)):
                break
    
    def update_all_tree_check_states(self, checked):
        """更新目录树中所有目录的勾选状态"""
        # 递归更新所有项
        def update_all_items(item):
            item.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
            for i in range(item.childCount()):
                update_all_items(item.child(i))
        
        for i in range(self.directory_tree.topLevelItemCount()):
            update_all_items(self.directory_tree.topLevelItem(i))
    
    def update_file_list(self):
        """更新文件列表"""
        self.file_list.clear()
        
        if not self.selected_directories:
            self.file_info_label.setText("已选择 0 个目录，共 0 个文件")
            return
        
        # 收集所有图片文件
        all_files = []
        for directory in self.selected_directories:
            if self.include_subdirs_check.isChecked():
                # 包含子目录
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if self.is_image_file(file):
                            all_files.append(os.path.join(root, file))
            else:
                # 仅当前目录
                try:
                    files = os.listdir(directory)
                    for file in files:
                        file_path = os.path.join(directory, file)
                        if os.path.isfile(file_path) and self.is_image_file(file):
                            all_files.append(file_path)
                except PermissionError:
                    continue
        
        # 添加到文件列表
        for file_path in all_files:
            self.file_list.addItem(os.path.basename(file_path))
        
        self.file_info_label.setText(f"已选择 {len(self.selected_directories)} 个目录，共 {len(all_files)} 个文件")
    
    def is_image_file(self, filename):
        """检查文件是否为图片文件"""
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        return any(filename.lower().endswith(ext) for ext in image_extensions)
    
    def navigate_to_address(self):
        """导航到地址栏指定的路径"""
        path = self.address_bar.text().strip()
        if path and os.path.isdir(path):
            self.navigate_to_directory(path)
    
    def browse_directory(self):
        """浏览目录对话框"""
        directory = QFileDialog.getExistingDirectory(self, "选择目录", self.address_bar.text())
        if directory:
            self.navigate_to_directory(directory)
    
    def navigate_up(self):
        """导航到上级目录"""
        current_path = self.address_bar.text().strip()
        if current_path and os.path.isdir(current_path):
            parent_path = os.path.dirname(current_path)
            if parent_path and os.path.isdir(parent_path):
                self.navigate_to_directory(parent_path)
    
    def navigate_to_program_dir(self):
        """导航到程序所在目录或初始路径"""
        if self.initial_path and os.path.exists(self.initial_path):
            self.navigate_to_directory(self.initial_path)
        else:
            program_dir = os.path.dirname(os.path.abspath(__file__))
            self.navigate_to_directory(program_dir)
    
    def navigate_to_directory(self, directory_path):
        """导航到指定目录"""
        try:
            # 更新地址栏
            self.address_bar.setText(directory_path)
            
            # 重新填充目录树，使用指定路径作为根节点
            self.populate_directory_tree(directory_path)
            
            # 更新文件列表
            self.update_file_list()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法导航到目录: {str(e)}")
    
    def selectedFiles(self):
        """返回选中的目录列表"""
        return self.selected_directories



class SpriteAlignerGUI(QMainWindow):
    """精灵图对齐工具的图形界面"""
    
    def __init__(self):
        super().__init__()
        # 初始化语言字典
        self.language_dict = self.load_language_dict()
        self.current_language = 'zh_CN'  # 默认中文
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
        # 路径记忆功能
        self.last_selected_path = "."  # 默认当前目录
        self.config_file = os.path.join("config", "sprite_aligner_config.json")
        self.load_config()
        # 然后调用init_ui
        self.init_ui()
    
    def load_language_dict(self):
        """从JSON文件加载语言字典"""
        language_file = os.path.join("translations", "languages_Sprite2SpriteSheet.json")
        try:
            with open(language_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"无法加载语言文件: {e}")
            # 如果加载失败，返回默认的语言字典
            return {
                'zh_CN': {
                    'window_title': '精灵图对齐工具',
                    'control_options': '控制选项',
                    'import_images': '导入分割图片',
                    'grid_size': '网格大小:',
                    'show_grid': '显示网格 (Ctrl+\')',
                    'show_center': '显示中心点',
                    'show_current_image': '显示当前图片 (H)',
                    'reference_image': '参考图:',
                    'show_reference': '显示参考图 (C)',
                    'reference_opacity': '参考图透明度:',
                    'workspace_zoom': '工作区缩放:',
                    'zoom_out': '-',
                    'zoom_in': '+',
                    'reset_zoom': '重置缩放',
                    'image_list': '图片列表',
                    'move_up': '上移 (Q)',
                    'move_down': '下移 (E)',
                    'set_as_reference': '设为参考图 (F)',
                    'delete_image': '删除图片 (Delete)',
                    'alignment_control': '对齐控制',
                    'x_offset': 'X偏移:',
                    'y_offset': 'Y偏移:',
                    'reset_offset': '重置偏移',
                    'auto_alignment': '自动对齐:',
                    'apply_to_current': '应用到当前图片 (F5)',
                    'batch_apply': '批量应用到所有图片 (Ctrl+F5)',
                    'workspace': '工作区',
                    'stitch_settings': '拼接设置',
                    'columns': '列数:',
                    'rows': '行数:',
                    'horizontal_spacing': '水平间距:',
                    'vertical_spacing': '垂直间距:',
                    'stitch_save': '拼接并保存精灵图 (Ctrl+S)',
                    'select_split_images': '选择分割后的小图片',
                    'success': '成功',
                    'success_imported': '成功导入 {0} 张图片',
                    'success_set_reference': '已将 \'{0}\' 设为参考图',
                    'confirm_remove': '确认移除',
                    'confirm_remove_image': '确定要移除图片 \'{0}\' 吗？',
                    'warning': '警告',
                    'cannot_load_image': '无法加载图片: {0}',
                    'confirm_batch_align': '确认批量对齐',
                    'confirm_batch_align_message': '确定要将 \'{0}\' 应用到所有 {1} 张图片吗？',
                    'please_select_align_type': '请先选择对齐类型',
                    'language': '语言:',
                    'yes': '是',
                    'no': '否',
                    'none': '无',
                    'left_align': '左对齐',
                    'right_align': '右对齐',
                    'top_align': '上对齐',
                    'bottom_align': '下对齐',
                    'center_align': '中心对齐',
                    'no_image_selected': '请导入图片',
                    'single_image_width': '单个图片宽度:',
                    'single_image_height': '单个图片高度:',
                    'export_offset': '导出偏移设置',
                    'import_offset': '导入偏移设置'
                },
                'en_US': {
                    'window_title': 'Sprite Aligner',
                    'control_options': 'Control Options',
                    'import_images': 'Import Split Images',
                    'grid_size': 'Grid Size:',
                    'show_grid': 'Show Grid (Ctrl+\')',
                    'show_center': 'Show Center Point',
                    'show_current_image': 'Show Current Image (H)',
                    'reference_image': 'Reference:',
                    'show_reference': 'Show Reference (C)',
                    'reference_opacity': 'Reference Opacity:',
                    'workspace_zoom': 'Workspace Zoom:',
                    'zoom_out': '-',
                    'zoom_in': '+',
                    'reset_zoom': 'Reset Zoom',
                    'image_list': 'Image List',
                    'move_up': 'Move Up (Q)',
                    'move_down': 'Move Down (E)',
                    'set_as_reference': 'Set as Reference (F)',
                    'delete_image': 'Delete Image (Delete)',
                    'alignment_control': 'Alignment Control',
                    'x_offset': 'X Offset:',
                    'y_offset': 'Y Offset:',
                    'reset_offset': 'Reset Offset',
                    'auto_alignment': 'Auto Alignment:',
                    'apply_to_current': 'Apply to Current Image (F5)',
                    'batch_apply': 'Batch Apply to All Images (Ctrl+F5)',
                    'workspace': 'Workspace',
                    'stitch_settings': 'Stitch Settings',
                    'columns': 'Columns:',
                    'rows': 'Rows:',
                    'horizontal_spacing': 'Horizontal Spacing:',
                    'vertical_spacing': 'Vertical Spacing:',
                    'stitch_save': 'Stitch and Save Spritesheet (Ctrl+S)',
                    'select_split_images': 'Select Split Images',
                    'success': 'Success',
                    'success_imported': 'Successfully imported {0} images',
                    'success_set_reference': 'Set \'{0}\' as reference image',
                    'confirm_remove': 'Confirm Remove',
                    'confirm_remove_image': 'Are you sure you want to remove image \'{0}\'?',
                    'warning': 'Warning',
                    'cannot_load_image': 'Cannot load image: {0}',
                    'confirm_batch_align': 'Confirm Batch Alignment',
                    'confirm_batch_align_message': 'Are you sure you want to apply \'{0}\' to all {1} images?',
                    'please_select_align_type': 'Please select alignment type first',
                    'language': 'Language:',
                    'yes': 'Yes',
                    'no': 'No',
                    'none': 'None',
                    'left_align': 'Left Align',
                    'right_align': 'Right Align',
                    'top_align': 'Top Align',
                    'bottom_align': 'Bottom Align',
                    'center_align': 'Center Align',
                    'no_image_selected': 'Please import images',
                    'single_image_width': 'Single Image Width:',
                    'single_image_height': 'Single Image Height:',
                    'export_offset': 'Export Offset Settings',
                    'import_offset': 'Import Offset Settings'
                }
            }
    
    def load_config(self):
        """加载配置文件"""
        try:
            # 确保配置目录存在
            config_dir = os.path.dirname(self.config_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # 如果配置文件存在，则加载
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.last_selected_path = config.get('last_selected_path', '.')
        except Exception as e:
            print(f"加载配置失败: {e}")
            # 使用默认值
            self.last_selected_path = "."
    
    def save_config(self):
        """保存配置文件"""
        try:
            # 确保配置目录存在
            config_dir = os.path.dirname(self.config_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            config = {
                'last_selected_path': self.last_selected_path
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def update_last_selected_path(self, path):
        """更新最后选择的路径"""
        if path and os.path.exists(os.path.dirname(path)):
            self.last_selected_path = os.path.dirname(path)
            self.save_config()
        
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
        self.control_group.setTitle(self.language_dict[lang]['control_options'])
        self.list_group.setTitle(self.language_dict[lang]['image_list'])
        self.align_group.setTitle(self.language_dict[lang]['alignment_control'])
        self.preview_group.setTitle(self.language_dict[lang]['workspace'])
        self.stitch_group.setTitle(self.language_dict[lang]['stitch_settings'])
        
        # 更新按钮文本
        self.import_btn.setText(self.language_dict[lang]['import_images'])
        self.zoom_out_btn.setText(self.language_dict[lang]['zoom_out'])
        self.zoom_in_btn.setText(self.language_dict[lang]['zoom_in'])
        self.reset_zoom_btn.setText(self.language_dict[lang]['reset_zoom'])
        self.move_up_btn.setText(self.language_dict[lang]['move_up'])
        self.move_down_btn.setText(self.language_dict[lang]['move_down'])
        self.set_ref_btn.setText(self.language_dict[lang]['set_as_reference'])
        self.delete_btn.setText(self.language_dict[lang]['delete_image'])
        self.reset_btn.setText(self.language_dict[lang]['reset_offset'])
        self.auto_align_btn.setText(self.language_dict[lang]['apply_to_current'])
        self.batch_align_btn.setText(self.language_dict[lang]['batch_apply'])
        self.stitch_save_btn.setText(self.language_dict[lang]['stitch_save'])
        self.export_offset_btn.setText(self.language_dict[lang]['export_offset'])
        self.import_offset_btn.setText(self.language_dict[lang]['import_offset'])
        
        # 更新标签文本
        self.grid_size_label.setText(self.language_dict[lang]['grid_size'])
        self.grid_check.setText(self.language_dict[lang]['show_grid'])
        self.center_check.setText(self.language_dict[lang]['show_center'])
        self.current_image_check.setText(self.language_dict[lang]['show_current_image'])
        self.ref_label.setText(self.language_dict[lang]['reference_image'])
        self.ref_check.setText(self.language_dict[lang]['show_reference'])
        self.ref_opacity_label.setText(self.language_dict[lang]['reference_opacity'])
        self.zoom_label_text.setText(self.language_dict[lang]['workspace_zoom'])
        self.x_offset_label.setText(self.language_dict[lang]['x_offset'])
        self.y_offset_label.setText(self.language_dict[lang]['y_offset'])
        self.auto_label.setText(self.language_dict[lang]['auto_alignment'])
        self.columns_label.setText(self.language_dict[lang]['columns'])
        self.rows_label.setText(self.language_dict[lang]['rows'])
        self.h_spacing_label.setText(self.language_dict[lang]['horizontal_spacing'])
        self.v_spacing_label.setText(self.language_dict[lang]['vertical_spacing'])
        
        # 检查语言字典中是否包含单个图片大小相关的键，如果没有，添加默认值
        if 'single_image_width' not in self.language_dict[lang]:
            self.language_dict[lang]['single_image_width'] = '单个图片宽度:' if lang == 'zh_CN' else 'Single Image Width:'
        if 'single_image_height' not in self.language_dict[lang]:
            self.language_dict[lang]['single_image_height'] = '单个图片高度:' if lang == 'zh_CN' else 'Single Image Height:'
        
        self.single_image_width_label.setText(self.language_dict[lang]['single_image_width'])
        self.single_image_height_label.setText(self.language_dict[lang]['single_image_height'])
        
        # 更新复选框文本
        self.stitch_by_group_check.setText(self.language_dict[self.current_language]['stitch_by_group'])
        
        # 更新自动对齐下拉框选项
        self.auto_align_combo.clear()
        self.auto_align_combo.addItems([
            self.language_dict[lang]['none'],
            self.language_dict[lang]['left_align'],
            self.language_dict[lang]['right_align'],
            self.language_dict[lang]['top_align'],
            self.language_dict[lang]['bottom_align'],
            self.language_dict[lang]['center_align']
        ])
        
        # 更新工作区无图片提示
        if not self.images_data:
            self.workspace_label.setText(self.language_dict[lang]['no_image_selected'])
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(self.language_dict[self.current_language]['window_title'])
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
        main_layout.addLayout(language_layout)
        
        # 顶部控制区域
        self.control_group = QGroupBox(self.language_dict[self.current_language]['control_options'])
        control_layout = QGridLayout(self.control_group)
        # 限制控制选项区域的最大高度
        self.control_group.setMaximumHeight(180)
        
        # 导入图片按钮
        self.import_btn = QPushButton(self.language_dict[self.current_language]['import_images'])
        self.import_btn.clicked.connect(self.import_images)
        control_layout.addWidget(self.import_btn, 0, 0)
        
        # 网格大小设置
        self.grid_size_label = QLabel(self.language_dict[self.current_language]['grid_size'])
        control_layout.addWidget(self.grid_size_label, 0, 1)
        self.grid_spin = QSpinBox()
        self.grid_spin.setRange(8, 256)
        self.grid_spin.setValue(64)
        self.grid_spin.valueChanged.connect(self.update_grid_size)
        control_layout.addWidget(self.grid_spin, 0, 2)
        
        # 显示选项
        self.grid_check = QCheckBox(self.language_dict[self.current_language]['show_grid'])
        self.grid_check.setChecked(True)
        self.grid_check.stateChanged.connect(self.toggle_grid)
        control_layout.addWidget(self.grid_check, 0, 3)
        
        self.center_check = QCheckBox(self.language_dict[self.current_language]['show_center'])
        self.center_check.setChecked(True)
        self.center_check.stateChanged.connect(self.toggle_center)
        control_layout.addWidget(self.center_check, 0, 4)
        
        # 当前图片显示选项
        self.current_image_check = QCheckBox(self.language_dict[self.current_language]['show_current_image'])
        self.current_image_check.setChecked(True)
        self.current_image_check.stateChanged.connect(self.toggle_current_image)
        control_layout.addWidget(self.current_image_check, 0, 5)
        
        # 参考图选项
        self.ref_label = QLabel(self.language_dict[self.current_language]['reference_image'])
        control_layout.addWidget(self.ref_label, 1, 0)
        self.ref_combo = QComboBox()
        self.ref_combo.setEnabled(False)
        self.ref_combo.currentIndexChanged.connect(self.set_reference_image)
        control_layout.addWidget(self.ref_combo, 1, 1, 1, 2)
        
        self.ref_check = QCheckBox(self.language_dict[self.current_language]['show_reference'])
        self.ref_check.setChecked(False)
        self.ref_check.stateChanged.connect(self.toggle_reference)
        self.ref_check.setEnabled(False)
        control_layout.addWidget(self.ref_check, 1, 3)
        
        # 参考图透明度
        self.ref_opacity_label = QLabel(self.language_dict[self.current_language]['reference_opacity'])
        control_layout.addWidget(self.ref_opacity_label, 2, 0)
        self.ref_opacity_slider = QSlider(Qt.Horizontal)
        self.ref_opacity_slider.setRange(10, 100)
        self.ref_opacity_slider.setValue(50)
        self.ref_opacity_slider.setEnabled(False)
        self.ref_opacity_slider.valueChanged.connect(self.update_ref_opacity)
        control_layout.addWidget(self.ref_opacity_slider, 2, 1, 1, 3)
        # 参考图透明度值标签
        self.ref_opacity_value_label = QLabel("50%") 
        control_layout.addWidget(self.ref_opacity_value_label, 2, 4)
        
        # 工作区缩放控制
        self.zoom_label_text = QLabel(self.language_dict[self.current_language]['workspace_zoom'])
        control_layout.addWidget(self.zoom_label_text, 3, 0)
        zoom_layout = QHBoxLayout()
        
        self.zoom_out_btn = QPushButton(self.language_dict[self.current_language]['zoom_out'])
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_out_btn.setEnabled(False)
        zoom_layout.addWidget(self.zoom_out_btn)
        
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(int(self.min_zoom * 100), int(self.max_zoom * 100))
        self.zoom_slider.setValue(int(self.zoom_factor * 100))
        self.zoom_slider.setEnabled(False)
        self.zoom_slider.valueChanged.connect(self.update_zoom)
        zoom_layout.addWidget(self.zoom_slider, 1)
        
        self.zoom_in_btn = QPushButton(self.language_dict[self.current_language]['zoom_in'])
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_in_btn.setEnabled(False)
        zoom_layout.addWidget(self.zoom_in_btn)
        
        self.reset_zoom_btn = QPushButton(self.language_dict[self.current_language]['reset_zoom'])
        self.reset_zoom_btn.clicked.connect(self.reset_zoom)
        self.reset_zoom_btn.setEnabled(False)
        zoom_layout.addWidget(self.reset_zoom_btn)
        
        self.zoom_label = QLabel("100%")
        zoom_layout.addWidget(self.zoom_label)
        
        control_layout.addLayout(zoom_layout, 3, 1, 1, 4)
        
        # 中间工作区域
        work_layout = QHBoxLayout()
        
        # 左侧图片列表
        self.list_group = QGroupBox(self.language_dict[self.current_language]['image_list'])
        list_layout = QVBoxLayout(self.list_group)
        
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
        
        self.move_up_btn = QPushButton(self.language_dict[self.current_language]['move_up'])
        self.move_up_btn.clicked.connect(self.move_selected_up)
        self.move_up_btn.setEnabled(False)
        order_layout.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton(self.language_dict[self.current_language]['move_down'])
        self.move_down_btn.clicked.connect(self.move_selected_down)
        self.move_down_btn.setEnabled(False)
        order_layout.addWidget(self.move_down_btn)
        
        self.set_ref_btn = QPushButton(self.language_dict[self.current_language]['set_as_reference'])
        self.set_ref_btn.clicked.connect(self.set_selected_as_reference)
        self.set_ref_btn.setEnabled(False)
        order_layout.addWidget(self.set_ref_btn)
        
        self.delete_btn = QPushButton(self.language_dict[self.current_language]['delete_image'])
        self.delete_btn.clicked.connect(self.delete_selected_image)
        self.delete_btn.setEnabled(False)
        order_layout.addWidget(self.delete_btn)
        
        list_layout.addLayout(order_layout)
        
        # 右侧对齐控制
        self.align_group = QGroupBox(self.language_dict[self.current_language]['alignment_control'])
        align_layout = QVBoxLayout(self.align_group)
        
        # X坐标控制
        x_layout = QHBoxLayout()
        self.x_offset_label = QLabel(self.language_dict[self.current_language]['x_offset'])
        x_layout.addWidget(self.x_offset_label)
        self.x_spin = QSpinBox()
        self.x_spin.setRange(-500, 500)
        self.x_spin.setValue(0)
        self.x_spin.valueChanged.connect(self.update_offset)
        x_layout.addWidget(self.x_spin)
        align_layout.addLayout(x_layout)
        
        # Y坐标控制
        y_layout = QHBoxLayout()
        self.y_offset_label = QLabel(self.language_dict[self.current_language]['y_offset'])
        y_layout.addWidget(self.y_offset_label)
        self.y_spin = QSpinBox()
        self.y_spin.setRange(-500, 500)
        self.y_spin.setValue(0)
        self.y_spin.valueChanged.connect(self.update_offset)
        y_layout.addWidget(self.y_spin)
        align_layout.addLayout(y_layout)
        
        # 重置偏移按钮
        self.reset_btn = QPushButton(self.language_dict[self.current_language]['reset_offset'])
        self.reset_btn.clicked.connect(self.reset_offset)
        align_layout.addWidget(self.reset_btn)
        
        # 自动对齐选项
        auto_layout = QVBoxLayout()
        
        # 创建水平布局来容纳标签和下拉框
        auto_label_layout = QHBoxLayout()
        self.auto_label = QLabel(self.language_dict[self.current_language]['auto_alignment'])
        auto_label_layout.addWidget(self.auto_label)
        self.auto_align_combo = QComboBox()
        self.auto_align_combo.addItems([
            self.language_dict[self.current_language]['none'],
            self.language_dict[self.current_language]['left_align'],
            self.language_dict[self.current_language]['right_align'],
            self.language_dict[self.current_language]['top_align'],
            self.language_dict[self.current_language]['bottom_align'],
            self.language_dict[self.current_language]['center_align']
        ])
        auto_label_layout.addWidget(self.auto_align_combo)
        auto_label_layout.addStretch()  # 添加拉伸空间，将组件靠左对齐
        
        # 添加到垂直布局中
        auto_layout.addLayout(auto_label_layout)
        
        # 检查语言字典中是否包含导入导出偏移设置的键
        if 'export_offset' not in self.language_dict[self.current_language]:
            self.language_dict[self.current_language]['export_offset'] = '导出偏移设置'
            self.language_dict[self.current_language]['import_offset'] = '导入偏移设置'
        
        # 单个对齐按钮
        self.auto_align_btn = QPushButton(self.language_dict[self.current_language]['apply_to_current'])
        self.auto_align_btn.clicked.connect(self.apply_auto_align)
        
        # 批量对齐按钮
        self.batch_align_btn = QPushButton(self.language_dict[self.current_language]['batch_apply'])
        self.batch_align_btn.clicked.connect(self.batch_apply_auto_align)
        
        # 导出偏移设置按钮
        self.export_offset_btn = QPushButton(self.language_dict[self.current_language]['export_offset'])
        self.export_offset_btn.clicked.connect(self.export_offset_settings)
        self.export_offset_btn.setEnabled(False)
        
        # 导入偏移设置按钮
        self.import_offset_btn = QPushButton(self.language_dict[self.current_language]['import_offset'])
        self.import_offset_btn.clicked.connect(self.import_offset_settings)
        self.import_offset_btn.setEnabled(False)
        
        auto_layout.addWidget(self.auto_align_btn)
        auto_layout.addWidget(self.batch_align_btn)
        auto_layout.addWidget(self.export_offset_btn)
        auto_layout.addWidget(self.import_offset_btn)
        align_layout.addLayout(auto_layout)
        
        # 中间工作区预览
        self.preview_group = QGroupBox(self.language_dict[self.current_language]['workspace'])
        preview_layout = QVBoxLayout(self.preview_group)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.workspace_label = QLabel()
        self.workspace_label.setAlignment(Qt.AlignCenter)
        self.workspace_label.setMinimumSize(600, 600)
        self.workspace_label.setStyleSheet("border: 1px solid #ccc")
        self.workspace_label.setText(self.language_dict[self.current_language]['no_image_selected'])
        self.workspace_label.mousePressEvent = self.workspace_click
        self.workspace_label.mouseMoveEvent = self.workspace_drag
        self.workspace_label.mouseReleaseEvent = self.workspace_release
        self.workspace_label.wheelEvent = self.workspace_wheel_event  # 添加鼠标滚轮事件处理
        
        scroll_area.setWidget(self.workspace_label)
        preview_layout.addWidget(scroll_area)
        
        # 使用QSplitter来分割区域
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.list_group)
        splitter.addWidget(self.preview_group)
        splitter.addWidget(self.align_group)
        
        # 设置初始大小
        splitter.setSizes([200, 600, 200])
        
        # 设置拉伸因子，让工作区获得更多空间
        # 参数：索引，拉伸因子
        splitter.setStretchFactor(0, 1)  # 左侧图片列表
        splitter.setStretchFactor(1, 4)  # 中间工作区（更大的拉伸因子，横向占比更多）
        splitter.setStretchFactor(2, 1)  # 右侧对齐控制
        
        work_layout.addWidget(splitter)
        
        # 底部拼接控制
        self.stitch_group = QGroupBox(self.language_dict[self.current_language]['stitch_settings'])
        stitch_layout = QGridLayout(self.stitch_group)
        # 限制拼接设置区域的高度
        self.stitch_group.setMaximumHeight(160)

        # 按组拼接选项
        self.stitch_by_group_check = QCheckBox(self.language_dict[self.current_language]['stitch_by_group'])
        self.stitch_by_group_check.setChecked(True)  # 默认勾选
        self.stitch_by_group_check.stateChanged.connect(self.toggle_stitch_mode)
        stitch_layout.addWidget(self.stitch_by_group_check, 0, 0, 1, 2)

        # 行列数设置
        self.columns_label = QLabel(self.language_dict[self.current_language]['columns'])
        stitch_layout.addWidget(self.columns_label, 1, 0)
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 100)
        self.cols_spin.setValue(10)
        stitch_layout.addWidget(self.cols_spin, 1, 1)
        
        self.rows_label = QLabel(self.language_dict[self.current_language]['rows'])
        stitch_layout.addWidget(self.rows_label, 1, 2)
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 100)
        self.rows_spin.setValue(10)
        stitch_layout.addWidget(self.rows_spin, 1, 3)
        # 初始状态：按组拼接选中时禁用行列数设置
        self.toggle_stitch_mode()

        # 间距设置
        self.h_spacing_label = QLabel(self.language_dict[self.current_language]['horizontal_spacing'])
        stitch_layout.addWidget(self.h_spacing_label, 2, 0)
        self.h_spacing_spin = QSpinBox()
        self.h_spacing_spin.setRange(0, 100)
        self.h_spacing_spin.setValue(0)
        stitch_layout.addWidget(self.h_spacing_spin, 2, 1)
        
        self.v_spacing_label = QLabel(self.language_dict[self.current_language]['vertical_spacing'])
        stitch_layout.addWidget(self.v_spacing_label, 2, 2)
        self.v_spacing_spin = QSpinBox()
        self.v_spacing_spin.setRange(0, 100)
        self.v_spacing_spin.setValue(0)
        stitch_layout.addWidget(self.v_spacing_spin, 2, 3)
        
        # 单个图片大小设置
        # 首先检查语言字典中是否包含单个图片宽度和高度的键
        if 'single_image_width' not in self.language_dict[self.current_language]:
            self.language_dict[self.current_language]['single_image_width'] = '单个图片宽度:'
            self.language_dict[self.current_language]['single_image_height'] = '单个图片高度:'
        
        # 检查语言字典中是否包含导入导出偏移设置的键
        if 'export_offset' not in self.language_dict[self.current_language]:
            self.language_dict[self.current_language]['export_offset'] = '导出偏移设置'
            self.language_dict[self.current_language]['import_offset'] = '导入偏移设置'
        
        self.single_image_width_label = QLabel(self.language_dict[self.current_language]['single_image_width'])
        stitch_layout.addWidget(self.single_image_width_label, 3, 0)
        self.single_image_width_spin = QSpinBox()

        self.single_image_width_spin.setRange(0, 4096)
        self.single_image_width_spin.setValue(0)
        stitch_layout.addWidget(self.single_image_width_spin, 3, 1)
        
        self.single_image_height_label = QLabel(self.language_dict[self.current_language]['single_image_height'])
        stitch_layout.addWidget(self.single_image_height_label, 3, 2)
        self.single_image_height_spin = QSpinBox()
        self.single_image_height_spin.setRange(0, 4096)
        self.single_image_height_spin.setValue(0)
        stitch_layout.addWidget(self.single_image_height_spin, 3, 3)
        
        # 底部按钮区域
        button_layout = QHBoxLayout()
        
        self.stitch_save_btn = QPushButton(self.language_dict[self.current_language]['stitch_save'])
        self.stitch_save_btn.clicked.connect(self.stitch_and_save_sprites)
        self.stitch_save_btn.setEnabled(False)
        button_layout.addWidget(self.stitch_save_btn)
        
        # 添加到主布局
        main_layout.addWidget(self.control_group)
        main_layout.addLayout(work_layout)
        main_layout.addWidget(self.stitch_group)
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
        # 询问用户导入方式
        msg_box = QMessageBox()
        msg_box.setWindowTitle(self.language_dict[self.current_language]['select_split_images'])
        msg_box.setText(self.language_dict[self.current_language]['select_import_method'])
        
        # 添加按钮
        file_btn = msg_box.addButton(self.language_dict[self.current_language]['import_by_files'], QMessageBox.ActionRole)
        folder_btn = msg_box.addButton(self.language_dict[self.current_language]['import_by_folders'], QMessageBox.ActionRole)
        cancel_btn = msg_box.addButton(QMessageBox.Cancel)
        
        msg_box.exec_()
        
        # 获取用户选择
        clicked_btn = msg_box.clickedButton()
        
        if clicked_btn == file_btn:
            # 文件方式导入
            dialog = QFileDialog()
            dialog.setWindowTitle(self.language_dict[self.current_language]['select_split_images'])
            dialog.setFileMode(QFileDialog.ExistingFiles)
            dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp *.gif)")
            dialog.setDirectory(self.last_selected_path)
            
            if dialog.exec_():
                selected_files = dialog.selectedFiles()
                if selected_files:
                    # 更新最后选择的路径
                    if selected_files:
                        self.update_last_selected_path(selected_files[0])
                    self.process_imported_items(selected_files, is_files=True)
        elif clicked_btn == folder_btn:
            # 文件夹方式导入
            # 创建自定义文件选择对话框
            dialog = AdvancedImageFileDialog(self, self.language_dict, self.current_language, self.last_selected_path)
            dialog.setWindowTitle(self.language_dict[self.current_language]['select_split_images'])
            if dialog.exec_():
                selected_folders = dialog.selectedFiles()
                if selected_folders:
                    # 更新最后选择的路径
                    if selected_folders:
                        self.update_last_selected_path(selected_folders[0])
                    self.process_imported_items(selected_folders, is_files=False)
    
    def process_imported_items(self, items, is_files):
        """处理导入的文件或文件夹"""
        # 清空之前的数据
        self.image_files = []
        self.images_data = []
        self.image_list.clear()
        self.ref_combo.clear()
        
        # 收集所有图片文件
        all_image_files = []
        
        if is_files:
            # 处理文件列表
            for file_path in items:
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    folder_path = os.path.dirname(file_path)
                    all_image_files.append((folder_path, file_path))
        else:
            # 处理文件夹列表
            for folder_path in items:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                            file_path = os.path.join(root, file)
                            all_image_files.append((folder_path, file_path))
        
        # 添加图片文件
        for folder_path, file_path in all_image_files:
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
            # 添加到列表，带文件夹前缀
            group_name = os.path.basename(folder_path)
            filename = os.path.basename(file_path)
            display_name = f"[{group_name}] {filename}"
            self.image_list.addItem(display_name)
            self.ref_combo.addItem(display_name)
        
        QMessageBox.information(self, self.language_dict[self.current_language]['success'], 
                               self.language_dict[self.current_language]['success_imported'].format(len(all_image_files)))
        
        self.stitch_save_btn.setEnabled(True)
        self.export_offset_btn.setEnabled(True)
        self.import_offset_btn.setEnabled(True)
        
        # 启用相关控件
        if len(all_image_files) > 0:
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
            QMessageBox.information(self, self.language_dict[self.current_language]['success'], 
                                   self.language_dict[self.current_language]['success_set_reference'].format(
                                       os.path.basename(self.images_data[self.selected_index]['file_path'])))
            self.update_workspace()
    
    def delete_selected_image(self):
        """删除选中的图片"""
        # 获取当前选中的行索引，直接从列表控件获取
        current_row = self.image_list.currentRow()
        if current_row < 0 or current_row >= len(self.images_data):
            return
        
        # 使用当前行索引而不是self.selected_index
        delete_index = current_row
        
        # 获取要删除的图片信息
        img_data = self.images_data[delete_index]
        img_name = os.path.basename(img_data['file_path'])
        
        # 显示确认对话框
        reply = QMessageBox.question(
            self, self.language_dict[self.current_language]['confirm_remove'], 
            self.language_dict[self.current_language]['confirm_remove_image'].format(img_name),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除图片
            # 1. 从图片列表中删除
            self.image_list.takeItem(delete_index)
            
            # 2. 从数据列表中删除
            del self.images_data[delete_index]
            
            # 3. 从文件路径列表中删除对应的项
            if delete_index < len(self.image_files):
                del self.image_files[delete_index]
            
            # 4. 更新参考图下拉框
            self.update_ref_combo_order()
            
            # 5. 检查是否删除的是参考图
            if self.ref_index == delete_index:
                self.ref_index = -1
                self.show_ref = False
                self.ref_check.setChecked(False)
            elif self.ref_index > delete_index:
                # 如果参考图索引大于删除的索引，需要递减
                self.ref_index -= 1
            
            # 6. 更新当前选中索引
            total_items = self.image_list.count()
            if total_items > 0:
                # 如果还有图片，选择新的图片
                new_index = min(delete_index, total_items - 1)
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
                self.export_offset_btn.setEnabled(False)
                self.import_offset_btn.setEnabled(False)
                # 禁用缩放控件
                self.zoom_slider.setEnabled(False)
                self.zoom_in_btn.setEnabled(False)
                self.zoom_out_btn.setEnabled(False)
                self.reset_zoom_btn.setEnabled(False)
                # 禁用参考图控件
                self.ref_combo.setEnabled(False)
                self.ref_check.setEnabled(False)
                self.ref_opacity_slider.setEnabled(False)
            
            # 7. 更新工作区显示
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
        """根据图片列表的顺序更新images_data列表和image_files列表"""
        new_order = []
        new_files_order = []
        for i in range(self.image_list.count()):
            # 获取项目文本
            item_text = self.image_list.item(i).text()
            # 找到对应的图片数据
            for img_data in self.images_data:
                if os.path.basename(img_data['file_path']) == item_text:
                    new_order.append(img_data)
                    # 添加到新的文件路径列表
                    new_files_order.append(img_data['file_path'])
                    break
        # 更新images_data列表
        self.images_data = new_order
        # 更新image_files列表
        self.image_files = new_files_order
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
        self.ref_opacity_value_label.setText(f"{value}%")
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
        if align_type == self.language_dict[self.current_language]['none'] or self.selected_index < 0:
            return
        
        # 获取当前图片数据
        img_data = self.images_data[self.selected_index]
        img_width = img_data['width']
        img_height = img_data['height']
        
        # 计算偏移量
        offset_x, offset_y, update_x, update_y = self.calculate_align_offset(img_width, img_height, align_type)
        
        # 更新偏移量（只更新相关方向）
        if update_x:
            self.images_data[self.selected_index]['offset_x'] = offset_x
        if update_y:
            self.images_data[self.selected_index]['offset_y'] = offset_y
        
        # 更新控件值
        self.x_spin.setValue(self.images_data[self.selected_index]['offset_x'])
        self.y_spin.setValue(self.images_data[self.selected_index]['offset_y'])
        
        # 更新工作区显示
        self.update_workspace()
    
    def batch_apply_auto_align(self):
        """批量应用自动对齐到所有图片"""
        align_type = self.auto_align_combo.currentText()
        if align_type == self.language_dict[self.current_language]['none']:
            QMessageBox.warning(self, self.language_dict[self.current_language]['warning'], 
                              self.language_dict[self.current_language]['please_select_align_type'])
            return
        
        # 显示确认对话框
        reply = QMessageBox.question(
            self, self.language_dict[self.current_language]['confirm_batch_align'], 
            self.language_dict[self.current_language]['confirm_batch_align_message'].format(
                align_type, len(self.images_data)),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 批量应用对齐方案
            for i, img_data in enumerate(self.images_data):
                img_width = img_data['width']
                img_height = img_data['height']
                
                # 计算偏移量
                offset_x, offset_y, update_x, update_y = self.calculate_align_offset(img_width, img_height, align_type)
                
                # 更新偏移量（只更新相关方向）
                if update_x:
                    self.images_data[i]['offset_x'] = offset_x
                if update_y:
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
        offset_x = 0
        offset_y = 0
        update_x = False
        update_y = False
        
        if align_type == self.language_dict[self.current_language]['center_align']:
            # 图片中心点精确对齐到工作区中心点
            offset_x = 0
            offset_y = 0
            update_x = True
            update_y = True
        elif align_type == self.language_dict[self.current_language]['left_align']:
            # 图片中心点对齐到工作区中心点左侧，距离为图片宽度的一半
            offset_x = -img_width // 2
            update_x = True
            update_y = False
        elif align_type == self.language_dict[self.current_language]['right_align']:
            # 图片中心点对齐到工作区中心点右侧，距离为图片宽度的一半
            offset_x = img_width // 2
            update_x = True
            update_y = False
        elif align_type == self.language_dict[self.current_language]['top_align']:
            # 图片中心点对齐到工作区中心点上方，距离为图片高度的一半
            offset_y = -img_height // 2
            update_x = False
            update_y = True
        elif align_type == self.language_dict[self.current_language]['bottom_align']:
            # 图片中心点对齐到工作区中心点下方，距离为图片高度的一半
            offset_y = img_height // 2
            update_x = False
            update_y = True
        else:
            offset_x = 0
            offset_y = 0
            update_x = False
            update_y = False
        
        return offset_x, offset_y, update_x, update_y
    
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
            
            # 更新偏移量（考虑缩放因子）
            if 0 <= self.selected_index < len(self.images_data):
                # 将鼠标移动的像素值除以缩放因子，得到原始像素偏移量
                adjusted_delta_x = int(delta.x() / self.zoom_factor)
                adjusted_delta_y = int(delta.y() / self.zoom_factor)
                
                self.images_data[self.selected_index]['offset_x'] += adjusted_delta_x
                self.images_data[self.selected_index]['offset_y'] += adjusted_delta_y
                
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
            
            # 获取用户指定的单个图片大小（如果有）
            single_width = self.single_image_width_spin.value()
            single_height = self.single_image_height_spin.value()
            
            # 1. 首先计算所有图片的原始尺寸和最大尺寸
            all_images = []
            
            # 如果用户指定了单个图片大小，使用指定大小作为单元格大小
            if single_width > 0 and single_height > 0:
                cell_width = single_width + h_spacing
                cell_height = single_height + v_spacing
            else:
                # 否则，计算所有图片的最大原始尺寸作为单元格大小
                max_width = 0
                max_height = 0
                for img_data in self.images_data:
                    with Image.open(img_data['file_path']) as img:
                        orig_width, orig_height = img.size
                        max_width = max(max_width, orig_width)
                        max_height = max(max_height, orig_height)
                
                cell_width = max_width + h_spacing
                cell_height = max_height + v_spacing
            
            # 收集所有图片数据，并按组名分组
            grouped_images = {}
            for img_data in self.images_data:
                with Image.open(img_data['file_path']) as img:
                    orig_width, orig_height = img.size
                    # 从列表项文本中获取组名
                    list_item_text = self.image_list.item(self.images_data.index(img_data)).text()
                    group_name = "默认组"
                    # 检查是否包含组名前缀
                    if list_item_text.startswith('['):
                        group_end = list_item_text.find(']')
                        if group_end > 0:
                            group_name = list_item_text[1:group_end]
                    
                    # 将图片添加到对应组
                    if group_name not in grouped_images:
                        grouped_images[group_name] = []
                    grouped_images[group_name].append((img_data, orig_width, orig_height))
            
            # 确定单元格的基准尺寸（不包含间距）
            if single_width > 0 and single_height > 0:
                base_cell_width = single_width
                base_cell_height = single_height
            else:
                base_cell_width = max_width
                base_cell_height = max_height
            
            # 3. 计算所有图片在拼接图中的实际位置和尺寸
            # 我们需要找到整个拼接图的最小和最大坐标，以确定最终尺寸
            min_x = float('inf')
            min_y = float('inf')
            max_x = 0
            max_y = 0
            
            # 收集所有图片的位置信息
            image_positions = []
            
            # 检查是否按组拼接
            stitch_by_group = self.stitch_by_group_check.isChecked()
            
            if stitch_by_group:
                # 按组拼接：每个组占据一行
                current_row = 0
                
                # 遍历每个组
                for group_name, images in grouped_images.items():
                    # 为每个组创建一行
                    for i, (img_data, orig_width, orig_height) in enumerate(images):
                        if i >= cols:
                            break
                        
                        # 计算当前图片在网格中的行列位置
                        # 同一组的图片在同一行
                        row = current_row
                        col = i % cols
                        
                        # 计算单元格左上角坐标（不考虑偏移）
                        cell_x = col * cell_width
                        cell_y = row * cell_height
                        
                        # 计算图片在单元格中的偏移量（考虑用户调整）
                        offset_x = img_data['offset_x']
                        offset_y = img_data['offset_y']
                        
                        # 计算单元格中心位置
                        cell_center_x = cell_x + base_cell_width // 2
                        cell_center_y = cell_y + base_cell_height // 2
                        
                        # 计算图片中心点在单元格中的位置（考虑偏移量）
                        center_x = cell_center_x + offset_x
                        center_y = cell_center_y + offset_y
                        
                        # 计算图片左上角和右下角坐标
                        # 如果用户指定了单个图片大小，使用指定大小，否则使用原始图片大小
                        if single_width > 0 and single_height > 0:
                            # 使用用户指定的大小计算坐标
                            img_left = center_x - single_width // 2
                            img_top = center_y - single_height // 2
                            img_right = center_x + single_width // 2
                            img_bottom = center_y + single_height // 2
                        else:
                            # 使用原始图片大小计算坐标
                            img_left = center_x - orig_width // 2
                            img_top = center_y - orig_height // 2
                            img_right = center_x + orig_width // 2
                            img_bottom = center_y + orig_height // 2
                        
                        # 更新全局坐标范围
                        min_x = min(min_x, img_left)
                        min_y = min(min_y, img_top)
                        max_x = max(max_x, img_right)
                        max_y = max(max_y, img_bottom)
                        
                        # 保存图片位置信息
                        image_positions.append({
                            'img_data': img_data,
                            'orig_width': orig_width,
                            'orig_height': orig_height,
                            'left': img_left,
                            'top': img_top,
                            'center_x': center_x,
                            'center_y': center_y
                        })
                    
                    # 下一组换行
                    current_row += 1
            else:
                # 不按组拼接：按照指定的列数和行数依次摆放所有图片
                all_images = []
                for group_name, images in grouped_images.items():
                    for img_data, orig_width, orig_height in images:
                        all_images.append((img_data, orig_width, orig_height))
                
                # 按照指定的行数和列数依次摆放
                total_images = len(all_images)
                max_images = cols * rows
                
                for i in range(min(total_images, max_images)):
                    img_data, orig_width, orig_height = all_images[i]
                    
                    # 计算当前图片在网格中的行列位置
                    row = i // cols
                    col = i % cols
                    
                    # 计算单元格左上角坐标（不考虑偏移）
                    cell_x = col * cell_width
                    cell_y = row * cell_height
                    
                    # 计算图片在单元格中的偏移量（考虑用户调整）
                    offset_x = img_data['offset_x']
                    offset_y = img_data['offset_y']
                    
                    # 计算单元格中心位置
                    cell_center_x = cell_x + base_cell_width // 2
                    cell_center_y = cell_y + base_cell_height // 2
                    
                    # 计算图片中心点在单元格中的位置（考虑偏移量）
                    center_x = cell_center_x + offset_x
                    center_y = cell_center_y + offset_y
                    
                    # 计算图片左上角和右下角坐标
                    # 使用与工作区显示相同的逻辑：中心点对齐 + 偏移量
                    # 如果用户指定了单个图片大小，使用指定大小，否则使用原始图片大小
                    if single_width > 0 and single_height > 0:
                        # 使用用户指定的大小计算坐标
                        img_left = center_x - single_width // 2 + offset_x
                        img_top = center_y - single_height // 2 + offset_y
                        img_right = center_x + single_width // 2 + offset_x
                        img_bottom = center_y + single_height // 2 + offset_y
                    else:
                        # 使用原始图片大小计算坐标
                        img_left = center_x - orig_width // 2 + offset_x
                        img_top = center_y - orig_height // 2 + offset_y
                        img_right = center_x + orig_width // 2 + offset_x
                        img_bottom = center_y + orig_height // 2 + offset_y
                    
                    # 更新全局坐标范围
                    min_x = min(min_x, img_left)
                    min_y = min(min_y, img_top)
                    max_x = max(max_x, img_right)
                    max_y = max(max_y, img_bottom)
                    
                    # 保存图片位置信息
                    image_positions.append({
                        'img_data': img_data,
                        'orig_width': orig_width,
                        'orig_height': orig_height,
                        'left': img_left,
                        'top': img_top,
                        'center_x': center_x,
                        'center_y': center_y
                    })
            
            # 4. 计算最终拼接图的尺寸
            # 使用自动计算的尺寸，基于单个图片大小和行列数
            total_width = max(int(max_x - min_x), 0)
            total_height = max(int(max_y - min_y), 0)
            offset_adjust_x = -min_x
            offset_adjust_y = -min_y
            
            # 5. 创建新的空白图片
            stitch_img = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
            
            # 6. 粘贴所有图片到正确位置
            for pos in image_positions:
                img_data = pos['img_data']
                orig_width = pos['orig_width']
                orig_height = pos['orig_height']
                
                # 计算调整后的粘贴位置
                paste_x = int(pos['left'] + offset_adjust_x)
                paste_y = int(pos['top'] + offset_adjust_y)
                
                # 打开图片
                with Image.open(img_data['file_path']) as img:
                    # 如果用户指定了单个图片大小，将图片调整到指定大小，填充透明背景
                    if single_width > 0 and single_height > 0:
                        # 创建指定大小的透明背景图片
                        resized_img = Image.new('RGBA', (single_width, single_height), (0, 0, 0, 0))
                        
                        # 计算原始图片在透明背景中的居中位置
                        paste_center_x = (single_width - orig_width) // 2
                        paste_center_y = (single_height - orig_height) // 2
                        
                        # 将原始图片居中粘贴到透明背景上
                        resized_img.paste(img, (paste_center_x, paste_center_y), img if img.mode == 'RGBA' else None)
                        
                        # 使用调整后的图片进行粘贴
                        stitch_img.paste(resized_img, (paste_x, paste_y), resized_img)
                    else:
                        # 否则，直接使用原始图片进行粘贴
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
                    self, "保存拼接结果", self.last_selected_path, "PNG Files (*.png);;All Files (*)"
                )
                
                if file_path:
                    # 更新最后选择的路径
                    self.update_last_selected_path(file_path)
                    # 保存拼接结果
                    stitch_img.save(file_path, 'PNG')
                    QMessageBox.information(self, "成功", f"拼接结果已保存到：{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败：{str(e)}")
    
    def export_offset_settings(self):
        """导出图片偏移设置到文件"""
        if not self.images_data:
            QMessageBox.warning(self, "警告", "没有图片数据可以导出")
            return
        
        try:
            # 收集所有图片的偏移数据
            offset_data = []
            for img_data in self.images_data:
                offset_info = {
                    'file_path': img_data['file_path'],
                    'filename': os.path.basename(img_data['file_path']),
                    'offset_x': img_data['offset_x'],
                    'offset_y': img_data['offset_y']
                }
                offset_data.append(offset_info)
            
            # 打开文件保存对话框
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出偏移设置", self.last_selected_path, "JSON Files (*.json);;All Files (*)"
            )
            
            if file_path:
                # 更新最后选择的路径
                self.update_last_selected_path(file_path)
                # 将偏移数据保存到JSON文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(offset_data, f, ensure_ascii=False, indent=4)
                
                QMessageBox.information(self, "成功", f"偏移设置已导出到：{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：{str(e)}")
    
    def import_offset_settings(self):
        """从文件导入图片偏移设置"""
        if not self.images_data:
            QMessageBox.warning(self, "警告", "请先导入图片")
            return
        
        try:
            # 打开文件选择对话框
            file_path, _ = QFileDialog.getOpenFileName(
                self, "导入偏移设置", self.last_selected_path, "JSON Files (*.json);;All Files (*)"
            )
            
            if file_path:
                # 更新最后选择的路径
                self.update_last_selected_path(file_path)
                # 从JSON文件加载偏移数据
                with open(file_path, 'r', encoding='utf-8') as f:
                    offset_data = json.load(f)
                
                # 应用偏移数据到图片
                applied_count = 0
                for offset_info in offset_data:
                    # 查找对应的图片
                    for img_data in self.images_data:
                        if os.path.basename(img_data['file_path']) == offset_info['filename']:
                            # 应用偏移量
                            img_data['offset_x'] = offset_info['offset_x']
                            img_data['offset_y'] = offset_info['offset_y']
                            applied_count += 1
                            break
                
                # 更新当前选中图片的偏移控件值
                if 0 <= self.selected_index < len(self.images_data):
                    current_img = self.images_data[self.selected_index]
                    self.x_spin.setValue(current_img['offset_x'])
                    self.y_spin.setValue(current_img['offset_y'])
                
                # 更新工作区显示
                self.update_workspace()
                
                QMessageBox.information(self, "成功", f"已应用 {applied_count} 个偏移设置")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败：{str(e)}")
    
    def toggle_stitch_mode(self):
        """切换拼接模式：按组拼接时禁用行列数设置，否则启用"""
        stitch_by_group = self.stitch_by_group_check.isChecked()
        
        # 启用或禁用行列数设置控件
        self.columns_label.setEnabled(not stitch_by_group)
        self.cols_spin.setEnabled(not stitch_by_group)
        self.rows_label.setEnabled(not stitch_by_group)
        self.rows_spin.setEnabled(not stitch_by_group)
    
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
