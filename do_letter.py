#!/usr/bin/python3
#encoding=utf8

import argparse
import os
import shutil
from subprocess import Popen, PIPE, STDOUT, run
import sys

settings = {}

################## DEFAULTS ##################

#TODO: Zwei Durchlaeufe, um Mindestanzahl Tags zu pruefen
#TODO: ADDRESSER funktioniert nicht richtig
#TODO: Write GUI
#TODO: Flags automatically
settings['<PHONE_TRIG>']    = r'off'
settings['<EMAIL_TRIG>']    = r'off'
settings['<URL_TRIG>']      = r'off'
settings['<LANGUAGE>']      = r'english'
settings['<DATE>']          = r'\DTMtoday'
settings['<SIGNATURE>']     = r'on'
settings['<REFERENCERIGHT>']= r'off'

##############################################

# Tags that are fed possibly by miltiply lines of the input file
multiliners = ['<RECIPIENT>','<CONTENT>','<FROMADDRESS>','<CC>','<PS>','<ENCLOSED>']

#################### INIT ####################

# Essential
settings['<RECIPIENT>']     = r''
settings['<SUBJECT>']       = r''
settings['<OPENING>']       = r''
settings['<CONTENT>']       = r''
settings['<CLOSING>']       = r''
settings['<FROMNAME>']      = r''
settings['<FROMADDRESS>']   = r''

# Non-essential
settings['<FROMPHONE>']     = r''
settings['<FROMEMAIL>']     = r''
settings['<ADDRESSER>']     = r''
settings['<REF0>']          = r''
settings['<REF1>']          = r''
settings['<REF2>']          = r''
settings['<REF3>']          = r''
settings['<REF4>']          = r''
settings['<REF0C>']         = r''
settings['<REF1C>']         = r''
settings['<REF2C>']         = r''
settings['<REF3C>']         = r''
settings['<REF4C>']         = r''
settings['<SPECIALMAIL>']   = r''
settings['<CC>']            = r''
settings['<PS>']            = r''
settings['<ENCLOSED>']      = r''

# Trigger variable if gui was used
gui = 0

##############################################

content = r'''\documentclass%%
%
%% BASIC SETUP
%
%-----------------------------------------------------------------------
  [fontsize=12pt,%%          fontsize
%-----------------------------------------------------------------------
   paper=a4,%%               paper size
   enlargefirstpage=on,%%
   pagenumber=headcenter,%%  page number (headright, headleft)
%-----------------------------------------------------------------------
   headsepline=on,%%         seperator line
   parskip=half,%%           distance paragraphs
%-----------------------------------------------------------------------
   fromalign=left,%%         position letterhat
   fromphone=<PHONE_TRIG>,%% display telephone number sender
   fromrule=on,%%            hline below sender (aftername, afteraddress)
   fromfax=off,%%            fax
   fromemail=<EMAIL_TRIG>,%% email
   fromurl=<URL_TRIG>,%%     homepage
   addrfield=on,%%           envelope with window
   backaddress=on,%%         backaddress within window
   subject=beforeopening,%%  placement subject
   locfield=narrow,%%        additional sender text box
   foldmarks=on,%%           folding marks
   refline=wide,%%           reference line according to page (type area:narrow, just useful if box not right)
%-----------------------------------------------------------------------
% formatting
   draft=off%%               draft mode
   version=last%%            latest version of KOMA-script
]{scrlttr2}
%-----------------------------------------------------------------------

%
%% PACKAGES
%

\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[<LANGUAGE>]{babel}
\usepackage[useregional]{datetime2}
% TODO: locale
\usepackage[detect-weight=true, detect-family=true, range-phrase = {--},version-1-compatibility,locale=DE]{siunitx}
\usepackage{calc,url,graphicx,ragged2e,eurosym}
\usepackage{tabularx, booktabs, multirow}

% Place references right
<REFERENCERIGHT>

% Euro sign
\DeclareSIUnit{\EUR}{\text{\euro}}

% Enlarge distance of signature
\makeatletter
\@setplength{sigbeforevskip}{3\baselineskip}
\makeatother


%-----------------------------------------------------------------------

%
%% ALTERNATIVE FONTS
%

%\setkomafont{fromname}{\sffamily \LARGE}
%\setkomafont{fromaddress}{\sffamily}%% instead \small
%\setkomafont{pagenumber}{\sffamily}
%\setkomafont{subject}{\mdseries}
%\setkomafont{backaddress}{\mdseries}
%\usepackage{mathpazo}%% Font Palatino
%\setkomafont{fromname}{\LARGE}
%-----------------------------------------------------------------------


\begin{document}
%
% Config
%
\renewcommand{\phonename}{}
\setkomavar{phoneseparator}{}
\renewcommand{\emailname}{}
\setkomavar{emailseparator}{}
\setkomavar{backaddressseparator}{ - }
%-----------------------------------------------------------------------
\setkomavar{fromname}{<FROMNAME>}
\setkomavar{fromaddress}{<FROMADDRESS>}
\setkomavar{fromphone}{<FROMPHONE>}
\setkomavar{fromemail}{<FROMEMAIL>}
<ADDRESSER>
%-----------------------------------------------------------------------
%
%\setkomavar{firsthead}{custom letter head}
%\setkomavar{firstfoot}{custom footer}
%
%-----------------------------------------------------------------------
%
%% References
%
\setkomavar{date}{<DATE>}
\setkomavar{yourmail}[<REF0>]{<REF0C>}
\setkomavar{yourref}[<REF1>]{<REF1C>}
\setkomavar{customer}[<REF2>]{<REF2C>}
\setkomavar{invoice}[<REF3>]{<REF3C>}
\setkomavar{myref}[<REF4>]{<REF4C>}
\setkomavar{specialmail}{<SPECIALMAIL>}

\begin{letter}{<RECIPIENT>}

\setkomavar{subject}{<SUBJECT>}

\opening{<OPENING>}

<CONTENT>

\closing{<CLOSING>}

\ps{<PS>}
\encl{<ENCLOSED>}
<CC>

\end{letter}
\end{document}'''

