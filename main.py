#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, ColorSensor
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait, StopWatch, DataLog
from pybricks.robotics import DriveBase
from pybricks.iodevices import UARTDevice

# 設定コーナー ====================================================
ev3 = EV3Brick()
timer = StopWatch()

# センサーとモーターをEV3と接続していくぅ↑---------------------------
# 失敗した時はその内容を吐露しながら停止するよ

# カラーセンサを接続
try:
    colorLeft = ColorSensor(Port.S4)
    colorRight = ColorSensor(Port.S3)
except OSError as oserror:
    while True:
        ev3.speaker.say("color")
        wait(1000)

# Lモーターを接続
try:
    motorLeft = Motor(Port.D)
    motorRight = Motor(Port.A)
except OSError as oserror:
    while True:
        ev3.speaker.say("motor")
        wait(1000)

# Mモーターを接続
try:
    arm_bucket = Motor(Port.B)
    arm_rotate = Motor(Port.C)
except OSError as oserror:
    while True:
        ev3.speaker.say("m motor")
        wait(1000)

# Raspberry Pi Picoを接続
# try:
#     pico = UARTDevice(Port.S2, 19200,100)
# except OSError as oserror:
#     while True:
#         ev3.speaker.say("pico")
#         wait(1000)
# else:
#     pico.clear()

# ESP32を接続
try:
    esp = UARTDevice(Port.S1, 115200,100)
except OSError as oserror:
    while True:
        ev3.speaker.say("ESP32")
        wait(1000)
else:
    esp.clear() # 受信バッファをクリア
# ----------------------------------------------------------------
highest_refrection_of_Black = const(15)
basic_speed = 30
# 設定コーナー終わり ===============================================

class Tank:
    """
    ・モーター関連のクラス
    ・Mindstormsのタンクとステアリングの機能+アルファ
    ・このクラスは実行速度を一切考慮していないので注意
    ・回転方向の指定はパワーですることを想定している
    """
    def drive(self, left_speed, right_speed):
        """
        機体を進める
        ストップするまで止まらんで
        """
        motorLeft.run(powertodegs(left_speed))
        motorRight.run(powertodegs(right_speed))

    def drive_for_seconds(self, left_speed, right_speed, time, stop_type = "brake", wait=True):
        """
        指定されたスピード(%)と時間(ms)で進む
        こいつにだけwait機能がある 他は非同期処理を習得したら考える
        """
        motorLeft.run_time(powertodegs(left_speed), time, stop_type, False)
        motorRight.run_time(powertodegs(right_speed), time, stop_type, False)
        if wait:
            wait(time)
        
        self.stop(stop_type)

    def drive_for_degrees(self, left_speed, right_speed, degrees, stop_type = "brake"):
        left_angle = motorLeft.angle()
        right_angle = motorRight.angle()
        motorLeft.run(powertodegs(left_speed))
        motorRight.run(powertodegs(right_speed))
        while abs(left_angle - motorLeft.angle()) <= degrees and abs(right_angle - motorRight.angle()) <= degrees:
            pass
        self.stop(stop_type)

    def drive_for_rotations(self, left_speed, right_speed, rotations, stop_type = "brake"):
        self.drive_for_degrees(left_speed,right_speed,rotations* 360,stop_type)

    def steering(self,speed,steering):
        """
        ステアリング機能
        デバッグしてないYO
        """
        if -100 > speed or 100 > speed:
            raise ValueError
        if -100 <= steering < 0:
            motorLeft.run(powertodegs((speed / 50) * steering + speed))
            motorRight.run(powertodegs(speed))
        elif 0 <= steering <= 100:
            motorLeft.run(powertodegs(speed))
            motorRight.run(powertodegs(-1 * (speed / 50) * steering + speed))
        else:
            raise ValueError

    def steering_for_seconds(self,speed,steering,seconds,stop_type = "brake"):
        if seconds <= 0:
            raise ValueError
        time_run = timer.time() + seconds
        while timer.time() <= time_run:
            self.steering(speed,steering)
        self.stop(stop_type)

    def steeing_for_degrees(self,power,steering,degrees,stop_type = "brake"):
        if degrees < 0:
            degrees *= -1
            steering *= -1
        left_angle = motorLeft.angle()
        right_angle = motorRight.angle()
        self.steering(power,steering)
        while not abs(left_angle - motorLeft.angle()) > degrees or abs(right_angle - motorRight.angle()) > degrees:
            pass
        self.stop(stop_type)

    def steering_for_rotations(self,power,steering,rotations,stop_type = "brake"):
        self.steeing_for_degrees(power,steering,rotations * 360,stop_type)

    def stop_option(self,stop_type):
        """
        単一モーターを標準関数でストップするときのオプションを返す
        他の関数と同じ感覚でストップできるように
        """
        if stop_type == "stop":
            return Stop.COAST
        elif stop_type == "brake":
            return Stop.BRAKE
        else:
            return Stop.HOLD

    def stop(self, stop_type):
        """
        
        """
        if stop_type == "stop":
            motorLeft.stop()
            motorRight.stop()
        elif stop_type == "brake":
            motorLeft.brake()
            motorRight.brake()
        else:
            motorLeft.hold()
            motorRight.hold()

