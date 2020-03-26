import os.path
import re


def _matching_paren_pos(string, open_paren='{', close_paren='}'):
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
        raise Exception('leading character ('
                + string[0]
                + ') should be '
                + open_paren)

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


def _remove_line_comments(text):
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


def _remove_accents(text):
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


def _normalize_commands(text):
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
        'text',
        'textit',
        'textrm',
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
    return normalized_commands_regex.sub('',text)


def _remove_environments(text):
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
        r'equation(\*)?',
        r'multline(\*)?',
        r'align(\*)?',
        r'gather(\*)?',
    ]
    for env in removed_env:
        env_regex = re.compile(r'\\begin{'
                               + env
                               + r'}[\s\S]*?\\end{'
                               + env 
                               + r'}')
        text = env_regex.sub('', text)
    return text


def _strip_environments_labels(text):
    '''
    Remove environment delimiters and labels.
    '''
    env_regex = re.compile(r'\\(begin|end|label){.*?}')
    return env_regex.sub(' ', text)


def _remove_commands(text):
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
    '''
    # Matches anything of the form '\word*' and '\word'.
    command_regex = re.compile(r'\\\w*\*?')
    if not command_regex.search(text):
        return text
    paren_dict = {
            '{': '}',
            '[': ']',
            }
    # Split the input at the first occurring command, replacing the
    # command by a space.
    broken_text = command_regex.split(text, maxsplit=1)
    head = broken_text[0] + ' '
    tail = broken_text[1]
    # Iteratively remove anything between between brackets in tail.
    while tail:
        if tail[0] in paren_dict.keys():
            try:
                close_pos = _matching_paren_pos(
                        tail,
                        open_paren=tail[0],
                        close_paren=paren_dict[tail[0]]
                        )
                tail = tail[close_pos + 1:]
            except Exception:
                tail = tail[1:]
        else:
            break
    return head + _remove_commands(tail)
    

def _remove_equations(text):
    '''
    Remove inline and display equations.

    Removes inline equations delimited by $ and \(, and removes display
    equations delimited by $$ and \[. Ignores dollar signs preceded by
    a single backslash, as the latex compiler renders that as a dollar
    sign.
    '''
    eqn_regex = re.compile(r'''
                    ((?<!\\)\${1,2}[\s\S]+?(?<!\\)\${1,2})
                    |((?<!\\)\\\[[\s\S]*?(?<!\\)\\\])
                    |((?<!\\)\\\([\s\S]*?(?<!\\)\\\))
                           ''', 
                           re.VERBOSE)
    return eqn_regex.sub(' ', text)


def _remove_special_characters(text):
    '''
    Replace characters that are not letters or whitespaces by a space.
    '''
    non_alphabet_regex = re.compile(r'[^a-zA-Z\s]')
    return non_alphabet_regex.sub(' ', text)


def _remove_white_space(text):
    '''
    Replace white space (including tabs and newlines) by a single space.
    '''
    return " ".join(text.split())


def latex_normalizer(text):
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
    text = _remove_equations(text)
    text = _remove_commands(text)
    text = _remove_special_characters(text)
    text = _remove_white_space(text)
    return text

def tex_file_normalizer(path):
    '''
    Takes path to original tex file, "original"
    and writes normalized version to "original_normalized"
    in the same directory.
    '''
    abs_path = os.path.realpath(path)
    directory, file_name = os.path.split(abs_path)
    normalized_file_name = file_name + '_normalized'
    normalized_path = directory \
                    + os.path.sep \
                    + normalized_file_name
    while os.path.isfile(normalized_path):
        print('A file with the name '
             + normalized_file_name
             + ' already exists. \n'
             + 'Please enter a new filename (or press <RETURN> to exit): ')
        normalized_file_name = input()
        if normalized_file_name:
            normalized_path = directory \
                            + os.path.sep \
                            + normalized_file_name
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
