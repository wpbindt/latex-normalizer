import os.path
import re
from typing import List, Tuple


def _matching_paren_pos(string: str, open_paren: str='{',
                        close_paren: str='}') -> int:
    r'''
    Find the position of the parenthesis closing the one a string
    starts with.

    >>> _matching_paren_pos('{{a}{}}b')
    6

    >>> _matching_paren_pos('a')
    Traceback (most recent call last):
        ...
    Exception: leading character (a) should be {

    >>> _matching_paren_pos('{{}')
    Traceback (most recent call last):
        ...
    Exception: unmatched parenthesis
    '''
    if string[0] != open_paren:
        raise Exception(f'leading character ({string[0]}) '
                        f'should be {open_paren}')

    # Iterating over the string, put the opening brackets encountered
    # in a stack, and pop it every time a closing bracket occurs.
    # When the stack is empty, return the position.
    open_parens = []
    for pos, char in enumerate(string):
        if char == open_paren:
            open_parens.append(char)
        elif char == close_paren:
            open_parens.pop()
            if not open_parens:
                return pos
    raise Exception('unmatched parenthesis')


def _matching_brackets_digram(text: str, open_bracket: str=r'\(',
                              close_bracket: str=r'\)'
                              ) -> List[Tuple[int, int]]:
    r'''
    Match two-character brackets in a string, and return lists of pairs
    of positions of the matching brackets, indexed in a dictionary by
    bracket type.

    Positional arguments:
    text -- The string where we want to find the matching brackets.
    brackets -- Dictionary whose keys are the closing brackets, and
    whose values are the opening brackets.

    >>> _matching_brackets_digram('abcd')
    []

    >>> _matching_brackets_digram(r'\( \)')
    [(0, 4)]

    >>> _matching_brackets_digram(r'\(\(\)\)')
    [(2, 5), (0, 7)]

    >>> _matching_brackets_digram(r'\(\(\(\)')
    Traceback (most recent call last):
        ...
    Exception: brackets are unbalanced

    >>> _matching_brackets_digram(r'\(')
    Traceback (most recent call last):
        ...
    Exception: brackets are unbalanced

    >>> _matching_brackets_digram(r'\)')
    Traceback (most recent call last):
        ...
    Exception: brackets are unbalanced
    '''
    opening_brackets = []
    matches = []
    digrams = [a + b for a, b in zip(text, text[1:])]
    for pos, digram in enumerate(digrams):
        if digram == open_bracket:
            opening_brackets.append((digram, pos))
        elif digram == close_bracket:
            try:
                open_bracket, open_pos = opening_brackets.pop()
                # pos is the position of the first character of the
                # closing bracket, but we want to include both
                # of its characters in the interval, so we append
                # pos + 1.
                matches.append((open_pos, pos + 1))
            except IndexError:
                raise Exception('brackets are unbalanced')
    if opening_brackets:
        raise Exception('brackets are unbalanced')
    else:
        return matches


def _interval_to_indices(interval: Tuple[int, int]) -> List[int]:
    '''
    Takes an interval, and returns the set of indices that the interval
    comprises, right and left inclusive.

    >>> _interval_to_indices((1,1))
    [1]

    >>> _interval_to_indices((3,5))
    [3, 4, 5]

    >>> _interval_to_indices((3,2))
    Traceback (most recent call last):
        ...
    Exception: interval out of order
    '''
    x, y = interval
    if y < x:
        raise Exception('interval out of order')
    else:
        return list(range(x, y+1))


