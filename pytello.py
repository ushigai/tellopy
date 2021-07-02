import numpy as np
import threading
import traceback
import socket
import sys
import time
import os
import cv2


class PYtello:
    def setup_tello(self, host="", port=8889, COMMAND_DELAY=True):
        """
        Telloのセットアップを行う。
        """
        # Create a UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.locaddr = ("", 9000)
        self.tello_address = ('192.168.10.1', 8889)
        udp_video_address = "udp://@192.168.10.1:11111"
        self.sock.bind(self.locaddr)
        self.rect = []
        self.command_delay = COMMAND_DELAY
        self.RECEIVE_DATA = None  # Telloの応答
        self.VIDEO_FRAME = None  # Telloのカメラのフレームデータ
        self.DATA_FLAG = True  # タイムアウト検出用のフラグ
        self._receive_going = True # reveilce threadをぶんまわすかどうか
        self._video_going = True # video threadをぶんまわすかどうか
        self.cap = None 
        self.cascade_path = "C:/(Pythonのインストール先)/Lib/site-packages/cv2/data/haarcascade_frontalface_default.xml"
        self.frame_folder_name = "camera_frame"
        self.frame_save_path = f"./{self.frame_folder_name}/"  # フレームデータの保存先
        self.frame_filename = "0"  # フレームデータのファイル名
        try:
            os.makedirs(self.frame_folder_name)  # フレームデータ保存用のフォルダ作成
        except FileExistsError:
            pass
        try:
            os.makedirs("_" + self.frame_folder_name)
        except FileExistsError:
            pass

        # SDKモードに移行
        # `command`は`ok`or`Error`が返ってくるかをまたず、
        # 無条件で1秒待機させている(というか大体それでうまくいく)
        self.go_tello('command')

        # receive thread起動
        self.RECV_THREAD = threading.Thread(target=self.__receive_thread__)
        self.RECV_THREAD.daemon = True
        self.RECV_THREAD.start()

        # videoストリームを有効に
        self.video_on()
        if self.cap is None:
            self.cap = cv2.VideoCapture(udp_video_address)
        if not self.cap.isOpened():
            self.cap.open(udp_video_address)
        
        self.camera_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.camera_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print("[*]width =", self.camera_width, "\n[*]height =", self.camera_height)

        # video threadを立ち上げる
        self.VIDEO_THREAD = threading.Thread(target=self.__video_thread__)
        self.VIDEO_THREAD.deamon = True
        self.VIDEO_THREAD.start()

        # Telloのカメラがなんか安定するまで撮り続ける
        # めちゃくちゃ困ってるわけじゃないけど回避する方法があるかも?
        self.take_picture("temp")
        while os.path.getsize("./camera_frame/temp.jpg") == 0:
            self.take_picture("temp")
            time.sleep(0.3)


    def __video_thread__(self):
        """
        ビデオスレッド
        カメラのフレームデータをself.VIDEO_FRAMEに格納する
        """
        self.VIDEO_FRAME = None
        self.rect = []
        while self._video_going:
            ret, self.VIDEO_FRAME = self.cap.read()
            if len(self.rect) == 1: # 顔が検出された場合、四角で囲む
                x, y, w, h = self.rect[0]
                cv2.rectangle(self.VIDEO_FRAME, tuple([x, y]), tuple([x + w, y + h]), (0, 0, 255), thickness=3)
            cv2.imshow("frame_data", self.VIDEO_FRAME)
            _ = cv2.waitKey(1)
        #cv2.destroyAllWindows()


    def __receive_thread__(self):
        """
        Telloからの応答監視スレッド
        最後の応答がreceive_dataに格納される
        """
        while self._receive_going:
            try:
                self.RECEIVE_DATA, ip = self.sock.recvfrom(3000)
            except:
                print(traceback.format_exc())


    def go_tello(self, S, interval=1.0):
        """
        S : コマンド(大文字小文字どちらでもいい)
        interval : 入力コマンド間の遅延

        command
        takeoff
        land
        up[down, left, right, forward, back] "Value" : "Value" = 20-500
        cw[ccw] "Value" : "Value" = 1-360
        flip "Direction" : "Direction" = l(left), r(right), f(forward), b(back)
        """

        # command, emergency は処理上ない
        _CONTROL_COMMANDS_ = ["takeoff", "land", "streamon", "streamoff", "up", "down", "left",
                              "right", "forward", "back", "cw", "ccw", "flip", "go", "stop",
                              "curve", "jump"]

        _SET_COMMANDS_ = ["speed", "rc", "wifi",
                          "mon", "moff", "mdirection", "ap"]

        _READ_COMMANDS_ = ["speed?", "battery?", "time?", "wifi?", "height?", "temp?", "attitude?"
                           "baro?", "acceleration?", "tof?"]

        _ALL_COMMANDS_ = _CONTROL_COMMANDS_ + _SET_COMMANDS_ + _READ_COMMANDS_

        if isinstance(S, str):
            S = S.lower()
            self.DATA_FLAG = False
            sent = self.sock.sendto(S.encode("utf-8"),
                                    self.tello_address)  # コマンド送信
            print(S, ">> Tello")

            # タイマースレッドで処理待ち状態に
            # time.sleepとかだとうまくいかない
            timer = threading.Timer(interval, self.set_flag_TRUE)
            timer.start()  # タイマースレッドスタート

            S = S.split()
            S = S[0]

            while self.RECEIVE_DATA is None:
                if S in _ALL_COMMANDS_:
                    continue
                if self.DATA_FLAG:
                    break
            timer.cancel()  # タイマースレッドストップ

            if self.RECEIVE_DATA is None:
                response = "NULL"
            else:
                response = self.RECEIVE_DATA.decode("utf-8")
            self.RECEIVE_DATA = None
            print(response + " << Tello")
        else:
            raise TypeError
        self.DATA_FLAG = False
        timer = threading.Timer(interval, self.set_flag_TRUE)
        timer.start()  # タイマースレッドスタート
        while True:
            if self.DATA_FLAG:
                break


    def set_flag_TRUE(self):
        """
        タイムアウト検出フラグをTrueにセットする
        """
        self.DATA_FLAG = True


    def close_tello(self):
        print("Exit...")
        self.video_off()
        #self.go_tello("END")
        self._receive_going = False
        self._video_going = False
        """
        self.RECV_THREAD.join()
        self.VIDEO_THREAD.join()
        """
        self.cap.release()
        cv2.destroyAllWindows()
        self.sock.close()


    def query(self, Query=["battery", "speed", "time", "height", "wifi", "sdk", "sn"]):
        """
        Telloに現在の設定項目を問い合わせる。
        Queryになんかぶち込んでみて
        """
        if not isinstance(Query, list):
            raise TypeError
        Query_words = {
            "battery": "バッテリー残量",
            "speed": "設定速度",
            "time": "現在の飛行時間",
            "height": "現在の高さ",
            "temp": "ドローンの温度",
            "attitude": "ドローンの姿勢",
            "tof": "get distance value from TOF",
            "wifi": "接続Wi-FiのS/N比",
            "sdk": "SDKのバージョン",
            "sn": "シリアルナンバー"
        }
        for query_word, S in Query_words.items():
            if query_word not in Query:
                continue
            ans = self.go_tello(query_word + "?", interval=0.3)
            print(S, ":", ans)


    def set_speed(self, N=100):
        """
        Telloの速度を変更する。
        入力値Nに対しN[cm/s]に設定する。
        設定可能範囲：10 <= N <= 100
        初期値：100
        """
        try:
            N = int(N)
        except ValueError:
            raise ValueError
        self.go_tello("speed " + str(N), interval=0.3)


    def video_on(self):
        """
        Telloのビデオストリームをオンにする
        """
        self.go_tello("streamon")


    def video_off(self):
        """
        Telloのビデオストリームをオフにする
        """
        self.go_tello("streamoff")


    def take_picture(self, filename=None):
        """
        Telloのカメラの最新フレームを保存する
        保存先はself.frame_save_path
        保存名はself.frame_filename
        """
        if filename is None:  # ユーザがファイル名を指定しなかった場合ファイル名をナンバリング
            filename = self.frame_filename
            self.frame_filename = str(int(self.frame_filename))
            self.frame_filename = str(eval(self.frame_filename + " + 1"))
            self.frame_filename = self.frame_filename.zfill(6)  # 整形のためゼロ埋め
            filename = self.frame_filename
        cv2.imwrite(self.frame_save_path + filename + ".jpg", self.VIDEO_FRAME)
        print(f"Saved the photo as filename:{filename} << Tello")
        

    def face_detection(self):
        """
        現在のフレームデータ(self.VIDEO_FRAME)にて人の顔があるかどうか識別
        肝心な顔認識の部分はHaar Cascadeで殴ってる
        返し値は認識した顔の[(左上のx座標), (左上のy座標), (横幅), (縦線)]が、
        認識した顔の数だけlistで返される
        """
        self.rect = []
        cv2.imwrite("./_camera_frame/temp.jpg", self.VIDEO_FRAME)  # いったん空打
        src = cv2.imread("./_camera_frame/temp.jpg", 0)
        gray = cv2.cvtColor(src, cv2.cv2.COLOR_BAYER_BG2GRAY)
        cascade = cv2.CascadeClassifier(self.cascade_path)
        self.rect = cascade.detectMultiScale(gray, minSize=(100, 100))
        return self.rect
        

    def find_specific_color(self, frame, AREA_RATIO_THRESHOLD, LOW_COLOR, HIGH_COLOR): # https://gist.github.com/TonyMooori/4cc29c94f7bdbade6ff6102fef45232e
        """
        指定した範囲の色の物体の座標を取得する関数
        frame: 画像
        AREA_RATIO_THRESHOLD: area_ratio未満の塊は無視する
        LOW_COLOR: 抽出する色の下限(h,s,v)
        HIGH_COLOR: 抽出する色の上限(h,s,v)
        """
        h, w, c = frame.shape
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        ex_img = cv2.inRange(hsv, LOW_COLOR, HIGH_COLOR)

        # 面積を計算
        _, contours, hierarchy = cv2.findContours(
            ex_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        areas = np.array(list(map(cv2.contourArea, contours)))

        if len(areas) == 0 or np.max(areas) / (h * w) * 10000 < AREA_RATIO_THRESHOLD:
            # 見つからなかったらNoneを返す
            return None, None, None
        else:
            # 面積が最大の塊の重心を計算し返す
            max_idx = np.argmax(areas)
            max_area = areas[max_idx]
            result = cv2.moments(contours[max_idx])
            x = int(result["m10"]/result["m00"])
            y = int(result["m01"]/result["m00"])
            return [x, y, np.max(areas) / (h * w) * 10000]


    def color_detection(self, lower, upper):
        """
        閾値に対して色検出を行いその座標を返す。
        lower, upperにそれぞれ[h, s, v]を指定してぶち込む。
        """
        cv2.imwrite("./_camera_frame/temp.jpg", self.VIDEO_FRAME)
        img = cv2.imread("./_camera_frame/temp.jpg")

        # HSVに変換
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # numpyのarrayじゃなきゃだめじゃね？
        lower = np.array(lower) 
        upper = np.array(upper)

        # 指定色範囲以外をマスク
        img_mask = cv2.inRange(hsv, lower, upper)
        res = cv2.bitwise_and(img, img, mask=img_mask)
        cv2.imwrite("./_camera_frame/teemp.jpg", res)  # マスクした結果を保存

        # 認識対象の色のx座標, y座標, 面積を返す
        return self.find_specific_color(img, 0, lower, upper)

