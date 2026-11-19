from datetime import datetime
import os
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image
import pillow_heif

pillow_heif.register_heif_opener()


class PhotoOrganizerApp:

  def __init__(self, root):
    self.root = root
    self.root.title("iPhone 照片全能整理助手 v2.0")
    self.root.geometry("560x510")
    self.root.resizable(False, False)

    frame_top = tk.Frame(root, pady=12, padx=20)
    frame_top.pack(fill="x")
    tk.Label(
        frame_top, text="目标照片文件夹：", font=("微软雅黑", 10, "bold")
    ).pack(anchor="w")

    frame_path = tk.Frame(frame_top, pady=5)
    frame_path.pack(fill="x")
    self.path_var = tk.StringVar()
    self.entry_path = tk.Entry(
        frame_path, textvariable=self.path_var, width=52, state="readonly"
    )
    self.entry_path.pack(side="left", padx=(0, 10))
    tk.Button(
        frame_path, text="选择文件夹", command=self.select_folder, width=10
    ).pack(side="right")

    frame_opts = tk.LabelFrame(
        root, text="整理功能选项", padx=15, pady=10, font=("微软雅黑", 9, "bold")
    )
    frame_opts.pack(fill="x", padx=20, pady=5)

    self.var_clean = tk.BooleanVar(value=True)
    tk.Checkbutton(
        frame_opts,
        text="1. 自动清理所有 .AAE 编辑记录及 ._ 隐藏垃圾小文件",
        variable=self.var_clean,
    ).pack(anchor="w")

    self.var_live = tk.BooleanVar(value=True)
    tk.Checkbutton(
        frame_opts,
        text="2. 自动识别实况照片(Live Photo)配套短视频，单独放入 [LivePhoto_实况短视频]",
        variable=self.var_live,
    ).pack(anchor="w", pady=(4, 0))

    self.var_heic = tk.BooleanVar(value=True)
    tk.Checkbutton(
        frame_opts,
        text="3. 自动将苹果 .HEIC 照片转换为通用高画质 .JPG",
        variable=self.var_heic,
    ).pack(anchor="w", pady=(4, 0))

    self.var_del_heic = tk.BooleanVar(value=False)
    tk.Checkbutton(
        frame_opts,
        text="    └─ 转换 JPG 成功后，自动删除原 .HEIC 文件（不勾选则保留双份）",
        variable=self.var_del_heic,
        fg="#555555",
    ).pack(anchor="w")

    self.var_sort = tk.BooleanVar(value=True)
    tk.Checkbutton(
        frame_opts,
        text="4. 剩余照片与正常视频按日期自动归类到 [年-月] 文件夹",
        variable=self.var_sort,
    ).pack(anchor="w", pady=(4, 0))

    self.btn_start = tk.Button(
        root,
        text="开始一键全能整理",
        command=self.start_thread,
        bg="#0078D7",
        fg="white",
        font=("微软雅黑", 11, "bold"),
        height=2,
        width=22,
    )
    self.btn_start.pack(pady=12)

    tk.Label(root, text="处理日志：", font=("微软雅黑", 9)).pack(
        anchor="w", padx=20
    )
    self.log_area = scrolledtext.ScrolledText(
        root, height=9, width=70, font=("Consolas", 9)
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
    self.btn_start.config(state="disabled", text="正在全力处理中...")
    threading.Thread(
        target=self.process_files, args=(folder,), daemon=True
    ).start()

  def safe_move(self, src_path, target_dir, filename):
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, filename)
    if os.path.exists(target_path):
      base, ext = os.path.splitext(filename)
      target_path = os.path.join(target_dir, f"{base}_dup{ext}")
    shutil.move(src_path, target_path)

  def process_files(self, folder):
    del_junk = 0
    live_count = 0
    heic_count = 0
    sort_count = 0

    photo_exts = {".jpg", ".jpeg", ".png", ".heic", ".raw", ".dng"}
    media_exts = photo_exts | {".mov", ".mp4", ".gif"}

    try:
      if self.var_clean.get():
        self.log(">>> [1/4] 扫描并清理 .AAE 与 ._ 垃圾小文件...")
        for root_dir, _, files in os.walk(folder):
          for file in files:
            if file.lower().endswith(".aae") or file.startswith("._"):
              try:
                os.remove(os.path.join(root_dir, file))
                del_junk += 1
              except Exception as e:
                self.log(f"删除失败 {file}: {e}")
        self.log(f"清理完成：删除 {del_junk} 个垃圾文件。")

      if self.var_live.get():
        self.log(">>> [2/4] 识别实况照片 (Live Photo) 短视频...")
        files = os.listdir(folder)
        photo_bases = set()
        for f in files:
          if os.path.isfile(os.path.join(folder, f)):
            b, e = os.path.splitext(f)
            if e.lower() in photo_exts:
              photo_bases.add(b.lower())

        live_dir = os.path.join(folder, "LivePhoto_实况短视频")
        for f in files:
          file_path = os.path.join(folder, f)
          if os.path.isfile(file_path):
            base, ext = os.path.splitext(f)
            if ext.lower() == ".mov" and base.lower() in photo_bases:
              self.safe_move(file_path, live_dir, f)
              live_count += 1
        self.log(f"分离完成：归类 {live_count} 个实况短视频。")

      if self.var_heic.get():
        self.log(">>> [3/4] 转换 .HEIC 照片为高画质 .JPG...")
        for f in os.listdir(folder):
          file_path = os.path.join(folder, f)
          if os.path.isfile(file_path) and f.lower().endswith(".heic"):
            base, _ = os.path.splitext(f)
            jpg_path = os.path.join(folder, f"{base}.jpg")
            try:
              mtime = os.path.getmtime(file_path)
              with Image.open(file_path) as img:
                rgb_img = img.convert("RGB")
                rgb_img.save(jpg_path, "JPEG", quality=95)
              os.utime(jpg_path, (mtime, mtime))
              heic_count += 1
              if self.var_del_heic.get():
                os.remove(file_path)
            except Exception as e:
              self.log(f"转换失败 {f}: {e}")
        self.log(f"转换完成：成功转换 {heic_count} 张 HEIC 照片。")

      if self.var_sort.get():
        self.log(">>> [4/4] 按年月归类剩余照片与视频...")
        for f in os.listdir(folder):
          file_path = os.path.join(folder, f)
          if os.path.isfile(file_path):
            _, ext = os.path.splitext(f)
            if ext.lower() in media_exts:
              mtime = os.path.getmtime(file_path)
              date_folder = datetime.fromtimestamp(mtime).strftime("%Y-%m")
              target_dir = os.path.join(folder, date_folder)
              self.safe_move(file_path, target_dir, f)
              sort_count += 1
        self.log(f"归类完成：整理 {sort_count} 个媒体文件。")

      self.log("=== 全部处理顺利完成！ ===")
      messagebox.showinfo(
          "整理完成",
          f"全部处理完成！\n\n"
          f"• 删除垃圾小文件：{del_junk} 个\n"
          f"• 归类实况短视频：{live_count} 个\n"
          f"• HEIC 转换 JPG：{heic_count} 张\n"
          f"• 按年月归类文件：{sort_count} 个",
      )

    except Exception as e:
      self.log(f"发生错误: {e}")
      messagebox.showerror("错误", f"处理过程中出现问题：{e}")
    finally:
      self.btn_start.config(state="normal", text="开始一键全能整理")


if __name__ == "__main__":
  root = tk.Tk()
  app = PhotoOrganizerApp(root)
  root.mainloop()