tank = Tank()

class Arm:
    """アーム関係の動作"""
    def open_arm(self):
        """アームを展開"""
        arm_rotate.run_angle(powertodegs(40),250,Stop.COAST,True) 
    def close_arm(self):
        """アームをしまう"""
        arm_rotate.run_angle(powertodegs(-40),250,Stop.BRAKE,True)

    def open_bucket(self):
        """回るやつを開放状態にする"""
        arm_bucket.run_angle(powertodegs(-40),150,Stop.BRAKE,True)

    def close_bucket(self):
        """回るやつを閉じる"""
        arm_bucket.run_angle(powertodegs(40),150,Stop.BRAKE,True)

    def rescuekit(self):
        """レスキューキット検知後の動作"""
        tank.drive_for_degrees(-1*basic_speed,-1*basic_speed,350) # 一歩下がる
        arm_rotate.run_angle(powertodegs(40),250,Stop.COAST,True) # アームを下ろす
        tank.drive_for_degrees(basic_speed,basic_speed,350) # 前に進む
        arm_bucket.run_angle(powertodegs(40),50,Stop.COAST,True) # バケットを少し回す(初速を付けるため)
        arm_bucket.run(powertodegs(40)) # バケットを回す
        while abs(arm_bucket.speed()) >= 5: # パワーが5以下(つまりこれ以上回せなくなる)になるまで回し続ける
            pass
        arm_bucket.brake() # がっちり固定
        arm_rotate.run_angle(powertodegs(-40),250,Stop.BRAKE,True) # アームを上げる
        arm_bucket.run_angle(powertodegs(-40),30,Stop.COAST,True) # レスキューキット開放
        arm_bucket.run_angle(powertodegs(40),200,Stop.BRAKE,True) # 元の位置に戻す

arm = Arm()

# ライントーレスのグッズ ==================================================
# ただの計算だからネイティブコードエミッタで高速化してる
@micropython.native
def powertodegs(power):
    """スピード(%)をdeg/sに変換する"""
    return 950 * power /100

@micropython.native
def changeRGBtoHSV(rgb):
    """
    RGBをHSVに変換して返す(タプル型)
    色相(H)は 0~360
    彩度(S)は 0~100
    明度(V)は 0~255 の範囲
    """
    # RGBのしきい値を0~100から0~255に修正 Blueの値が異様に大きい問題があるので÷2して実際に見える色に寄せている
    rgb0_255 = rgb[0] * 255 / 100, rgb[1] * 255 / 100, rgb[2] * 255 / 200
    maxRGB, minRGB = max(rgb0_255), min(rgb0_255)
    diff = maxRGB - minRGB

    # Hue
    if maxRGB == minRGB : hue = 0
    elif maxRGB == rgb0_255[0] : hue = 60 * ((rgb0_255[1]-rgb0_255[2])/diff)
    elif maxRGB == rgb0_255[1] : hue = 60 * ((rgb0_255[2]-rgb0_255[0])/diff) + 120
    elif maxRGB == rgb0_255[2] : hue = 60 * ((rgb0_255[0]-rgb0_255[1])/diff) + 240
    if hue < 0 : hue += 360

    # Saturation
    if maxRGB != 0:
        saturation = diff / maxRGB * 100
    else:
        saturation = 0

    # Value(Brightness)
    value = maxRGB

    return hue,saturation,value

