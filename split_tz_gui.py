import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox

import geopandas as gpd
import threading
import os
import traceback


class GISSplitterApp:

    def __init__(self, root):

        self.root = root
        self.root.title("TAB Splitter")
        self.root.geometry("900x700")

        # =========================
        # ПЕРЕМЕННЫЕ
        # =========================

        self.np_file = tk.StringVar()
        self.tz_file = tk.StringVar()
        self.output_folder = tk.StringVar()

        self.name_field = tk.StringVar()

        self.mode_var = tk.StringVar(value="centroid")

        # =========================
        # UI
        # =========================

        self.build_ui()

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        padding = 10

        # ---------------------------------
        # NP FILE
        # ---------------------------------

        frame_np = ttk.LabelFrame(self.root, text="Таблица НП")
        frame_np.pack(fill="x", padx=padding, pady=padding)

        ttk.Entry(
            frame_np,
            textvariable=self.np_file,
            width=100
        ).pack(side="left", padx=5, pady=5)

        ttk.Button(
            frame_np,
            text="Выбрать",
            command=self.select_np_file
        ).pack(side="left", padx=5)

        # ---------------------------------
        # TZ FILE
        # ---------------------------------

        frame_tz = ttk.LabelFrame(self.root, text="Таблица ТЗ")
        frame_tz.pack(fill="x", padx=padding, pady=padding)

        ttk.Entry(
            frame_tz,
            textvariable=self.tz_file,
            width=100
        ).pack(side="left", padx=5, pady=5)

        ttk.Button(
            frame_tz,
            text="Выбрать",
            command=self.select_tz_file
        ).pack(side="left", padx=5)

        # ---------------------------------
        # OUTPUT
        # ---------------------------------

        frame_out = ttk.LabelFrame(self.root, text="Папка результата")
        frame_out.pack(fill="x", padx=padding, pady=padding)

        ttk.Entry(
            frame_out,
            textvariable=self.output_folder,
            width=100
        ).pack(side="left", padx=5, pady=5)

        ttk.Button(
            frame_out,
            text="Выбрать",
            command=self.select_output_folder
        ).pack(side="left", padx=5)

        # ---------------------------------
        # FIELD
        # ---------------------------------

        frame_field = ttk.LabelFrame(self.root, text="Поле с названием НП")
        frame_field.pack(fill="x", padx=padding, pady=padding)

        self.field_combo = ttk.Combobox(
            frame_field,
            textvariable=self.name_field,
            width=40,
            state="readonly"
        )

        self.field_combo.pack(padx=5, pady=5, anchor="w")

        # ---------------------------------
        # MODE
        # ---------------------------------

        frame_mode = ttk.LabelFrame(self.root, text="Режим пространственного поиска")
        frame_mode.pack(fill="x", padx=padding, pady=padding)

        ttk.Radiobutton(
            frame_mode,
            text="intersects (рекомендуется)",
            variable=self.mode_var,
            value="intersects"
        ).pack(anchor="w", padx=10, pady=5)

        ttk.Radiobutton(
            frame_mode,
            text="within (только полностью внутри)",
            variable=self.mode_var,
            value="within"
        ).pack(anchor="w", padx=10, pady=5)

        ttk.Radiobutton(
            frame_mode,
            text="centroid (по центроиду, рекомендуется)",
            variable=self.mode_var,
            value="centroid"
        ).pack(anchor="w", padx=10, pady=5)

        # ---------------------------------
        # START BUTTON
        # ---------------------------------

        ttk.Button(
            self.root,
            text="СТАРТ",
            command=self.start_processing
        ).pack(pady=15)

        # ---------------------------------
        # PROGRESS
        # ---------------------------------

        self.progress = ttk.Progressbar(
            self.root,
            orient="horizontal",
            mode="determinate"
        )

        self.progress.pack(fill="x", padx=padding, pady=5)

        # ---------------------------------
        # LOGS
        # ---------------------------------

        frame_logs = ttk.LabelFrame(self.root, text="Логи")
        frame_logs.pack(fill="both", expand=True, padx=padding, pady=padding)

        self.log_text = tk.Text(
            frame_logs,
            wrap="word",
            undo=True
        )

        self.log_text.pack(fill="both", expand=True)

        # =====================================
        # HOTKEYS
        # =====================================

        self.log_text.bind("<Control-a>", self.select_all)
        self.log_text.bind("<Control-A>", self.select_all)

        self.log_text.bind("<Control-c>", self.copy_selected)
        self.log_text.bind("<Control-C>", self.copy_selected)

        # Русская раскладка
        self.log_text.bind("<KeyPress>", self.handle_hotkeys)

        # =====================================
        # CONTEXT MENU
        # =====================================

        self.context_menu = tk.Menu(
            self.root,
            tearoff=0
        )

        self.context_menu.add_command(
            label="Копировать",
            command=self.copy_selected
        )

        self.context_menu.add_separator()

        self.context_menu.add_command(
            label="Выделить всё",
            command=self.select_all
        )

        self.log_text.bind(
            "<Button-3>",
            self.show_context_menu
        )

    # =====================================================
    # HOTKEY FUNCTIONS
    # =====================================================

    def select_all(self, event=None):

        self.log_text.tag_add(
            "sel",
            "1.0",
            "end"
        )

        return "break"

    def copy_selected(self, event=None):

        try:

            selected = self.log_text.get(
                "sel.first",
                "sel.last"
            )

            self.root.clipboard_clear()
            self.root.clipboard_append(selected)

        except:
            pass

        return "break"

    def show_context_menu(self, event):

        self.context_menu.tk_popup(
            event.x_root,
            event.y_root
        )

    def handle_hotkeys(self, event):

        try:

            ctrl_pressed = (event.state & 0x4) != 0

            if not ctrl_pressed:
                return

            key = event.keysym.lower()

            # Ctrl+A / Ctrl+Ф
            if key in ["a", "ф"]:
                self.select_all()

                return "break"

            # Ctrl+C / Ctrl+С
            if key in ["c", "с"]:
                self.copy_selected()

                return "break"

        except:
            pass

    # =====================================================
    # LOG
    # =====================================================

    def log(self, text):

        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")

        print(text)

    # =====================================================
    # FILES
    # =====================================================

    def select_np_file(self):

        filename = filedialog.askopenfilename(
            filetypes=[("MapInfo TAB", "*.tab")]
        )

        if filename:
            self.np_file.set(filename)
            self.load_fields(filename)

    def select_tz_file(self):

        filename = filedialog.askopenfilename(
            filetypes=[("MapInfo TAB", "*.tab")]
        )

        if filename:
            self.tz_file.set(filename)

    def select_output_folder(self):

        folder = filedialog.askdirectory()

        if folder:
            self.output_folder.set(folder)

    # =====================================================
    # LOAD FIELDS
    # =====================================================

    def load_fields(self, filename):

        try:

            gdf = gpd.read_file(filename)

            fields = list(gdf.columns)

            if "geometry" in fields:
                fields.remove("geometry")

            self.field_combo["values"] = fields

            if fields:
                self.name_field.set(fields[0])

            self.log(f"Загружены поля: {fields}")

        except Exception as e:
            self.log(str(e))

    # =====================================================
    # START
    # =====================================================

    def start_processing(self):

        thread = threading.Thread(target=self.process)
        thread.start()

    # =====================================================
    # PROCESS
    # =====================================================

    def process(self):

        try:

            np_path = self.np_file.get()
            tz_path = self.tz_file.get()
            output_folder = self.output_folder.get()
            name_field = self.name_field.get()
            mode = self.mode_var.get()

            if not np_path:
                messagebox.showerror("Ошибка", "Не выбрана таблица НП")
                return

            if not tz_path:
                messagebox.showerror("Ошибка", "Не выбрана таблица ТЗ")
                return

            if not output_folder:
                messagebox.showerror("Ошибка", "Не выбрана папка результата")
                return

            self.log("==============================")
            self.log("Загрузка таблиц...")

            np_gdf = gpd.read_file(np_path)
            tz_gdf = gpd.read_file(tz_path)

            self.log(f"НП: {len(np_gdf)} объектов")
            self.log(f"ТЗ: {len(tz_gdf)} объектов")

            # --------------------------------------
            # CRS
            # --------------------------------------

            if np_gdf.crs != tz_gdf.crs:
                raise Exception("Системы координат не совпадают")

            # --------------------------------------
            # VALIDATION
            # --------------------------------------

            self.log("Проверка геометрии...")

            np_gdf = np_gdf[np_gdf.is_valid]
            tz_gdf = tz_gdf[tz_gdf.is_valid]

            remaining_tz = tz_gdf.copy()

            total_np = len(np_gdf)
            exported_count = 0

            self.progress["maximum"] = total_np
            self.progress["value"] = 0

            # --------------------------------------
            # MAIN LOOP
            # --------------------------------------

            for index, np_row in np_gdf.iterrows():

                np_name = str(np_row[name_field]).strip()

                self.log("--------------------------------")
                self.log(f"НП: {np_name}")

                np_geom = np_row.geometry

                # ==================================
                # SPATIAL SEARCH
                # ==================================

                if mode == "within":

                    selected_tz = remaining_tz[
                        remaining_tz.within(np_geom)
                    ]

                elif mode == "centroid":

                    centroids = remaining_tz.geometry.centroid

                    selected_tz = remaining_tz[
                        centroids.within(np_geom)
                    ]

                else:

                    selected_tz = remaining_tz[
                        remaining_tz.intersects(np_geom)
                    ]

                self.log(f"Найдено ТЗ: {len(selected_tz)}")

                if selected_tz.empty:

                    self.progress["value"] += 1
                    self.root.update_idletasks()

                    continue

                # ==================================
                # SAVE ORIGINAL INDEXES
                # ==================================

                original_indexes = selected_tz.index.tolist()

                # ==================================
                # SAFE NAME
                # ==================================

                safe_name = (
                    np_name
                    .replace("/", "_")
                    .replace("\\", "_")
                    .replace(":", "_")
                    .replace("*", "_")
                    .replace("?", "_")
                    .replace('"', "_")
                    .replace("<", "_")
                    .replace(">", "_")
                    .replace("|", "_")
                )

                output_file = os.path.join(
                    output_folder,
                    f"{safe_name}.tab"
                )

                # ==================================
                # DISSOLVE BY NOTE
                # ==================================

                self.log("Слияние ТЗ по NOTE...")

                if "NOTE" not in selected_tz.columns:
                    raise Exception(
                        "В таблице ТЗ отсутствует поле NOTE"
                    )

                selected_tz["NOTE"] = (
                    selected_tz["NOTE"]
                    .fillna("EMPTY")
                    .astype(str)
                )

                selected_tz = selected_tz.dissolve(
                    by="NOTE",
                    aggfunc="first"
                )

                selected_tz = selected_tz.reset_index()

                self.log(
                    f"После слияния NOTE: {len(selected_tz)}"
                )

                # ==================================
                # SAVE
                # ==================================

                selected_tz.to_file(
                    output_file,
                    driver="MapInfo File"
                )

                self.log(f"Сохранено: {output_file}")

                exported_count += 1

                # ==================================
                # REMOVE EXPORTED
                # ==================================

                remaining_tz = remaining_tz.drop(original_indexes)

                self.log(
                    f"Осталось ТЗ: {len(remaining_tz)}"
                )

                self.progress["value"] += 1
                self.root.update_idletasks()

            # --------------------------------------
            # SAVE OUTSIDE
            # --------------------------------------

            self.log("==============================")
            self.log("Сохранение Вне_НП")

            outside_file = os.path.join(
                output_folder,
                "Вне_НП.tab"
            )

            remaining_tz.to_file(
                outside_file,
                driver="MapInfo File"
            )

            self.log(f"Сохранено: {outside_file}")

            # --------------------------------------
            # CHECK
            # --------------------------------------

            self.log("==============================")
            self.log("ПРОВЕРКА")

            self.log(f"Количество НП: {total_np}")
            self.log(f"Создано таблиц: {exported_count}")

            if exported_count == total_np:
                self.log("Проверка пройдена")
            else:
                self.log(
                    "ВНИМАНИЕ: количество таблиц не совпадает"
                )

            self.log("==============================")
            self.log("ГОТОВО")

            messagebox.showinfo(
                "Готово",
                "Обработка завершена"
            )

        except Exception as e:

            self.log("==============================")
            self.log("ОШИБКА")
            self.log(str(e))
            self.log(traceback.format_exc())

            messagebox.showerror(
                "Ошибка",
                str(e)
            )


# =========================================================
# START APP
# =========================================================

root = tk.Tk()
app = GISSplitterApp(root)
root.mainloop()