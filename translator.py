import requests
import json
import threading
from tokenBucket import TokenBucket
from PyQt5.QtCore import QObject,pyqtSignal

class XAI_API(QObject):
    translation_finished = pyqtSignal(str)
    get_text_signal = pyqtSignal(str)
    def __init__(self) -> None:
        super(XAI_API,self).__init__()
        self.url = 'https://api.x.ai/v1/chat/completions'
        self.authorization = 'your api key'

        self.current_task = None  
        self.task_lock = threading.Lock()
        self.running = True

        self.get_text_signal.connect(self.add_data)

        self.log = []
        # 初始化令牌桶（1 秒產生 1 個令牌，最大容量為 1 個令牌）
        self.token_bucket = TokenBucket(rate=1, capacity=1)

        self.worker_thread = threading.Thread(target=self.process_task, daemon=True)
        self.worker_thread.start()
    def getPayload(self,content):
        payload = {
            "messages": [
                {
                "role": "user",
                "content": f"翻譯成中文:{content}"
                }
            ],
            "model": "grok-beta",
            "stream": False,
            "temperature": 0
        }
        return payload 
    def translate(self,content):
        payload = self.getPayload(content)
        r = requests.post(self.url,json=payload,headers={
            'Content-Type':'application/json',
            'Authorization':self.authorization
        })
        if r.status_code == 200:
            parsed_data = json.loads(r.text)
            content = parsed_data["choices"][0]["message"]["content"]

            self.translation_finished.emit(content)
        else:
            print(f"Error: Received status code {r.status_code}")

    def process_task(self):
        while self.running:
            with self.task_lock:
                if self.current_task is None:
                    continue
                task_to_process = self.current_task
                self.current_task = None
            self.token_bucket.acquire()
            self.translate(task_to_process)
    def add_data(self, content):
        with self.task_lock:
            self.current_task = content  
            self.log.append(content)
            print(f"New task added: {content}")

    def stop(self):
        self.running = False
        with self.condition:
            self.condition.notify_all() 
        self.worker_thread.join()