def _excise_intervals(text: str, intervals: List[Tuple[int, int]]) -> str:
    r'''
    Takes a string and a list of intervals, and returns the string with
    these intervals replaced by single white spaces.

    >>> _excise_intervals('hey', [])
    'hey'

    >>> _excise_intervals('Remove this and nothing else', [(7, 10)])
    'Remove   and nothing else'

    >>> _excise_intervals('Remove this and nothing else', [(7, 8), (9, 10)])
    'Remove    and nothing else'

    >>> _excise_intervals('Remove this and nothing else', [(7, 10), (8, 9)])
    'Remove   and nothing else'

    >>> _excise_intervals('Remove this and nothing else', [(7, 9), (8, 10)])
    Traceback (most recent call last):
        ...
    Exception: non-trivially overlapping intervals

    >>> _excise_intervals('hey', [(3, 4)])
    Traceback (most recent call last):
        ...
    Exception: interval out of bounds

    >>> _excise_intervals('hey', [(2, 3)])
    Traceback (most recent call last):
        ...
    Exception: interval out of bounds
    '''
    # Store the indices spanned by the intervals in a list ii_list of
    # tuples of the form (index, indicator), where indicator is 1 if 
    # index does not occur as a non-first element of an interval. That
    # is, if we have intervals (1,3), (2,3), then ii_list will consist
    # of (1,1), (2,0), (3,0), not (1,1), (2,1), (3,0).
    ii_list = []
    indices_list = []
    for start, end in sorted(intervals):
        if start in indices_list:
            if end in indices_list:
                continue
            else:
                raise Exception('non-trivially overlapping intervals')
        else:
            indicators = [1] + [0] * (end - start)
            indices = _interval_to_indices((start, end))
            indices_indicators = list(zip(indices, indicators))
            indices_list = indices_list + indices
            ii_list = ii_list + indices_indicators

    # Reverse the indices because removal by index is not a commutative
    # operation.
    ii_list = sorted(ii_list, reverse=True)
    # Remove the indices from the string, taking care to replace it by
    # a single space if the index does not occur as a non-first
    # character in the intervals.
    if intervals:
        if max(indices_list) > len(text) - 1:
            raise Exception('interval out of bounds')
        for index, indicator in ii_list:
            if indicator:
                text = text[:index] + ' ' + text[index + 1:]
            else:
                text = text[:index] + text[index + 1:]
    return text


def _remove_line_comments(text: str) -> str:
    r'''
    Remove line comments from latex code.

    Specifically, this takes all text between % and the next newline,
    and replaces it with a single space. This is not done if the percent
    symbol is preceded by an odd number of back slashes. This is because
    for example "\\\% " is not ignored by the latex compiler. It prints
    a percent symbol on a new line.

    >>> _remove_line_comments('Hi, I do not contain any comments. \n')
    'Hi, I do not contain any comments. \n'

    >>> _remove_line_comments('Hi, I do. %comment\nNext line.')
    'Hi, I do.  Next line.'

    >>> _remove_line_comments('Me too. \\\\% comment\n')
    'Me too. \\\\ '

    >>> _remove_line_comments('0\\%\n')
    '0\\%\n'
    '''
    line_comment_regex = re.compile(r'(?<!\\)((?:\\\\)*)%.*\n')
    return line_comment_regex.sub(r'\1 ', text)


def _remove_accents(text: str) -> str:
    r'''
    Replace latex code for diacritics with the empty string.

    Replace letters with diacritics by their non-diacritical
    counterpart. For example, hyperk\"ahler becomes hyperkahler.
    Moreover, hyperk\"{a}hler becomes hyperkahler too.

    >>> _remove_accents('Nothing happens to me')
    'Nothing happens to me'

    >>> _remove_accents('hyperk\\"ahler is hyperk\\"{a}hler')
    'hyperkahler is hyperkahler'

    >>> _remove_accents('\\c Ca va? \\c{C}a va')
    'Ca va? Ca va'
    '''
    letters = [
            'u',
            'v',
            'H',
            't',
            'c',
            'd',
            'b',
            'k',
            ]
    letter_accent_regex = re.compile(
            r'\\(?:'
            + '|'.join(letters)
            + r')(?:\ |{(\w{1,2})})'
            )
    non_letters = [
            r'\'',
            r'`',
            r'\^',
            r'"',
            r'~',
            r'=',
            r'\.',
            ]
    non_letter_accent_regex = re.compile(
            r'\\(?:'
            + '|'.join(non_letters)
            + r')(?:{(\w)})?'
            )
    output = letter_accent_regex.sub(r'\1', text)
    output = non_letter_accent_regex.sub(r'\1', output)
    return output


