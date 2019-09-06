import vk_api as vk
import sys
from os import path

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from bot import Bot, botcommand, userauth
from tools.say import say

class Wall:
    def __init__(self, bot):
        self.bot = bot
        self.group_session = bot.group_session
        self.vkapi = self.group_session.get_api()
    
    @botcommand('post','пост')
    @userauth
    async def wallpost(self, session, event):
        uvkapi = session.get_api()
        
        say(self.vkapi, event, 'Введите текст',
        keyboard = self.bot.keyboard([[['@', 'Ожидание..', 'secondary']]]))
        
        event = await self.bot.wait_for_message(event.user_id)
        try:
            response = uvkapi.wall.post(owner_id=event.user_id, message=event.text)
        except vk.ApiError:
            say(self.vkapi, event, 'У бота нет доступа к этой комманде. Напишите "Сменить категории" и выберете "Стена".',
            keyboard = self.bot.user_keyboard(event.user_id))
            return

        say(self.vkapi, event, f"Создана запись на стене с id {response['post_id']}",
        keyboard = self.bot.user_keyboard(event.user_id))

def setup(bot):
    bot.add_class(Wall(bot))