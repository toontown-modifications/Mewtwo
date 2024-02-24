# This is a hacky solution for Disney endpoints.
# I cannot get parameters from the endpoint requests in PHP.

from aiohttp import web
import asyncio, requests, lxml.etree as et, random, sys

deleteEndpoint = 'https://127.0.0.1/api/authDelete'
usernameAvailabilityEndpoint = 'https://127.0.0.1/api/checkUsernameAvailability'
regEndpoint = 'https://127.0.0.1/register/'

headers = {
    'User-Agent': 'Sunrise Games - EndpointManager'
}

isDevelopment = '--dev' in sys.argv

if isDevelopment:
    # openssl req -config openssl.cnf -new -out sunrise.csr -keyout sunrise.pem
    # openssl rsa -in sunrise.pem -out sunrise.key
    # openssl x509 -in sunrise.csr -out sunrise.cert -req -signkey sunrise.key -days 365
    import os, urllib3
    urllib3.disable_warnings()

    os.environ['REQUESTS_CA_BUNDLE'] = os.getcwd() + r'\config\web\toontastic-sunrise-games-chain.pem'
    os.environ['SSL_CERT_FILE'] = os.getcwd() + r'\config\web\toontastic-sunrise-games-chain.pem'

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
        'password': password,
        'bdayYear': bdayYear
    }

    response = requests.post(regEndpoint, data, headers = headers)

    return web.Response(text = response.text)

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

        suggestedUsername1 = f'{username}{random.randint(1, 100)}'
        suggestedUsername2 = f'{username}{random.randint(1, 100)}'
        suggestedUsername3 = f'{random.choice(words)}{username}'

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