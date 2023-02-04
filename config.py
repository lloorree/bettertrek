import logging
from typing import Dict

import yaml

SERIES: Dict[str, str] = {
    'The Next Generation': 'NextGen',
    'Deep Space Nine': 'DS9',
    'The Original Series': 'StarTrek',
    'Voyager': 'Voyager',
    'Enterprise': 'Enterprise',
    'Andromeda': 'Andromeda', 
}



class Config:

    def __init__(self, config_filename: str = 'config.yaml'):
        with open(config_filename, 'r') as configuration_file:
            self.settings = yaml.safe_load(configuration_file)
        logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            level=logging.getLevelName(self.settings['logging']), force=True)
