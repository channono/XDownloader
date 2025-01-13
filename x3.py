import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLineEdit, QPushButton, QLabel, 
                            QFileDialog, QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, QSettings, QThread, pyqtSignal
import yt_dlp

class DownloaderThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str, str)

    def __init__(self, url, output_dir):
        super().__init__()
        self.url = url
        self.output_dir = os.path.abspath(output_dir)  # 确保使用绝对路径
        self.downloaded_file = None

    def run(self):
        try:
            # 确保输出目录存在
            os.makedirs(self.output_dir, exist_ok=True)
            
            # 构建完整的输出路径模板
            output_template = os.path.join(self.output_dir, '%(title)s.%(ext)s')
            self.progress.emit(f"下载目录: {self.output_dir}")

            ydl_opts = {
                'format': 'best',
                'outtmpl': output_template,
                'progress_hooks': [self.progress_hook],
                'verbose': True,
                'retries': 10,
                'fragment_retries': 10,
                'continuedl': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 下载前先获取信息
                info = ydl.extract_info(self.url, download=False)
                if info:
                    # 预先计算文件名
                    title = info.get('title', 'video')
                    ext = info.get('ext', 'mp4')
                    safe_title = "".join(x for x in title if x.isalnum() or x in (' ', '-', '_')).strip()
                    expected_filename = f"{safe_title}.{ext}"
                    self.downloaded_file = os.path.join(self.output_dir, expected_filename)
                    
                    self.progress.emit(f"准备下载到: {self.downloaded_file}")
                    
                    # 开始下载
                    ydl.download([self.url])
                    
                    # 检查文件是否存在
                    if os.path.exists(self.downloaded_file):
                        self.progress.emit(f"文件已保存到: {self.downloaded_file}")
                        self.finished.emit(True, "下载完成！", self.downloaded_file)
                    else:
                        # 尝试在目录中查找最新下载的文件
                        files = [f for f in os.listdir(self.output_dir) if f.endswith(ext)]
                        if files:
                            newest_file = max(files, key=lambda x: os.path.getctime(os.path.join(self.output_dir, x)))
                            actual_file = os.path.join(self.output_dir, newest_file)
                            self.downloaded_file = actual_file
                            self.progress.emit(f"文件已保存到: {actual_file}")
                            self.finished.emit(True, "下载完成！", actual_file)
                        else:
                            raise Exception(f"无法找到下载的文件在: {self.output_dir}")
            
        except Exception as e:
            self.progress.emit(f"错误: {str(e)}")
            self.finished.emit(False, f"下载失败: {str(e)}", "")

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                progress = d.get('_percent_str', '未知')
                speed = d.get('_speed_str', '未知')
                filename = os.path.basename(d.get('filename', ''))
                self.progress.emit(f'正在下载: {filename}\n进度: {progress} 速度: {speed}')
            except Exception as e:
                self.progress.emit(f'下载中... {str(e)}')
        elif d['status'] == 'finished':
            try:
                filename = os.path.basename(d.get('filename', ''))
                self.progress.emit(f'下载完成: {filename}\n正在处理...')
            except:
                self.progress.emit('下载完成，正在处理...')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('XDownloader', 'Settings')
        self.initUI()
        self.downloader = None

    def initUI(self):
        self.setWindowTitle('X.com 媒体下载器')
        self.setMinimumWidth(600)

        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 添加标题标签
        title_label = QLabel('😄 大牛大巨婴 👌')
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                margin: 10px;
                padding: 10px;
            }
        """)
        layout.addWidget(title_label)

        # URL输入区域
        url_layout = QHBoxLayout()
        url_label = QLabel('URL:')
        self.url_input = QLineEdit()
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)

        # 其余代码保持不变...
        # 下载路径选择区域
        path_layout = QHBoxLayout()
        path_label = QLabel('保存位置:')
        self.path_input = QLineEdit()
        self.path_input.setText(self.settings.value('last_directory', 
                            os.path.expanduser('~/Downloads')))
        browse_button = QPushButton('浏览...')
        browse_button.clicked.connect(self.browse_directory)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_button)
        layout.addLayout(path_layout)

        # 设为默认按钮
        set_default_button = QPushButton('设为默认下载路径')
        set_default_button.clicked.connect(self.set_default_directory)
        layout.addWidget(set_default_button)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel('')
        layout.addWidget(self.status_label)

        # 下载按钮
        download_button = QPushButton('开始下载')
        download_button.clicked.connect(self.start_download)
        layout.addWidget(download_button)

        # 设置窗口位置
        self.center()


    def center(self):
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, 
            "选择下载目录",
            self.path_input.text(),
            QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.path_input.setText(directory)
            self.settings.setValue('last_directory', directory)

    def set_default_directory(self):
        current_dir = self.path_input.text()
        if os.path.exists(current_dir):
            self.settings.setValue('default_directory', current_dir)
            QMessageBox.information(self, '成功', '已设置为默认下载目录')
        else:
            QMessageBox.warning(self, '错误', '请选择有效的目录')

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, '错误', '请输入URL')
            return

        output_dir = os.path.abspath(self.path_input.text())
        self.status_label.setText(f'输出目录: {output_dir}')
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                self.status_label.setText(f'创建目录: {output_dir}')
            except Exception as e:
                QMessageBox.warning(self, '错误', f'创建目录失败: {str(e)}')
                return

        self.status_label.setText(f'准备下载到: {output_dir}')
        self.progress_bar.setFormat('准备中...')
        
        self.downloader = DownloaderThread(url, output_dir)
        self.downloader.progress.connect(self.update_progress)
        self.downloader.finished.connect(self.download_finished)
        self.downloader.start()

    def update_progress(self, progress_text):
        self.status_label.setText(progress_text)
        self.progress_bar.setFormat(progress_text)

    def download_finished(self, success, message, file_path=''):
        if success:
            if os.path.exists(file_path):
                QMessageBox.information(
                    self, 
                    '完成', 
                    f"{message}\n\n文件已保存到：\n{file_path}\n\n文件大小：{os.path.getsize(file_path) / 1024 / 1024:.2f} MB"
                )
                self.open_file_location(file_path)
            else:
                QMessageBox.warning(
                    self,
                    '警告',
                    f"下载似乎完成了，但文件未找到：\n{file_path}"
                )
        else:
            QMessageBox.warning(self, '错误', message)
        
        self.status_label.setText('')
        self.progress_bar.setFormat('')

    def open_file_location(self, file_path):
        """打开文件所在文件夹"""
        if os.path.exists(file_path):
            if sys.platform == 'darwin':  # macOS
                os.system(f'open -R "{file_path}"')
            elif sys.platform == 'win32':  # Windows
                os.system(f'explorer /select,"{file_path}"')
            else:  # Linux
                os.system(f'xdg-open "{os.path.dirname(file_path)}"')

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
