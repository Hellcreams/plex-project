#!/usr/bin/env python3

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib import request
from urllib.error import URLError
import xml.etree.ElementTree as ET
import threading
import time
from datetime import datetime
import os
import logging
import json


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

# 설정값
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

COLLECT_INTERVAL = config["collect_interval"]
PORT = config["port"]
HOST = config["host"]
    

# 데이터 수집 스레드
class Collector(threading.Thread):
    DECISIONS = (
        "directplay",
        "directstream",
        "transcode",
        "copy",
        "burn",
        "unknown",
    )

    # 고정 값
    cache = {}


    def __init__(self, name, interval=5):
        super().__init__()
        self.name = name
        self.interval = interval
        Collector.reset_cache()
    
    
    @staticmethod
    def empty_decision_map():
        return {k: 0 for k in Collector.DECISIONS}


    @staticmethod
    def reset_cache():
        Collector.cache = {
                "timestamp":"",     # UTC 기준 수집 시각
                "now_playing":"",   # 이용자 수
                "video_decision":Collector.empty_decision_map(),  # 비디오 재생현황
                "audio_decision":Collector.empty_decision_map(),  # 오디오 재생현황
                "subtitle_decision":Collector.empty_decision_map(),   # 자막 재생현황
                "now_working":0,
                }


    def run(self):
        while True:
            try:
                source = request.urlopen("http://127.0.0.1:32400/status/sessions", timeout=3)
        
            except URLError:
                logging.warning("GET : URL Not found (Maybe Server is offline?)")
        
            else:
                if source.status==200:
                    tree = ET.XML(source.read())

                    # 캐시 초기화
                    Collector.reset_cache()

                    # 사용자 수
                    Collector.cache["now_playing"] = tree.attrib["size"]

                    # 재생 현황
                    for pl in tree:
                        trans_sessions = pl.findall("TranscodeSession")
                        
                        for ts in trans_sessions:
                            # Decision
                            if (i := ts.get("videoDecision")) is not None:
                                Collector.cache["video_decision"][i] += 1

                            if (i := ts.get("audioDecision")) is not None:
                                Collector.cache["audio_decision"][i] += 1

                            if (i := ts.get("subtitleDecision")) is not None:
                                Collector.cache["subtitle_decision"][i] += 1

                            # throttled
                            if (i := ts.get("throttled")) is not None:
                                if not int(i):
                                    Collector.cache["now_working"] += 1


                    # 기록 시간
                    Collector.cache["timestamp"] = time.time()
                    logging.debug(f"GET : {source.status} / {Collector.cache['timestamp']}")
                else:
                    logging.debug(f"GET : {source.status}")


            time.sleep(COLLECT_INTERVAL)


# __main__
if __name__=="__main__":
    # 정보 수집 스레드
    c_th = Collector("hi")                # sub thread 생성
    c_th.start()

    # 정보 전송
    class MyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                self.send_response(302)
                self.send_header("Location", "/metrics")
                self.end_headers()
                return 0

            if self.path == "/metrics":
                self.send_response(200)
                self.send_header("Content-type", "text/plain; chartset=utf-8")
                self.end_headers()
                
                # for 문
                content = ""
                for c_key, c_value in zip(Collector.cache, Collector.cache.values()):
                    # dictionary
                    if isinstance(c_value, dict):
                        for d_key, d_value in zip(c_value, c_value.values()):
                            content += f"plex_{c_key}_{d_key} {d_value}\n"

                    # int, float, str...
                    else:
                        content += f"plex_{c_key} {c_value}\n"


                self.wfile.write(bytes(content, "utf-8"))

                return 0
 

    try:
        server = HTTPServer((HOST, PORT), MyHandler)
    except OSError as e:
        if e.errno == 98:
            logging.error(f"Port {port} is already in use!")
            os._exit(1)
        else:
            raise

    # 실행
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt detected. Terminating process..")
        os._exit(0)
