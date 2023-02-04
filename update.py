import requests as requests


class Update:

    def __init__(self, config, convos):
        self.conversations: [Conversation] = convos
        self.external_id = config['external_id']
        self.short_description = config['short_description']
        self.visibility = config['visibility']
        self.long_description = config['long_description']
        self.greeting = config['greeting']
        self.name = config['name']

    def format(self):
        return {
            'external_id': self.external_id,
            'title': self.short_description,
            'name': '',
            'categories': [
                'Movies & TV'
            ],
            'visibility': 'UNLISTED',
            'copyable': False,
            'description': self.long_description,
            'greeting': self.greeting,
            'definition': self.conversation_texts(),
            'img_gen_enabled': False,
            'base_img_prompt': '',
            'strip_img_prompt_from_msg': False,
            'voice_id': 18
        }

    def conversation_texts(self, sep="\\n"):
        return sep.join([convo.format(sep) for convo in self.conversations])

    def submit(self):
        # todo this doesn't do anything; haven't bothered with their auth system
        update_json = self.format()
        headers = {
            # todo
        }
        response = requests.post('https://beta.character.ai/chat/character/update/', json=update_json,
                                 headers=headers
                                 )
        print(response)


class Conversation:

    def __init__(self):
        self.lines = []

    def format(self, sep="\\n"):
        return sep.join(self.lines)

