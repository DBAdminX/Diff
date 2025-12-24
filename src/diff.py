import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import difflib
from tkinter.scrolledtext import ScrolledText


class SimpleDiffViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Diff Viewer")
        self.geometry("1300x850")

        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # --- TOP SECTION: Input Areas ---
        input_container = ttk.Frame(main)
        input_container.pack(fill=tk.BOTH, expand=True)

        self.master_scroll = ttk.Scrollbar(input_container, orient=tk.VERTICAL, command=self._on_scrollbar_scroll)
        self.master_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        paned = ttk.PanedWindow(input_container, orient=tk.HORIZONTAL)
        paned.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create Sides
        self.left_text, self.left_gutter = self._create_text_with_gutter(paned, "Original File")
        self.right_text, self.right_gutter = self._create_text_with_gutter(paned, "Modified File")

        # Sync scrolling and content changes
        self._sync_lock = False
        for widget in (self.left_text, self.right_text):
            widget.bind("<MouseWheel>", self._on_mousewheel)
            widget.bind("<Button-4>", self._on_mousewheel)
            widget.bind("<Button-5>", self._on_mousewheel)
            widget.bind("<<Modified>>", self._update_all_gutters)

        # --- MIDDLE SECTION: Controls ---
        ctrl_frame = ttk.Frame(main)
        ctrl_frame.pack(fill=tk.X, pady=10)

        # Center the buttons in a sub-frame
        btn_container = ttk.Frame(ctrl_frame)
        btn_container.pack(anchor=tk.CENTER)

        ttk.Button(btn_container, text="Compare", command=self.show_diff).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_container, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=5)

        # --- BOTTOM SECTION: Diff Output ---
        diff_frame = ttk.LabelFrame(main, text="Differences Output", padding=5)
        diff_frame.pack(fill=tk.BOTH, expand=True)

        self.diff_view = ScrolledText(diff_frame, wrap=tk.NONE, font=("Consolas", 10),
                                      bg="#fdf6e3", state='disabled')
        self.diff_view.pack(fill=tk.BOTH, expand=True)

        # Tags for highlighting
        self.diff_view.tag_configure("add", foreground="#006400", background="#e6ffe6")
        self.diff_view.tag_configure("remove", foreground="#8B0000", background="#ffe6e6")
        self.diff_view.tag_configure("sign", foreground="#555")
        self.diff_view.tag_configure("lineno", foreground="#666", font=("Consolas", 10, "bold"))

    def _create_text_with_gutter(self, parent, label):
        outer = ttk.Frame(parent)
        parent.add(outer, weight=1)
        ttk.Label(outer, text=label).pack(pady=(0, 4))

        btn_bar = ttk.Frame(outer)
        btn_bar.pack(fill=tk.X, pady=(0, 6))

        cmd = self.load_left if "Original" in label else self.load_right
        ttk.Button(btn_bar, text="Open File", command=cmd).pack(side=tk.LEFT)

        text_frame = ttk.Frame(outer)
        text_frame.pack(fill=tk.BOTH, expand=True)

        gutter = tk.Text(text_frame, width=5, padx=5, takefocus=0, border=0,
                         background="#f0f0f0", foreground="#999999",
                         font=("Consolas", 10), state='disabled')
        gutter.pack(side=tk.LEFT, fill=tk.Y)

        txt = tk.Text(text_frame, wrap=tk.NONE, font=("Consolas", 10),
                      undo=True, borderwidth=1, relief="sunken",
                      yscrollcommand=self._sync_scroll)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        return txt, gutter

    # --- ACTIONS ---

    def clear_all(self):
        """Wipes all text widgets and resets the UI state."""
        # Clear Input Text
        self.left_text.delete("1.0", tk.END)
        self.right_text.delete("1.0", tk.END)

        # Clear Results
        self.diff_view.configure(state='normal')
        self.diff_view.delete("1.0", tk.END)
        self.diff_view.configure(state='disabled')

        # Reset scrollbars and gutters
        self.left_text.yview_moveto(0)
        self.right_text.yview_moveto(0)
        self._update_all_gutters()

    def _update_all_gutters(self, event=None):
        self._update_gutter(self.left_text, self.left_gutter)
        self._update_gutter(self.right_text, self.right_gutter)
        if event:
            event.widget.edit_modified(False)

    def _update_gutter(self, text_widget, gutter_widget):
        gutter_widget.config(state='normal')
        gutter_widget.delete("1.0", tk.END)
        line_count = int(text_widget.index('end-1c').split('.')[0])
        line_numbers = "\n".join(str(i) for i in range(1, line_count + 1))
        gutter_widget.insert("1.0", line_numbers)
        gutter_widget.config(state='disabled')

    # --- SCROLLING LOGIC ---

    def _sync_scroll(self, *args):
        if self._sync_lock: return
        self._sync_lock = True
        self.master_scroll.set(*args)
        for w in (self.left_text, self.right_text, self.left_gutter, self.right_gutter):
            w.yview_moveto(args[0])
        self._sync_lock = False

    def _on_scrollbar_scroll(self, *args):
        for w in (self.left_text, self.right_text, self.left_gutter, self.right_gutter):
            w.yview(*args)

    def _on_mousewheel(self, event):
        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            delta = -int(event.delta / 120)
        for w in (self.left_text, self.right_text, self.left_gutter, self.right_gutter):
            w.yview_scroll(delta, "units")
        return "break"

    # --- FILE HANDLING & DIFF ---

    def load_left(self):
        self._load_file(self.left_text, "Original")

    def load_right(self):
        self._load_file(self.right_text, "Modified")

    def _load_file(self, widget, title):
        path = filedialog.askopenfilename(title=f"Select {title} File")
        if not path: return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            widget.delete("1.0", tk.END)
            widget.insert("1.0", content)
            self._update_all_gutters()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_diff(self):
        self.diff_view.configure(state='normal')
        self.diff_view.delete("1.0", tk.END)
        lines1 = self.left_text.get("1.0", "end-1c").splitlines()
        lines2 = self.right_text.get("1.0", "end-1c").splitlines()

        differ = difflib.Differ()
        diff_result = list(differ.compare(lines1, lines2))

        old_ln = new_ln = 0
        changes_found = False
        for line in diff_result:
            prefix, content = line[:2], line[2:]
            if prefix == "  ":
                old_ln += 1;
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
            self.diff_view.insert(tk.END, ">>> Files are identical.\n", "sign")
        self.diff_view.configure(state='disabled')

    def _insert_diff_line(self, old_num, new_num, sign, content, tag):
        l_part = f"{old_num:4}" if old_num else "    "
        r_part = f"{new_num:4}" if new_num else "    "
        self.diff_view.insert(tk.END, f"{l_part} | {r_part} | {sign} ", ("sign", "lineno"))
        self.diff_view.insert(tk.END, content + "\n", tag)


if __name__ == "__main__":
    app = SimpleDiffViewer()
    app.mainloop()