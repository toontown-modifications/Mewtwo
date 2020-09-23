# This is a hacky solution.
# I cannot get the authDelete parameters from the request in PHP.
# Most likely will be used for other Disney endpoints, too.

from aiohttp import web
import asyncio, requests

deleteEndpoint = 'http://download.rocketprogrammer.me/api/authDelete'

async def handleAuthDelete(request):
    args = await request.post()

    username, password = args.get('n'), args.get('p')

    data = {
        'n': username,
        'p': password
    }

    request = requests.get(deleteEndpoint, params = data)
    response = request.text

    validResponse = 'ACCOUNT SERVER RESPONSE'
    invalidResponse = 'ACCOUNT SERVER RESPONSE\n\nerrorCode=20\nerrorMsg=bad password'

    if response == invalidResponse:
        return web.Response(text = invalidResponse)

    return web.Response(text = validResponse)

async def initializeService():
    app = web.Application()
    app.router.add_post('/api/authDelete', handleAuthDelete)

    return app

loop = asyncio.get_event_loop()
app = loop.run_until_complete(initializeService())
web.run_app(app, host = '0.0.0.0', port = 4500)