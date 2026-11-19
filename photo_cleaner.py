import os
import shutil
import threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, scrolledtext


class PhotoOrganizerApp:

  def __init__(self, root):
    self.root = root
    self.root.title("iPhone 照片一键清理与归类助手")
    self.root.geometry("520x420")
    self.root.resizable(False, False)

    frame_top = tk.Frame(root, pady=15, padx=20)
    frame_top.pack(fill="x")

    tk.Label(
        frame_top, text="目标照片文件夹：", font=("微软雅黑", 10, "bold")
    ).pack(anchor="w")

    frame_path = tk.Frame(frame_top, pady=5)
    frame_path.pack(fill="x")

    self.path_var = tk.StringVar()
    self.entry_path = tk.Entry(
        frame_path, textvariable=self.path_var, width=48, state="readonly"
    )
    self.entry_path.pack(side="left", padx=(0, 10))

    btn_browse = tk.Button(
        frame_path, text="选择文件夹", command=self.select_folder, width=10
    )
    btn_browse.pack(side="right")

    frame_opts = tk.LabelFrame(
        root, text="整理选项", padx=15, pady=10, font=("微软雅黑", 9)
    )
    frame_opts.pack(fill="x", padx=20, pady=5)

    self.var_clean = tk.BooleanVar(value=True)
    tk.Checkbutton(
        frame_opts,
        text="自动清理所有 .AAE 编辑记录及 ._ 隐藏垃圾小文件",
        variable=self.var_clean,
    ).pack(anchor="w")

    self.var_sort = tk.BooleanVar(value=True)
    tk.Checkbutton(
        frame_opts,
        text="按照片/视频日期自动归类到 [年-月] 文件夹",
        variable=self.var_sort,
    ).pack(anchor="w", pady=(5, 0))

    self.btn_start = tk.Button(
        root,
        text="开始一键整理",
        command=self.start_thread,
        bg="#0078D7",
        fg="white",
        font=("微软雅黑", 11, "bold"),
        height=2,
        width=20,
    )
    self.btn_start.pack(pady=15)

    tk.Label(root, text="处理日志：", font=("微软雅黑", 9)).pack(
        anchor="w", padx=20
    )
    self.log_area = scrolledtext.ScrolledText(
        root, height=8, width=65, font=("Consolas", 9)
    )
    self.log_area.pack(padx=20, pady=(2, 15))

  def log(self, message):
    self.log_area.insert(tk.END, message + "\n")
    self.log_area.see(tk.END)

  def select_folder(self):
    folder = filedialog.askdirectory()
    if folder:
      self.path_var.set(folder)
      self.log(f"已选择文件夹: {folder}")

  def start_thread(self):
    folder = self.path_var.get()
    if not folder or not os.path.exists(folder):
      messagebox.showwarning("提示", "请先选择一个有效的照片文件夹！")
      return
    self.btn_start.config(state="disabled", text="正在处理中...")
    threading.Thread(
        target=self.process_files, args=(folder,), daemon=True
    ).start()

  def process_files(self, folder):
    deleted_count = 0
    moved_count = 0
    media_exts = {
        ".jpg",
        ".jpeg",
        ".png",
        ".heic",
        ".mov",
        ".mp4",
        ".gif",
        ".raw",
        ".dng",
    }

    try:
      if self.var_clean.get():
        self.log(">>> 开始扫描并清理无用小文件...")
        for root_dir, dirs, files in os.walk(folder):
          for file in files:
            lower_name = file.lower()
            if lower_name.endswith(".aae") or file.startswith("._"):
              file_path = os.path.join(root_dir, file)
              try:
                os.remove(file_path)
                deleted_count += 1
              except Exception as e:
                self.log(f"删除失败 {file}: {e}")
        self.log(f"清理完成：共删除 {deleted_count} 个垃圾小文件。")

      if self.var_sort.get():
        self.log(">>> 开始按年月归类照片和视频...")
        for file in os.listdir(folder):
          file_path = os.path.join(folder, file)
          if os.path.isfile(file_path):
            ext = os.path.splitext(file).lower()
            if ext in media_exts:
              mtime = os.path.getmtime(file_path)
              date_folder = datetime.fromtimestamp(mtime).strftime("%Y-%m")
              target_dir = os.path.join(folder, date_folder)
              os.makedirs(target_dir, exist_ok=True)

              target_path = os.path.join(target_dir, file)
              if os.path.exists(target_path):
                base, extension = os.path.splitext(file)
                target_path = os.path.join(
                    target_dir, f"{base}_dup{extension}"
                )

              shutil.move(file_path, target_path)
              moved_count += 1
        self.log(f"归类完成：共整理 {moved_count} 个照片/视频文件。")

      self.log("=== 全部处理完成！ ===")
      messagebox.showinfo(
          "完成",
          f"整理完成！\n删除垃圾文件：{deleted_count} 个\n归类媒体文件：{moved_count} 个",
      )

    except Exception as e:
      self.log(f"发生错误: {e}")
      messagebox.showerror("错误", f"处理过程中出现问题：{e}")
    finally:
      self.btn_start.config(state="normal", text="开始一键整理")


if __name__ == "__main__":
  root = tk.Tk()
  app = PhotoOrganizerApp(root)
  root.mainloop()