def _normalize_commands(text: str) -> str:
    r'''
    Replace a list of specified latex commands with their arguments.

    More concretely, this function replaces "\command{argument}" with
    " argument ", where command is a command from the list
        subsubsection,
        subsection,
        section,
        chapter,
        title,
        author,
        footnote,
        emph,
        text,
        textit,
        textrm.
    If no argument is passed to the command, the command is replaced
    with an empty string.

    >>> _normalize_commands('\shouldnt{change}')
    '\\shouldnt{change}'

    >>> _normalize_commands('\chapter{On{e}')
    ' On{e}'

    >>> _normalize_commands('\chapter{Hyperk\\"{a}hlers}')
    ' Hyperk\\"{a}hlers '

    >>> _normalize_commands('\chapter{One} \section{two}')
    ' One   two '

    >>> _normalize_commands('\sectionheader')
    '\\sectionheader'
    '''
    normalized_commands = [
        'subsubsection',
        'subsection',
        'section',
        'chapter',
        'title',
        'author',
        'footnote',
        'emph',
    ]
    normalized_commands_regex = re.compile(
        r'\\('
        + '|'.join(normalized_commands)
        + ')(?={)'
        )
    matches = normalized_commands_regex.finditer(text)
    for match in matches:
        _, open_pos = match.span()
        try:
            # Try to find the bracket matching the bracket at the end
            # of the command. If successful, replace both by a single
            # space.
            delta = _matching_paren_pos(text[open_pos:])
            close_pos = open_pos + delta
            text = text[:open_pos] \
                + ' ' \
                + text[open_pos + 1:close_pos] \
                + ' ' \
                + text[close_pos + 1:]
        except Exception:
            # if the opening bracket is unmatched, only have to replace
            # the opening bracket
            text = text[:open_pos] \
                    + ' ' \
                    + text[open_pos + 1:]

    normalized_commands_regex = re.compile(
        r'\\('
        + '|'.join(normalized_commands)
        + ')(?= )'
        )
    return normalized_commands_regex.sub('', text)


def _remove_environments(text: str) -> str:
    r'''
    Remove a specified list of latex environments.

    Specifically, replace "\begin{environment} contents
    \end{environment}" with the empty string, where environment is
    an environment on the list
        comment,
        figure,
        tikzpicture,
        equation(*),
        multline(*),
        align(*),
        gather(*).
    '''
    removed_env = [
        r'comment',
        r'figure',
        r'tikzpicture',
        r'equation\*?',
        r'multline\*?',
        r'align\*?',
        r'gather\*?',
    ]
    for env in removed_env:
        env_regex = re.compile(r'\\begin{'
                               + env
                               + r'}[\s\S]*?\\end{'
                               + env
                               + r'}')
        text = env_regex.sub('', text)
    return text


def _strip_environments_labels(text: str) -> str:
    '''
    Remove environment delimiters and labels.
    '''
    env_regex = re.compile(r'\\(begin|end|label){.*?}')
    return env_regex.sub(' ', text)


