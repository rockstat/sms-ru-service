"""
Band service skeleton
(c) Dmitry Rodin 2018
---------------------
"""
import aiohttp
from prodict import Prodict as pdict
from band import expose, settings, logger, rpc
from random import randrange
from .helpers import ms
from .structs import ServiceId


state = pdict(
    codes=pdict(),
    services_phones=pdict(),
    redis_pool=None
)

@expose()
async def confirm(service_id, code):
    sid = ServiceId(*service_id)
    sid_str = str(sid)
    phone_id = state.services_phones.get(sid_str, None)
    print(f'check code for phone {phone_id}. given {code}')
    if phone_id and code and state.codes[sid_str] == code:
        state.codes.pop(sid_str, None)
        await rpc.request('id', 'update', service_id=sid, ids=[[phone_id, ms()]])
        await rpc.request('id', 'update', service_id=phone_id, ids=[[sid, ms()]])
        return {'success': 1}


@expose()
async def verify(phone, service_id):
    code = new_code()
    sid = ServiceId(*service_id)
    sid_str = str(sid)
    phone_id = ServiceId('phone', phone)
    state.codes[sid_str] = code
    state.services_phones[sid_str] = phone_id
    print(f'sending code {code} to {phone_id.id}')
    await send_sms(phone_id.id, f'Your code is {code}')
    return {}


@expose()
async def send_sms(to, msg):
    params = dict(sender=settings.sender, to=to, msg=msg)
    result = await api_call(settings.endpoint.format(**params))
    logger.debug('send_sms', p=params, r=result)
    return result


async def api_call(url, params=None, json=None, method='post'):
    async with aiohttp.ClientSession() as session:
        method = getattr(session, method.lower())
        async with method(url, json=json, params=params) as res:
            print(url, res.status)
            if res.status == 204:
                return {}
            if res.status == 200:
                return await res.json()


def new_code():
    return str(randrange(1000, 9999))


def gen_key(key, section='g'):
    return f"id:{section}:{key}"
