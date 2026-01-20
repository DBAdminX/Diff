import customtkinter as ctk
from tkinter import filedialog, messagebox
import difflib

ctk.set_appearance_mode("System")          # "System" / "Light" / "Dark"
ctk.set_default_color_theme("blue")        # blue / dark-blue / green  — blue 最接近 Material You

class SimpleDiffViewer(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Material You Diff Viewer")
        self.geometry("1300x850")

        # 主布局
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 上半部分：左右文本对比区
        paned = ctk.CTkFrame(self)
        paned.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.left_frame = ctk.CTkFrame(paned)
        self.right_frame = ctk.CTkFrame(paned)

        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # 左侧和右侧文本区域
        self._create_side(self.left_frame, "Original (Left)", is_left=True)
        self._create_side(self.right_frame, "Modified (Right)", is_left=False)

        # 下半部分：Diff 输出
        diff_frame = ctk.CTkFrame(self)
        diff_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        diff_frame.grid_rowconfigure(0, weight=1)
        diff_frame.grid_columnconfigure(0, weight=1)

        self.diff_view = ctk.CTkTextbox(
            diff_frame,
            wrap="none",
            font=("Consolas", 11),
            state="disabled",
            fg_color=("#fdf6e3", "#2d2d2d"),  # 浅色/深色背景
            text_color=("#333", "#ddd"),
            border_width=0
        )
        self.diff_view.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # 标签样式（使用 tag_config 而非 tag_configure）
        self.diff_view.tag_config("add",    foreground="#006400", background="#e6ffe6")
        self.diff_view.tag_config("remove", foreground="#8B0000", background="#ffe6e6")
        self.diff_view.tag_config("sign",   foreground="#888")
        self.diff_view.tag_config("lineno", foreground="#666")

        # 控制按钮栏
        btn_frame = ctk.CTkFrame(self)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkButton(btn_frame, text="Compare", command=self.show_diff).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="CLEAR ALL", command=self.clear_all,
                      fg_color="#ff4d4d", hover_color="#cc0000").pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="COPY RESULTS", command=self.copy_results).pack(side="left", padx=8)

        # 同步滚动相关
        self._sync_lock = False
        self.left_text.bind("<MouseWheel>", self._on_mousewheel)
        self.right_text.bind("<MouseWheel>", self._on_mousewheel)
        self.left_text.bind("<<Modified>>", self._update_all_gutters)
        self.right_text.bind("<<Modified>>", self._update_all_gutters)

    def _create_side(self, parent, label, is_left):
        # 标题
        ctk.CTkLabel(parent, text=label, font=("Segoe UI", 14, "bold")).pack(pady=(10, 5))

        # 按钮栏
        btn_bar = ctk.CTkFrame(parent)
        btn_bar.pack(fill="x", pady=(0, 8))

        target_text = lambda: self.left_text if is_left else self.right_text

        ctk.CTkButton(btn_bar, text="Open File", width=120,
                      command=lambda: self._load_file(target_text())).pack(side="left", padx=4)
        ctk.CTkButton(btn_bar, text="Paste", width=120,
                      command=lambda: self._paste_from_clipboard(target_text())).pack(side="left", padx=4)

        # 文本 + 行号
        text_frame = ctk.CTkFrame(parent)
        text_frame.pack(fill="both", expand=True)

        gutter = ctk.CTkTextbox(text_frame, width=60, height=10, state="disabled",
                                fg_color=("#f0f0f0", "#3a3a3a"), text_color="#888",
                                font=("Consolas", 11), border_width=0)
        gutter.pack(side="left", fill="y")

        txt = ctk.CTkTextbox(text_frame, wrap="none", font=("Consolas", 11),
                             undo=True, fg_color=("#ffffff", "#1e1e1e"), text_color=("#111", "#eee"))
        txt.pack(side="left", fill="both", expand=True)

        if is_left:
            self.left_text = txt
            self.left_gutter = gutter
        else:
            self.right_text = txt
            self.right_gutter = gutter

    # ------------------- 功能函数 -------------------
    def _paste_from_clipboard(self, widget):
        try:
            content = self.clipboard_get()
            widget.delete("0.0", "end")
            widget.insert("0.0", content)
            self._update_all_gutters()
        except:
            messagebox.showwarning("Warning", "Clipboard is empty.")

    def copy_results(self):
        content = self.diff_view.get("0.0", "end").strip()
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)
            messagebox.showinfo("Success", "Copied to clipboard!")
        else:
            messagebox.showwarning("Warning", "Nothing to copy!")

    def clear_all(self):
        self.left_text.delete("0.0", "end")
        self.right_text.delete("0.0", "end")
        self.diff_view.configure(state="normal")
        self.diff_view.delete("0.0", "end")
        self.diff_view.configure(state="disabled")
        self._update_all_gutters()

    def _update_all_gutters(self, event=None):
        self._update_gutter(self.left_text, self.left_gutter)
        self._update_gutter(self.right_text, self.right_gutter)
        if event:
            event.widget.edit_modified(False)

    def _update_gutter(self, text_widget, gutter_widget):
        gutter_widget.configure(state="normal")
        gutter_widget.delete("0.0", "end")
        line_count = int(text_widget.index("end-1c").split('.')[0])
        line_numbers = "\n".join(str(i) for i in range(1, line_count + 1))
        gutter_widget.insert("0.0", line_numbers)
        gutter_widget.configure(state="disabled")

    def _on_mousewheel(self, event):
        delta = -1 if event.delta < 0 else 1
        self.left_text.yview_scroll(delta, "units")
        self.right_text.yview_scroll(delta, "units")
        self.left_gutter.yview_scroll(delta, "units")
        self.right_gutter.yview_scroll(delta, "units")
        return "break"

    def _load_file(self, widget):
        path = filedialog.askopenfilename()
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            widget.delete("0.0", "end")
            widget.insert("0.0", content)
            self._update_all_gutters()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_diff(self):
        self.diff_view.configure(state="normal")
        self.diff_view.delete("0.0", "end")

        lines1 = self.left_text.get("0.0", "end-1c").splitlines()
        lines2 = self.right_text.get("0.0", "end-1c").splitlines()

        differ = difflib.Differ()
        diff_result = list(differ.compare(lines1, lines2))

        old_ln = new_ln = 0
        changes_found = False

        for line in diff_result:
            prefix, content = line[:2], line[2:]
            if prefix == "  ":
                old_ln += 1
                new_ln += 1
            elif prefix == "- ":
                old_ln += 1
                self._insert_diff_line(old_ln, None, "-", content, "remove")
                changes_found = True
            elif prefix == "+ ":
                new_ln += 1
                self._insert_diff_line(None, new_ln, "+", content, "add")
                changes_found = True

        if not changes_found:
            self.diff_view.insert("end", ">>> Files are identical.\n", "sign")

        self.diff_view.configure(state="disabled")

    def _insert_diff_line(self, old_num, new_num, sign, content, tag):
        l_part = f"{old_num:4}" if old_num else "    "
        r_part = f"{new_num:4}" if new_num else "    "
        self.diff_view.insert("end", f"{l_part} | {r_part} | {sign} ", ("sign", "lineno"))
        self.diff_view.insert("end", content + "\n", tag)


if __name__ == "__main__":
    app = SimpleDiffViewer()
    app.mainloop()