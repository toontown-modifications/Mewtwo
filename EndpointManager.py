# This is a hacky solution for Disney endpoints.
# I cannot get parameters from the endpoint requests in PHP.

from aiohttp import web
import asyncio, requests, lxml.etree as et, random

deleteEndpoint = 'https://sunrisegames.tech/api/authDelete'
usernameAvailabilityEndpoint = 'https://sunrisegames.tech/api/checkUsernameAvailability'
regEndpoint = 'https://sunrisegames.tech/register'

headers = {
    'User-Agent': 'Sunrise Games - EndpointManager'
}

async def crossdomain(request):
    data = open('data/web/crossdomain.xml').read()

    return web.Response(text = data)

async def registerAccount(request):
    args = await request.post()

    doLogin = args.get('doLogin')
    bdayYear = args.get('bdayYear')
    templateId = args.get('templateId')
    bdayDay = args.get('bdayDay')
    isoCountry = args.get('isoCountry')
    username = args.get('username')
    registration = args.get('Toontown_Registration')
    agreedToTOU = args.get('agreedToTOU')

    if args.get('parentEmail'):
        email = args.get('parentEmail')
    else:
        email = args.get('email')

    lastName = args.get('lastName')

    if not lastName:
        lastName = 'test'

    subscribe = args.get('subscribe')
    firstName = args.get('firstName')
    password = args.get('password')
    bdayMonth = args.get('bdayMonth')
    siteCode = args.get('siteCode')
    promotionName = args.get('promotionName')

    data = {
        'doLogin': doLogin,
        'username': username,
        'email': email,
        'firstName': firstName,
        'lastName': lastName,
        'password': password
    }

    requestGet = requests.get(regEndpoint, data, headers = headers)
    print(requestGet.text)

async def checkUsernameAvailability(request):
    args = await request.post()

    username = args.get('username')
    siteCode = args.get('siteCode')

    data = {
        'username': username,
        'siteCode': siteCode
    }

    requestResponse = requests.get(usernameAvailabilityEndpoint, data, headers = headers).text

    root = et.Element('config')

    if requestResponse == '1':
        success = 'true'
    else:
        success = 'false'
        resultsRoot = et.SubElement(root, 'results')

        words = [
            'Amazing',
            'Cool',
            'Super',
            'Fantastic'
        ]

        suggestedUsername1 = '{0}{1}'.format(username, random.randint(1, 100))
        suggestedUsername2 = '{0}{1}'.format(username, random.randint(1, 100))
        suggestedUsername3 = '{0}{1}'.format(random.choice(words), username)

        resultsFields = [
            ('suggestedUsername1', suggestedUsername1),
            ('suggestedUsername2', suggestedUsername2),
            ('suggestedUsername3', suggestedUsername3)
        ]

        for key, value in resultsFields:
            et.SubElement(resultsRoot, key).text = value

    fields = [
        ('success', success)
    ]

    for key, value in fields:
        et.SubElement(root, key).text = value

    response = et.tostring(root, pretty_print = True).decode()

    if requestResponse in ('0', '1'):
        return web.Response(text = response)

async def handleAuthDelete(request):
    args = await request.post()

    username, password = args.get('n'), args.get('p')

    data = {
        'n': username,
        'p': password
    }

    request = requests.get(deleteEndpoint, params = data, headers = headers)
    response = request.text

    validResponse = 'ACCOUNT SERVER RESPONSE'
    invalidResponse = 'ACCOUNT SERVER RESPONSE\n\nerrorCode=20\nerrorMsg=bad password'

    if response in (validResponse, invalidResponse):
        return web.Response(text = response)

async def initializeService():
    app = web.Application()
    app.router.add_post('/api/authDelete', handleAuthDelete)
    app.router.add_post('/checkUsernameAvailability', checkUsernameAvailability)
    app.router.add_post('/register', registerAccount)
    app.router.add_get('/crossdomain.xml', crossdomain)

    return app

loop = asyncio.get_event_loop()
app = loop.run_until_complete(initializeService())
web.run_app(app, host = '0.0.0.0', port = 4500)