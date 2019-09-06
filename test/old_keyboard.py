import json


def gen_keyboard(rows, btn_name = 'button', one_time=False):
    """Generate keyboard for vk chat.
    
    Parameters
    ----------
    rows : list
        Example: keyboard([
            [["payload", "label", "color]], #first line of buttons
            [["payload2", "label2", color], ["payload3", "label3", color]] #second line of buttons
            ]) 
    
    one_time : bool
    """

    dict_keyboard = {
        "one_time": one_time,
        "buttons": []
    }
    
    for row in range(len(rows)):
        dict_keyboard['buttons'].append([])
        for button in rows[row]:
            dict_keyboard['buttons'][row].append(
                {
                    "action": {
                        "type": "text",
                        "payload": '{"'+btn_name+'": "'+button[0]+'"}',
                        "label": button[1]
                    },
                    "color": button[2]
                }
            )
    print(dict_keyboard)
    return json.dumps(dict_keyboard)

def change_keyboard(rows, target, edit, n=1):
    for row in rows:
        for button in row:
            if target in button:
                button[n] = edit
    
    return rows

def new_user_keyboard():
    return gen_keyboard([
       [['', 'Здесь будут ваши самые популярые комманды', 'secondary']],
       [['', 'Помощь',                                    'secondary'],
        ['', 'Новый скрипт',                              'secondary']
        ['', 'Выход',                                     'negative' ]]
    ])