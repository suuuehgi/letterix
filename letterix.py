#!/usr/bin/python3.8
#encoding=utf8

import argparse
import configparser
import sys
from pathlib import Path
import tempfile
import shutil
from subprocess import Popen, PIPE, STDOUT, run

latex_source = r'''\documentclass[%
        backaddress=on,%%         backaddress within window
        foldmarks=<NOFOLDMARKS>,%
        foldmarks=H,%
        %fromrule=on,%
        version=last%
         ]{scrlttr2}
\usepackage[<LANGUAGE>]{babel}
\begin{document}
  \setkomavar{fromname}{<FROMNAME>}
  \setkomavar{fromaddress}{<FROMADDRESS>}
  \setkomavar{fromphone}{<FROMPHONE>}
  \setkomavar{fromemail}{<FROMEMAIL>}
  \setkomavar{backaddressseparator}{ - }
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
config_lineseparator = ";;"

path_config = Path("~/.config/letterix.conf").expanduser()

class Entry:
  def __init__(self, content=None, default=None, optional=None):
    self.default = False
    self.optional = False
    self.content = []
    if content  is not None: self.content  = content
    if default  is not None: self.default  = default
    if optional is not None: self.optional = optional
  def __getitem__(self, arg):
    return self.content[arg]

content = {
    'CONTENT':    Entry(),
    'RECIPIENT':  Entry(),
    'SENDER':     Entry(),
    'FROMNAME':   Entry(optional=True),
    'FROMADDRESS':Entry(optional=True),
    'SUBJECT':    Entry(),
    'OPENING':    Entry( default={'ngerman': r'Sehr geehrte Damen und Herren,'} ),
    'CLOSING':    Entry( default={'ngerman': r'Mit freundlichen Gr\"u\ss{}en'} ),
    'ENCL':       Entry(),
    'PS':         Entry(),
    'CC':         Entry(),
    'LANGUAGE':   Entry( default='ngerman' )
    }

# Default is always False
flags = {
  'NOFOLDMARKS': Entry( False, default={True:"false", False:"true"})
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

megroup = parser.add_mutually_exclusive_group()

megroup.add_argument(
           '-co', '--configout',
           type=str,
           default=False,
           help='Read infile and write everything as given str in {}'.format(path_config)
           )

megroup.add_argument(
           '-cd', '--configdelete',
           type=str,
           default=False,
           help='Delete key from config \"{}\".'.format(path_config)
           )

megroup.add_argument(
          '-cp', '--configprint',
          default=False,
          action="store_true",
          help='Print config'
          )

parser.add_argument(
          '-G', '--generate',
          default=False,
          nargs='?',
          type=str,
          help='Generate infile from config. Leave empty for all possibilities.'
          )

parser.add_argument(
          '-f', '--overwrite',
          default=False,
          action="store_true",
          help='Overwrite existing pdf files.'
          )

p = parser.parse_args()

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

def derive_defaults_that_require_content(content=content, flags=flags):
  """
  Fill in specific language independent defaults that are dependent on the content
  """
  for key in [k for k,v in content.items() if v.content == []]:
    if key == 'FROMNAME':
      content['FROMNAME'].content.append( content['SENDER'][0] )
    elif key == 'FROMADDRESS':
      content['FROMADDRESS'].content = content['SENDER'][1:]
  return content, flags

def parse_infile(infile, content, flags):
  """
  infile: pathlib.Path object
  content: {'key': class Entry}
  flags: {'key': class Entry}
  """
  def is_header(line):
    if line.startswith(char_section): return True
    else: return False

  def is_flag(line):
    if line.startswith(char_flag): return True
    else: return False

  def is_header_or_flag(line):
    if is_header(line) is True or is_flag(line) is True: return True
    else: return False

  with infile.open() as f:

    while (line := next_line(f)):

      if is_header_or_flag(line) is True:

        # Set flag
        if is_flag(line) is True:
          verbose( "Found flag {}".format(line[1:].strip()), 2)
          flags[line[1:].strip()].content = True

        # Save current active section for below lines ...
        elif is_header(line) is True:
          verbose( "Found section {}".format(line[1:].strip()), 2)
          curr_section = line[1:].strip()

      # ... that is here.
      else:
        content[curr_section].content.append(line)

  return content, flags

def write_to_config(name, config=path_config, content=content, flags=flags):
  """
  name:     str for section in config
  config:   pathlib.Path object
  content:  {'key': class Entry}
  flags:    {'key': class Entry}
  """

  # Read in config
  config = configuration(config)

  if name in config:
    raise RuntimeError("Key \"{}\" is already in \"{}\". Choose different key or remove first using --configdelete".format(
      name, config.path))

  else:
    config[name] = {}

    for key in content:
      # Everything that was specified in infile
      if (value := content[key].content) != []:
        config[name][key] = config_lineseparator.join(value)

    for flag in flags:
      if flags[flag].content is True:
        config[name][flag] = 'True'

    verbose( 'Writing content of \"{}\" using key \"{}\" to \"{}\".'.format(p.infile, p.configout, path_config) )
    config.writeout()

def fill_source(source=latex_source, content=content, flags=flags):
  """
  source: docstring
  content: {'key': class Entry}
  flags: {'key': class Entry}
  """
  for key in content:

    # Take from infile
    if content[key].content != []:
      source = source.replace( '<{}>'.format(key), r'\\'.join(content[key].content) )

    # Not present in infile, read language specific default
    else:
      if key == 'LANGUAGE':
        source = source.replace( '<{}>'.format(key), r'\\'.join(content[key].default) )
      else:
        if content[key].default is not False:
          source = source.replace( '<{}>'.format(key), r'\\'.join(content[key].default[content['LANGUAGE']]) )

  for flag, value in flags.items():
    source = source.replace( '<{}>'.format(flag), r'{}'.format(value.default[value.content]) )

  return source

def compile(source, file_out, overwrite=p.overwrite):
  """
  Compiles the latex source "source" in a temp folder and copies the resulting pdf to "file_out".

  source:   docstring
  file_out: pathlib.Path object
  overwrite:Bool
  """
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

  # Create secure tmp folder for compilation
  with tempfile.TemporaryDirectory() as tmpdir:

    # Write to source file
    with Path(tmpdir).joinpath('source.tex').open('w') as file_source:
      file_source.writelines(source)

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

    if file_out.exists():
      if p.overwrite is True or query_yes_no('{} already exists! Overwrite?'.format(file_out), default='yes') is True:
        pass
      else:
        sys.exit(0)

    shutil.copy(Path(tmpdir).joinpath('source.pdf'),file_out)

def verbose( message, verbosity=1, args=p ):
  '''Print "message" if "verbosity" <= verbosity level  '''
  if args.verbose >= verbosity and message != '':
    print(message)

def delete_from_config( config, section ):
  config = configuration(config)

  if section in config:
    config.remove_section(section)
    config.writeout()
    verbose( 'Removed \"{}\" from config \"{}\".'.format(p.configdelete, path_config) )
  else:
    print("Couldn't find \"{}\" in config \"{}\"".format(
      section, config.path))

def generate_stdout(config, section, content=content, flags=flags, verbosity=p.verbose):
  """
  If section != None, read config file "config" and extract section "section" to content and flags
  config:       pathlib.Path object
  section:      str or None
  content:      {'key': class Entry}
  flags:        {'key': class Entry}
  verbosity:    int
  """

  def readin_config(config, section, content=content, flags=flags):
    """
    Open config file "config" with configparser, extract section "section" and save it to content and flags.

    config:       pathlib.Path object
    section:      str or None
    content:      {'key': class Entry}
    flags:        {'key': class Entry}
    """
    # Read configuration file
    config = configuration(config)

    # Grep desired section section
    section_config = dict( config[section] )
    section_config = {k.upper(): v for k, v in section_config.items()}

    # Split up multiline values via config_lineseparator
    for key in [k for k in section_config if not k == "DEFAULT"]:

      for elem in section_config[key].split(config_lineseparator):

        if key in content:
          content[key].content.append(elem)

        # Actual value of a flag in config file is irrelevant
        # E.g. flagx=blabla will result in True
        elif key in flags:
          flags[key].content = True

    return content, flags

  # Read from config
  if section is not None:
    verbose("Reading \"{}\" from config \"{}\"".format( section, config ))
    content, flags = readin_config(config, section, content, flags)

  # Example comment
  print(char_comment, 'This is a comment.')
  for key, value in content.items():

    # Print header
    if value.optional is True and value.content == []:
      print(char_comment, char_section, key)
    else:
      print(char_section, key)

    # Had been defined in config
    if (entries := content[key].content) != []:
      print( "\n".join(entries) )

    print()

  print( char_comment, "Flags" )
  for flag in flags:
    if flags[flag].content is True:
      print(char_flag, flag, '\n')
    else:
      print(char_comment, char_flag, flag, '\n')


class configuration(configparser.ConfigParser):
  """ConfigParser meta class with add. features for ease of reading"""
  def __init__(self, path=None):
    super().__init__(self)
    if path is not None: self.readin(path)

  def verbose( self, message, verbosity_thresh=1, verbosity_curr=p.verbose ):
    '''Print "message" if "verbosity" <= verbosity level  '''
    if verbosity_curr >= verbosity_thresh and message != '':
      print(message)

  def writeout(self):
    with self.path.open('w') as f:
      self.write(f)

  def readin( self, path = path_config ):
    """path: pathlib.Path object"""
    self.path = path
    if self.path.exists(): self.read(self.path)
    else: self.verbose( 'No config file found. Creating new one: {}'.format(
      self.path) )


##### Generate example file to stdout #####

if p.generate is not False:
  generate_stdout(path_config, p.generate, content, flags)
  sys.exit(0)

###########################################

##### Print config #####

if p.configprint is True:
  print(path_config.read_text())
  sys.exit(0)

########################

##### Remove section from config #####

if p.configdelete is not False:
  delete_from_config(path_config, p.configdelete)
  sys.exit(0)

######################################

if p.infile:

  ##### Parse infile #####

  content, flags = parse_infile( p.infile, content, flags )

  ########################

  ##### Write parsed content to config file #####

  if p.configout is not False:
      write_to_config( p.configout.strip() )
      sys.exit(0)

  ###############################################

  ##### Fill source code with keys or defaults #####

  # Content specifig defaults are derived and hence don't go to the configuration file
  content, flags = derive_defaults_that_require_content( content, flags )
  latex_source = fill_source(latex_source, content, flags)

  ##### Write source to file and compile  #####

  file_out = Path().cwd().joinpath( '{}.pdf'.format(p.infile.stem) )
  compile( latex_source, file_out, p.overwrite )
