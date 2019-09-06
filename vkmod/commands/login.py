import vk_api as vk
import sys
from os import path
from random import randint

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from bot import Bot, botcommand
from tools.say import say

class Login:
    def __init__(self, bot):
        self.bot = bot
        self.group_session = bot.group_session
        self.vkapi = self.group_session.get_api()

    @botcommand('войти','логин','login')
    async def login(self, event):
        if event.user_id in self.bot.user_sessions: #Already login
            say(self.vkapi, event, 'Вы уже авторизованны',
                keyboard = self.bot.user_keyboard(event.user_id))
            return

        else: 
            if self.bot.user_get(event.user_id, 'id') != None: # Login
                say(self.vkapi, event, 'Введите пароль', 
                    keyboard = self.bot.keyboard([[['@', 'Ожидание..', 'secondary']]]))
                
                event = await self.bot.wait_for_message(event.user_id)
                password = event.text
                response = self.bot.user_login(event.user_id, password=password)

                if response:
                    say(self.vkapi, event, 'Вы авторизовались!',
                        keyboard = self.bot.user_keyboard(event.user_id))
                    return

                else:
                    keyboard = [[['', 'Войти', 'primary' ]],
                                [['', 'Войти с другого аккаунта', 'primary']],
                                [['', 'Уйти в забвение', 'secondary']]]
                    say(self.vkapi, event, 'Пароль не подходит',
                        keyboard = self.bot.keyboard(keyboard))
                    return

        # Registration
        access_token = await self.auth(event)
        if access_token:
            say(self.vkapi, event, 'Введите пароль', 
                keyboard = self.bot.keyboard([[['@', 'Ожидание..', 'secondary']]]))
            
            event = await self.bot.wait_for_message(event.user_id)
            password = event.text

            access_to = await self.get_access_to_users(event)

            self.bot.user_login(event.user_id, access_token, password, access_to)

            say(self.vkapi, event, 'Вы успешно авторизовались!',
                keyboard = self.bot.user_keyboard(event.user_id))
    
    @botcommand('войти с другого аккаунта', 'loginas')
    async def login_as(self, event):
        if event.main_user_id != event.user_id:
            say(self.vkapi, event, 'Вы не можете зайти с другого аккаунта в другой аккаунт, вообще зачем вам это?')
            return

        if self.bot.user_get(event.user_id, 'login'): #if user logged in then give user keyboard, else login keyboard
            keyboard = self.bot.user_get(event.user_id, 'keyboard') # Get rows of keyboard, not json
        else:
            keyboard = [[['', 'Войти', 'primary' ]],
                        [['', 'Войти с другого аккаунта', 'primary']],
                        [['', 'Уйти в забвение', 'secondary']]] 
        
        say(self.vkapi, event, 'Введите id пользователя', 
            keyboard = self.bot.keyboard([[['@', 'Ожидание..', 'secondary']]]))

        event = await self.bot.wait_for_message(event.user_id)
        try:
            owner_id = int(event.text)
        except:
            owner_id = None

        if self.bot.user_get(owner_id, 'id'):
            say(self.vkapi, event, 'Введите пароль пользователя')

            event = await self.bot.wait_for_message(event.user_id)
            password = event.text

            if self.bot.user_get(owner_id, 'password') == password:
                if self.bot.login_as(event.user_id, owner_id):
                    say(self.vkapi, event, 'Вы авторизовались!',
                        keyboard = self.bot.user_keyboard(owner_id))
                    return
                else:
                    say(self.vkapi, event, 'Пользователь не добавил вас в список тех, у кого есть доступ к его аккаунту в vkMod.',
                        keyboard = self.bot.keyboard(keyboard))
                    return
        say(self.vkapi, event, 'Неверный id или пароль',
        keyboard = self.bot.keyboard(keyboard))
                      
    @botcommand('выход', 'unlogin')
    async def unlogin(self, event):
        self.bot.unlogin_user(int(event.main_user_id if hasattr(event, 'main_user_id') else event.user_id))

        keyboard = [[['', 'Войти', 'primary' ]],
                    [['', 'Войти с другого аккаунта', 'primary']],
                    [['', 'Уйти в забвение', 'secondary']]]
        
        say(self.vkapi, event, 'Вы вышли',
            keyboard = self.bot.keyboard(keyboard))

    @botcommand('уйти в забвение', 'deletemyself')
    async def deletemyself(self, event):
        if event.main_user_id != event.user_id:
            say(self.vkapi, event, 'Вы не можете удалить не ваш аккаунт.')
            return

        self.bot.delete_user(event.user_id)

        say(self.vkapi, event, 'Вы ушли в забвение..',
            keyboard = self.bot.keyboard([[['', 'Начать', 'positive' ]]]))

    @botcommand('сменить категории', 'сменить права', 'changeperm')
    async def change_perm(self, event):
        if event.main_user_id != event.user_id:
            say(self.vkapi, event, 'Вы не можете менять категории не в вашем аккаунте. Как вы вообще это себе представляете?')
            return
        
        elif not self.bot.user_get(event.user_id, 'login'):
            say(self.vkapi, event, 'Вы не вошли в аккаунт')
            return

        access_token = await self.auth(event)
        if access_token:
            self.bot.user_login(event.user_id, access_token) # Relogin with new token
            say(self.vkapi, event, 'Вы успешно сменили категории!',
                keyboard= self.bot.user_keyboard(event.user_id))

    @botcommand('настройки', 'settings')
    async def settings(self, event):
        if event.user_id != event.main_user_id: 
            say(self.vkapi, event, 'Вы не можете смотреть и изменять данные не в своем аккаунте')
            return
        
        elif not self.bot.user_get(event.user_id, 'login'):
            say(self.vkapi, event, 'Вы не вошли в аккаунт')
            return

        # Specific stats
        stats = '\n'.join(f'• Комманда {key} была вызвана {value} раз' for key, value in self.bot.user_get(event.user_id, 'stats').items())
        access_to = self.bot.user_get(event.user_id, 'access_to') 

        info = f'''Информация о вас:
        • Id: {self.bot.user_get(event.user_id, 'id')}
        • Пароль: {self.bot.user_get(event.user_id, 'password')}
        • Токен: {self.bot.user_get(event.user_id, 'token')}
        • Доступ к аккаунту: {', '.join(access_to if access_to != [] else ['Никто'])}
        
        Статистика: 
        {stats}'''

        keyboard = [
           [['', 'Изменить пароль',            'primary'],
            ['', 'Изменить доступ к аккаунту', 'primary']],
           [['', 'Отмена',                     'negative']]
            
        ]

        say(self.vkapi, event, info,
            keyboard = self.bot.keyboard(keyboard))

        event = await self.bot.wait_for_message(event.user_id)
        response = event.text
        
        if response == 'Изменить пароль':
            say(self.vkapi, event, 'Напишите действующий пароль', 
                keyboard = self.bot.keyboard([[['@', 'Ожидание..', 'secondary']]]))

            event = await self.bot.wait_for_message(event.user_id)
            password = event.text

            if password == self.bot.user_get(event.user_id, 'password'):
                say(self.vkapi, event, 'Напишите новый пароль')

                event = await self.bot.wait_for_message(event.user_id)
                password = event.text 

                self.bot.user_edit(event.user_id, 'password', password)

                say(self.vkapi, event, 'Пароль успешно изменен',
                    keyboard = self.bot.user_keyboard(event.user_id))
            
            else:
                say(self.vkapi, event, 'Пароли не совпадают',
                    keyboard = self.bot.user_keyboard(event.user_id))
        
        elif response == 'Изменить доступ к аккаунту':
            access_to = await self.get_access_to_users(event)
            self.bot.user_edit(event.user_id, 'access_to', access_to)

            say(self.vkapi, event, 'Готово!',
                keyboard = self.bot.user_keyboard(event.user_id))
        else:
            say(self.vkapi, event, 'Отменено',
                keyboard = self.bot.user_keyboard(event.user_id))
          
    async def get_access_to_users(self, event):
        text = '''Введите id пользователей, которые смогут зайти в ваш аккаунт. 
                Напишите "Все" и к вам в аккаунт смогут зайти все кто знают пароль.
                Не пишите ничего и нажмите "Готово!" и кроме вас никто не сможет зайти в ваш аккаунт.'''
        say(self.vkapi, event, text, 
            keyboard=self.bot.keyboard([[['', 'Готово!', 'positive']]]))
        
        access_to = []
        while True:
            event = await self.bot.wait_for_message(event.user_id)
            if not event.text in access_to:
                if event.text == 'Готово!':
                    break
                elif event.text == 'Все':
                    access_to.append('all')
                    break
                try:
                    access_to.append(int(event.text))
                    say(self.vkapi, event, 'Добавлено!')
                except:
                    say(self.vkapi, event, 'Невозможно добавить пользователя')
                
        return access_to

    async def auth(self, event):
        permissions = await self.wait_for_permissions(event)

        auth_link = f"https://oauth.vk.com/authorize?client_id={self.bot.bot_id}&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope={','.join(perm for perm in permissions)},offline&response_type=token"
        say(self.vkapi, event, f'Авторизация: {auth_link} \nПосле подтверждения, скопируйте ссылку из адресной строки и вставьте сюда.', 
            keyboard=self.bot.keyboard([[['@', 'Ожидание..', 'secondary']]]))
        
        event = await self.bot.wait_for_message(event.user_id)

        access_token = event.text[event.text.find('token=')+6:event.text.find('&amp;e')]
        user_session = vk.VkApi(token=access_token)
        
        try:
            uvkapi = user_session.get_api()
            uvkapi.account.setOnline()
            
        except vk.ApiError:
            say(self.vkapi, event, 'Невозможно получить доступ. Попробуйте снова.', 
                keyboard = self.bot.keyboard([[['', 'Войти', 'primary' ]]]))
            return False
        
        return access_token
        
    async def wait_for_permissions(self, event):
        keyboard_pattern = [
           [['friends',       'Друзья',          'secondary'],
            ['groups',        'Группы',          'secondary'],
            ['wall',          'Стена',           'secondary'],
            ['notifications', 'Оповещения',      'secondary']],
           [['status',        'Статус',          'secondary'],
            ['stories',       'Истории',         'secondary'],
            ['video',         'Видеозаписи',     'secondary'],
            ['audio',         'Аудиозаписи',     'secondary']],
           [['end',           'Готово!',         'positive' ]]
        ]

        say(self.vkapi, event, 'Выберете категории к которым будет иметь доступ бот. Вы сможете изменить категории написав "Сменить категории"',
            keyboard = self.bot.keyboard(keyboard_pattern))

        permissions = []
        while True:
            event = await self.bot.wait_for_message(event.user_id)
            try:
                permission = eval(event.payload)['button']
            except:
                continue

            if permission == 'end':
                if permissions == []:
                   say(self.vkapi, event, 'Выберете категории к которым будет иметь доступ бот.')
                else:
                    return permissions
            
            elif not permission in permissions:
                permissions.append(permission) 

                keyboard_pattern = self.bot.change_keyboard(keyboard_pattern, permission, 'primary', 2)
                keyboard = self.bot.keyboard(keyboard_pattern)
                say(self.vkapi, event, 'Добавлено', keyboard=keyboard)

            elif permission in permissions:
                permissions.remove(permission)

                keyboard_pattern = self.bot.change_keyboard(keyboard_pattern, permission, 'secondary', 2)
                keyboard = self.bot.keyboard(keyboard_pattern)
                say(self.vkapi, event, 'Убрано', keyboard=keyboard)

def setup(bot):
    bot.add_class(Login(bot))