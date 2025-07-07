from common.log import Logger
from config.ini.read_config_ini import ReadConfigIni
from config.yaml.read_config_yaml import ReadConfigYaml

logger = Logger().get_logger()

class TestRunner(object):
    def __init__(self):
        self.ini_config = ReadConfigIni()
        self.yaml_config = ReadConfigYaml()