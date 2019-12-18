#!/usr/bin/python3.8
#encoding=utf8

# TODO: References
import argparse
import configparser
import sys
from pathlib import Path
import tempfile
import shutil
from subprocess import Popen, PIPE, STDOUT, run

latex_source = r'''\documentclass[%
        backaddress=<NOBACKADDRESS>,%%         backaddress within window
        % TODO
        fromalign=<FROMRIGHT>,%
        firsthead=<NOFIRSTHEAD>,%
        foldmarks=<NOFOLDMARKS>,%
        foldmarks=H,%
        % TODO
        fromphone=<FROMPHONE_TRIG>,%
        frommobilephone=<FROMMOBILE_TRIG>,%
        fromemail=<FROMEMAIL_TRIG>,%
        fromfax=<FROMFAX_TRIG>,%
        fromurl=<FROMURL_TRIG>,%
        %fromrule=on,%
        refline=<REFLINEWIDE>,%
        version=last%
         ]{scrlttr2}
\usepackage{microtype}
\usepackage[<LANGUAGE>]{babel}
\usepackage[utf8]{inputenc}
\usepackage[useregional]{datetime2}
\usepackage{blindtext}
\usepackage{calc}
\usepackage[%
    autostyle=true, %
    csdisplay=true, %
    ]{csquotes}
\usepackage{eurosym}
\usepackage{ragged2e}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{phonenumbers}
\usepackage[%
     detect-weight=true,        %
     detect-family=true,        %
     range-phrase = {--},       %
     version-1-compatibility,   %
     locale=DE                  %
     ]{siunitx}
\usepackage{tabularx, booktabs, multirow}
%
% Move quotation marks ahead of block
\makeatletter
\renewcommand\mkblockquote[4]{\leavevmode\llap{\openautoquote\csq@eqgroup}\csq@bqgroup\advance\csq@qlevel\@ne#1#2#3\closeautoquote#4}
\makeatother
%
<PREAMBLE>
<REFERENCESRIGHT>
%
\DeclareSIUnit{\EUR}{\text{\euro}}
%
\begin{document}
  % Distance
  \setplength{foldmarkhpos}{5mm}
  \setkomavar{fromname}{<FROMNAME>}
  \setkomavar{fromaddress}{<FROMADDRESS>}
  \setkomavar{fromphone}<DFROMPHONE>{<FROMPHONE>}
  \setkomavar{frommobilephone}<DFROMMOBILE>{<FROMMOBILE>}
  \setkomavar{fromemail}<DFROMEMAIL>{<FROMEMAIL>}
  \setkomavar{fromfax}<DFROMFAX>{<FROMFAX>}
  \setkomavar{fromurl}<DFROMURL>{<FROMURL>}
  \urlstyle{same}
  \setkomavar{backaddressseparator}{ - }
  \setkomavar{specialmail}{<SPECIALMAIL>}
  %
  \setkomavar{date}{<DATE>}
  \setkomavar{yourref}[<REF0K>]{<REF0V>}
  \setkomavar{yourmail}[<REF1K>]{<REF1V>}
  \setkomavar{myref}[<REF2K>]{<REF2V>}
  \setkomavar{customer}[<REF3K>]{<REF3V>}
  \setkomavar{invoice}[<REF4K>]{<REF4V>}
  %
  \setkomavar{title}{<TITLE>}
  \setkomavar{subject}{<SUBJECT>}
  %
  <SIGNATURE>
  \setplength{sigbeforevskip}{4\baselineskip}
  <DENCL>
  <DCC>
  %
  \begin{letter}{<RECIPIENT>}
  \opening{<OPENING>}
  \noindent <CONTENT>
  \closing{<CLOSING>}
  \ps{<PS>}
  <ENCL>
  <CC>
  \end{letter}
\end{document}'''

references_right = r'''\makeatletter
\@setplength{refvpos}{\useplength{toaddrvpos}}
\@setplength{refhpos}{\paperwidth-14em}
\@setplength{refwidth}{3cm}
\@setplength{refaftervskip}{\useplength{toaddrvpos}-2\baselineskip}
\makeatother'''

##### Seperators #####
char_flag='!'
char_section='%'
char_comment='#'
char_cfg_lineseparator = ";;"
char_cfg_kvseparator = "|"
######################


path_config = Path("~/.config/letterix.conf").expanduser()

class Entry:
  def __init__(self,
               content=None,
               default=None,
               optional=None,
               description=None
              ):
    self.default     = False
    self.description = False
    self.optional    = False
    self.content     = []
    if content      is not None: self.content  = content
    if default      is not None: self.default  = default
    if description  is not None: self.description  = description
    if optional     is not None: self.optional = optional
  def is_optional(self):
    return self.optional
  def is_defined(self):
    return self.content != []
  def __getitem__(self, arg):
    return self.content[arg]

