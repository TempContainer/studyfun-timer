from utils import *
import json
import time

class TimeTracker:
    def __init__(self):
        self.current_activity = None # STUDY or ENTERTAINMENT
        self.paused_time = None # Time when pause started
        self.is_paused = False
        self.total_study_time = 0
        self.total_entertainment_time = 0
        self.session_start_time = None # Start time of the current activity segment
        self.elapsed_time = 0

        self.load_today_data()

    def load_today_data(self):
        """Loads total times from today's data file."""
        filepath = get_data_file_path()
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    self.total_study_time = data.get("total_study", 0)
                    self.total_entertainment_time = data.get("total_entertainment", 0)
                    # We don't restore the 'current' state, just totals
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading data for today: {e}")
            self.total_study_time = 0
            self.total_entertainment_time = 0

    def save_today_data(self):
        """Saves the current total times to today's data file."""
        filepath = get_data_file_path()
        data = {
            "date": date.today().strftime(DATE_FORMAT),
            "total_study": self.total_study_time,
            "total_entertainment": self.total_entertainment_time,
            # Optionally add more detailed logs later
        }
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
        except IOError as e:
            print(f"Error saving data: {e}")

    def _update_totals(self):
        """Updates total time for the completed activity segment."""
        if self.session_start_time and self.current_activity:
            end_time = self.paused_time if self.is_paused else time.time()
            elapsed = end_time - self.session_start_time
            self.elapsed_time += elapsed
            if self.current_activity == STUDY:
                self.total_study_time += elapsed
            elif self.current_activity == ENTERTAINMENT:
                self.total_entertainment_time += elapsed
            self.session_start_time = None # Reset segment start time

    def start_activity(self, activity_type):
        """Starts or switches to a new activity."""
        if self.current_activity == activity_type: # Already doing this
            return

        self._update_totals() # Add time from previous activity

        self.current_activity = activity_type
        self.session_start_time = time.time()
        self.elapsed_time = 0
        self.is_paused = False
        self.paused_time = None
        print(f"Started: {self.current_activity}")

    def switch_activity(self):
        was_paused = self.is_paused
        if not self.current_activity:
            self.start_activity(STUDY)
        elif self.current_activity == STUDY:
            self.start_activity(ENTERTAINMENT)
        else:
            self.start_activity(STUDY)
        if was_paused:
            self.pause()

    def pause(self):
        """Pauses the current timer."""
        if self.current_activity and not self.is_paused:
            self.is_paused = True
            self.paused_time = time.time()
            self._update_totals() # Add time up to the pause point
            print("Paused")

    def resume(self):
        """Resumes the current timer."""
        if self.current_activity and self.is_paused:
            self.is_paused = False
            # paused_duration = time.time() - self.paused_time
            self.session_start_time = time.time()
            self.paused_time = None
            print("Resumed")

    def get_current_duration(self):
        """Gets the duration of the current active (or paused) segment."""
        if not self.current_activity:
            return 0
        if self.is_paused:
            return self.elapsed_time
        elif self.session_start_time:
            return time.time() - self.session_start_time + self.elapsed_time
        else:
            # Should not happen if running
            return 0
        
    def get_status(self):
        """Gets the current status string."""
        if self.is_paused:
            return f"{self.current_activity} ({PAUSED})"
        elif self.current_activity:
            return self.current_activity
        else:
            return "Idle"

    def get_totals(self):
        """Gets the total study and entertainment time including current session."""
        current_study = self.total_study_time
        current_ent = self.total_entertainment_time

        if self.current_activity and not self.is_paused and self.session_start_time:
            elapsed_current = time.time() - self.session_start_time
            if self.current_activity == STUDY:
                current_study += elapsed_current
            elif self.current_activity == ENTERTAINMENT:
                current_ent += elapsed_current

        return current_study, current_ent