import os, subprocess, sys

districtNames = [
    'Boingy Acres',
    'Boingy Bay',
    'Boingy Summit',
    'Boingyboro',
    'Bouncy Summit',
    'Crazy Grove',
    'Crazy Hills',
    'Crazyham',
    'Funnyfield',
    'Giggly Bay',
    'Giggly Grove',
    'Giggly Hills',
    'Giggly Point',
    'Gigglyfield',
    'Gigglyham',
    'Goofy Valley',
    'Goofyport',
    'Kooky Grove',
    'Kookyboro',
    'Loopy Harbor',
    'Nutty Hills',
    'Nutty River',
    'Nutty Summit',
    'Nuttyville',
    'Nuttywood',
    'Silly Rapids',
    'Silly Valley',
    'Sillyham',
    'Toon Valley',
    'Zany Acres'
]

startingNum = 401000000

if sys.platform == 'win32':
    os.chdir('startup/win32')

for index, elem in enumerate(districtNames):
    subprocess.shell = True
    os.environ['DISTRICT_NAME'] = str(districtNames[index])
    os.environ['BASE_CHANNEL'] = str(startingNum)
    os.system('start cmd /c districtStarter.bat')
    startingNum = startingNum + 1000000