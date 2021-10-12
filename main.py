from root import TorSession, Parser


class DoRequests(TorSession):
    session_requests = 0
    parser = Parser

    def __init__(self, tor_path: str):
        super(DoRequests, self).__init__(tor_path)
        self.session = self.receive_session()
        self.start_tor()

    def __del__(self):
        self.close_tor()

    def __str__(self):
        return 'Объект тора'

    def start(self, domain: str, page: str, rules: [str], num_range: [int, int] = None, step: int = 1) -> tuple:
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
        for url in urls:
            html = self.parser.get_html(self.session, domain + url)
            for script_num in range(len(find_scripts)):
                full_script, this_getter = find_scripts[script_num], getters[script_num]

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

                data.append(finded)
        return data

    @staticmethod
    def __generate_urls(page: str, num_range: [int, int] = None, step: int = 1) -> tuple:
        if not (isinstance(num_range, list) and len(num_range) == 2):
            raise ValueError(f'{num_range=} является некорректным аргументом. Нужен список из 2 чисел!')

        start, finish = num_range
        if not (isinstance(start, int) and isinstance(finish, int)):
            raise ValueError('Значения длинны генерации должны быть целочисленными')

        if start - finish < 1:
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


requester = DoRequests('.\\tor\\Tor\\tor.exe')
a = requester.start(domain='https://technical.city/',
                    page='cpu/rating?pg=($)&sort_field=default&sort_order=up',
                    rules=['div(class=block)>tbody>tr>td'],
                           #'div(class=block)>tbody>tr>td(style=text-align:left)>a~href'],
                    num_range=[3, 0])
print(len(a))
for i in a:
    print(i)


