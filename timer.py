from datetime import datetime, timezone, timedelta
        
class Timer:
    def __init__(self):  # Use double underscores to correctly define the constructor
        self.start_time = None
        self.end_time = None
    
    def start_timer(self):
        self.start_time = datetime.now(timezone.utc)
        
    def stop_timer(self):
        self.end_time = datetime.now(timezone.utc)
        
    def timeout(self):
        if self.start_time is None:  # Check if the timer has been started
            return False  # Return False or handle the situation appropriately
        time_now = datetime.now(timezone.utc)
        elapsed_time = time_now - self.start_time
        if elapsed_time >= timedelta(seconds=5):
            return True
        else: 
            return False