reference_right =r'''\makeatletter
\@setplength{refvpos}{\useplength{toaddrvpos}}
\@setplength{refhpos}{\paperwidth-8cm}
\@setplength{sigbeforevskip}{3\baselineskip}
\@setplength{refwidth}{6cm}
\@setplength{refaftervskip}{\useplength{toaddrvpos}-2\baselineskip}
\makeatother'''

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
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

################## ARGUMENT PARSER ##################

parser = argparse.ArgumentParser(description='Simple LaTeX letter generator')
parser.add_argument('-of', '--outfile', help="Set filename for the compiled pdf (without extension)", type=str)
parser.add_argument('-if', '--infile', help="Letter file to look for.", type=str)
parser.add_argument('--stdout', help="Print LaTeX source to stdout. No pdf is being created.", default=False, action="store_true")
args = parser.parse_args()

#####################################################

######################## GUI ########################
# Enables the user to work without a terminal
# Comment out this block if undesired.

# Create:
    # infile
    # outfile
    # texfile
    # directory_out

import tkinter as tk
import tkinter.messagebox
import tkinter.filedialog as fd

class display_log(tk.Tk):

    def __init__(self):
        tk.Tk.__init__(self)
        self.title("pdflatex output")
        #self.geometry("500x300+500+200")
        self.make_topmost()
        self.protocol("WM_DELETE_WINDOW", self.on_exit)
        S = tk.Scrollbar(self)
        T = tk.Text(self, height=200, width=200)
        S.pack(side=tk.RIGHT, fill=tk.Y)
        T.pack(side=tk.LEFT, fill=tk.Y)
        S.config(command=T.yview)
        T.config(yscrollcommand=S.set)
        T.insert(tk.END, result[1])

    def on_exit(self):
        """When you click to exit, this function is called"""
        self.destroy()

    def center(self):
        """Centers this Tk window"""
        self.eval('tk::PlaceWindow %s center' % app.winfo_pathname(app.winfo_id()))

    def make_topmost(self):
        """Makes this window the topmost window"""
        self.lift()
        self.attributes("-topmost", 1)
        self.attributes("-topmost", 0)

root = tk.Tk()
root.withdraw()

# show an "Open" dialog box and return the path to the selected file
if not args.infile:
    infile = fd.askopenfilename()
    # If "cancel" was pressed
    if infile == (): sys.exit(0)
    gui = 1

