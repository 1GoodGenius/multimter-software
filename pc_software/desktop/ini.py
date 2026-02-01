# Simple INI helpers and legacy compatibility module
import configparser

class INIConfig:
    def __init__(self, path):
        self.path = path
        self.parser = configparser.ConfigParser()
        if os.path.exists(path):
            self.parser.read(path)

    def get(self, section, key, fallback=None):
        return self.parser.get(section, key, fallback=fallback)

    def set(self, section, key, value):
        if section not in self.parser.sections():
            self.parser.add_section(section)
        self.parser.set(section, key, value)
        with open(self.path, 'w') as f:
            self.parser.write(f)
