import vk_api as vk
import sys
from os import path
from random import randint

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from bot import Bot, botcommand
from tools.say import say

class Start:
    def __init__(self, bot):
        self.bot = bot
        self.group_session = bot.group_session

    @botcommand('начать')
    async def start(self, event):
        greeting = """Привет!
        Я - чат-бот. Я могу модерировать твою страничку вконтакте,
        выполнять созданые тобою условия, и добавить новые возможности.

        Чтобы я мог выполнять свои функции вы должны дать мне права,
        нажмите снизу на кнопку "Войти" и следуйте инструкциям.

        P.s Ваши данные и доступ к ним НЕ Будет использоваться в 
        корыстных целях. 
        (Также вы можете выбрать, к каким данным будет иметь доступ бот). 
        """
        
        vkapi = self.group_session.get_api()

        # Get chat
        if event.from_user:
            chat = {'user_id':event.user_id}
        elif event.from_chat:
            chat = {'chat_id':event.chat_id}

        # Generate keyboard
        keyboard = self.bot.keyboard([[['', 'Войти', 'primary' ]]])
        
        #Send message & keyboard
        say(vkapi, event, greeting, keyboard=keyboard)

def setup(bot):
    bot.add_class(Start(bot))