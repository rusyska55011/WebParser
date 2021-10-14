import os
from datetime import datetime
from tkinter import Tk, Label, Button, Listbox, Entry, END
from threading import Thread
from time import sleep

from root import TorSession, Parser, File


class DoRequests(TorSession):
    session_requests = 0
    parser = Parser
    file_manager = File('.\\results')

    def __init__(self, tor_path: str):
        super(DoRequests, self).__init__(tor_path)
        self.session = self.receive_session()
        self.start_tor()

    def start(self, domain: str, page: str, rules: [str], num_range: [int, int] = None, step: int = 1) -> str:
        if num_range:
            urls = self.__generate_urls(page, num_range, step)
        else:
            if '($)' in page:
                raise ValueError('Задано "($)" при отсутвующей итерации')
            urls = [page]

        if not rules:
            raise ValueError('Правило для парсинга не задано')

        if domain[-1] != '/':
            domain += '/'

        decoded = [self.__decode_rule(rule) for rule in rules]
        find_scripts, getters = list(), list()
        for find_script, getter in decoded:
            find_scripts.append(find_script)
            getters.append(getter)

        data = list()
        for _ in find_scripts:
            data.append(list())

        save_dirs = self.__create_save_dir(domain, page)
        self.file_manager.create_dirs(save_dirs)
        for url in urls:
            sleep(0.7)
            html = self.parser.get_html(self.session, domain + url)
            for script_num in range(len(find_scripts)):
                data_cell, full_script, this_getter = data[script_num], find_scripts[script_num], getters[script_num]

                if len(full_script) == 1:
                    finded = self.parser.find_elements(html, *full_script[0])
                else:
                    first_step, *another_steps, last_step = full_script
                    finded = self.parser.find_elements(html, *first_step)

                    for script in another_steps:
                        finded_clone = list()
                        for item in finded:
                            finded_clone.append(self.parser.find_elements(str(item), *script))
                        finded = finded_clone.copy()

                    finded = self.parser.find_elements(str(finded), *last_step, get=this_getter)

                self.__write_data(save_dirs, script_num, url, full_script, finded)
                data_cell.append(finded)

            self.__check_refresh_moment()

        return save_dirs

    def __check_refresh_moment(self):
        if self.session_requests > 15:
            self.change_session()
            self.session = self.receive_session()
            self.session_requests = 0
        self.session_requests += 1

    def __write_data(self, dir_path: str, script_num: int, url: list, script: list, finded: list):
        self.file_manager.append(dir_path + f'\\script{script_num + 1}_result.txt', f'\n===== {url=} | {script=} =====\n', *finded)

    @staticmethod
    def __generate_urls(page: str, num_range: [int, int] = None, step: int = 1) -> tuple:
        if not (isinstance(num_range, list) and len(num_range) == 2):
            raise ValueError(f'{num_range=} является некорректным аргументом. Нужен список из 2 чисел!')

        start, finish = num_range
        if not (isinstance(start, int) and isinstance(finish, int)):
            raise ValueError('Значения длинны генерации должны быть целочисленными')

        if finish - start < 0:
            raise KeyError('Длинна не может быть отрицательной')

        if step < 1:
            raise KeyError('Шаг не может быть меньше чем 1')

        page_elements = page.split('($)')
        total = list()
        for page_number in range(num_range[0], num_range[1] + 1, step):
            total_item = str(page_number).join(page_elements)
            total.append(total_item)

        return tuple(total)

    @staticmethod
    def __decode_rule(rule: str) -> [(str, dict, str)]:
        getter = None
        if '~' in rule:
            try:
                rule, getter = rule.split('~')
            except ValueError:
                raise ValueError(f'Кажется, вы поставили лишний знак "~": {rule}')

        nested_tags_list = rule.split('>')
        nested_tags = list()
        for tag_rule in nested_tags_list:
            item_name = tag_rule.strip()
            item_attributes = dict()

            if '(' in tag_rule:
                tag_name, tag_attributes = tag_rule.split('(')
                if not (')' in tag_rule):
                    raise ValueError(f'Кажется, вы не закрыли скобку описания: {tag_rule}')
                tag_attributes = tag_attributes.split(')')[0]

                tag_attributes_list = tag_attributes.split(',')

                for tag_attribute in tag_attributes_list:
                    attribute_name, attribute_property = tag_attribute.split('=')
                    item_attributes[attribute_name.strip()] = attribute_property.strip()
                item_name = tag_name

            nested_tags.append((item_name, item_attributes))
        return nested_tags, getter

    @staticmethod
    def __create_save_dir(domain: str, page: str):
        return domain.split('//')[1].split('/')[0] + '\\' + '\\'.join(page.split('?')[0].split('/')) + '\\' + str(datetime.now().strftime("%d.%m.%Y %H-%M-%S"))


