from collections import OrderedDict
import warnings


class Field:
    __categories = [
        'address',
        'annote',
        'author',
        'booktitle',
        'chapter',
        'crossref',
        'doi',
        'edition',
        'editor',
        'howpublished',
        'institution',
        'journal',
        'key',
        'month',
        'note',
        'number',
        'organization',
        'pages',
        'publisher',
        'school',
        'series',
        'title',
        'type',
        'volume',
        'year'
        ]

    def __init__(self, category='', value=''):
        self.category = category
        self.value = value
        self.__is_concatenated = False
        self.__is_number = False
        self.__check_category()
        self.__check_value()

    @staticmethod
    def __check_if_number(value):
        try:
            int(value)
        except ValueError:
            if len(value) > 2:
                try:
                    int(value[1:-1])
                except ValueError:
                    return False
            else:
                return False
        return True

    def is_concatenated(self):
        return self.__is_concatenated

    def is_number(self):
        return self.__is_number

    def __check_opened_closed(self):
        opened_braces = 0
        opened_quotes = 0
        for char in self.value:
            if char == '{':
                opened_braces += 1
            elif char == '}':
                opened_braces -= 1
            elif char == '"':
                opened_quotes += 1
        if opened_braces != 0 or opened_quotes % 2 != 0:
            return False
        return True

    def __check_category(self):
        if self.category.lower() not in self.__categories:
            warnings.warn('Non-standard category tag: "{}"'.format(self.category))

    def __check_value(self):
        if not self.value:
            raise ValueError('The field value cannot be empty.')
        if self.__check_if_number(self.value):
            self.__is_number = True
            return
        if len(self.value) < 2:
            raise ValueError('The field value is shorter than 2 characters and is not a number.')
        if '#' in self.value:
            if r'\#' in self.value:
                if self.value.count('#') != self.value.count(r'\#'):
                    self.__is_concatenated = True
                else:
                    self.__is_concatenated = False
            else:
                self.__is_concatenated = True
        if not self.__is_concatenated:
            if self.value[0] not in ['{', '"']:
                raise ValueError('Wrong opening character.')
            if not self.__check_opened_closed():
                raise ValueError('The numbers of open and close tokens ({, }, ") do not match.')
            if self.value[-1] not in ['}', '"']:
                raise ValueError('Wrong closing character.')

    def get_formatted_value(self):
        if self.__is_number:
            if self.value[0] in ['{', '"'] and self.value[-1] in ['}', '"']:
                return '{{{}}}'.format(self.value[1:-1].strip())
            else:
                return '{{{}}}'.format(self.value)
        if not self.__is_concatenated:
            return '{{{}}}'.format(self.value[1:-1].strip())
        return self.value


class Entry:
    __categories = [
        'article',
        'book',
        'booklet',
        'conference',
        'inbook',
        'incollection',
        'inproceedings',
        'manual',
        'mastersthesis',
        'misc',
        'phdthesis',
        'proceedings',
        'techreport',
        'unpublished'
        ]

    def __init__(self, content=None):
        self.category = None
        self.fields = {}
        if content:
            self.__parse_content(content)

    def __parse_content(self, content):
        opened_idx = content.find('{')
        closed_idx = content.rfind('}')
        self.category = content[:opened_idx].strip()
        inner_content = content[opened_idx + 1:closed_idx].strip()
        comma_idx = inner_content.find(',')
        self.id = inner_content[:comma_idx].strip()
        no_id = inner_content[comma_idx + 1:].strip()
        no_extra_space = ' '.join(no_id.split())
        no_terminal_comma = no_extra_space[:-1] if no_extra_space.endswith(',') else no_extra_space
        split_on_equals = no_terminal_comma.split('=')
        for i in range(len(split_on_equals) - 1):
            token = split_on_equals[i]
            next_token = split_on_equals[i + 1]
            key = token.strip().lower() if i == 0 else token[token.rfind(',') + 1:].strip().lower()
            value = next_token.strip() if i + 2 == len(split_on_equals) else next_token[:next_token.rfind(',')].strip()
            self.fields[key] = Field(key, value)

    def generate_output(self, indent=4):
        output = '@' + self.category.replace('@', '').lower() + '{' + self.id + ',\n'
        max_len = len(max(self.fields.keys(), key=len))
        field_keys = OrderedDict(sorted(self.fields.items())).keys()
        count = 0
        for key in field_keys:
            output += ' ' * indent + key.ljust(max_len + 1) + '= ' + self.fields[key].get_formatted_value()
            if count + 1 < len(field_keys):
                output += ',\n'
            else:
                output += '\n}'
            count += 1
        return output

    def get_category(self):
        return self.category

    def get_categories(self):
        return self.__categories

    def get_field_value(self, category):
        return self.fields[category].value


class Bib:
    def __init__(self):
        self.entries = []

    @staticmethod
    def __read_file(filename):
        try:
            with open(filename, 'r') as fl:
                return fl.read()
        except IOError:
            raise IOError('Error reading the file')

    @staticmethod
    def __write_file(content, filename):
        try:
            with open(filename, 'w+') as fl:
                fl.write(content)
        except IOError:
            raise IOError('Error writing the file')

    def parse_file(self, filename):
        source = self.__read_file(filename)
        self.parse_text(source)

    def parse_text(self, source):
        open_count = 0
        self.entries = []
        closed_idx = 0
        for i in range(len(source)):
            if source[i] == '{':
                open_count += 1
            elif source[i] == '}':
                if open_count == 1:
                    entry = Entry(source[:i + 1]) if len(self.entries) == 0 else Entry(source[closed_idx + 1:i + 1])
                    closed_idx = i
                    self.entries.append(entry)
                open_count -= 1

    def generate_output(self, indent=4):
        output = ''
        for i in range(len(self.entries)):
            output += self.entries[i].generate_output(indent)
            if i + 1 < len(self.entries):
                output += '\n\n'
            else:
                output += '\n'
        return output

    def save_as(self, filename):
        output = self.generate_output()
        self.__write_file(output, filename)
