# import pytesseract
# import cv2

# img = cv2.imread('image.png', cv2.IMREAD_GRAYSCALE)
# d = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
# img = cv2.cvtColor(img,cv2.COLOR_GRAY2RGB)

# n_boxes = len(d['level'])
# for i in range(n_boxes):
#     (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
#     cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

# cv2.imshow('image', img)
# cv2.waitKey(0)

import pywinctl
import pymonctl
import time

time.sleep(2)
window = pywinctl.getActiveWindow()
print(window.getAppName())
print(window.title)
print(window.bottomright)
print(pymonctl.getPrimary().size)