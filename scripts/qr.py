import qrcode


def generate_qr_code(text, filename="qrcode.png"):
    img = qrcode.make(text)
    type(img)
    img.save(filename)