# show an "Save As" dialog box and return the file object of the selected file
if not args.outfile and not args.stdout:
    outfile = fd.asksaveasfile(mode='r')
    # If "cancel" was pressed
    if outfile == None: sys.exit(0)

    # Close outfile again. Pdf will be created by pdflatex
    # But before, get path and filename
    directory_out = os.path.realpath(outfile.name)
    outfile.close()
    outfile = os.path.basename(directory_out)
    directory_out = directory_out.replace('/'+outfile, '')

    # Ensure that contains a .pdf extension
    # Paternalism here ... :(
    # If not .pdf extension
    if not outfile.split('.')[-1] == 'pdf':
        texfile = outfile + '.tex'
        outfile = outfile + '.pdf'
    # If .pdf extension
    else:
        texfile = '.'.join(outfile.split('.')[:-1]) + '.tex'

root.update()
root.destroy()

#####################################################

###################### NON-GUI ######################

# Creates:
    # infile
    # outfile
    # texfile
    # directory_out

#           ######## SET FILENAMES  ########

if args.infile:
    infile = args.infile
    if not os.path.isfile(infile):
        raise ValueError('File {} not found!'.format(infile))

elif gui:pass
else:
    raise ValueError('No input file given! See --help for syntax.')


if args.outfile:

    directory_out = os.getcwd()
    if not os.access(directory_out, os.W_OK | os.X_OK):
        raise RuntimeError('No write permission for {}'.format(directory_out))

    # Ensure that contains a .pdf extension
    # Paternalism here ... :(
    # If not .pdf extension
    if not args.outfile.split('.')[-1] == 'pdf':
        texfile = args.outfile + '.tex'
        outfile = args.outfile + '.pdf'
    # If .pdf extension
    else:
        texfile = '.'.join(args.outfile.split('.')[:-1]) + '.tex'
        outfile = args.outfile

    if os.path.isfile(outfile) and not query_yes_no('{} already exists! Overwrite?'.format(outfile), default='yes'):
        sys.exit(1)

elif args.stdout:pass
elif gui:pass
else:
    outfile = infile + '.pdf'
    print('No output filename given, taking {} now!'.format(outfile))
    if os.path.isfile(outfile):
        raise ValueError('File {} already exists!'.format(outfile))

#####################################################

#           ### CREATE WORKING DIRECTORY ###
directory_temp = '/tmp/temp_{}'.format(os.getpid())

if not os.path.exists(directory_temp):
    os.makedirs(directory_temp)
else: raise RuntimeError('Folder {} already exists. Try again.'.format(directory_temp))

#################### PARSE FILE #####################

with open(infile, 'r') as f:

    # Filter out blank lines
    lines = filter(None, (line.rstrip() for line in f))

    for line in lines:

        if line.startswith('#'):
            skip = 1

        elif line.startswith('%'):
            temp_attr = '<' + line[1:].strip().upper() + '>'
            counter = 0
            skip = 1

#               ####### FLAGS ######
        elif line.startswith('!'):
            temp_attr = line[1:].strip().upper()
            skip = 1

            if temp_attr == 'REFERENCES_RIGHT':
                settings['<REFERENCERIGHT>']= r'on'

            if temp_attr == '!ADDRESSER':
                settings['<SIGNATURE>']= r'off'

        if not skip and not line.strip().startswith('\n'):

#               ##### <SENDER> #####
            if temp_attr == '<SENDER>':

                if counter == 1:
                    settings['<FROMNAME>'] = line.strip()
                else:
                    if settings['<FROMADDRESS>'] == '': linebreak = ''
                    else: linebreak = r'\\'
                    settings['<FROMADDRESS>'] = linebreak.join([settings['<FROMADDRESS>'],line.strip()])

#               #### <PHONE> ###
            elif temp_attr == '<PHONE>':

                if settings['<FROMPHONE>'] == '': linebreak = ''
                else: linebreak = r'\\'
                settings['<FROMPHONE>'] = linebreak.join([settings['<FROMPHONE>'],line.strip()])
                settings['<PHONE_TRIG>'] = 'on'

