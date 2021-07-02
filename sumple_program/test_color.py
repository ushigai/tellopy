import numpy as np
import cv2


def find_specific_color(frame, AREA_RATIO_THRESHOLD, LOW_COLOR, HIGH_COLOR):
    """
    指定した範囲の色の物体の座標を取得する関数
    frame: 画像
    AREA_RATIO_THRESHOLD: area_ratio未満の塊は無視する
    LOW_COLOR: 抽出する色の下限(h,s,v)
    HIGH_COLOR: 抽出する色の上限(h,s,v)
    """
    # 高さ，幅，チャンネル数
    h, w, c = frame.shape

    # hsv色空間に変換
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # 色を抽出する
    ex_img = cv2.inRange(hsv, LOW_COLOR, HIGH_COLOR)

    # 輪郭抽出
    _, contours, hierarchy = cv2.findContours(
        ex_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 面積を計算
    areas = np.array(list(map(cv2.contourArea, contours)))

    if len(areas) == 0 or np.max(areas) / (h*w) < AREA_RATIO_THRESHOLD:
        # 見つからなかったらNoneを返す
        print("the area is too small")
        return None
    else:
        # 面積が最大の塊の重心を計算し返す
        max_idx = np.argmax(areas)
        max_area = areas[max_idx]
        result = cv2.moments(contours[max_idx])
        x = int(result["m10"]/result["m00"])
        y = int(result["m01"]/result["m00"])
        return (x, y, areas)


# image info
image_file = "./camera_frame/000001.jpg"
img = cv2.imread(image_file)

# detect pink
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
lower = np.array([30, 90, 80])  # 紫に近いピンク
upper = np.array([160, 255, 255])  # 赤に近いピンク
img_mask = cv2.inRange(hsv, lower, upper)
img_color = cv2.bitwise_and(img, img, mask=img_mask)

print(find_specific_color(frame=img, AREA_RATIO_THRESHOLD=0,
                          LOW_COLOR=lower, HIGH_COLOR=upper))

# debug
cv2.imwrite("./camera_frame/teemp.jpg", img_color)
