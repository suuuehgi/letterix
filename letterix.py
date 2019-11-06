#!/usr/bin/python3
#encoding=utf8

import argparse
import sys
from pathlib import Path

latex_source = r'''\documentclass[foldmarks=true,foldmarks=H,
               version=last%
               ]{scrlttr2}
\usepackage[ngerman]{babel}
\begin{document}
  \begin{letter}{%
                 Petra Mustermann\\
                 Vor dem Berg 1\\
                 12345 Musterhausen%
                }
  \opening{Liebe Vereinsvorsitzende,}
  seit einem Jahr gab es keine Mitgliederversammlung
  mehr. Ich erinnere daran, dass unsere Satzung eine
  solche jedes halbe Jahr vorsieht. Ich fordere den
  Vorstand daher auf, umgehend eine solche in
  Angriff zu nehmen.
  \closing{In Erwartung einer Einladung}
  \ps PS: Ich hoffe, Du nimmst mir das nicht krumm.
  \setkomavar*{enclseparator}{Anlage}
  \encl{Auszug aus der Satzung, in dem die
  Mitgliederversammlungen geregelt sind}
  \cc{Die Vereinsvorsitzende\\Alle Mitglieder}
  \end{letter}
\end{document}'''

parser = argparse.ArgumentParser()

parser.add_argument(
                    "infile",
                    type=lambda p: Path(p).absolute(),
                    nargs='?',
                    help=".ltr file to parse",
                    )

parser.add_argument(
                    '-v',
                    '--verbose',
                    action='count',
                    default=0,
                    help='Increase verbosity'
                    )

p = parser.parse_args()
#parser = argparse.ArgumentParser(description='LaTeX letter generator')
#parser.add_argument( 'file',                 type=str, nargs='?',
#                     help='Room to generate instance for (See --list).' )
#parser.add_argument('-of', '--outfile', help="Set filename for the compiled pdf (without extension)", type=str)
#parser.add_argument('-if', '--infile', help="Letter file to look for.", type=str)
#parser.add_argument('--stdout', help="Print LaTeX source to stdout. No pdf is being created.", default=False, action="store_true")
#args = parser.parse_args()

if p.infile is None:
    sys.exit(0)
else:
    print(p.infile)
