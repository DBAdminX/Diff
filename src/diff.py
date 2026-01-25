import customtkinter as ctk
from tkinter import filedialog, messagebox, Menu
import difflib
from datetime import datetime

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class SimpleDiffViewer(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Material You Diff Viewer")
        self.geometry("1300x850")

        # 存储文件路径
        self.left_file_path = None
        self.right_file_path = None

        # 主布局
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 上半部分：左右文本对比区
        paned = ctk.CTkFrame(self)
        paned.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        paned.grid_columnconfigure(0, weight=1)
        paned.grid_columnconfigure(1, weight=1)
        paned.grid_rowconfigure(0, weight=1)

        self.left_frame = ctk.CTkFrame(paned)
        self.right_frame = ctk.CTkFrame(paned)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)

        # 初始化文本控件
        self.left_text = None
        self.right_text = None
        self.left_gutter = None
        self.right_gutter = None
        self.left_file_label = None
        self.right_file_label = None

        # 左侧和右侧文本区域
        self._create_side(self.left_frame, "Original", is_left=True)
        self._create_side(self.right_frame, "Modified", is_left=False)

        # 下半部分：Diff 输出
        diff_frame = ctk.CTkFrame(self)
        diff_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        diff_frame.grid_rowconfigure(0, weight=1)
        diff_frame.grid_columnconfigure(0, weight=1)

        # Diff 输出标题栏
        diff_header = ctk.CTkFrame(diff_frame)
        diff_header.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
        ctk.CTkLabel(diff_header, text="Diff Output", font=("Segoe UI", 12, "bold")).pack(side="left", padx=10)

        # 统计信息标签
        self.stats_label = ctk.CTkLabel(diff_header, text="", font=("Segoe UI", 10))
        self.stats_label.pack(side="right", padx=10)

        self.diff_view = ctk.CTkTextbox(
            diff_frame,
            wrap="none",
            font=("Consolas", 11),
            state="disabled",
            fg_color=("#fdf6e3", "#2d2d2d"),
            text_color=("#333", "#ddd"),
            border_width=0
        )
        self.diff_view.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # 初始化标签样式（使用单一颜色，稍后根据模式更新）
        self._setup_diff_tags()

        # 控制按钮栏
        btn_frame = ctk.CTkFrame(self)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        # 按钮组
        ctk.CTkButton(btn_frame, text="Compare", command=self.show_diff).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Swap Files", command=self.swap_files).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Clear All", command=self.clear_all,
                      fg_color="#ff4d4d", hover_color="#cc0000").pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Copy Results", command=self.copy_results).pack(side="left", padx=8)

        # 绑定滚动事件
        self._bind_scroll_events()

        # 添加右键菜单
        self._setup_context_menu()

        # 初始化时显示欢迎信息
        self._show_welcome_message()

        # 绑定外观模式变化事件
        self.bind("<<AppearanceModeChanged>>", self._on_appearance_mode_changed)

    def _setup_diff_tags(self):
        """设置Diff输出区域的标签样式"""
        # 清除现有标签
        for tag in self.diff_view.tag_names():
            self.diff_view.tag_delete(tag)

        # 根据当前外观模式设置颜色
        current_mode = ctk.get_appearance_mode()

        if current_mode == "Dark":
            # 深色模式
            self.diff_view.tag_config("add", foreground="#00cc00", background="#1a3c1a")
            self.diff_view.tag_config("remove", foreground="#ff6666", background="#3c1a1a")
            self.diff_view.tag_config("sign", foreground="#888")
            self.diff_view.tag_config("lineno", foreground="#aaa")
            self.diff_view.tag_config("info", foreground="#66b3ff")
        else:
            # 浅色模式
            self.diff_view.tag_config("add", foreground="#006400", background="#e6ffe6")
            self.diff_view.tag_config("remove", foreground="#8B0000", background="#ffe6e6")
            self.diff_view.tag_config("sign", foreground="#666")
            self.diff_view.tag_config("lineno", foreground="#444")
            self.diff_view.tag_config("info", foreground="#0066cc")

        # info标签不使用特殊字体，使用默认字体但颜色不同

    def _on_appearance_mode_changed(self, event=None):
        """当外观模式改变时更新标签颜色"""
        self._setup_diff_tags()

    def _bind_scroll_events(self):
        """绑定滚动事件"""
        if self.left_text and self.right_text:
            for widget in [self.left_text, self.right_text, self.left_gutter, self.right_gutter]:
                widget.bind("<MouseWheel>", self._on_mousewheel)
                widget.bind("<Button-4>", self._on_mousewheel)  # Linux向上滚动
                widget.bind("<Button-5>", self._on_mousewheel)  # Linux向下滚动

    def _setup_context_menu(self):
        """设置右键菜单"""
        # 为左侧文本区域创建右键菜单
        self.left_context_menu = Menu(self.left_text, tearoff=0)
        self.left_context_menu.add_command(label="Copy", command=lambda: self._copy_text(self.left_text))
        self.left_context_menu.add_command(label="Select All", command=lambda: self._select_all(self.left_text))
        self.left_text.bind("<Button-3>", lambda e: self._show_context_menu(e, self.left_context_menu))

        # 为右侧文本区域创建右键菜单
        self.right_context_menu = Menu(self.right_text, tearoff=0)
        self.right_context_menu.add_command(label="Copy", command=lambda: self._copy_text(self.right_text))
        self.right_context_menu.add_command(label="Select All", command=lambda: self._select_all(self.right_text))
        self.right_text.bind("<Button-3>", lambda e: self._show_context_menu(e, self.right_context_menu))

        # 为Diff输出区域创建右键菜单
        self.diff_context_menu = Menu(self.diff_view, tearoff=0)
        self.diff_context_menu.add_command(label="Copy", command=lambda: self._copy_text(self.diff_view))
        self.diff_context_menu.add_command(label="Select All", command=lambda: self._select_all(self.diff_view))
        self.diff_view.bind("<Button-3>", lambda e: self._show_context_menu(e, self.diff_context_menu))

    def _show_context_menu(self, event, menu):
        """显示右键菜单"""
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _copy_text(self, widget):
        """复制选中文本"""
        try:
            # 对于CTkTextbox，需要获取内部的tkinter文本控件
            if hasattr(widget, 'textbox'):
                text_widget = widget.textbox
            else:
                text_widget = widget

            selected = text_widget.get("sel.first", "sel.last")
            self.clipboard_clear()
            self.clipboard_append(selected)
        except:
            pass

    def _select_all(self, widget):
        """全选文本"""
        try:
            # 对于CTkTextbox，需要获取内部的tkinter文本控件
            if hasattr(widget, 'textbox'):
                text_widget = widget.textbox
            else:
                text_widget = widget

            text_widget.tag_add("sel", "1.0", "end")
        except:
            pass

    def _create_side(self, parent, label, is_left):
        """创建一侧的文本编辑区域"""
        # 标题和文件路径显示
        header = ctk.CTkFrame(parent)
        header.pack(fill="x", pady=(10, 5), padx=10)

        ctk.CTkLabel(header, text=label, font=("Segoe UI", 14, "bold")).pack(side="left")

        # 文件路径标签
        file_label = ctk.CTkLabel(header, text="No file loaded", font=("Segoe UI", 10),
                                  text_color=("#666", "#aaa"))
        file_label.pack(side="right")

        # 按钮栏
        btn_bar = ctk.CTkFrame(parent)
        btn_bar.pack(fill="x", pady=(0, 8), padx=10)

        # 使用lambda函数延迟获取文本控件
        if is_left:
            ctk.CTkButton(btn_bar, text="Open File", width=120,
                          command=lambda: self._load_file(is_left)).pack(side="left", padx=4)
            ctk.CTkButton(btn_bar, text="Paste", width=120,
                          command=lambda: self._paste_from_clipboard(is_left)).pack(side="left", padx=4)
            ctk.CTkButton(btn_bar, text="Clear", width=120,
                          command=lambda: self._clear_side(is_left)).pack(side="left", padx=4)
        else:
            ctk.CTkButton(btn_bar, text="Open File", width=120,
                          command=lambda: self._load_file(is_left)).pack(side="left", padx=4)
            ctk.CTkButton(btn_bar, text="Paste", width=120,
                          command=lambda: self._paste_from_clipboard(is_left)).pack(side="left", padx=4)
            ctk.CTkButton(btn_bar, text="Clear", width=120,
                          command=lambda: self._clear_side(is_left)).pack(side="left", padx=4)

        # 文本 + 行号
        text_frame = ctk.CTkFrame(parent)
        text_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        gutter = ctk.CTkTextbox(text_frame, width=60, height=10, state="disabled",
                                fg_color=("#f0f0f0", "#3a3a3a"), text_color="#888",
                                font=("Consolas", 11), border_width=0)
        gutter.pack(side="left", fill="y")

        txt = ctk.CTkTextbox(text_frame, wrap="none", font=("Consolas", 11),
                             undo=True, fg_color=("#ffffff", "#1e1e1e"),
                             text_color=("#111", "#eee"))
        txt.pack(side="left", fill="both", expand=True)

        # 添加右侧滚动条
        scrollbar = ctk.CTkScrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        # 配置滚动条
        txt.configure(yscrollcommand=scrollbar.set)
        gutter.configure(yscrollcommand=scrollbar.set)

        # 配置滚动命令
        def on_scroll(*args):
            txt.yview(*args)
            gutter.yview(*args)

        scrollbar.configure(command=on_scroll)

        # 存储控件引用
        if is_left:
            self.left_text = txt
            self.left_gutter = gutter
            self.left_file_label = file_label
        else:
            self.right_text = txt
            self.right_gutter = gutter
            self.right_file_label = file_label

    def _show_welcome_message(self):
        """显示欢迎信息"""
        self.diff_view.configure(state="normal")
        self.diff_view.delete("0.0", "end")

        welcome_msg = """=== Material You Diff Viewer ===

Instructions:
1. Load files using the 'Open File' buttons or paste text
2. Click 'Compare' to see differences
3. Use mouse wheel to scroll all panels simultaneously
4. Right-click for context menu (copy/select all)

Tips:
- You can swap files with 'Swap Files' button
- Copy results with 'Copy Results' button
- Clear all with 'Clear All' button

"""
        self.diff_view.insert("end", welcome_msg, "info")
        self.diff_view.configure(state="disabled")

    def _clear_side(self, is_left):
        """清除单侧内容"""
        if is_left:
            text_widget = self.left_text
            gutter_widget = self.left_gutter
            self.left_file_path = None
            self.left_file_label.configure(text="No file loaded")
        else:
            text_widget = self.right_text
            gutter_widget = self.right_gutter
            self.right_file_path = None
            self.right_file_label.configure(text="No file loaded")

        text_widget.delete("0.0", "end")
        self._update_gutter(text_widget, gutter_widget)

    def _paste_from_clipboard(self, is_left):
        """从剪贴板粘贴到指定侧"""
        text_widget = self.left_text if is_left else self.right_text
        try:
            content = self.clipboard_get()
            text_widget.delete("0.0", "end")
            text_widget.insert("0.0", content)
            self._update_all_gutters()
        except:
            messagebox.showwarning("Warning", "Clipboard is empty or contains invalid data.")

    def copy_results(self):
        content = self.diff_view.get("0.0", "end").strip()
        if content and content != self.diff_view.get("0.0", "end"):
            self.clipboard_clear()
            self.clipboard_append(content)
            messagebox.showinfo("Success", "Results copied to clipboard!")
        else:
            messagebox.showwarning("Warning", "Nothing to copy!")

    def clear_all(self):
        self.left_text.delete("0.0", "end")
        self.right_text.delete("0.0", "end")
        self.left_file_path = None
        self.right_file_path = None
        self.left_file_label.configure(text="No file loaded")
        self.right_file_label.configure(text="No file loaded")

        self.diff_view.configure(state="normal")
        self.diff_view.delete("0.0", "end")
        self.diff_view.configure(state="disabled")
        self._update_all_gutters()
        self.stats_label.configure(text="")

        self._show_welcome_message()

    def _update_all_gutters(self, event=None):
        self._update_gutter(self.left_text, self.left_gutter)
        self._update_gutter(self.right_text, self.right_gutter)
        if event and hasattr(event, 'widget'):
            event.widget.edit_modified(False)

    def _update_gutter(self, text_widget, gutter_widget):
        gutter_widget.configure(state="normal")
        gutter_widget.delete("0.0", "end")
        line_count = int(text_widget.index("end-1c").split('.')[0])
        if line_count > 0:
            line_numbers = "\n".join(str(i) for i in range(1, line_count))
        else:
            line_numbers = ""
        gutter_widget.insert("0.0", line_numbers)
        gutter_widget.configure(state="disabled")

    def _on_mousewheel(self, event):
        """处理鼠标滚轮事件，支持跨平台"""
        if event.num == 4:  # Linux向上滚动
            delta = -1
        elif event.num == 5:  # Linux向下滚动
            delta = 1
        else:  # Windows/Mac
            delta = -1 if event.delta < 0 else 1

        self.left_text.yview_scroll(delta, "units")
        self.right_text.yview_scroll(delta, "units")
        self.left_gutter.yview_scroll(delta, "units")
        self.right_gutter.yview_scroll(delta, "units")
        return "break"

    def _load_file(self, is_left):
        """加载文件到指定侧"""
        path = filedialog.askopenfilename()
        if not path:
            return

        text_widget = self.left_text if is_left else self.right_text
        file_label = self.left_file_label if is_left else self.right_file_label

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            text_widget.delete("0.0", "end")
            text_widget.insert("0.0", content)

            # 更新文件路径标签
            if is_left:
                self.left_file_path = path
            else:
                self.right_file_path = path

            file_label.configure(text=path.split('/')[-1])
            self._update_all_gutters()
        except UnicodeDecodeError:
            try:
                with open(path, 'r', encoding='latin-1') as f:
                    content = f.read()
                text_widget.delete("0.0", "end")
                text_widget.insert("0.0", content)
                self._update_all_gutters()
                messagebox.showinfo("Info", "File loaded with Latin-1 encoding")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot read file: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot read file: {str(e)}")

    def show_diff(self):
        """显示差异比较结果"""
        self.diff_view.configure(state="normal")
        self.diff_view.delete("0.0", "end")

        lines1 = self.left_text.get("0.0", "end-1c").splitlines()
        lines2 = self.right_text.get("0.0", "end-1c").splitlines()

        # 显示比较信息
        timestamp = datetime.now().strftime("%Y-%m-d %H:%M:%S")
        info = f"=== Comparison Results ({timestamp}) ===\n"
        info += f"Original lines: {len(lines1)} | Modified lines: {len(lines2)}\n"
        self.diff_view.insert("end", info + "\n", "info")

        differ = difflib.Differ()
        diff_result = list(differ.compare(lines1, lines2))

        old_ln = new_ln = 0
        add_count = remove_count = 0

        for line in diff_result:
            prefix, content = line[:2], line[2:]
            if prefix == "  ":
                old_ln += 1
                new_ln += 1
            elif prefix == "- ":
                old_ln += 1
                self._insert_diff_line(old_ln, None, "-", content, "remove")
                remove_count += 1
            elif prefix == "+ ":
                new_ln += 1
                self._insert_diff_line(None, new_ln, "+", content, "add")
                add_count += 1
            elif prefix == "? ":
                continue  # 忽略difflib的上下文行

        # 显示统计信息
        self.stats_label.configure(
            text=f"Additions: {add_count} | Removals: {remove_count} | Changes: {add_count + remove_count}"
        )

        if add_count == 0 and remove_count == 0:
            self.diff_view.insert("end", "\n>>> Files are identical.\n", "info")
        else:
            summary = f"\n>>> Summary: {add_count} additions, {remove_count} removals\n"
            self.diff_view.insert("end", summary, "info")

        self.diff_view.configure(state="disabled")

    def _insert_diff_line(self, old_num, new_num, sign, content, tag):
        l_part = f"{old_num:4}" if old_num else "    "
        r_part = f"{new_num:4}" if new_num else "    "
        self.diff_view.insert("end", f"{l_part} | {r_part} | {sign} ", ("sign", "lineno"))
        self.diff_view.insert("end", content + "\n", tag)

    def swap_files(self):
        """交换左右两侧的内容"""
        # 交换文本内容
        left_content = self.left_text.get("0.0", "end-1c")
        right_content = self.right_text.get("0.0", "end-1c")

        self.left_text.delete("0.0", "end")
        self.right_text.delete("0.0", "end")
        self.left_text.insert("0.0", right_content)
        self.right_text.insert("0.0", left_content)

        # 交换文件路径
        self.left_file_path, self.right_file_path = self.right_file_path, self.left_file_path

        # 更新文件标签
        if self.left_file_path:
            self.left_file_label.configure(text=self.left_file_path.split('/')[-1])
        else:
            self.left_file_label.configure(text="No file loaded")

        if self.right_file_path:
            self.right_file_label.configure(text=self.right_file_path.split('/')[-1])
        else:
            self.right_file_label.configure(text="No file loaded")

        self._update_all_gutters()
        messagebox.showinfo("Info", "Files swapped successfully!")


if __name__ == "__main__":
    app = SimpleDiffViewer()
    app.mainloop()