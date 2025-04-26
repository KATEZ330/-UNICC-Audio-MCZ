import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import time
import os
import traceback
import logging
import tempfile
from config import ANALYSIS_TYPES
from api.iflytek_api import IflytekAPI
from utils.audio_utils import process_mp3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import ttkthemes

logger = logging.getLogger(__name__)

class MediaAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("English Media Content Analyzer")
        self.root.geometry("1200x900")
        
        # 添加取消分析标志
        self.cancel_analysis = False
        
        # 应用现代主题
        self.style = ttkthemes.ThemedStyle(self.root)
        self.style.set_theme("arc")  # 使用现代化的arc主题
        
        try:
            # Initialize iFlytek API
            self.iflytek_api = IflytekAPI()
            logger.info("API initialized successfully")
            
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            messagebox.showerror("Error", f"Initialization failed: {str(e)}")
        
        self.setup_gui()
        
    def setup_gui(self):
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题和描述
        title_frame = ttk.Frame(self.main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, pady=10)
        
        title_label = ttk.Label(title_frame, text="English Media Content Analyzer", 
                               font=('Helvetica', 20, 'bold'))
        title_label.pack()
        
        desc_label = ttk.Label(title_frame, 
                              text="Analyze English media content for quality and compliance",
                              font=('Helvetica', 12))
        desc_label.pack()
        
        # 左侧面板 - 控制区域
        control_frame = ttk.LabelFrame(self.main_frame, text="Controls", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # 分析类型选择
        analysis_frame = ttk.LabelFrame(control_frame, text="Analysis Types", padding="5")
        analysis_frame.pack(fill=tk.X, pady=5)
        
        self.analysis_vars = {
            key: tk.BooleanVar(value=True) for key in ANALYSIS_TYPES.keys()
        }
        
        for key, var in self.analysis_vars.items():
            ttk.Checkbutton(analysis_frame, text=ANALYSIS_TYPES[key], 
                           variable=var).pack(anchor=tk.W)
        
        # URL输入框
        url_frame = ttk.Frame(control_frame)
        url_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(url_frame, text="Audio file URL:").pack(side=tk.LEFT, padx=5)
        self.url_entry = ttk.Entry(url_frame, width=40)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.url_entry.insert(0, "https://drive.google.com/file/d/1EJgCY7GXiVnTMfFAfKU7bQZfAJakTmkc/view?usp=drive_link")
        
        # 分析按钮和取消按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.analyze_btn = ttk.Button(button_frame, text="Start Analysis", 
                                    command=self.analyze_from_url)
        self.analyze_btn.pack(side=tk.LEFT, padx=5)
        
        self.cancel_btn = ttk.Button(button_frame, text="Cancel Analysis",
                                   command=self.cancel_analysis_process,
                                   state='disabled')
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # 进度条
        progress_frame = ttk.Frame(control_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(progress_frame, 
                                      variable=self.progress_var,
                                      maximum=100,
                                      mode='determinate',
                                      length=200)
        self.progress.pack(fill=tk.X, pady=5)
        
        # 状态显示
        self.status_label = ttk.Label(control_frame, text="Ready", 
                                     font=('Helvetica', 10))
        self.status_label.pack(pady=5)
        
        # 右侧面板 - 结果显示区域
        result_frame = ttk.Frame(self.main_frame)
        result_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # 文本显示区域
        text_frame = ttk.LabelFrame(result_frame, text="Analysis Results", padding="5")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_area = scrolledtext.ScrolledText(text_frame, 
                                                 width=60, 
                                                 height=20,
                                                 font=('Consolas', 10))
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 图表显示区域
        self.fig = Figure(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=result_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 配置网格权重
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
        # 设置窗口最小大小
        self.root.minsize(800, 600)
        
    def select_media_file(self):
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("MP3 Files", "*.mp3")]
            )
            if file_path:
                logger.info(f"Selected MP3 file: {file_path}")
                # 更新文件信息显示
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # 转换为MB
                self.file_info.configure(
                    text=f"File: {os.path.basename(file_path)}\nSize: {file_size:.2f} MB"
                )
                self.process_media_file(file_path)
        except Exception as e:
            logger.error(f"File selection failed: {str(e)}")
            messagebox.showerror("Error", f"File selection failed: {str(e)}")
            
    def process_media_file(self, file_path):
        temp_file = None
        try:
            logger.info(f"Processing MP3 file: {file_path}")
            self.progress_var.set(10)
            self.update_status("Processing audio file...")
            
            # Process MP3 file
            temp_file = process_mp3(file_path)
            logger.info(f"MP3 file processed: {temp_file}")
            self.progress_var.set(30)
            
            # Analyze content using iFlytek API
            self.analyze_content(temp_file)
                
        except Exception as e:
            logger.error(f"File processing error: {str(e)}")
            logger.error(traceback.format_exc())
            error_msg = f"File processing error: {str(e)}\n\n"
            error_msg += "Please ensure:\n"
            error_msg += "1. File format is MP3\n"
            error_msg += "2. File is not corrupted"
            self.update_status(error_msg)
            messagebox.showerror("Error", error_msg)
        finally:
            # Clean up temporary file
            if temp_file and temp_file != file_path and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logger.debug(f"Temporary file deleted: {temp_file}")
                except:
                    logger.warning(f"Failed to delete temporary file: {temp_file}")
            
    def cancel_analysis_process(self):
        self.cancel_analysis = True
        self.update_status("Analyzing cancelled...")
        self.cancel_btn.configure(state='disabled')
        
    def analyze_from_url(self):
        try:
            url = self.url_entry.get().strip()
            if not url:
                messagebox.showerror("Error", "Please enter audio file URL")
                return
                
            logger.info(f"Analyzing audio from URL: {url}")
            self.update_status("Analyzing audio file...")
            self.update_progress(10)
            
            # 重置取消标志
            self.cancel_analysis = False
            
            # 禁用分析按钮，启用取消按钮
            self.analyze_btn.configure(state='disabled')
            self.cancel_btn.configure(state='normal')
            
            # 在新线程中执行分析
            analysis_thread = threading.Thread(target=self.analyze_content, args=(url,))
            analysis_thread.daemon = True
            analysis_thread.start()
                
        except Exception as e:
            logger.error(f"URL analysis error: {str(e)}")
            logger.error(traceback.format_exc())
            error_msg = f"URL analysis error: {str(e)}\n\n"
            error_msg += "Please check:\n"
            error_msg += "1. URL is correct\n"
            error_msg += "2. Network connection is stable\n"
            error_msg += "3. Audio file is accessible"
            self.update_status(error_msg)
            messagebox.showerror("Error", error_msg)
            self.progress_var.set(0)
            self.enable_analyze_button()
            
    def disable_analyze_button(self):
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Button) and widget.cget('text') == "Start Analysis":
                widget.configure(state='disabled')
                
    def enable_analyze_button(self):
        self.analyze_btn.configure(state='normal')
        self.cancel_btn.configure(state='disabled')
        
    def update_progress(self, value):
        """Update progress bar and status"""
        self.progress_var.set(value)
        self.root.update_idletasks()
        
        # Update status text
        if value == 0:
            self.status_label.configure(text="Ready")
        elif value < 20:
            self.status_label.configure(text="Submitting analysis request...")
        elif value < 80:
            self.status_label.configure(text="Analyzing audio content...")
        elif value < 100:
            self.status_label.configure(text="Processing analysis results...")
        else:
            self.status_label.configure(text="Analysis completed")
        
    def analyze_content(self, audio_file):
        try:
            logger.debug(f"Analyzing content: {audio_file}")
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            self.text_area.insert(tk.END, f"\n[{timestamp}] Starting audio analysis...\n")
            self.update_status("Analyzing audio file...")
            self.update_progress(10)
            
            # Analyze content using iFlytek API
            analysis_results = self.iflytek_api.analyze_audio(audio_file)
            
            if self.cancel_analysis:
                self.update_status("Analysis cancelled")
                self.update_progress(0)
                self.enable_analyze_button()
                return
                
            self.update_progress(80)
            
            # Clear previous results
            self.text_area.delete(1.0, tk.END)
            
            # Display analysis results
            if analysis_results.get("status") == "success":
                suggest = analysis_results.get("suggest", "pass")
                violations = analysis_results.get("violations", [])
                
                # Display overall suggestion
                if suggest == "pass":
                    self.text_area.insert(tk.END, "✅ Pass: No violations found\n\n")
                elif suggest == "review":
                    self.text_area.insert(tk.END, "⚠️ Review required: Potential violations found\n\n")
                else:  # block
                    self.text_area.insert(tk.END, "❌ Block: Violations found\n\n")
                
                # Display violation details
                if violations:
                    self.text_area.insert(tk.END, "Violation Details:\n")
                    for violation in violations:
                        self.text_area.insert(tk.END, f"\nTime: {violation['offset_time']}s")
                        self.text_area.insert(tk.END, f"\nDuration: {violation['duration']}s")
                        self.text_area.insert(tk.END, f"\nContent: {violation['content']}")
                        self.text_area.insert(tk.END, f"\nSuggestion: {'Pass' if violation['suggest'] == 'pass' else 'Review' if violation['suggest'] == 'review' else 'Block'}")
                        
                        # Display category information
                        if violation['categories']:
                            self.text_area.insert(tk.END, "\nCategories:")
                            for category in violation['categories']:
                                self.text_area.insert(tk.END, f"\n  - {category['description']}")
                                if category['words']:
                                    self.text_area.insert(tk.END, f"\n    Keywords: {', '.join(category['words'])}")
                        self.text_area.insert(tk.END, "\n" + "-"*50 + "\n")
                else:
                    self.text_area.insert(tk.END, "No violations found\n")
            else:
                self.text_area.insert(tk.END, f"Analysis failed: {analysis_results.get('message', 'Unknown error')}\n")
            
            self.text_area.see(tk.END)
            self.update_progress(100)
            self.update_status("Analysis completed")
            self.enable_analyze_button()
            
        except Exception as e:
            if not self.cancel_analysis:
                logger.error(f"Content analysis error: {str(e)}")
                logger.error(traceback.format_exc())
                error_msg = f"Analysis failed:\n{str(e)}\n\n"
                error_msg += "Please check:\n"
                error_msg += "1. API credentials are correct\n"
                error_msg += "2. Network connection is stable\n"
                error_msg += "3. Audio file format is supported\n"
                error_msg += "4. Audio file size is within limit (10MB)"
                self.update_status(error_msg)
                messagebox.showerror("Error", error_msg)
                self.progress_var.set(0)
            self.enable_analyze_button()
    
    def update_chart(self, results_count):
        # 清除之前的图表
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        # 创建柱状图
        categories = list(results_count.keys())
        values = list(results_count.values())
        
        bars = ax.bar(categories, values)
        
        # 自定义图表
        ax.set_title('Analysis Results Summary')
        ax.set_ylabel('Number of Items')
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom')
        
        self.fig.tight_layout()
        self.canvas.draw()
        
    def update_status(self, message):
        logger.debug(f"Status update: {message}")
        self.status_label.configure(text=message) 