def _remove_commands(text: str) -> str:
    r'''
    Remove entire commands.

    More concretely, this remove all commands and their arguments
    (optional or otherwise). That is, "\a*{b}[c]{d}$ is replaced with
    a single space.

    >>> _remove_commands('abc')
    'abc'

    >>> _remove_commands('\command*{baba}[caba]{daba}a')
    ' a'

    >>> _remove_commands('\command')
    ' '

    >>> _remove_commands('\command[option]')
    ' '

    >>> _remove_commands('\command{argument')
    ' argument'

    >>> _remove_commands('a \command and \\another{one}')
    'a   and  '

    >>> _remove_commands('\@command')
    ' '
    '''
    # The values and keys of this dictionary will be used as input for
    # _matching_paren_pos later.
    paren_dict = {
            '{': '}',
            '[': ']',
            }
    # The next regex matches anything of the form '\word*' and '\word'.
    command_regex = re.compile(r'\\[\w@]*\*?')

    head = ''
    tail = text
    while tail:
        # Split the tail at the first occurring command, replacing the
        # command by a space. Should only do one split at a time,
        # because input like "\command{\command}" is possible.
        broken_text = command_regex.split(tail, maxsplit=1)
        if len(broken_text) == 1:
            head = head + broken_text[0]
            break
        head = head + broken_text[0] + ' '
        tail = broken_text[1]
        # Iteratively remove everything between consecutive brackets in
        # tail.
        while tail:
            if tail[0] in paren_dict.keys():
                try:
                    close_pos = _matching_paren_pos(
                            tail,
                            open_paren=tail[0],
                            close_paren=paren_dict[tail[0]]
                            )
                    tail = tail[close_pos + 1:]
                # If the opening bracket is unmatched, an exception
                # is raised and we only remove the opening bracket,
                # and we go back to searching for a command.
                except Exception:
                    tail = tail[1:]
                    break
        # If the leading character of tail is not an opening bracket,
        # go back to searching for a command.
            else:
                break
    return head


def _remove_bracket_equations(text: str) -> str:
    r'''
    Remove inline and display equations delimited by \( and \[.

    >>> _remove_bracket_equations('abc')
    'abc'

    >>> _remove_bracket_equations(r'These too: \(1 + 1\)')
    'These too:  '

    >>> _remove_bracket_equations(r'This is an equation: \[1 + 1 = \$\]')
    'This is an equation:  '

    >>> _remove_bracket_equations(r'This is not: \(1 \[+\] 1\)')
    'This is not:  '

    >>> _remove_bracket_equations(r'This is not: \[1 \(+\) 1\]')
    'This is not:  '
    '''
    round_bracket_intervals = _matching_brackets_digram(text)
    square_bracket_intervals = _matching_brackets_digram(text,
                                                         open_bracket=r'\[',
                                                         close_bracket=r'\]')
    intervals_to_remove = round_bracket_intervals + square_bracket_intervals
    return _excise_intervals(text, intervals_to_remove)


def _remove_dollar_equations(text: str) -> str:
    r'''
    Remove inline and display equations delimited by $ or $$.

    >>> _remove_dollar_equations(r'No equation, \$3.50, \$2')
    'No equation, \\$3.50, \\$2'

    >>> _remove_dollar_equations('An equation $1 + 1\$$ should go')
    'An equation   should go'

    >>> _remove_dollar_equations('Display equations $$\n 1 + 1 \n $$ too')
    'Display equations   too'

    >>> _remove_dollar_equations('$ back $$ to $$ back $')
    '   '

    >>> _remove_dollar_equations('$$ $$$$ $$')
    '  '
    
    >>> _remove_dollar_equations(r'$$ \text{$nested$} $$')
    Traceback (most recent call last):
        ...
    Exception: LaTeX syntax error

    >>> _remove_dollar_equations('$ back $$$ to back $$')
    '  '
    '''
    # First check if the latex syntax is valid. Up to 4 dollar signs
    # in a row are allowed, 5 if the first is preceded by and odd
    # number of backslashes (compiling to a bunch of line breaks and a
    # dollar sign).
    bad_syntax_regex = re.compile(r'(?<!\\)(?:\\\\)*\${5}')
    if bad_syntax_regex.search(text):
        raise Exception('LaTeX syntax error')
    # Store the starting positions of delimiters of the form $, $$,
    # $$$, $$$$, and their lengths in tokens.
    token_regex = re.compile(r'(?<!\\)(?:\\\\)*(\${1,4})')
    spans = [match.span() for match in token_regex.finditer(text)]
    tokens = [(start, finish - start) for start, finish in spans]
    # Going from right to left through tokens, match each token to a
    # substring of the next token of equal length. Store the resulting
    # interval in intervals, and append the remainder of the next token
    # to tokens. If this is not possible, raise a syntax error. The
    # correctness of this algorithm relies on there not being any
    # nested equations. For example, it does not distinguish between
    # '$1 + \text{$1 = 2$ and } 1 + 2 = 3$' and the equations
    # '$1 + 1 = 2$ and $1 + 2 = 3$'.
    intervals = []
    while tokens:
        try:
            close_pos, close_len = tokens.pop()
            open_pos, open_len = tokens.pop()
        except:
            raise Exception('LaTeX syntax error')
        if close_len == 3:
            raise Exception('LaTeX syntax error')
        elif close_len == open_len:
            intervals.append((open_pos, close_pos + close_len - 1))
        elif open_len > close_len:
            remainder = open_len - close_len
            intervals.append((open_pos + remainder, close_pos + close_len - 1))
            tokens.append((open_pos, remainder))
        else:
            raise Exception('LaTeX syntax error')
    return _excise_intervals(text, intervals)


