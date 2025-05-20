import tkinter as tk
from tkinter import ttk
import difflib
from tkinter.scrolledtext import ScrolledText


class TextDiffViewer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Text Diff Viewer")
        self.geometry("900x600")

        # Create main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create top frame for text inputs
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.BOTH, expand=True)

        # Left text input
        left_frame = ttk.LabelFrame(input_frame, text="Original Text")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.text1 = ScrolledText(left_frame, wrap=tk.WORD, width=40, height=10)
        self.text1.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Right text input
        right_frame = ttk.LabelFrame(input_frame, text="Modified Text")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.text2 = ScrolledText(right_frame, wrap=tk.WORD, width=40, height=10)
        self.text2.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Compare button
        self.compare_btn = ttk.Button(main_frame, text="Compare Texts", command=self.compare_texts)
        self.compare_btn.pack(pady=10)

        # Diff output
        diff_frame = ttk.LabelFrame(main_frame, text="Differences")
        diff_frame.pack(fill=tk.BOTH, expand=True)

        self.diff_text = ScrolledText(diff_frame, wrap=tk.WORD, height=15)
        self.diff_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Configure tags for highlighting
        self.diff_text.tag_configure('added', background='#90EE90')  # Light green
        self.diff_text.tag_configure('removed', background='#FFB6C1')  # Light red

    def compare_texts(self):
        # Get text from both inputs
        text1 = self.text1.get('1.0', tk.END).splitlines()
        text2 = self.text2.get('1.0', tk.END).splitlines()

        # Clear previous diff
        self.diff_text.delete('1.0', tk.END)

        # Generate diff
        differ = difflib.Differ()
        diff = list(differ.compare(text1, text2))

        # Display diff with highlighting
        for line in diff:
            if line.startswith('+ '):
                self.diff_text.insert(tk.END, line[2:] + '\n', 'added')
            elif line.startswith('- '):
                self.diff_text.insert(tk.END, line[2:] + '\n', 'removed')
            elif line.startswith('  '):
                self.diff_text.insert(tk.END, line[2:] + '\n')
            # Skip '?' lines as they're not needed for basic diff viewing


if __name__ == '__main__':
    app = TextDiffViewer()
    app.mainloop()
