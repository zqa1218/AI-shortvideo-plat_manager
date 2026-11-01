import sys

import cv2

source, target = sys.argv[1], sys.argv[2]
capture = cv2.VideoCapture(source)
ok, frame = capture.read()
capture.release()
if ok:
    height, width = frame.shape[:2]
    scale = 320 / max(height, width)
    if scale < 1:
        frame = cv2.resize(frame, (int(width * scale), int(height * scale)))
    cv2.imwrite(target, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
