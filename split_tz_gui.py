import tkinter as tk
from tkinter import filedialog, ttk, messagebox

import geopandas as gpd
import threading
import os
import traceback
import warnings

warnings.filterwarnings("ignore")


class GISSplitterApp:

    def __init__(self, root):
        self.root = root
        self.root.title("TAB Splitter")
        self.root.geometry("900x650")

        self.np_file = tk.StringVar()
        self.tz_file = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.name_field = tk.StringVar()

        self.build_ui()

    def build_ui(self):
        p = 10

        frame_np = ttk.LabelFrame(self.root, text="Таблица НП (границы)")
        frame_np.pack(fill="x", padx=p, pady=p)
        ttk.Entry(frame_np, textvariable=self.np_file, width=100).pack(side="left", padx=5, pady=5)
        ttk.Button(frame_np, text="Выбрать", command=self.select_np_file).pack(side="left", padx=5)

        frame_tz = ttk.LabelFrame(self.root, text="Таблица ТЗ")
        frame_tz.pack(fill="x", padx=p, pady=p)
        ttk.Entry(frame_tz, textvariable=self.tz_file, width=100).pack(side="left", padx=5, pady=5)
        ttk.Button(frame_tz, text="Выбрать", command=self.select_tz_file).pack(side="left", padx=5)

        frame_out = ttk.LabelFrame(self.root, text="Папка результата")
        frame_out.pack(fill="x", padx=p, pady=p)
        ttk.Entry(frame_out, textvariable=self.output_folder, width=100).pack(side="left", padx=5, pady=5)
        ttk.Button(frame_out, text="Выбрать", command=self.select_output_folder).pack(side="left", padx=5)

        frame_field = ttk.LabelFrame(self.root, text="Поле с названием НП")
        frame_field.pack(fill="x", padx=p, pady=p)
        self.field_combo = ttk.Combobox(
            frame_field, textvariable=self.name_field, width=50, state="readonly"
        )
        self.field_combo.pack(padx=5, pady=5, anchor="w")

        ttk.Button(self.root, text="  СТАРТ  ", command=self.start_processing).pack(pady=12)

        self.progress = ttk.Progressbar(self.root, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=p, pady=4)

        frame_logs = ttk.LabelFrame(self.root, text="Логи")
        frame_logs.pack(fill="both", expand=True, padx=p, pady=p)
        self.log_text = tk.Text(frame_logs, wrap="word")
        self.log_text.pack(fill="both", expand=True)

        for seq in ("<Control-a>", "<Control-A>"):
            self.log_text.bind(seq, lambda e: self.select_all())
        for seq in ("<Control-c>", "<Control-C>"):
            self.log_text.bind(seq, lambda e: self.copy_selected())
        self.log_text.bind("<KeyPress>", self.handle_hotkeys)

        ctx = tk.Menu(self.root, tearoff=0)
        ctx.add_command(label="Копировать", command=self.copy_selected)
        ctx.add_separator()
        ctx.add_command(label="Выделить всё", command=self.select_all)
        self.log_text.bind("<Button-3>", lambda e: ctx.tk_popup(e.x_root, e.y_root))

    def select_all(self):
        self.log_text.tag_add("sel", "1.0", "end")

    def copy_selected(self):
        try:
            txt = self.log_text.get("sel.first", "sel.last")
            self.root.clipboard_clear()
            self.root.clipboard_append(txt)
        except Exception:
            pass

    def handle_hotkeys(self, event):
        if not (event.state & 0x4):
            return
        key = event.keysym.lower()
        if key in ("a", "ф"):
            self.select_all()
            return "break"
        if key in ("c", "с"):
            self.copy_selected()
            return "break"

    def log(self, text):
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        print(text)

    def select_np_file(self):
        f = filedialog.askopenfilename(filetypes=[("MapInfo TAB", "*.tab")])
        if f:
            self.np_file.set(f)
            self.load_np_fields(f)

    def select_tz_file(self):
        f = filedialog.askopenfilename(filetypes=[("MapInfo TAB", "*.tab")])
        if f:
            self.tz_file.set(f)

    def select_output_folder(self):
        f = filedialog.askdirectory()
        if f:
            self.output_folder.set(f)

    def load_np_fields(self, path):
        try:
            gdf = gpd.read_file(path)
            fields = [c for c in gdf.columns if c != "geometry"]
            self.field_combo["values"] = fields
            if fields:
                self.name_field.set(fields[0])
            self.log(f"Поля НП: {fields}")
        except Exception as e:
            self.log(f"Ошибка чтения полей: {e}")

    @staticmethod
    def to_safe_filename(name: str) -> str:
        for ch in r'/\:*?"<>|':
            name = name.replace(ch, "_")
        return name.strip()

    @staticmethod
    def delete_tab(path: str):
        base = os.path.splitext(path)[0]
        for ext in ("tab", "TAB", "dat", "DAT", "id", "ID",
                    "ind", "IND", "map", "MAP"):
            p = f"{base}.{ext}"
            if os.path.exists(p):
                os.remove(p)

    @staticmethod
    def fix_geom(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        gdf = gdf.copy()
        gdf["geometry"] = gdf.geometry.buffer(0)
        gdf = gdf[~gdf.geometry.is_empty & gdf.is_valid].reset_index(drop=True)
        return gdf

    def start_processing(self):
        threading.Thread(target=self.process, daemon=True).start()

    def process(self):
        try:
            np_path  = self.np_file.get()
            tz_path  = self.tz_file.get()
            out_dir  = self.output_folder.get()
            name_fld = self.name_field.get()

            if not np_path:
                messagebox.showerror("Ошибка", "Не выбрана таблица НП"); return
            if not tz_path:
                messagebox.showerror("Ошибка", "Не выбрана таблица ТЗ"); return
            if not out_dir:
                messagebox.showerror("Ошибка", "Не выбрана папка результата"); return
            if not name_fld:
                messagebox.showerror("Ошибка", "Не выбрано поле с названием НП"); return

            os.makedirs(out_dir, exist_ok=True)

            self.log("=" * 50)
            self.log("Загрузка данных...")

            np_gdf = gpd.read_file(np_path)
            tz_gdf = gpd.read_file(tz_path)

            self.log(f"НП загружено: {len(np_gdf)}")
            self.log(f"ТЗ загружено: {len(tz_gdf)}")

            np_gdf = self.fix_geom(np_gdf)
            tz_gdf = self.fix_geom(tz_gdf)

            if np_gdf.crs != tz_gdf.crs:
                self.log("Выравниваю системы координат...")
                tz_gdf = tz_gdf.to_crs(np_gdf.crs)

            # MultiPolygon → Polygon
            np_exp = np_gdf.explode(index_parts=False).reset_index(drop=True)

            # --------------------------------------------------------
            # representative_point — в отличие от centroid всегда
            # гарантированно лежит ВНУТРИ полигона, даже у вытянутых
            # и подковообразных ТЗ
            # --------------------------------------------------------
            self.log("Вычисление representative_point для ТЗ...")
            tz_rep = tz_gdf.copy()
            tz_rep["geometry"] = tz_gdf.geometry.apply(lambda g: g.representative_point())

            # --------------------------------------------------------
            # Шаг 1: строгий within
            # --------------------------------------------------------
            self.log("Шаг 1: пространственное соединение (within)...")

            joined = gpd.sjoin(
                tz_rep[["geometry"]],
                np_exp[[name_fld, "geometry"]],
                how="left",
                predicate="within"
            )

            good_mask    = joined["index_right"].notna() & ~joined.index.duplicated(keep=False)
            problem_mask = joined.index.duplicated(keep=False) & joined["index_right"].notna()
            outside_mask = joined["index_right"].isna()

            good_joined    = joined[good_mask]
            outside_idx    = joined[outside_mask].index.unique().tolist()
            problem_idx    = joined[problem_mask].index.unique().tolist()

            self.log(f"  Попали строго в НП: {len(good_joined)}")
            self.log(f"  На границе двух НП: {len(problem_idx)}")
            self.log(f"  Не попали (погрешность координат): {len(outside_idx)}")

            # --------------------------------------------------------
            # Шаг 2: для оставшихся — ближайший НП до 150 м
            # 150 м перекрывает все реальные случаи погрешности
            # границ в кадастровых данных
            # --------------------------------------------------------
            nearest_joined = None
            still_outside_idx = []

            if outside_idx:
                self.log("Шаг 2: поиск ближайшего НП (до 150 м)...")

                nearest_joined = gpd.sjoin_nearest(
                    tz_rep.loc[outside_idx, ["geometry"]],
                    np_exp[[name_fld, "geometry"]],
                    how="left",
                    max_distance=150
                )
                # дропаем дубли (равноудалённые НП) — берём первый
                nearest_joined = nearest_joined[~nearest_joined.index.duplicated(keep="first")]

                found = nearest_joined["index_right"].notna()
                still_outside_idx = nearest_joined[~found].index.tolist()

                self.log(f"  Нашли ближайший НП: {found.sum()}")
                self.log(f"  Реально вне НП: {len(still_outside_idx)}")

            # --------------------------------------------------------
            # Итоговый маппинг: индекс ТЗ → название НП
            # --------------------------------------------------------
            tz_to_np = {}

            for tz_idx, row in good_joined.iterrows():
                tz_to_np[tz_idx] = row[name_fld]

            if nearest_joined is not None:
                for tz_idx, row in nearest_joined[nearest_joined["index_right"].notna()].iterrows():
                    tz_to_np[tz_idx] = row[name_fld]

            # --------------------------------------------------------
            # Сохраняем файл на каждый НП
            # --------------------------------------------------------
            np_names = np_gdf[name_fld].unique()
            self.progress["maximum"] = len(np_names)
            self.progress["value"]   = 0

            skipped = []

            for np_name in np_names:
                self.log("-" * 40)
                self.log(f"НП: {np_name}")

                tz_idx_for_np = [idx for idx, name in tz_to_np.items() if name == np_name]
                subset = tz_gdf.loc[tz_idx_for_np].copy().reset_index(drop=True)

                if subset.empty:
                    self.log("  ТЗ не найдено! Проверьте данные.")
                    skipped.append(np_name)
                    self.progress["value"] += 1
                    self.root.update_idletasks()
                    continue

                self.log(f"  ТЗ: {len(subset)}")

                out_path = os.path.join(
                    out_dir,
                    f"{self.to_safe_filename(np_name)}.tab"
                )
                self.delete_tab(out_path)
                subset.to_file(out_path, driver="MapInfo File")
                self.log(f"  Сохранено: {out_path}")

                self.progress["value"] += 1
                self.root.update_idletasks()

            # --------------------------------------------------------
            # Проблемные (на стыке двух НП)
            # --------------------------------------------------------
            if problem_idx:
                out_prob = os.path.join(out_dir, "Проблемные_ТЗ.tab")
                self.delete_tab(out_prob)
                tz_gdf.loc[problem_idx].reset_index(drop=True).to_file(out_prob, driver="MapInfo File")
                self.log(f"\nПроблемные ТЗ ({len(problem_idx)} шт.) → {out_prob}")

            # --------------------------------------------------------
            # Реально вне НП (>150 м от любой границы)
            # --------------------------------------------------------
            real_outside = still_outside_idx if nearest_joined is not None else outside_idx
            if real_outside:
                out_outside = os.path.join(out_dir, "Вне_НП.tab")
                self.delete_tab(out_outside)
                tz_gdf.loc[real_outside].reset_index(drop=True).to_file(out_outside, driver="MapInfo File")
                self.log(f"Вне НП ({len(real_outside)} шт.) → {out_outside}")

            # --------------------------------------------------------
            # Итог
            # --------------------------------------------------------
            self.log("=" * 50)
            self.log("ИТОГ")
            self.log(f"  НП всего:           {len(np_names)}")
            self.log(f"  Файлов создано:     {len(np_names) - len(skipped)}")
            if skipped:
                self.log(f"  НП без ТЗ ({len(skipped)}):")
                for s in skipped:
                    self.log(f"    - {s}")
            self.log(f"  Проблемных ТЗ:      {len(problem_idx)}")
            self.log(f"  Реально вне НП:     {len(real_outside)}")
            self.log("=" * 50)
            self.log("ГОТОВО")

            messagebox.showinfo(
                "Готово",
                f"Готово!\n\n"
                f"Файлов создано: {len(np_names) - len(skipped)}\n"
                f"НП без ТЗ: {len(skipped)}\n"
                f"Проблемных ТЗ: {len(problem_idx)}\n"
                f"Реально вне НП: {len(real_outside)}"
            )

        except Exception as e:
            self.log("ОШИБКА:")
            self.log(str(e))
            self.log(traceback.format_exc())
            messagebox.showerror("Ошибка", str(e))


root = tk.Tk()
app = GISSplitterApp(root)
root.mainloop()