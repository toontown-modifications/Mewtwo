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

isWindows = sys.platform == 'win32'
isLinux = sys.platform == 'linux'

if isWindows:
    os.chdir('startup/win32')
elif isLinux:
    os.chdir('startup/unix')

for index, elem in enumerate(districtNames):
    subprocess.shell = True

    districtName = str(districtNames[index])

    os.environ['DISTRICT_NAME'] = districtName
    os.environ['BASE_CHANNEL'] = str(startingNum)

    if isWindows:
        os.system('start cmd /c districtStarter.bat')
    elif isLinux:
        os.system(f'screen -dmS "{districtName}" ./districtStarter.sh')

    startingNum = startingNum + 1000000