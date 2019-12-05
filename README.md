# letterix
Generate LaTeX scrlttr2 letters

## Usage

`letterix` reads a generic configuration / letter file

```
[...]

% RECIPIENT
Joanna Public
1 Hillside
SAMPLESTEAD

! NOFOLDMARKS

[...]
```
translates it to LaTeX source code and compiles it using `pdflatex`.

There are

```
# Comments

% SECTIONS
Potential
multi-line content
goes here.

# Boolean True/False
! FLAGS
```

They can be changed using:

```python
char_flag='!'
char_section='%'
char_comment='#'
char_cfg_lineseparator = ";;"
char_cfg_kvseparator = "|"
```

```bash
$ letterix --help
usage: letterix [-h] [-v] [-l] [--source] [-co CONFIGOUT | -cd CONFIGDELETE | -cp] [-G [GENERATE]] [-f] [infile]

positional arguments:
  infile                Input file to parse

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Increase verbosity
  -l, --log             Print stdout of pdflatex
  --source              Print generated LaTeX source code
  -co CONFIGOUT, --configout CONFIGOUT
                        Read infile and write everything as given str in "/home/stephan/.config/letterix.conf"
  -cd CONFIGDELETE, --configdelete CONFIGDELETE
                        Delete key from config "/home/stephan/.config/letterix.conf".
  -cp, --configprint    Print config
  -G [GENERATE], --generate [GENERATE]
                        Generate infile from config. Leave empty for all possibilities.
  -f, --overwrite       Overwrite existing pdf files.
```

## Minimal Example

```
%SENDER
John Doe
351 Murfreesboro Pike
Nashville, TN 37210
USA

%RECIPIENT
Joanna Public
1 Hillside
SAMPLESTEAD
WX12 3YZ

%OPENING
Dear Madam Chair,

%CONTENT
The last general meeting was more than a year ago.
I would like to remind you that the articles of our club stipulate that one should be held every six months.
For this reason, I call on the executive board to arrange such a meeting immediately.
```

> ![MWE](./samples/minimal.svg)

## Examples

### Save to config

The config file can be auto-filled from a letter file.
You might remove non-general entries such as `content`.

```bash
# Store sample.ltr as sample within config
$ letterix.py sample.ltr -co sample

# Print config file
$ letterix.py -cp
[DEFAULT]
opening = ngerman|Sehr geehrte Damen und Herren,
closing = ngerman|Mit freundlichen Gr\"u\ss{}en;;english|Best regards,

[sample]
content = The last general meeting was more than a year ago.;;I would like to remind you that the articles of our club stipulate that one should be held every six months.;;For this reason, I call on the executive board to arrange such a meeting immediately.
recipient = Joanna Public;;1 Hillside;;SAMPLESTEAD;;WX12 3YZ
references = Your reference|123.456;;Customer No.|12345;;Your letter from| November 6, 2001
sender = John Doe;;351 Murfreesboro Pike;;Nashville, TN 37210;;USA
subject = Next Meeting
opening = Dear Madam Chair,
closing = Anticipating an invitation
encl = Excerpt from the articles governing general meetings
dencl = Enclosure
ps = PS: I hope you do not take this request amiss.
cc = executive board;;all members
specialmail = Registered Mail
language = english
reflinewide = True
```

### Read from config

You can pre-populate a letter file from the config.
Optional sections are commented out unless they had been read from config.

```bash
# Generate empty letter (in-)file using saved credentials from "sample"
$ letterix.py -G sample
# This is a comment.

# Content of the letter.
% CONTENT
The last general meeting was more than a year ago.
I would like to remind you that the articles of our club stipulate that one should be held every six months.
For this reason, I call on the executive board to arrange such a meeting immediately.

# String to be used as date, default: \today
# % DATE

# Everything that should go to the address window.
% RECIPIENT
Joanna Public
1 Hillside
SAMPLESTEAD
WX12 3YZ

# Up to five references, separated by |
# E.g. "Your reference|12345"
% REFERENCES
Your reference|123.456
Customer No.|12345
Your letter from| November 6, 2001

# Everything that should go to the backaddress of the address window.
% SENDER
John Doe
351 Murfreesboro Pike
Nashville, TN 37210
USA

# Explanation of the signature, default: Frist line of SENDER
# % SIGNATURE

# The subject ...
% SUBJECT
Next Meeting

# Additional boldface title.
# % TITLE

# Complete name of the sender, default: Frist line of SENDER
# % FROMNAME

# Complete address of the sender, default: Everything but the frist line of SENDER
# % FROMADDRESS

# Optional content for the LaTeX preamble.
# % PREAMBLE

# The opening phrase
% OPENING
Dear Madam Chair,

# The closing phrase
% CLOSING
Anticipating an invitation

# List additional attachments
% ENCL
Excerpt from the articles governing general meetings

# Description to be used for ENCL
% DENCL
Enclosure

# Additional textline below the letter.
% PS
PS: I hope you do not take this request amiss.

# Description to be used for CC
# % DCC

# List of recipients getting a copy.
% CC
executive board
all members

# Special notice within the address window.
% SPECIALMAIL
Registered Mail

# The babel language code, default: ngerman
% LANGUAGE
english

### Flags
# Remove the SENDERs information above the address window.
# ! NOFIRSTHEAD

# Remove foldmarks on the left-hand margin.
# ! NOFOLDMARKS

# Don't print a backaddress within the address window.
# ! NOBACKADDRESS

# Use a wide reference line.
! REFLINEWIDE
```

### Compile

```bash
$ letterix.py -G sample > sample2.ltr
$ letterix sample2.ltr
```

<kbd>![Example](./samples/sample.svg)</kbd>
