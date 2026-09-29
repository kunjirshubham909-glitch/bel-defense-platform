import os, base64
os.chdir(r'c:\Users\kunji\NODE')
data = open('sih-frontend/src/components/Navbar.jsx', 'rb').read()
encoded = base64.b64encode(data).decode()
open('navbar_b64.txt', 'w').write(encoded)
print(len(encoded))