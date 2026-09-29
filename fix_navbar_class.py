import os
os.chdir(r'c:\Users\kunji\NODE')

with open('sih-frontend/src/components/Navbar.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "className='mobile-nav-item ' + (activeView === tab.id ? 'active' : '')",
    "className={'mobile-nav-item ' + (activeView === tab.id ? 'active' : '')}"
)

with open('sih-frontend/src/components/Navbar.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print('Navbar fixed')