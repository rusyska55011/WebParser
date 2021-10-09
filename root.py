# TODO: Добавить bs4 в локальные бибилиотеки
import os

from libraries.stem.stem import Signal, SocketError
from libraries.stem.stem.control import Controller
from libraries.requests import requests
from bs4 import BeautifulSoup #from libraries.beautifulsoup4.bs4 import BeautifulSoup
from libraries.subprocess.subprocess import check_output
from libraries.shutil.shutil import copy as copy_file


class TorSession:
    def __init__(self, tor_path: str):
        self.tor_path = tor_path
        self.session = self.__create_session()

    def __create_session(self):
        session = requests.session()
        session.proxies = {
            'http': 'socks5://127.0.0.1:9050',
            'https': 'socks5://127.0.0.1:9050'
        }
        return session

    def receive_session(self) -> requests.session:
        return self.session

    def change_session(self):
        try:
            with Controller.from_port(port=9051) as controller:
                controller.authenticate(password='makeamericagreateagain')
                controller.signal(Signal.NEWNYM)
        except SocketError:
            self.close_tor()
            self.setup_controller()
            self.start_tor()

        self.session = self.__create_session()

    def setup_controller(self):
        config_file_path = os.getenv("APPDATA") + '\\tor'
        torrc_path = '\\'.join(self.tor_path.split('\\')[:-2])
        copy_file(torrc_path + '\\torrc', config_file_path)

    def start_tor(self):
        for line in check_output('tasklist').splitlines():
            try:
                process = line.split()[0]
            except IndexError:
                continue
            else:
                if process == b'tor.exe':
                    self.close_tor()

        os.startfile(self.tor_path)

    def close_tor(self):
        os.system('TASKKILL /F /IM ' + str(self.tor_path.split("\\")[-1]))


class Parser:
    @staticmethod
    def get_html(session: TorSession.receive_session, link: str) -> str:
        return session.get(link).text

    @staticmethod
    def get_img(session: TorSession.receive_session, img_link: str, save_folder: str) -> str:
        img = session.get(img_link)
        img_url = save_folder + img_link.split('/')[-1]
        with open(img_url, 'wb') as file:
            file.write(img.content)
        return img_url

    @staticmethod
    def find_elements(html: str, tag: str, attribute=None, get='') -> [str]:
        def get_text(finded: str) -> [str]:
            total = list()
            for el in finded:
                try:
                    txt = el.get_text().strip()
                    if txt:
                        total.append(txt)
                except KeyError:
                    pass
            return total

        def get_attribute(finded: str, get: str) -> [str]:
            total = list()
            for el in finded:
                try:
                    total.append(el[get])
                except KeyError:
                    pass
            return total

        soup = BeautifulSoup(html, 'html.parser')
        finded = soup.find_all(tag, attribute)

        if get:
            return get_text(finded) if get == 'text' else get_attribute(finded, str(get))
        else:
            return finded

    @staticmethod
    def find_element(html: str, tag: str, attribute=None, get='') -> str:
        soup = BeautifulSoup(html, 'html.parser')
        finded = soup.find(tag, attribute)

        if get:
            return finded.get_text().strip() if get == 'text' else finded[str(get)]
        else:
            return finded
