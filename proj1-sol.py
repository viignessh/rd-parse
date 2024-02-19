import re
import sys
import json

class CustomLexer:
    def __init__(self, input_text):
        self.input_text = input_text
        self.tokens = []

    def tokenize(self):
        patterns = [
            ('BOOLEAN', r'true|false'),
            ('INTEGER', r'\d[\d_]*'),
            ('ATOM', r':[a-zA-Z_]\w*'),
            ('COMMA', r','),
            ('LEFT_BRACE', r'{'),
            ('RIGHT_BRACE', r'}'),
            ('LEFT_BRACKET', r'\['),
            ('RIGHT_BRACKET', r'\]'),
            ('LEFT_PERCENT_BRACE', r'%{'),
            ('RIGHT_PERCENT_BRACE', r'}'),
            ('ARROW', r'=>'),
            ('COMMENT', r'#.*$'),
            ('WHITESPACE', r'\s+'),
        ]

        regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in patterns)
        for match in re.finditer(regex, self.input_text):
            kind = match.lastgroup
            content = match.group()
            if kind not in ['WHITESPACE', 'COMMENT']:
                self.tokens.append((kind, content))

class CustomParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.token_index = 0

    def build_abstract_syntax_tree(self):
        ast = self.construct_sentence()
        return ast

    def construct_sentence(self):
        elements = []
        while self.token_index < len(self.tokens):
            element = self.parse_data()
            if element:
                elements.append(element)
        return elements

    def parse_data(self):
        kind, data = self.tokens[self.token_index]
        self.token_index += 1 
        if kind == 'INTEGER':
            return {'%k': 'int', '%v': int(data.replace('_', ''))}
        elif kind == 'ATOM':
            return {'%k': 'atom', '%v': data}
        elif kind == 'BOOLEAN':
            return {'%k': 'bool', '%v': data == 'true'}
        elif kind in ('LEFT_BRACKET', 'LEFT_BRACE', 'LEFT_PERCENT_BRACE'):
            return getattr(self, f"parse_{kind.lower()}")()

    def parse_left_bracket(self):
        items = []
        while self.tokens[self.token_index][0] != 'RIGHT_BRACKET':
            item = self.parse_data()
            if item:
                items.append(item)
        self.token_index += 1 
        return {'%k': 'list', '%v': items}

    def parse_left_brace(self):
        items = []
        while self.token_index < len(self.tokens) and self.tokens[self.token_index][0] != 'RIGHT_BRACE':
            item = self.parse_data()
            if item:
                items.append(item)
            if self.token_index < len(self.tokens) and self.tokens[self.token_index][0] == 'COMMA':
                self.token_index += 1
                continue
        self.token_index += 1 
        return {'%k': 'tuple', '%v': items}

    def parse_left_percent_brace(self):
        items = []
        while self.tokens[self.token_index][0] != 'RIGHT_PERCENT_BRACE':
            if self.tokens[self.token_index][0] == 'COMMA':
                self.token_index += 1
                continue
            key = self.parse_data()
            if key:
                if key['%k'] != 'atom':
                    if key['%v'] == '#:ignored':
                        self.token_index += 1  
                        continue
                    else:
                        self.error('Expected atom key in map')
                if self.token_index < len(self.tokens) and self.tokens[self.token_index][0] == 'ARROW':
                    self.token_index += 1
                    value = self.parse_data()
                else:
                    value = self.parse_data()
                if not value:
                    self.error('Expected value in map')
                items.append([key, value])
        self.token_index += 1  
        return {'%k': 'map', '%v': items}

def main():
    input_text = sys.stdin.read()
    custom_lexer = CustomLexer(input_text)
    custom_lexer.tokenize()
    custom_parser = CustomParser(custom_lexer.tokens)
    ast_structure = custom_parser.build_abstract_syntax_tree()
    print(json.dumps(ast_structure, indent=2))

if __name__ == "__main__":
    main()
