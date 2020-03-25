import os.path
import re


def _remove_line_comments(text):
    '''
    Remove line comments from latex code.
    
    Specifically, this takes all text between % and the next newline,
    and replaces it with a single space. This is not done if the percent
    symbol is preceded by an odd number of back slashes. This is because
    for example "\\\% " is not ignored by the latex compiler. It prints
    a percent symbol on a new line.
    '''
    line_comment_regex = re.compile(r'(?<!\\)(?:\\\\)*%.*\n')
    return line_comment_regex.sub(' ', text)


def _remove_accents(text):
    '''
    Replace latex code for diacritics with the empty string.

    Replace letters with diacritics by their non-diacritical
    counterpart. For example, hyperk\"ahler becomes hyperkahler. 
    Moreover, hyperk\"{a}hler becomes hyperkahler too.
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
    '''
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
    This is adapted from remove_command, from arxiv-latex-cleaner.
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
    normalized_commands_regex = "(" \
                                + "|".join(normalized_commands) \
                                + ")"
    command_regex = re.compile(r'\\'
                               + normalized_commands_regex
                               + r'{((?:[^}{]+|{(?:[^}{]+|{[^}{]*})*})*)}')
    return command_regex.sub(r' \2 ', text)


def _remove_environments(text):
    '''
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
    '''
    Remove entire commands.

    More concretely, this remove all commands and their arguments
    (optional or otherwise). That is, "\a*{b}[c]{d}$ is replaced with
    a single space.
    '''
    command_regex = re.compile(r'''
                        \\\w*(\*)?
                        ({(?:[^}{]+|{(?:[^}{]+|{[^}{]*})*})*}
                        |\[(?:[^\]\[]+|\[(?:[^\]\[]+|\[[^\]\[]*\])*\])*\])*
                               ''',
                               re.VERBOSE)
    return command_regex.sub(' ', text)


def _remove_equations(text):
    '''
    Remove inline and display equations.

    Removes inline equations delimited by $ and \(, and removes display
    equations delimited by $$ and \[. Ignores dollar signs preceded by
    a single backslash, as the latex compiler renders that as a dollar
    sign.
    '''
    eqn_regex = re.compile(r'''
                    ((?<!\\)\${1,2}.*?(?<!\\)\${1,2})
                    |((?<!\\)\\\[.*?(?<!\\)\\\])
                    |((?<!\\)\\\(.*?(?<!\\)\\\))
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
    text = _remove_commands(text)
    text = _remove_equations(text)
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

    '''
    Opens the tex file, and normalizes the result.
    '''
    with open(path, 'r') as file:
        text = file.read()
    text = latex_normalizer(text)

    '''        
    Writes the result to a file named original_file_name_normalized.
    '''
    with open(normalized_path, 'a') as normalized_file:
        normalized_file.write(text)

