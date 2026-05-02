import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD

class CodeBundlerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("代码上下文打包工具 (记忆配置版)")
        self.root.geometry("720x550")

        style = ttk.Style()
        style.configure("TButton", padding=6, font=('Microsoft YaHei', 10))

        # --- 配置文件与路径初始化 ---
        if getattr(sys, 'frozen', False):
            self.script_dir = os.path.dirname(sys.executable)
        else:
            self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.script_dir, "bundler_config.json")
        self.config = self.load_config() # 读取配置 (如果不存在会在这里自动创建)
        self.output_dir = self.config.get("output_dir", os.path.join(self.script_dir, "outputs"))

        # ==========================================
        # 1. 顶部基础操作区
        # ==========================================
        self.top_frame = ttk.Frame(root)
        self.top_frame.pack(fill="x", padx=20, pady=10)

        self.label_info = ttk.Label(self.top_frame, text="请将文件夹拖入下方，或点击按钮选择：", font=('Microsoft YaHei', 11))
        self.label_info.pack(pady=5)

        self.btn_browse = ttk.Button(self.top_frame, text="📁 手动选择输入文件夹", command=self.browse_folder)
        self.btn_browse.pack(pady=5)

        self.drop_frame = tk.Label(
            self.top_frame, text="\n将文件夹拖到这里\n",
            bg="#f0f0f0", fg="#666666",
            font=('Microsoft YaHei', 12, 'italic'),
            relief="solid", bd=1
        )
        self.drop_frame.pack(fill="both", expand=True, pady=10)

        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)

        self.path_label = ttk.Label(self.top_frame, text="未选择输入路径", foreground="blue", wraplength=650)
        self.path_label.pack(pady=5)
        self.selected_path = ""

        # ==========================================
        # 2. 输出目录设置区
        # ==========================================
        self.out_frame = ttk.Frame(root)
        self.out_frame.pack(fill="x", padx=20, pady=5)

        ttk.Label(self.out_frame, text="输出目录: ").pack(side="left")
        self.out_label = ttk.Label(self.out_frame, text=self.output_dir, foreground="#555555", wraplength=450)
        self.out_label.pack(side="left", padx=5)
        ttk.Button(self.out_frame, text="更改", command=self.change_out_dir).pack(side="left", padx=10)

        # ==========================================
        # 3. 高级选项折叠控制区
        # ==========================================
        self.toggle_frame = ttk.Frame(root)
        self.toggle_frame.pack(fill="x", padx=20, pady=10)

        self.show_advanced = False
        self.btn_toggle = ttk.Button(self.toggle_frame, text="▶ 高级选项 (自定义过滤规则)", command=self.toggle_advanced)
        self.btn_toggle.pack(fill="x")

        # ==========================================
        # 4. 高级选项面板
        # ==========================================
        self.advanced_frame = ttk.LabelFrame(root, text="⚙️ 自定义过滤规则 (支持回车换行)", padding=10)

        ttk.Label(self.advanced_frame, text="📁 忽略的文件夹").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(self.advanced_frame, text="📄 忽略的后缀名").grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(self.advanced_frame, text="❌ 忽略的特定文件").grid(row=0, column=2, sticky="w", padx=5, pady=2)

        text_config = {'width': 26, 'height': 8, 'font': ('Consolas', 10), 'relief': 'solid', 'bd': 1}

        # 填入读取到的配置
        self.txt_ignore_dirs = tk.Text(self.advanced_frame, **text_config)
        self.txt_ignore_dirs.grid(row=1, column=0, padx=5, pady=5)
        self.txt_ignore_dirs.insert("1.0", self.config.get("ignore_dirs", ""))

        self.txt_ignore_exts = tk.Text(self.advanced_frame, **text_config)
        self.txt_ignore_exts.grid(row=1, column=1, padx=5, pady=5)
        self.txt_ignore_exts.insert("1.0", self.config.get("ignore_exts", ""))

        self.txt_ignore_files = tk.Text(self.advanced_frame, **text_config)
        self.txt_ignore_files.grid(row=1, column=2, padx=5, pady=5)
        self.txt_ignore_files.insert("1.0", self.config.get("ignore_files", ""))

        # ==========================================
        # 5. 底部执行按钮
        # ==========================================
        self.bottom_frame = ttk.Frame(root)
        self.bottom_frame.pack(fill="x", padx=20, pady=15)

        self.btn_run = ttk.Button(self.bottom_frame, text="🚀 立即打包代码", command=self.run_bundler, state="disabled")
        self.btn_run.pack(pady=5)

    # --- 配置读取与保存模块 ---
    def load_config(self):
        """加载本地配置，如果不存在则自动创建并写入默认值"""
        default_config = {
            "ignore_dirs": ".git\nnode_modules\ndist\nbuild\nout\nvenv\n__pycache__\n.idea\n.vscode\ncoverage",
            "ignore_exts": ".png\n.jpg\n.jpeg\n.gif\n.svg\n.ico\n.mp4\n.pdf\n.exe\n.dll\n.so\n.pyc\n.zip\n.tar\n.gz",
            "ignore_files": "package-lock.json\nyarn.lock\npnpm-lock.yaml\npoetry.lock",
            "output_dir": os.path.join(self.script_dir, "outputs")
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    # 将保存的配置覆盖到默认配置上
                    for key in saved_config:
                        default_config[key] = saved_config[key]
            except Exception:
                pass # 读取或解析失败时，直接使用默认配置
        else:
            # 【新增逻辑】如果文件不存在，首次运行自动创建该文件并写入默认配置
            try:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"首次运行创建配置文件失败: {e}")

        return default_config

    def save_config(self):
        """将当前面板的状态保存到本地 JSON 文件"""
        config_to_save = {
            "ignore_dirs": self.txt_ignore_dirs.get("1.0", tk.END).strip(),
            "ignore_exts": self.txt_ignore_exts.get("1.0", tk.END).strip(),
            "ignore_files": self.txt_ignore_files.get("1.0", tk.END).strip(),
            "output_dir": self.output_dir
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")

    # --- 交互逻辑模块 ---
    def toggle_advanced(self):
        self.show_advanced = not self.show_advanced
        if self.show_advanced:
            self.btn_toggle.config(text="▼ 高级选项 (自定义过滤规则)")
            self.advanced_frame.pack(fill="x", padx=20, pady=5, before=self.bottom_frame)
            self.root.geometry("720x750")
        else:
            self.btn_toggle.config(text="▶ 高级选项 (自定义过滤规则)")
            self.advanced_frame.pack_forget()
            self.root.geometry("720x550")

    def change_out_dir(self):
        path = filedialog.askdirectory(title="选择输出目录", initialdir=self.output_dir)
        if path:
            self.output_dir = path
            self.out_label.config(text=self.output_dir)
            self.save_config()

    def process_selected_path(self, path):
        if os.path.isdir(path):
            self.selected_path = path
            self.path_label.config(text=f"当前输入: {path}", foreground="green")
            self.btn_run.config(state="normal")
            self.drop_frame.config(bg="#e1f5fe", text="\n已就绪，可以点击打包\n")
        else:
            messagebox.showwarning("错误", "请选择一个【文件夹】，而不是单个文件。")

    def handle_drop(self, event):
        path = event.data.strip('{').strip('}')
        self.process_selected_path(path)

    def browse_folder(self):
        path = filedialog.askdirectory(title="选择你要打包的项目文件夹")
        if path:
            self.process_selected_path(path)

    def get_items_from_text(self, text_widget):
        raw_text = text_widget.get("1.0", tk.END)
        items = [item.strip() for item in raw_text.replace('\n', ',').split(',') if item.strip()]
        return set(items)

    def run_bundler(self):
        if not self.selected_path:
            return

        self.save_config()

        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir)
            except Exception as e:
                messagebox.showerror("错误", f"无法创建输出目录: {str(e)}")
                return

        folder_name = os.path.basename(os.path.normpath(self.selected_path))
        if not folder_name:
            folder_name = "llm_context_bundle"
        output_name = f"{folder_name}.txt"
        final_output_path = os.path.join(self.output_dir, output_name)

        ignore_dirs = self.get_items_from_text(self.txt_ignore_dirs)
        ignore_exts = {e.lower() for e in self.get_items_from_text(self.txt_ignore_exts)}
        ignore_files = {f.lower() for f in self.get_items_from_text(self.txt_ignore_files)}

        try:
            with open(final_output_path, 'w', encoding='utf-8') as outfile:
                for root_dir, dirs, files in os.walk(self.selected_path):
                    dirs[:] = [d for d in dirs if d not in ignore_dirs]

                    for file in files:
                        ext = os.path.splitext(file)[1].lower()
                        file_lower = file.lower()

                        if ext in ignore_exts or file_lower in ignore_files:
                            continue

                        filepath = os.path.join(root_dir, file)
                        rel_path = os.path.relpath(filepath, self.selected_path)

                        outfile.write(f"\n{'='*60}\n")
                        outfile.write(f"// FILE PATH: {rel_path}\n")
                        outfile.write(f"{'='*60}\n")

                        try:
                            with open(filepath, 'r', encoding='utf-8') as infile:
                                outfile.write(infile.read())
                                outfile.write("\n")
                        except Exception:
                            outfile.write("// [无法读取此文件内容，可能是编码不支持或二进制文件]\n")

            messagebox.showinfo("成功", f"打包完成！\n\n文件已保存至：\n{final_output_path}")
        except Exception as e:
            messagebox.showerror("失败", f"打包过程中出错: {str(e)}")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = CodeBundlerGUI(root)
    root.mainloop()