from PIL import Image
img = Image.open('PROJECT_ROOT/logo.png')
img.save('PROJECT_ROOT/logo.ico', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
print('ok')

