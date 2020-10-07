# This is a hacky solution.
# I cannot get the authDelete parameters from the request in PHP.
# This is used for other Disney endpoints, too.

from aiohttp import web
import asyncio, requests

deleteEndpoint = 'http://download.sunrisegames.tech/api/authDelete'
usernameAvailabilityEndpoint = 'https://demo.sunrisegames.tech/checkUsernameAvailability'
regEndpoint = 'https://demo.sunrisegames.tech/register'

headers = {
    'User-Agent': 'Sunrise Games - EndpointManager'
}

async def crossdomain(request):
    data = open('data/web/crossdomain.xml').read()

    return web.Response(text = data)

async def login(request):
    args = await request.post()
    print(args)

async def AccountLoginRequest(request):
    args = await request.post()

    print('e')

    response = open('data/web/AccountLoginRequest.xml', 'r').read()

    return web.Response(text = response)

async def WhoAmIRequest(request):
    args = await request.post()

    print(args)

    response = open('data/web/WhoAmIRequest.xml', 'r').read()

    return web.Response(text = response)

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

    requestGet = requests.get(usernameAvailabilityEndpoint, data, headers = headers)

    if requestGet.text == '1':
        response = open('data/web/success.xml', 'r').read()
    else:
        response = open('data/web/fail.xml', 'r').read()

    if requestGet.text in ('0', '1'):
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
    app.router.add_post('/api/WhoAmIRequest', WhoAmIRequest)
    app.router.add_post('/api/AccountLoginRequest', AccountLoginRequest)
    app.router.add_post('/api/login', login)
    app.router.add_get('/crossdomain.xml', crossdomain)

    return app

loop = asyncio.get_event_loop()
app = loop.run_until_complete(initializeService())
web.run_app(app, host = '0.0.0.0', port = 4500)