# ============================================================
def onGreenMarker(direction):
    if direction == "l": # 左のカラーセンサーが緑を見つけた
        # 50°進みつつ右にも緑がないか確認 結果はisRightGreenに格納
        start_angle_deg = motorRight.angle()
        isRightGreen = False
        motorLeft.run(powertodegs(basic_speed))
        motorRight.run(powertodegs(basic_speed))
        while abs(motorRight.angle() - start_angle_deg) <= 50:
            if isGreen('r'):
                isRightGreen = True
        motorLeft.brake()
        motorRight.brake()

        if isRightGreen: # 反対にもマーカーがあったらUターン
            u_turn()
        else:
            # ほんまもんの左折
            print('turn left')
            tank.drive_for_degrees(30,30,180) # 180°前に進んで機体を交差点の中心に持ってく
            tank.drive_for_degrees(-30,30,160,"stop") # 180°回転して左のカラーセンサー下にラインがないようにする
            tank.drive(-30,30)
            while colorLeft.rgb()[1] > highest_refrection_of_Black: # 緑ないし黒を左のセンサが見つけるまで回る
                pass
            tank.drive_for_degrees(-30,30,110) # 機体をラインに沿わせる
            motorLeft.brake()
            motorRight.brake()
            tank.drive_for_degrees(30,30,50) # 緑マーカーかぶりを回避したい
    else: # # 左のカラーセンサーが緑を見つけた(消去法的にね) -------------------------------------------------------------------
        # 50°進みつつ左にも緑がないか確認 結果はisRightGreenに格納
        start_angle_deg = motorLeft.angle()
        isLeftGreen = False

        motorLeft.run(powertodegs(30))
        motorRight.run(powertodegs(30))

        while abs(motorLeft.angle() - start_angle_deg) <= 50:
            if isGreen('r'):
                isLeftGreen = True
        motorLeft.brake()
        motorRight.brake()

        if isLeftGreen: # 反対にもマーカーがあったらUターン
            u_turn()
        else:
            print('turn right')
            tank.drive_for_degrees(30,30,180) # 180°前に進んで機体を交差点の中心に持ってく
            tank.drive_for_degrees(30,-30,180,"stop") # 180°回転して左のカラーセンサー下にラインがないようにする
            tank.drive(30,-30)
            while colorRight.rgb()[1] > highest_refrection_of_Black: # 緑ないし黒を右のセンサが見つけるまで回る
                pass
            tank.drive_for_degrees(30,-30,110) # 機体をラインに沿わせる
            motorLeft.brake() # 回転方向の運動を止める
            motorRight.brake()
            tank.drive_for_degrees(30,30,50) # 緑マーカーかぶりを回避したい

def isGreen(direction):
    """
    onGreenMarkerの付属品
    directionで渡された方向のカラーセンサが緑を見ているか判定
    """
    # RGBを取得して
    if direction == "l":
        rgb = colorLeft.rgb()
    else:
        rgb = colorRight.rgb()
    # HSVに変換して
    hsv = changeRGBtoHSV(rgb)
    # 緑かどうかの真偽値を返す
    return (120 < hsv[0] < 160 and hsv[1] > 60 and hsv[2] > 20)

