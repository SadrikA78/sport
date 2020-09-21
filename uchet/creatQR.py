import qrcode
from key_generation import generate_key
def return_qr(centr,section,data):
    key = generate_key()
    print('-'*20 + key)
    img = qrcode.make(f'http://194.67.86.151:1111/?centr={centr}&section={section}&data={data}')
    img.save(f'{key}.png')
#return_qr(id,data)
    return(f'{key}.png')