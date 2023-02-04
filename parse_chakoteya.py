import json
import logging
import pickle
from collections import Counter
from os.path import isfile

import requests as requests
from bs4 import BeautifulSoup
from re import sub, split

from update import Conversation, Update
from config import Config, SERIES


class Downloader:

    def __init__(self, config):
        self.base_url = config['url_root']
        self.character_name = config['character_name']
        self.char_upper = self.character_name.upper()
        self.primary_series = SERIES[config['primary_series']]
        self.include_movies = config['include_movies']
        self.episode = config['episode'] if 'episode' in config else None
        self.suffix = str(self.episode) if self.episode is not None else 'ALL'
        self.target_tempfile = 'output/parsed_chakoteya_{}_{}_{}.pkl'.format(self.char_upper, self.primary_series, self.suffix)
        self.longest_line = ''

    def download(self) -> [Conversation]:
        if isfile(self.target_tempfile):
            with open(self.target_tempfile, 'rb') as file:
                return pickle.load(file)
        else:
            convos = self.scrape_conversations()
            with open(self.target_tempfile, 'wb') as file:
                pickle.dump(convos, file)
            return convos

    def scrape_conversations(self) -> [Conversation]:
        series_url = self.base_url + self.primary_series + '/episodes.htm'
        conversations: [Conversation] = []
        for episode_url in link_iterator(series_url, self.primary_series, self.base_url, self.episode):
            logging.info('Parsing episode from %s.', episode_url)
            # I care more about making it clear what is being done and why than efficiency here, so there is a lot of duplicate iterating.
            script_table = first_table(episode_url)
            if script_table is None:
            	continue
            script = script_table.text
            # Scenes are delimited by bolded bracketed text with newlines on either side, ex: [Bridge]
            scenes: [str] = split("\[.+\]\n", script)
            for scene in scenes:
                if self.character_name not in scene and self.char_upper not in scene:
                    logging.debug('Skipping scene as character %s is not present.', self.character_name)
                    continue
                conversation = self.parse_scene(scene)
                if len(conversation.lines) > 0:
                    conversations.append(conversation)
            logging.info('The character\'s longest line up to episode %s is %s.', episode_url, self.longest_line)
        logging.info('Done. %s conversations created.', len(conversations))
        return conversations

    def parse_scene(self, scene):
        clean = scene.strip().replace(" ", '')
        # Remove set blocking directions
        clean = sub("\([T|t]o .+\)", '', clean)
        clean = sub(" \[.+]:", '', clean)
        # Replace all lines inside () aka set directions with being inside ** aka italics
        clean = sub("[\(|\)]", "*", clean)
        lines = split(r'(?=\n.+:)', clean)
        lines = [line for line in [clean_text(line) for line in lines] if len(line) > 0]
        # Get chars of scene in descending number of lines
        cast = Counter([line.split(':')[0] for line in lines])
        top = cast.most_common(2)
        # Make the char with the highest lines that isn't the target char into user.
        user_char_upper = top[0][0] if top[0][0] not in {self.char_upper, self.character_name} else top[1][0] if len(top) == 2 else 'ONLY_DATA_PRESENT'
        if len(user_char_upper) > 20:
            # Special case of pure narration scene where character is mentioned. Default to Picard.
            user_char_upper = 'PICARD'
        # All speaker chars are single-word so we can be really dumb here
        user_char = user_char_upper[0] + user_char_upper[1:].lower()
        logging.debug('User char for this scene is %s.', user_char_upper)
        conversation: Conversation = Conversation()
        for line in lines:
            formatted_line: str = self.parse_line(line, user_char, user_char_upper)
            conversation.lines.append(formatted_line)
        return conversation

    def parse_line(self, line: str, user_char: str, user_char_upper: str) -> str:
        # Thankfully this source doesn't have many ellipses, but just in case
        line = line.replace("...", "")
        if ':' not in line:
            # Pure narration lines will be assigned to the character.
            line = self.char_upper + ': ' + line
        elif line.split(':')[0] == self.char_upper and len(line) > len(self.longest_line):
            self.longest_line = line
        # All uses of user char to user.
        line = line.replace(user_char, "{{user}}")
        line = line.replace(user_char_upper, "{{user}}")
        # All uses of target char to char
        line = line.replace(self.char_upper, "{{char}}")
        line = line.replace(self.character_name, "{{char}}")
        return line


def link_iterator(url, series_shortname, base_url, episode=None):
    urls = first_table(url).find_all('a')
    for page in urls:
        # http://www.chakoteya.net/NextGen/114.htm
        episode_name = page.text
        if episode is None or episode_name == episode:
            link = base_url + series_shortname + '/' + str(page.get('href'))
            logging.debug('Yielding episode called %s at url %s.', episode_name, link)
            yield link


def first_table(url):
    response = requests.get(url)
    content = response.content
    parser = BeautifulSoup(content, 'html.parser')
    return parser.find('table')


def clean_text(script):
    script_clean = script.strip()
    script_clean = script_clean.replace("\n", "")
    script_clean = script_clean.replace("\r", " ")
    script_clean = script_clean.replace("\r\n", "")
    return script_clean


if __name__ == '__main__':
    config = Config('config.yaml')
    downloader = Downloader(config.settings['CHAKOTEYA'])
    logging.info('Downloading conversations.')
    parsed_convos: [Conversation] = downloader.download()
    update = Update(config.settings['CAI'], parsed_convos)
    with open('output/chakoteya_convos_{}_{}_{}.txt'.format(downloader.char_upper, downloader.primary_series, downloader.suffix), 'a') as convofile:
        convofile.write(update.conversation_texts("\n"))
    with open('output/chakoteya_update_{}_{}_{}.json'.format(downloader.char_upper, downloader.primary_series, downloader.suffix), 'a') as tempfile:
        json.dump(update.format(), tempfile)