class Interface:
    h1 = dict(font=("Lucida Grande", 26), bg='#fafafa', padx=30)
    h2, h2['font'] = h1.copy(), ("Lucida Grande", 18)
    h3 = dict(font=("Lucida Grande", 13))

    entry_style = dict(font=("Lucida Grande", 12))

    button_style = dict(font=("Lucida Grande", 10), pady=5, padx=5)
    start_button_style, start_button_style['font'] = button_style.copy(), ("Lucida Grande", 15)

    save_folder = '.\\results'

    def __init__(self, size: [int, int], title: str):
        self.root = Tk()

        self.root.wm_title(title)
        self.root.geometry('x'.join(map(lambda item: str(item), size)))
        self.root.minsize(*size)
        self.root.maxsize(*size)
        self.elements()

    def start(self):
        self.root.mainloop()

    def quit(self):
        self.root.destroy()

    def elements(self):
        # Labels
        self.h1_label = Label(self.root, text='Web-парсер v1.0', **self.h1)
        self.h1_label.place(x=105, y=7)

        self.listbox_label = Label(self.root, text='Консоль :', **self.h3)
        self.listbox_label.place(x=10, y=370)

        self.setting_label = Label(self.root, text='Настройки :', **self.h2)
        self.setting_label.place(x=175, y=60)

        self.domain_label = Label(self.root, text='Домен', **self.h3)
        self.domain_label.place(x=10, y=107)

        self.urls_label = Label(self.root, text='Страницы', **self.h3)
        self.urls_label.place(x=10, y=147)

        self.range_label = Label(self.root, text='Генерировать', **self.h3)
        self.range_label.place(x=342, y=148)

        self.rule_label = Label(self.root, text='Алгоритм', **self.h3)
        self.rule_label.place(x=10, y=188)

        #ListBoxes
        self.listbox = Listbox(self.root, width=88, height=11)
        self.listbox.place(x=9, y=411)

        #Entries
        self.domain_entry = Entry(self.root, width=49, **self.entry_style)
        self.domain_entry.place(x=95, y=110)

        self.urls_entry = Entry(self.root, width=27, **self.entry_style)
        self.urls_entry.place(x=95, y=150)

        self.range_entry = Entry(self.root, width=9, **self.entry_style)
        self.range_entry.place(x=455, y=150)

        self.rule_entry = Entry(self.root, width=49, **self.entry_style)
        self.rule_entry.place(x=95, y=190)

        #Buttons
        self.show_folder_button = Button(self.root, text='Все сохранения', command=lambda: Thread(target=self.__open_folder).start(), **self.button_style)
        self.show_folder_button.place(x=422, y=360)

        self.start_button = Button(self.root, text='Начать парсинг', command=lambda: Thread(target=self.__start_parse).start(), **self.start_button_style)
        self.start_button.place(x=193, y=235)

    def __open_folder(self):
        os.startfile(os.path.realpath(self.save_folder))

    def __start_parse(self):
        domain = self.domain_entry.get()
        page = self.urls_entry.get()
        rules = self.rule_entry.get()
        num_range = self.range_entry.get()
        step = 1

        rules = list(map(lambda item: item.strip(), rules.split('&&')))

        try:
            num_range = list(map(lambda item: int(item), num_range.split(':')))
        except ValueError:
            num_range = None
        else:
            if len(num_range) == 3:
                step = num_range[2]
                num_range = num_range[0:2]
            elif len(num_range) == 2:
                pass
            else:
                num_range = None

        self.__append_listbox(f'({datetime.now().strftime("%H:%M:%S")}) Запросы отправляются... Не выключайте программу')
        try:
            dirs = DoRequests('.\\tor\\Tor\\tor.exe').start(domain=domain, page=page, rules=rules, num_range=num_range, step=step)
        except (ValueError, IndexError):
            self.__append_listbox('ОШИБКА ВВОДА ДАННЫХ')
            mistakes = list()
            if not domain:
                mistakes.append('- Вы не ввели domain')
            if not page:
                mistakes.append('- Вы не ввели page')
            if not rules[0]:
                mistakes.append('- Алгоритм не задан')
            if not num_range:
                if '($)' in page:
                    mistakes.append('- Вы задали "($)", но не указали генерацию')

            if isinstance(num_range, (list, tuple)):
                if not((len(num_range) == 2) or (not num_range)):
                    mistakes.append('- Некорректные данные для генератора')
            elif num_range != None:
                mistakes.append('- Некорректные данные для генератора')

            if not mistakes:
                mistakes.append(f'Не удалось получить данные с ресурса {domain}. Проверьте коректность введенных данных')

            self.__append_listbox(*mistakes)

        else:
            self.__append_listbox(f'Файл сохранен по пути: {dirs}')

    def __append_listbox(self, *data: str):
        listbox = self.listbox
        for item in data:
            listbox.insert(END, str(item))


Interface([550, 600], 'WebParser 1.0').start()
