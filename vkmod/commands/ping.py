import vk_api as vk
import sys
from os import path
from random import randint

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from bot import Bot, botcommand

class Ping:
    def __init__(self, bot):
        self.group_session = bot.group_session

    @botcommand('пинг','ping')
    async def ping(self, event):
        vkapi = self.group_session.get_api()

        if event.from_user:
            kwargs = {'user_id':event.user_id}
        elif event.from_chat:
            kwargs = {'chat_id':event.chat_id}
        
        vkapi.messages.send(
            message = 'Pong!',
            random_id = randint(0, event.user_id),
            **kwargs
        )

def setup(bot):
    bot.add_class(Ping(bot))