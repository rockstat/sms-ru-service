"""
SMSRU Rockstat service
(c) Dmitry Rodin 2018-2019
---------------------
"""
import aiohttp
from band import expose, settings, logger, rpc, worker
from random import randrange
from .helpers import ms
from datetime import date
from .structs import ServiceId
from userlib.redis import create_redis
from typing import NamedTuple


class WaitWithCode(NamedTuple):
    code: str
    service_id: ServiceId

    def check(self, code):
        return self.code == code


class state:
    waiting = dict()
    codes = dict()
    services_phones = dict()
    redis_pool = None


redis = create_redis(prefix='smsru')


@expose()
async def verify(phone, service_id, **kwargs):
    """
    Init verificatiuon process.
    --
    verify(phone:str, service_id:ServiceId)
    --
    result: {}
    """

    code = new_code()
    sid = ServiceId(*service_id)
    sid_str = str(sid)
    phone_id = ServiceId('phone', phone)
    # Temp store
    state.codes[sid_str] = WaitWithCode(code, phone_id)
    print(f'{sid}, {sid_str} requested verification. code {code} to {phone_id.id}')
    return await send_sms(phone_id.id, f'Your code is {code}')


@expose()
async def confirm(service_id, code):
    """
    Finish validation and save match
    --
    confirm(service_id:ServiceId, code:str)
    """
    logger.debug(f'confirm called {service_id}, {code}')
    if service_id and code:
        sid = ServiceId(*service_id)
        sid_str = str(sid)
        stored_code = state.codes.pop(sid_str, None)
        logger.debug(f'{sid} confirmation, checking code for phone {stored_code.service_id}. given {code}')
        if stored_code and stored_code.check(code):
            logger.debug('confirmed')
            await rpc.request('id', 'update', service_id=sid, ids=[[stored_code.service_id, ms()]])
            await rpc.request('id', 'update', service_id=stored_code.service_id, ids=[[sid, ms()]])
            return {'success': 1}


@expose()
async def send_sms(to=None, msg=None, to_phone=None):
    to = to or to_phone
    if not to or not msg:
        raise Exception('wronds params')
    logger.info(f'sending sms to {to}')
    curr_count = await redis.get(to + str(date.today()))
    curr_count = int(curr_count or 0)
    if to != '79261244141' and curr_count >= 3:
        logger.info('too many requests')
        return {'error': 'too many requests'}
    await redis.increx(to, 60*60*24)
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


@worker()
async def start():
    await redis.initialize()