def _remove_equations(text: str) -> str:
    r'''
    Remove inline and display equations.

    Removes inline equations delimited by $ and \(, and removes display
    equations delimited by $$ and \[. Ignores dollar signs preceded by
    a single backslash, as the latex compiler renders that as a dollar
    sign.

    >>> _remove_equations(r'No equation, \$3.50, \$2')
    'No equation, \\$3.50, \\$2'

    >>> _remove_equations('An equation $1 + 1\$$ should go')
    'An equation   should go'

    >>> _remove_equations('Display equations $$\n 1 + 1 \n $$ too')
    'Display equations   too'

    >>> _remove_equations(r'These too: \(1 + 1\)')
    'These too:  '

    >>> _remove_equations(r'This is an actual equation: \[1 + 1 = \$\]')
    'This is an actual equation:  '

    >>> _remove_equations('$ back $$ to $$ back $')
    '   '

    >>> _remove_equations(r'$$ \text{$nested$} $$')
    Traceback (most recent call last):
        ...
    Exception: LaTeX syntax error

    >>> _remove_equations('$ back $$$ to back $$')
    '  '
    '''
    text = _remove_dollar_equations(text)
    text = _remove_bracket_equations(text)
    return text


def _remove_special_characters(text: str) -> str:
    '''
    Replace characters that are not letters or whitespaces by a space.
    '''
    non_alphabet_regex = re.compile(r'[^a-zA-Z\s]')
    return non_alphabet_regex.sub(' ', text)


def _remove_white_space(text: str) -> str:
    '''
    Replace white space (including tabs and newlines) by a single space.
    '''
    return " ".join(text.split())


def latex_normalizer(text: str) -> str:
    '''
    Take a string containing latex syntax,
    and returns a string stripped of that
    syntax. For example,
    "\begin{document} Hi! \end{document}"
    becomes "Hi"
    '''
    text = _remove_line_comments(text)
    text = _remove_accents(text)
    text = _normalize_commands(text)
    text = _remove_environments(text)
    text = _strip_environments_labels(text)
    text = _remove_commands(text)
    text = _remove_equations(text)
    text = _remove_special_characters(text)
    text = _remove_white_space(text)
    return text


def tex_file_normalizer(path: str) -> None:
    '''
    Takes path to original tex file, "original"
    and writes normalized version to "original_normalized"
    in the same directory.
    '''
    abs_path = os.path.realpath(path)
    directory, file_name = os.path.split(abs_path)
    normalized_file_name = f'{file_name}_normalized'
    normalized_path = directory + os.path.sep + normalized_file_name
    while os.path.isfile(normalized_path):
        print(f'A file with the name {normalized_file_name} already exists. \n'
              'Please enter a new filename (or press <RETURN> to exit): ')
        normalized_file_name = input()
        if normalized_file_name:
            normalized_path = directory + os.path.sep + normalized_file_name
        else:
            return

    # Opens the tex file, and normalizes the result.
    with open(path, 'r') as file:
        text = file.read()
    text = latex_normalizer(text)

    # Writes the result to a file named original_file_name_normalized.
    with open(normalized_path, 'a') as normalized_file:
        normalized_file.write(text)


if __name__ == "__main__":
    import doctest
    doctest.testmod()