content = {
    'SENDER':     Entry(
        description='Everything that should go to the backaddress of the address window.'),
    'RECIPIENT':  Entry(
        description='Everything that should go to the address window.'),
    'SUBJECT':    Entry(optional=True, default='',
        description='The subject ...'),
    'OPENING':    Entry( default={'ngerman': r'Sehr geehrte Damen und Herren,'},
        description='The opening phrase'),
    'CLOSING':    Entry( default={
        'ngerman': r'Mit freundlichen Gr\"u\ss{}en',
        'english':'Best regards,'},
        description='The closing phrase'),
    'CONTENT':    Entry(
        description='Content of the letter.'),
    'REFERENCES': Entry(optional=True, default='',
        description='Up to five references, separated by {s}\nE.g. "Your reference{s}12345"'.format(s=char_cfg_kvseparator)),
    'DATE':       Entry(optional=True, default=r'\today',
        description='String to be used as date, default: \\today'),
    'SIGNATURE':  Entry(optional=True, default='',
        description='Explanation of the signature, default: Frist line of SENDER'),
    'TITLE':      Entry(optional=True, default='',
        description='Additional boldface title.'),
    'FROMNAME':   Entry(optional=True,
        description='Complete name of the sender, default: Frist line of SENDER'),
    'FROMEMAIL':   Entry(optional=True, default='',
        description='E-Mail addresse of the sender'),
    'DFROMEMAIL':  Entry(optional=True, default='',
        description='Description to be used for FROMEMAIL, you can use the keyword "empty"'),
    'FROMPHONE':  Entry(optional=True, default='',
        description='Phone number of the sender'),
    'DFROMPHONE': Entry(optional=True, default='',
        description='Description to be used for FROMPHONE, you can use the keyword "empty"'),
    'FROMMOBILE': Entry(optional=True, default='',
        description='Mobile phone number of the sender'),
    'DFROMMOBILE':Entry(optional=True, default='',
        description='Description to be used for FROMMOBILE, you can use the keyword "empty"'),
    'FROMFAX':    Entry(optional=True, default='',
        description='Fax number of the sender'),
    'DFROMFAX':   Entry(optional=True, default='',
        description='Description to be used for FROMFAX, you can use the keyword "empty"'),
    'FROMURL':    Entry(optional=True, default='',
        description='URL of the sender website'),
    'DFROMURL':   Entry(optional=True, default='',
        description='Description to be used for FROMURL, you can use the keyword "empty"'),
    'FROMNAME':   Entry(optional=True,
        description='Complete name of the sender, default: Frist line of SENDER'),
    'FROMADDRESS':Entry(optional=True,
        description='Complete address of the sender, default: Everything but the frist line of SENDER'),
    'PREAMBLE':   Entry(optional=True, default='',
        description='Optional content for the LaTeX preamble.'),
    'ENCL':       Entry(optional=True, default='',
        description='List additional attachments'),
    'DENCL':      Entry(optional=True, default='',
        description='Description to be used for ENCL'),
    'PS':         Entry(optional=True, default='',
        description='Additional textline below the letter.'),
    'DCC':        Entry(optional=True, default='',
        description='Description to be used for CC'),
    'CC':         Entry(optional=True, default='',
        description='List of recipients getting a copy.'),
    'SPECIALMAIL':Entry(optional=True, default='',
        description='Special notice within the address window.'),
    'LANGUAGE':   Entry(default='english',
        description='The babel language code, default: ngerman')
    }

# Default is always False
flags = {
  'FROMRIGHT':       Entry(False, default={True:'right',  False:'left'},
      description='Place the senders address information on the right.'),
  'NOFIRSTHEAD':     Entry(False, default={True:"off",   False:"on"},
      description='Remove the SENDERs information above the address window.'),
  'NOFOLDMARKS':     Entry(False, default={True:"false", False:"true"},
      description='Remove foldmarks on the left-hand margin.'),
  'NOBACKADDRESS':   Entry(False, default={True:"off",   False:"on"},
      description='Don\'t print a backaddress within the address window.'),
  'REFERENCESRIGHT': Entry(False, default={True:references_right,  False:''},
      description='Move the references into a block on the right.'),
  'REFLINEWIDE':     Entry(False, default={True:'wide',  False:'narrow'},
      description='Use a wide reference line.')
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
          '-l', '--log',
          default=False,
          action="store_true",
          help='Print stdout of pdflatex'
          )

parser.add_argument(
          '--source',
          default=False,
          action="store_true",
          help='Print generated LaTeX source code'
          )

