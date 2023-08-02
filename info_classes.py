from collections import defaultdict

class InfoContainer:
    def __init__(self):
        self.dict = defaultdict(ProcInfo)

    def delete_item(self, id):        
        self.dict.pop(id, None)

    def set_log(self, id, msg):
        self.dict[id].curr_log = msg

    def set_duration(self, id, msg):
        self.dict[id].duration = msg

    def get_log(self, id):
        return self.dict[id].curr_log

    def get_duration(self, id):
        return self.dict[id].duration

class ProcInfo:
    def __init__(self):
        self.duration = ""
        self.curr_log = ""        
