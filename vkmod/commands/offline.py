import vk_api as vk
import sys
from os import path

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from bot import Bot, botcommand, userauth
from tools.say import say

class Offline:
    def __init__(self, bot):
        self.bot = bot
        self.group_session = bot.group_session
        self.vkapi = self.group_session.get_api()
    
    @botcommand('оффлайн', 'офлайн', 'offline')
    @userauth
    async def offline(self, session, event):
        uvkapi = session.get_api()
        uvkapi.account.setOffline()

        say(self.vkapi, event, 'Вы оффлайн',
        keyboard = self.bot.user_keyboard(event.user_id))
    
    @botcommand('онлайн', 'online')
    @userauth
    async def online(self, session, event):
        uvkapi = session.get_api()
        uvkapi.account.setOnline()

        say(self.vkapi, event, 'Вы онлайн',
        keyboard = self.bot.user_keyboard(event.user_id))

def setup(bot):
    bot.add_class(Offline(bot))