def u_turn():
    tank.drive_for_degrees(30,30,160) # go down 160 deg
    # tank.drive_for_degrees(30,-30,240) # spin turn "right" 240 deg reqired to be optimized
    # tank.drive(30,-30)
    # while colorRight.rgb()[1] > highest_refrection_of_Black: # spin turn "right" until left color sensor finds black or green
    #     pass
    # tank.drive_for_degrees(30,-30,200) # spin turn "right" 110 deg to be over line
    # tank.drive(30,-30)
    # while colorRight.rgb()[1] > highest_refrection_of_Black: # spin turn "right" until left color sensor finds black or green
    #     pass
    # tank.drive_for_degrees(30,-30,110) # spin turn "right" 110 deg to be over line
    # motorLeft.brake()
    # motorRight.brake()

    # 柱にぶつからん為にタイルの中心で回転しようとしたら回転軸がぶれて、センサがいい感じにラインの上に乗ってくんない
    # もう考えたくないからジャイロで180°ぶん回すんじゃー

# ============================================================

def black(direction):
    """左右のラインセンサが黒を感知したときの"""
    if direction == "l":
        # 左折
        # 50°進みつつ右にも黒がないか確認する
        isRightBlack = False
        left_angle = motorLeft.angle()
        right_angle = motorRight.angle()
        motorLeft.run(powertodegs(basic_speed))
        motorRight.run(powertodegs(basic_speed))
        while abs(left_angle - motorLeft.angle()) <= 50 and abs(right_angle - motorRight.angle()) <= 50:
            line_statue = UARTwithESP32_LineMode(10)[0]
            if line_statue == 2 or line_statue == 3:
                isRightBlack = True
        
        if isRightBlack:
            # 無印の十字路 無視して突き進むんや
            tank.drive_for_degrees(30,30,180,"stop")
        else:
            # 本当の左折
            tank.drive_for_degrees(30,30,180) # 180°前に進んで機体を交差点の中心に持ってく
            tank.drive_for_degrees(-30,30,160,"stop") # 180°回転して左のカラーセンサー下にラインがないようにする
            tank.drive(-30,30)
            while colorLeft.rgb()[1] > highest_refrection_of_Black: # 緑ないし黒を左のセンサが見つけるまで回る
                pass
            tank.drive_for_degrees(-30,30,110) # 機体をラインに沿わせる
            motorLeft.brake()
            motorRight.brake()
            tank.drive_for_degrees(30,30,50,"stop") # ラインかぶりを回避したい
    elif direction == "r":
        # 右折
        # 50°進みつつ左にも黒がないか確認する
        isLeftBlack = False
        left_angle = motorLeft.angle()
        right_angle = motorRight.angle()
        motorLeft.run(powertodegs(basic_speed))
        motorRight.run(powertodegs(basic_speed))
        while abs(left_angle - motorLeft.angle()) <= 50 and abs(right_angle - motorRight.angle()) <= 50:
            line_statue = UARTwithESP32_LineMode(10)[0]
            if line_statue == 1 or line_statue == 3:
                isLeftBlack = True
        
        if isLeftBlack:
            # 無印の十字路 無視して突き進むんや
            tank.drive_for_degrees(30,30,180,"stop")
        else:
            # 本当の右折
            tank.drive_for_degrees(30,30,180) # 180°前に進んで機体を交差点の中心に持ってく
            tank.drive_for_degrees(30,-30,180,"stop") # 180°回転して左のカラーセンサー下にラインがないようにする
            tank.drive(30,-30)
            while colorRight.rgb()[1] > highest_refrection_of_Black: # 緑ないし黒を右のセンサが見つけるまで回る
                pass
            tank.drive_for_degrees(30,-30,110) # 機体をラインに沿わせる
            motorLeft.brake() # 回転方向の運動を止める
            motorRight.brake()
            tank.drive_for_degrees(30,30,50) # ラインかぶりを回避したい
    else: #多分"both"とかが来る
        # 無印の十字路 無視して突き進むんや
        tank.drive_for_degrees(30,30,180,"stop")

# ============================================================

def lost_line():
    """
    中央のラインセンサが黒を見失ったとき
    -ラインからずれた
    """
    pass

# ============================================================

