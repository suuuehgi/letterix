#!/usr/bin/python3.8
#encoding=utf8

import argparse
import configparser
import sys
from pathlib import Path
import tempfile
import shutil
from subprocess import Popen, PIPE, STDOUT, run

latex_source = r'''\documentclass[foldmarks=true,foldmarks=H,
         version=last%
         ]{scrlttr2}
\usepackage[<LANGUAGE>]{babel}
\begin{document}
  \begin{letter}{<RECIPIENT>}
  \opening{<OPENING>}
  \noindent <CONTENT>
  \closing{<CLOSING>}
  \ps{<PS>}
  \setkomavar*{enclseparator}{Anlage}
  \encl{<ENCL>}
  \cc{<CC>}
  \end{letter}
\end{document}'''

char_flag='!'
char_section='%'
char_comment='#'

path_config = Path("~/.config/letterix.conf").expanduser()
#config = configparser.ConfigParser()
#config.sections()
#config.read(path_config)

content = {
    'CONTENT':  ( [], False ),
    'RECIPIENT':( [], False ),
    'SENDER':   ( [], False ),
    'SUBJECT':  ( [], False ),
    'OPENING':  ( [], {'ngerman': r'Sehr geehrte Damen und Herren,'} ),
    'CLOSING':  ( [], {'ngerman': r'Mit freundlichen Gr\"u\ss{}en'} ),
    'ENCL':     ( [], False ),
    'PS':       ( [], False ),
    'CC':       ( [], False ),
    'LANGUAGE': ( [], 'ngerman' )
    }

flags = {
  'REFERENCES_RIGHT': False
}

parser = argparse.ArgumentParser()

parser.add_argument(
          "infile",
          type=lambda p: Path(p).absolute(),
          nargs='?',
          help="Input file to parse",
          )

parser.add_argument(
          '-v', '--verbose',
          action='count',
          default=0,
          help='Increase verbosity'
          )

parser.add_argument(
          '-G', '--generate',
          default=False,
          action="store_true",
          help='Print empty letter config'
          )

parser.add_argument(
          '-f', '--overwrite',
          default=False,
          action="store_true",
          help='Overwrite existing pdf files.'
          )

p = parser.parse_args()

def query_yes_no(question, default="yes"):
  """Ask a yes/no question via input() and return their answer.

  question: str: presented to the user
  default:  str: presumed answer if the user just hits <Enter>

  return: True for "yes", "y", "ye"
          False for "no", "n"
  """
  valid = {"yes": True, "y": True, "ye": True,
           "no": False, "n": False}
  if default is None:
    prompt = " [y/n] "
  elif default == "yes":
    prompt = " [Y/n] "
  elif default == "no":
    prompt = " [y/N] "
  else:
    raise ValueError("invalid default answer: '%s'" % default)

  while True:
    sys.stdout.write(question + prompt)
    choice = input().lower()
    if default is not None and choice == '':
      return valid[default]
    elif choice in valid:
      return valid[choice]
    else:
      sys.stdout.write("Please respond with 'yes' or 'no' "
                       "(or 'y' or 'n').\n")

def next_line(file):
  '''Return next relevant line from file (skip comments)'''
  line = file.readline()
  # EOF
  if line == '': return False
  else: line = line.strip()
  while line.startswith(char_comment) or line == '':
    line = file.readline()
    # EOF
    if line == '': return False
    else: line = line.strip()
  return line

def is_header(line):
  if line.startswith(char_section): return True
  else: return False

def is_flag(line):
  if line.startswith(char_flag): return True
  else: return False

def is_header_or_flag(line):
  if is_header(line) is True or is_flag(line) is True: return True
  else: return False


##### Generate example file to stdout #####
if p.generate is True:

  print(char_comment, 'This is a comment.')
  for key in content:
    print(char_section, key, '\n')
  for key in flags:
    print(char_flag, key, '\n')

  sys.exit(0)


##### Parse infile #####
if p.infile:
  with p.infile.open() as f:
    while (line := next_line(f)):
      if is_header_or_flag(line) is True:
        if is_flag(line) is True:
          flags[line[1:].strip()] = True
        elif is_header(line) is True:
          curr_section = line[1:].strip()
      else:
        content[curr_section][0].append(line)

  ##### Fill source code with keys or defaults #####
  for key in content:
    # Read from input file
    if content[key][0] != []:
      latex_source = latex_source.replace( '<{}>'.format(key), r'\\'.join(content[key][0]) )

    # Not present in input file, read language specific default
    else:
      if key == 'LANGUAGE':
        latex_source = latex_source.replace( '<{}>'.format(key), r'\\'.join(content[key][1]) )
      else:
        if content[key][1] is not False:
          latex_source = latex_source.replace( '<{}>'.format(key), r'\\'.join(content[key][1][content['LANGUAGE']]) )

  ##### Write source to file and compile  #####

  # Create secure tmp folder for compilation
  with tempfile.TemporaryDirectory() as tmpdir:
    # Write to source file
    with Path(tmpdir).joinpath('source.tex').open('w') as file_source:
      file_source.writelines(latex_source)

    # Compile
    log = Popen([
        'pdflatex',
        '-output-directory', tmpdir,
        '-interaction', 'nonstopmode',
        '-halt-on-error',
        '-shell-escape',
        '-file-line-error',
        file_source.name],
        stderr=STDOUT,stdout=PIPE)
    log.wait()
    result = log.returncode, log.communicate()[0].decode('cp1252').encode('utf-8')

    # Compilation failed
    if result[0] > 0:
      print(result[1])
      print('Compilation failed with exit code {}!'.format(result[0]))
      sys.exit(1)

    file_out = Path().cwd().joinpath( '{}.pdf'.format(p.infile.stem) )

    if file_out.exists():
      if p.overwrite is True or query_yes_no('{} already exists! Overwrite?'.format(file_out), default='yes') is True:
        pass
      else:
        sys.exit(0)

    shutil.copy(Path(tmpdir).joinpath('source.pdf'),file_out)