#               #### <EMAIL> ###
            elif temp_attr == '<EMAIL>':

                if settings['<FROMEMAIL>'] == '': linebreak = ''
                else: linebreak = r'\\'
                settings['<FROMEMAIL>'] = linebreak.join([settings['<FROMEMAIL>'],line.strip()])
                settings['<EMAIL_TRIG>'] = 'on'

#               #### <RECIPIENT> ###
            elif temp_attr == '<RECIPIENT>':

                if settings['<RECIPIENT>'] == '': linebreak = ''
                else: linebreak = r'\\'
                settings['<RECIPIENT>'] = linebreak.join([settings['<RECIPIENT>'],line.strip()])

#               #### <ENCLOSED> ###
            elif temp_attr == '<ENCL>':

                if settings['<ENCLOSED>'] == '': linebreak = ''
                else: linebreak = r'\\'
                settings['<ENCLOSED>'] = linebreak.join([settings['<ENCLOSED>'],line.strip()])

#               ### <REFERENCES> ###
            elif temp_attr == '<REFERENCES>':

                if counter <= 5:

                    if settings['<REF{}>'.format(counter-1)] == '': linebreak = ''
                    else: linebreak = '\n'

                    settings['<REF{}>'.format(counter-1)] = linebreak.join([settings['<REF{}>'.format(counter-1)],line.split('|')[0].strip()])
                    settings['<REF{}C>'.format(counter-1)] = linebreak.join([settings['<REF{}C>'.format(counter-1)],line.split('|')[1].strip()])
                else:
                    raise ValueError('To many References! Just 5 possible!')

#               ####### REST #######
            else:
                if temp_attr not in multiliners:
                    settings[temp_attr] = line.strip()
                else:
                    if settings[temp_attr] == '': linebreak = ''
                    else: linebreak = '\n'
                    settings[temp_attr] = linebreak.join([settings[temp_attr],line.strip()])
        skip = 0
        counter += 1

#####################################################

####################### FLAGS #######################

if settings['<REFERENCERIGHT>'] == 'on':
    settings['<REFERENCERIGHT>'] = reference_right
else: settings['<REFERENCERIGHT>'] = ''

#####################################################

# Replace placeholders
for key in settings:

    if key == "<ADDRESSER>" and not settings[key] == "":

        if settings["<SIGNATURE>"] == 'on':
            content = content.replace(key,r"\setkomavar{signature}{(<ADDRESSER>)}")
        else:
            content = content.replace(key,"\setkomavar{signature}{}")

    if key == "<CC>" and not settings[key] == "":
        content = content.replace(key,r"\cc{<CC>}")

    content = content.replace(key,settings[key])

####################### OUTPUT ######################

#               #### WRITE .TEX ####
if not args.stdout:
    with open('{}/{}'.format(directory_temp,texfile), 'w') as f:
        for line in content:
            f.write(line)

#               ###### COMPILE #####
    log = Popen([
        'pdflatex',
        '-output-directory', directory_temp,
        '-interaction', 'nonstopmode',
        '-halt-on-error',
        '-file-line-error',
        '{}/{}'.format(directory_temp,texfile)],
        stderr=STDOUT,stdout=PIPE)
    log.wait()
    result = log.returncode, log.communicate()[0].decode('cp1252').encode('utf-8')

#           #### COMPILATION FAILED ####
    if result[0] > 0:

#               ##### NO GUI #####
        if not gui:
            print(result[1])
            print('Compilation failed with exit code {}!'.format(result[0]))
            sys.exit(1)

#               ####### GUI #######
        else:
            # Clean up
            if os.path.isdir(directory_temp): run(['rm', '-r', directory_temp])

            # Display log
            display_log().mainloop()

            # Clean up
            if os.path.isdir(directory_temp): run(['rm', '-r', directory_temp])

#           #### COMPILATION SUCCEEDED ####
    else:
        if not os.path.isfile('{}/{}'.format(directory_temp,outfile)):
            raise RuntimeError('Something went wrong! No pdf file created!')

        else:
            # Copy pdf to desired location directory_out
            # Check of existence made above
            shutil.move('{}/{}'.format(directory_temp,outfile),
                        '{}/{}'.format(directory_out,outfile))

        # Clean up
        if os.path.isdir(directory_temp): run(['rm', '-r', directory_temp])

#               ###### STDOUT ######
else:
    print(content)
