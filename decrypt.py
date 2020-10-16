from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import binascii, json, base64

playTokenDecryptKey = 'eee39eae6e156222a460e240496876f00623ae6b5ad08701209de12ae298fac4'
playToken = 'eyJpdiI6InZhMW4yNDNGTkNoeW4yN3dLSmJvM2c9PSIsImRhdGEiOiJPWlhYZnR5Qmt0NGkyRjU4RUVUcVg5TlN4U2ZFRkJvd1dBdTV3YnRDXC9lcEJPT1FNMjhuVnh0XC9RemhxbWhcLzYzam5La0dsNm1HRnRwU0V2WFBJVkp3Zz09In0='

# Decrypt the play token.
key = binascii.unhexlify(playTokenDecryptKey)
encrypted = json.loads(base64.b64decode(playToken))
encryptedData = base64.b64decode(encrypted['data'])
iv = base64.b64decode(encrypted['iv'])
cipher = AES.new(key, AES.MODE_CBC, iv)
data = unpad(cipher.decrypt(encryptedData), AES.block_size)
jsonData = json.loads(data)

playToken = jsonData['playToken']
openChat = jsonData['OpenChat']
member = jsonData['Member']