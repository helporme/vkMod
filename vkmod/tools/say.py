import vk_api as vk
from random import randint

def say(vkapi, event, text=None, **kwargs):
    if event.from_user:
        if hasattr(event, 'main_user_id'):
            chat = {'user_id':event.main_user_id}
        else:
            chat = {'user_id':event.user_id}
    
    vkapi.messages.send(
        message = text,
        random_id = randint(0, event.user_id),
        **chat,
        **kwargs
    )
