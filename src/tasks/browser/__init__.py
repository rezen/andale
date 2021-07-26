import json
import asyncio
import hashlib
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from shared.mods import hooks

TAGS = ['http', 'network']
VALID_METHODS =  [
    'type',
    'dblclick',
    'click',
    'wait_for_selector',
    'wait_for_timeout',
    'evaluate',
    'fill',
    'hover',
]

SCHEMA = r"""
url:
    type: string
    format: uri
    required: true
method:
    type: string
    enum: [get, post, delete, put, head]
    default: get
port:
    type: integer
data:
    type string
headers:
    type: object
params: 
    type: object
actions:
    type: array
    items: 
        type: object
        properties:
            id:
                type: string
            method: 
                type: string
                enum: 
                    - type
                    - dblclick
                    - click
                    - wait_for_selector
                    - wait_for_timeout
                    - evaluate
                    - fill
                    - hover
            args:
                type: array
            record:
                type: string
                default: ''

wait_for:
    type: string
"""
async def task_async(self, url=None, method="get", port=None, data=None, headers={}, params=None, actions=[]):
    data = {}
    counter = 0
    debug_logs = []
    async with async_playwright() as p:
        browser = await p.firefox.launch()
        page = await browser.new_page()
        
        """
        # For rewriting requests
        async def handle_route(route):
            headers = route.request.headers
            print(type(headers))
            route.continue_(headers=headers)
        await page.route("**/*", handle_route)
        """

        lock = asyncio.Lock()
        hosts = set() # Unique hosts resources are loaded from
        page_weight = 0 # Total weight of resources on page
        counter = 0 # How many total requests are made

        async def on_response(response):
            nonlocal page_weight, counter, hosts
            parsed = urlparse(response.url)

            try:
                body = await response.body()
            except:
                return
    
            async with lock: 
                page_weight += len(body)
                counter += 1
                hosts.add(parsed.netloc)

        page.on("response", on_response)

        response = await page.goto(url)
        
        record_data = {}
        for action in actions:
            id = action.get('id')
            fn = action.get('method')
            args = action.get('args', [])
            if fn not in VALID_METHODS:
                continue
            
            try:
                d = await getattr(page, fn)(*args)
                if 'record' in action:
                    record_data[action['record']] = d
            except Exception as err:
                print(err)

        hooks.action("browser.page.ready", page)

        body = await page.evaluate('document.body.innerHTML', force_expr=True)
        # @todo save to central store based on response hashs
        request = response.request if response else None
        pointer = request.redirected_from if request else None
        redirects = 0
        while pointer:
            pointer = pointer.redirected_from
            redirects += 1

        url = urlparse(page.url)
        tmp = url.netloc.split(":")
        
        hash_of_body =  'md5:' + hashlib.md5(str(body).encode()).hexdigest()
        hash_of_headers = 'md5:' + hashlib.md5(json.dumps(response.headers).encode()).hexdigest() if response else None
        # body_ref = self.storage.put("http." + hash_of_body, text)

        data = {
            'title': await page.title(),
            'method': request.method if request else None,
            'path': url.path,
            'port': tmp[1] if len(tmp) > 1 else None,
            'host': tmp[0],
            'data': request.post_data if request else None,
            'params': url.params,
            'ip': None,
            'status_code': response.status if response else None,
            'headers': response.headers if response else None,
            'size': len(body),
            'redirects': redirects,
            'hash_of_headers': hash_of_headers,
            'hash_of_body': hash_of_body,
            'record': record_data,
            'meta': {
                'driver': 'playwright',
                'requests': counter,
                'hosts': list(hosts),
                'weight': page_weight,
                'debug': debug_logs,
            }
        }
        hooks.action("browser.before.close", browser)

        await browser.close()

    return data

