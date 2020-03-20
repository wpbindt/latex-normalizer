import os.path
import re


def _remove_line_comments(text_lines):
    '''
    Removes line comments, but not percent symbols.
    '''
    line_comment_regex = re.compile(r'(?<!\\)(?:\\\\)*%.*$')
    return [line_comment_regex.sub('', x) for x in text_lines]


def _normalize_accents(text):
    '''
    Replaces letters with diacritics by their non-
    diacritical counterpart. For example,
    "hyperk\"ahler" becomes hyperkahler
    '''
    accent_regex = re.compile(r'''\\ \'
                              |\\`
                              |\\\^
                              |\\"
                              |\\~
                              |\\=
                              |\\ \.
                              |\\u\ 
                              |\\v\ 
                              |\\H\ 
                              |\\t\ 
                              |\\c\ 
                              |\\d\ 
                              |\\b\ 
                              |\\k\ ''',
                          re.VERBOSE)
    return accent_regex.sub('', text)


def _normalize_commands(text):
    '''
    Replaces "\command{bla}" with " bla ". Useful
    for things like \emph, and \text. Adapted from
    remove_command from arxiv-latex-cleaner
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
    Removes environments and their content.
    '''
    removed_env = [
        r'comment',
        r'equation\*',
        r'equation',
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
    Removes environment delimiters and labels.
    '''
    env_regex = re.compile(r'\\(begin|end|label){.*?}')
    return env_regex.sub(' ', text)


def latex_normalizer(path):
    '''
    Takes path to original tex file, "original"
    and writes normalized version to "original_normalized"
    in the same directory.
    '''
    abs_path = os.path.realpath(path)
    directory, file_name = os.path.split(abs_path)
    normalized_file_name = file_name + '_normalized'
    normalized_path = directory 
                    + os.path.sep
                    + normalized_file_name
    while os.path.isfile(normalized_path):
        print('A file with the name '
             + normalized_file_name
             + ' already exists. \n'
             + 'Please enter a new filename (or press <RETURN> to exit): ')
        normalized_file_name = input()
        if normalized_file_name:
            normalized_path = directory 
                            + os.path.sep
                            + normalized_file_name
        else:
            return

    with open(path, 'r') as file:
        text_lines = file.readlines()

    text_lines = _remove_line_comments(text_lines)

    '''
    Removes blank lines, concatenates result.
    '''
    text_lines = [x.rstrip() for x in text_lines if x.rstrip()]
    text = "\n".join(text_lines)

    text = _normalize_accents(text)
    text = _normalize_commands(text)
    text = _remove_environments(text)
    text = _strip_environments_labels(text)

    '''        
    Writes result to file named original_file_name_normalized.
    '''
    with open(normalized_path, 'a') as normalized_file:
        normalized_file.write(text)

