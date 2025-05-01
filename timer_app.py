import tkinter as tk
from tkinter import ttk
import time
from utils import *
from timer_tracker import TimeTracker

class TimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Timer")
        self.width = 250
        self.height = 120
        self.tracker = TimeTracker()
        self.is_expanded = False
        self.update_job = None
        self._build_start_screen()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_start_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        frame = ttk.Frame(self.root, padding="20 20 20 20")
        frame.pack(expand=True)
        label = ttk.Label(frame, text="Select Activity to Start", font=("Helvetica", 14, "bold"))
        label.pack(pady=(0, 10))
        btn_study = ttk.Button(frame, text="Start Study", width=18, command=lambda: self._start_activity_and_show_timer(STUDY))
        btn_study.pack(pady=4)
        btn_ent = ttk.Button(frame, text="Start Entertainment", width=18, command=lambda: self._start_activity_and_show_timer(ENTERTAINMENT))
        btn_ent.pack(pady=4)

    def _start_activity_and_show_timer(self, activity):
        self.tracker.start_activity(activity)
        self._reset_window(self.width, self.height)
        self._build_timer_window()
        self._update_timer_ui()

    def _reset_window(self, width, height):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.geometry("{}x{}".format(width, height))
        self.root.minsize(self.width, self.height)
        self.root.attributes("-topmost", True)
    
    def _build_timer_window(self):
        # --- buttons ---
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=8, pady=(5, 2))
        self.pause_btn = ttk.Button(btn_frame, text="Pause" if not self.tracker.is_paused else "Resume", width=6, command=self._toggle_pause)
        self.pause_btn.pack(side="left", padx=2)
        self.switch_btn = ttk.Button(btn_frame, text="Switch", width=6, command=self._switch_activity)
        self.switch_btn.pack(side="left", padx=2)
        self.expand_btn = ttk.Button(btn_frame, text="Expand" if not self.is_expanded else "Collapse", width=7, command=self._expand_or_collapse)
        self.expand_btn.pack(side="right", padx=2)
        
        # --- status and time ---
        self.status_var = tk.StringVar(value=self.tracker.get_status())
        self.status_label = ttk.Label(self.root, textvariable=self.status_var, font=("Helvetica", 13, "bold"))
        self.status_label.pack(anchor="w", padx=12, pady=(4, 0))
        self.time_var = tk.StringVar(value=format_time(self.tracker.get_current_duration()))
        self.time_label = ttk.Label(self.root, textvariable=self.time_var, font=("Consolas", 18))
        self.time_label.pack(anchor="w", padx=12, pady=(0, 4))
        
        # --- bar ---
        self.canvas = tk.Canvas(self.root, height=10, width=220, bg="#f0f0f0", highlightthickness=0)
        self.canvas.pack(anchor="w", padx=15, pady=(0, 5))
        self.study_bar = self.canvas.create_rectangle(0, 0, 0, 10, fill="#4caf50", outline="")
        self.ent_bar = self.canvas.create_rectangle(0, 0, 0, 10, fill="#f44336", outline="")

    def _add_bar_tooltips(self):
        if not hasattr(self, 'canvas') or not self.canvas.winfo_exists():
            return
            
        study, ent = self.tracker.get_totals()
        total = study + ent
        
        study_percent = (study / total * 100) if total > 0 else 0
        ent_percent = (ent / total * 100) if total > 0 else 0
        
        tip_text = f"Study: {format_time(study)} ({study_percent:.1f}%)\nEntertainment: {format_time(ent)} ({ent_percent:.1f}%)"
        
        self._add_tooltip(self.canvas, self.study_bar, tip_text)
        self._add_tooltip(self.canvas, self.ent_bar, tip_text)

    def _update_timer_ui(self):
        now = time.time()
        self.status_var.set(self.tracker.get_status())
        self.time_var.set(format_time(self.tracker.get_current_duration()))
        self.pause_btn.config(text="Resume" if self.tracker.is_paused else "Pause")
        
        # update the bar widths based on study and entertainment time
        study, ent = self.tracker.get_totals()
        total = study + ent
        width = 220
        study_w = int(width * (study / total)) if total > 0 else 0
        ent_w = int(width * (ent / total)) if total > 0 else 0
        self.canvas.coords(self.study_bar, 0, 0, study_w, 18)
        self.canvas.coords(self.ent_bar, study_w, 0, study_w + ent_w, 18)
        
        self._add_bar_tooltips()
        
        # refresh the UI every 500ms
        if self.update_job:
            self.root.after_cancel(self.update_job)
        self.update_job = self.root.after(500, self._update_timer_ui)

    def _toggle_pause(self):
        if self.tracker.is_paused:
            self.tracker.resume()
        else:
            self.tracker.pause()
        self._update_timer_ui()

    def _switch_activity(self):
        self.tracker.switch_activity()
        self._update_timer_ui()

    def _expand_or_collapse(self):
        if not self.is_expanded:
            self._expand_window()
        else:
            self._collapse_window()

    def _expand_window(self):
        self.is_expanded = True
        self._reset_window(800, 260)
        self._build_timer_window()
        self._draw_heatmap()
        self._update_timer_ui()

    def _draw_heatmap(self):
        import glob, json
        from datetime import datetime, timedelta
        # we only display the last 365 days of data
        files = glob.glob(os.path.join(DATA_DIR, "data_*.json"))
        day_map = {}
        for f in files:
            try:
                with open(f, 'r') as fp:
                    d = json.load(fp)
                    day = d.get("date")
                    study = d.get("total_study", 0)
                    if day:
                        day_map[day] = study
            except Exception as e:
                print(f"Error reading file {f}: {e}")
                
        # ensure today's data is the latest
        if self.tracker.current_activity:
            today_str = date.today().strftime(DATE_FORMAT)
            study, ent = self.tracker.get_totals()
            day_map[today_str] = study
                
        today = date.today()
        days = []
        one_year_ago = today - timedelta(days=365)
        current_date = one_year_ago
        while current_date <= today:
            days.append(current_date)
            current_date += timedelta(days=1)
                
        actual_days = len(days)
        # print(f"Total days in heat map: {actual_days}")
        
        # obatin the study time for each day
        day_strs = [d.strftime(DATE_FORMAT) for d in days]
        study_list = [day_map.get(ds, 0) for ds in day_strs]
        
        max_study = max(study_list) if any(study_list) else 1
        
        # debug
        # print(f"Today: {today.strftime(DATE_FORMAT)}")
        # print(f"First day: {days[0].strftime(DATE_FORMAT)}")
        # print(f"Last day: {days[-1].strftime(DATE_FORMAT)}")
        # print(f"Max study time: {format_time(max_study)}")
        
        if hasattr(self, 'heatmap_canvas'):
            self.heatmap_canvas.destroy()
            
        cell_size = 12
        cell_pad = 2
        
        first_day_weekday = days[0].weekday()
        total_weeks = (actual_days + first_day_weekday + 6) // 7
        
        canvas_width = min(total_weeks * (cell_size + cell_pad) + 40, 800)  # restrict to 800px
        canvas_height = 7 * (cell_size + cell_pad) + 20  # 7 rows for 7 days
        
        heatmap_frame = ttk.Frame(self.root)
        heatmap_frame.pack(fill="both", expand=True, padx=10, pady=2)
        
        self.heatmap_canvas = tk.Canvas(heatmap_frame, width=canvas_width, height=canvas_height, 
                                     bg="#f8f8f8", highlightthickness=0)
        scrollbar = ttk.Scrollbar(heatmap_frame, orient="horizontal", command=self.heatmap_canvas.xview)
        self.heatmap_canvas.configure(xscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="bottom", fill="x")
        self.heatmap_canvas.pack(side="top", fill="both", expand=True)
        
        scroll_width = total_weeks * (cell_size + cell_pad) + 40
        self.heatmap_canvas.configure(scrollregion=(0, 0, scroll_width, canvas_height))
        
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(weekdays):
            self.heatmap_canvas.create_text(15, i*(cell_size+cell_pad) + cell_size//2 + 20, 
                                          text=day, font=("Arial", 8), fill="#666")
        
        grid_cells = []
        
        # append the first week with empty cells
        for i in range(first_day_weekday):
            grid_cells.append((i, 0, None))
            
        # append the rest of the days
        for i, day in enumerate(days):
            week = (i + first_day_weekday) // 7
            weekday = day.weekday()
            grid_cells.append((weekday, week, day))
            
        for row, col, date_obj in grid_cells:
            x0 = 30 + col*(cell_size+cell_pad)
            y0 = 20 + row*(cell_size+cell_pad)
            x1 = x0 + cell_size
            y1 = y0 + cell_size
            
            if date_obj is not None:
                date_str = date_obj.strftime(DATE_FORMAT)
                study_sec = day_map.get(date_str, 0)
                
                ratio = study_sec / max_study if max_study > 0 else 0
                
                if ratio == 0:
                    color = "#ebedf0"  # GitHub style gray
                else:
                    # from light green(#9be9a8) to dark green(#216e39)
                    if ratio < 0.2:
                        color = "#9be9a8"  # little study
                    elif ratio < 0.4:
                        color = "#40c463"  # fairly study
                    elif ratio < 0.6:
                        color = "#30a14e"  # medium study
                    elif ratio < 0.8:
                        color = "#216e39"  # high study
                    else:
                        color = "#0a492a"  # most study
                
                rect = self.heatmap_canvas.create_rectangle(x0, y0, x1, y1, 
                                                         fill=color, outline="", width=0)
                
                ent_sec = 0
                try:
                    file_path = get_data_file_path(date_obj)
                    if os.path.exists(file_path):
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            ent_sec = data.get("total_entertainment", 0)
                except Exception:
                    pass
                    
                total_day = study_sec + ent_sec
                study_percent = (study_sec / total_day * 100) if total_day > 0 else 0
                ent_percent = (ent_sec / total_day * 100) if total_day > 0 else 0
                
                weekday_name = date_obj.strftime("%A")
                tip = f"{weekday_name}, {date_str}\nStudy: {format_time(study_sec)} ({study_percent:.1f}%)\nEntertainment: {format_time(ent_sec)} ({ent_percent:.1f}%)"
                self._add_tooltip(self.heatmap_canvas, rect, tip)
            else:
                # use a light gray for empty cells
                self.heatmap_canvas.create_rectangle(x0, y0, x1, y1, 
                                                  fill="#f5f5f5", outline="#e0e0e0", width=1)
            
        # add month labels
        months = []
        current_month = None
        
        # collect month labels
        for i, day in enumerate(days):
            month = day.strftime("%b")  # month abbreviation
            if month != current_month:
                current_month = month
                week_position = (i + first_day_weekday) // 7
                months.append((month, week_position))
        
        for month, col in months:
            self.heatmap_canvas.create_text(30 + col*(cell_size+cell_pad) + cell_size//2, 
                                          10, text=month, font=("Arial", 8), fill="#666")
                                          
        # scroll to the rightmost position
        self.heatmap_canvas.xview_moveto(1.0)

    def _add_tooltip(self, canvas, item, text):
        self._tooltip_windows = getattr(self, '_tooltip_windows', {})
        if item in self._tooltip_windows and self._tooltip_windows[item]:
            tip = self._tooltip_windows[item]
            tip.winfo_children()[0].config(text=text)
        
        def on_enter(event):
            x = event.x_root + 15
            y = event.y_root + 10
            tip = tk.Toplevel(canvas)
            tip.wm_overrideredirect(True)
            tip.wm_geometry(f"+{x}+{y}")
            tip.attributes("-topmost", True)
            tip.configure(bg="#ffffe0", bd=1, relief="solid")
            
            label = tk.Label(tip, text=text, bg="#ffffe0", justify="left",
                           font=("Arial", 9), padx=5, pady=3)
            label.pack()
            
            self._tooltip_windows[item] = tip
        
        def on_leave(event):
            if item in self._tooltip_windows and self._tooltip_windows[item]:
                try:
                    self._tooltip_windows[item].destroy()
                except tk.TclError:
                    pass
                self._tooltip_windows[item] = None
                
        def on_motion(event):
            # update tooltip position on motion
            if item in self._tooltip_windows and self._tooltip_windows[item]:
                try:
                    self._tooltip_windows[item].geometry(f"+{event.x_root+15}+{event.y_root+10}")
                except tk.TclError:
                    pass
                
        # bind events to the item
        tag_id_enter = canvas.tag_bind(item, '<Enter>', on_enter)
        tag_id_leave = canvas.tag_bind(item, '<Leave>', on_leave)
        tag_id_motion = canvas.tag_bind(item, '<Motion>', on_motion)
        
        def cleanup_tooltips():
            for tip_item, tip_window in list(self._tooltip_windows.items()):
                if tip_window and tip_window.winfo_exists():
                    tip_window.destroy()
            self._tooltip_windows.clear()
        
        # bind cleanup to canvas destroy event
        if not hasattr(canvas, '_tooltip_cleanup_bound'):
            canvas.bind('<Destroy>', lambda e: cleanup_tooltips())
            canvas._tooltip_cleanup_bound = True

    def on_close(self):
        if self.tracker.current_activity and not self.tracker.is_paused:
            self.tracker._update_totals()
        self.tracker.save_today_data()
        self.root.destroy()

    def _collapse_window(self):
        self.is_expanded = False
        self._reset_window(self.width, self.height)
        self._build_timer_window()
        self._update_timer_ui()
        
if __name__ == "__main__":
    root = tk.Tk()
    app = TimerApp(root)
    root.mainloop()