megroup = parser.add_mutually_exclusive_group()

megroup.add_argument(
           '-co', '--configout',
           type=str,
           default=False,
           help='Read infile and write everything as given str in \"{}\"'.format(path_config)
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
  for key in [k for k,v in content.items() if not v.is_defined() ]:
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

  # Write DEFAULT to config the first time
  trigger_write_default = config.exists()

  # Read in config
  config = configuration(config)

  # Write DEFAULT to config the first time
  if trigger_write_default is False:
    for key, value in content.items():
      if isinstance( value.default, dict ) and key != 'LANGUAGE':
        config['DEFAULT'][key] = char_cfg_lineseparator.join([ char_cfg_kvseparator.join([k,v]) for k,v in value.default.items() ])

  # Entry already in config
  if name in config:
    raise RuntimeError("Key \"{}\" is already in \"{}\". Choose different key or remove first using --configdelete".format(
      name, config.path))

  # Create new config entry
  else:
    config[name] = {}

    for key in content:
      # Everything that was specified in infile
      if (value := content[key]).is_defined():
        config[name][key] = char_cfg_lineseparator.join(value.content)

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
    if content[key].is_defined():

      # Need special treatment
      if key == 'REFERENCES':

        # Iterate over all 5 possible references
        for iii in range(5):

          # Use, if defined ...
          if iii < len(content[key].content):
            K, V = content[key].content[iii].split(char_cfg_kvseparator)
            source = source.replace( '<REF{}K>'.format(iii), K.strip() )
            source = source.replace( '<REF{}V>'.format(iii), V.strip() )

          # ... otherwise fill with default (probably '')
          else:
            source = source.replace( '<REF{}K>'.format(iii), content['REFERENCES'].default )
            source = source.replace( '<REF{}V>'.format(iii), content['REFERENCES'].default )

      elif key in ['FROMFAX', 'FROMEMAIL', 'FROMMOBILE', 'FROMPHONE', 'FROMURL']:
        source = source.replace( '<{}_TRIG>'.format(key), 'on' )

        if key == 'FROMEMAIL':

          source = source.replace( '<{}>'.format(key),
            '\href{{mailto:{mail}}}{{{mail}}}'.format( mail=r'\\'.join(content[key].content) )
            )

        elif key == 'FROMURL':

          source = source.replace( '<{}>'.format(key),
            r'\url{{{}}}'.format( r'\\'.join(content[key].content) )
            )

        elif key in ['FROMMOBILE', 'FROMPHONE', 'FROMFAX']:

          source = source.replace( '<{}>'.format(key),
            '\phonenumber{{{}}}'.format( r'\\'.join(content[key].content) )
            )

        else:
          source = source.replace( '<{}>'.format(key), r'\\'.join(content[key].content) )

      elif key in ['DFROMFAX', 'DFROMEMAIL', 'DFROMMOBILE', 'DFROMPHONE', 'DFROMURL']:

        if content[key].content[0] == 'empty':
          source = source.replace( '<{}>'.format(key), '[]' )
        else:
          source = source.replace( '<{}>'.format(key), '[' + r'\\'.join(content[key].content) + ']' )

      elif key == 'SIGNATURE':

        source = source.replace( '<{}>'.format(key), r'\setkomavar{signature}{<SIGNATURE>}' )
        source = source.replace( '<{}>'.format(key), r'\\'.join(content[key].content) )

      elif key == 'DCC':

        source = source.replace( '<{}>'.format(key), r'\setkomavar*{ccseparator}{<DCC>}' )
        source = source.replace( '<{}>'.format(key), r'\\'.join(content[key].content) )

      elif key == 'CC':

        source = source.replace( '<{}>'.format(key), r'\cc{<CC>}' )
        source = source.replace( '<{}>'.format(key), r'\\'.join(content[key].content) )

      elif key == 'DENCL':

        source = source.replace( '<{}>'.format(key), r'\setkomavar*{enclseparator}{<DENCL>}' )
        source = source.replace( '<{}>'.format(key), r'\\'.join(content[key].content) )

      elif key == 'ENCL':

        source = source.replace( '<{}>'.format(key), r'\encl{<ENCL>}' )
        source = source.replace( '<{}>'.format(key), r'\\'.join(content[key].content) )

      elif key in ['PREAMBLE', 'CONTENT']:

        source = source.replace( '<{}>'.format(key), '\n'.join(content[key].content) )

      # General case
      else:
        source = source.replace( '<{}>'.format(key), r'\\'.join(content[key].content) )

    # Undefined / not present in infile, read language specific default
    else:

      if key == 'LANGUAGE':
        source = source.replace( '<{}>'.format(key), r'{}'.format(content['LANGUAGE'].default) )

      elif key == 'REFERENCES':

        # Iterate over all 5 possible references
        for iii in range(5):

          # fill with default (probably '')
          source = source.replace( '<REF{}K>'.format(iii), content['REFERENCES'].default )
          source = source.replace( '<REF{}V>'.format(iii), content['REFERENCES'].default )

      else:

        # Has language specific defaults
        if isinstance( ( defaults := content[key].default ), dict ):

          # Was LANGUAGE defined?
          if (lang := content['LANGUAGE']).is_defined():

            # LANGUAGE defined AND present among defaults
            if lang[0] in defaults:
              if isinstance( ( d := defaults[lang[0]] ), list ):
                source = source.replace( '<{}>'.format(key), r'\\'.join(d) )
              elif isinstance( d, str ):
                source = source.replace( '<{}>'.format(key), r'{}'.format(d) )

            else:
              raise RuntimeError("\"{}\" was not defined and no default given for language \"{}\"".format(key, lang[0]))

          # LANGUAGE was not defined
          else:

            # Is there a default value for the default language?
            if lang.default in defaults:
              if isinstance( ( d := defaults[lang.default] ), list ):
                source = source.replace( '<{}>'.format(key), r'\\'.join(d) )
              elif isinstance( d, str ):
                source = source.replace( '<{}>'.format(key), r'{}'.format(d) )

            else:
              raise RuntimeError("\"{}\" as well as LANGUAGE was not defined and no default given for fallback language \"{}\"".format(key, lang.default))

        # There is a language independent default str
        elif isinstance( ( default_str := content[key].default ), str ):

          if key in ['FROMFAX', 'FROMEMAIL', 'FROMMOBILE', 'FROMPHONE', 'FROMURL']:
            source = source.replace( '<{}_TRIG>'.format(key), 'off' )

          source = source.replace( '<{}>'.format(key), default_str )

  for flag, value in flags.items():
    source = source.replace( '<{}>'.format(flag), r'{}'.format(value.default[value.content]) )

  return source

def compile(source, file_out, overwrite=p.overwrite, show_log=False):
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

    if show_log is True:
        print( result[1].decode("utf-8") )

    # Compilation failed
    if result[0] > 0:
      print( result[1].decode("utf-8") )
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

    # Read in defaults from config: Config defaults override program defaults
    section_defaults = { k.upper(): v for k, v in dict( config['DEFAULT'] ).items() }
    for key, value in section_defaults.items():
      if key != 'DEFAULT':
        content[key].defaults = dict( [ i.split(char_cfg_kvseparator)
                for i in value.split(char_cfg_lineseparator) ] )

    # Grep desired section section
    section_config = {k.upper(): v for k, v in config.items_wodefault(section) }

    # Split up multiline values via char_cfg_lineseparator
    for key in [k for k in section_config if k != "DEFAULT"]:

      for elem in section_config[key].split(char_cfg_lineseparator):

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
  print()

  for key, value in content.items():

    ### Print headers

    # Print description if available
    if value.description:
      for d in value.description.split('\n'):
        print(char_comment, d)

    # Comment out optional and undefined headers
    if value.is_optional() and not value.is_defined():
      print(char_comment, char_section, key)

    # Print header
    else:
      print(char_section, key)

    # Had been defined in config
    if (value := content[key]).is_defined():
      print( "\n".join(value.content) )

    print()

  print( 3*char_comment, "Flags" )

  for flag in flags:
    if (desc := flags[flag].description):
      print(char_comment, desc)
    if flags[flag].content is True:
      print(char_flag, flag, '\n')
    else:
      print(char_comment, char_flag, flag, '\n')


class configuration(configparser.ConfigParser):
  """ConfigParser meta class with add. features for ease of reading"""
  def __init__(self, path=None):
    super().__init__(self)
    if path is not None: self.readin(path)

  def items_wodefault(self, section, **kwargs):
    try:
      return self._sections[section].items()
    except KeyError:
      raise NoSectionError(section)

  def verbose( self, message, verbosity_thresh=1, verbosity_curr=p.verbose ):
    '''Print "message" if "verbosity" <= verbosity level  '''
    if verbosity_curr >= verbosity_thresh and message != '':
      print(message)

  def writeout(self):
    if 'default' in self['DEFAULT']:
      self['DEFAULT'].pop('default')
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

  if p.source is True:
    print(latex_source)
    sys.exit(0)

  ##### Write source to file and compile  #####

  file_out = Path().cwd().joinpath( '{}.pdf'.format(p.infile.stem) )
  compile( latex_source, file_out, overwrite=p.overwrite, show_log=p.log )