def UARTwithESP32_LineMode(mode):
    """"
    ライントレースしてるときのUART
    通常時のと障害物回避ので2つつかえる
    """
    esp.write((mode).to_bytes(1,'big'))
    error_count = 0
    while esp.waiting() < 4:
        if error_count > 10: # 10回以上失敗してたら一時停止
            motorLeft.brake()
            motorRight.brake()
            ev3.speaker.say("ESP UART")
        wait(10)
        print("error")
        esp.write((10).to_bytes(1,'big'))
        error_count += 1
    whatread = esp.read(4)
    return whatread

# ============================================================
def main():
    """メインループ"""
    while 1:
        # init values
        Kp = 2.2
        Ki = 0.1
        Kd = 0.8
        last_error = 0
        error = 0
        basic_speed = 30
        start_time = timer.time()
        print("start")
        # Get ready!!
        ev3.speaker.beep()
        hill_statue = 0

        # wait until any button is pressed
        while not any(ev3.buttons.pressed()):
            pass
        while any(ev3.buttons.pressed()):
            pass
        
        # ここでESPとPicoにスタート信号を送る

        while not any(ev3.buttons.pressed()):
            rgb_left = colorLeft.rgb()
            rgb_right = colorRight.rgb()
            error = rgb_left[1] - rgb_right[1]
            u = Kp * error + Ki * (error + last_error) + Kd * (error - last_error)
            motorLeft.run(powertodegs(basic_speed + u))
            motorRight.run(powertodegs(basic_speed - u))
            hsv_left = changeRGBtoHSV(rgb_left)
            if 120 < hsv_left[0] < 160 and hsv_left[1] > 60 and hsv_left[2] > 20:
                print("Left sensor is over green")
                onGreenMarker("l")
            #print("left hsv:  "+str(hsv_left[0])+", "+str(hsv_left[1])+", "+str(hsv_left[2]))
            # print("left rgb:  "+str(rgb_left[0])+", "+str(rgb_left[1])+", "+str(rgb_left[2]))
            # wait(100)

            hsv_right = changeRGBtoHSV(rgb_right)
            if 120 < hsv_right[0] < 160 and hsv_right[1] > 60 and hsv_right[2] > 20:
                print("Right sensor is over green")
                onGreenMarker("r")
            #print("right hsv: "+str(hsv_right[0])+", "+str(hsv_right[1])+", "+str(hsv_right[2]))
            # print("right rgb: "+str(rgb_right[0])+", "+str(rgb_right[1])+", "+str(rgb_right[2]))
            # wait(100)
            
            # UART with ESP32
            esp.write((10).to_bytes(1,'big'))
            error_count = 0
            while esp.waiting() < 4:
                if error_count > 10: # 10回以上失敗してたら一時停止
                    motorLeft.brake()
                    motorRight.brake()
                    ev3.speaker.say("ESP UART")
                wait(10)
                print("error")
                esp.write((10).to_bytes(1,'big'))
                error_count += 1
            whatread = esp.read(4)
            #print(str(whatread[0])+", "+str(whatread[1])+", "+str(whatread[2])+", "+str(whatread[3]))

            # # 直角系
            # if whatread[0] != 0:
            #     if whatread[0] == 1:
            #         # 左折コーナー
            #         black("l")
            #     elif whatread[0] == 2:
            #         # 右折コーナー
            #         black("r")
            #     elif whatread[0] == 3:
            #         black("both")

            if whatread[2] == 2:
                arm.rescuekit()
                continue # ループの最初に戻る(通信の内容を更新)

            # 坂関係
            if hill_statue == 0:
                if whatread[3] == 0:
                    pass
                elif whatread[3] == 1:
                    basic_speed = 80
                    hill_statue = 1
                elif whatread [3] == 2:
                    basic_speed = 20
                    hill_statue = 2
            elif whatread[3] == 0:
                basic_speed = 30
                hill_statue = 0

            # UARTも鑑みつつ13ms待つ
            if error_count == 0:
                wait(15)
            elif error_count == 1:
                wait(5)
        
        motorLeft.brake()
        motorRight.brake()

        # ここでESPとPicoにストップ&リセット信号を送る(予定)
        
        while any(ev3.buttons.pressed()):
            pass

main()
