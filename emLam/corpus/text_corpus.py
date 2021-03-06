#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""
Reads a regular text corpus where the relevant units (usually paragraphs)
are separated by newlines.
"""

from __future__ import absolute_import, division, print_function
from contextlib import contextmanager

from emLam.corpus.corpus_base import RawCorpus
from emLam.corpus.hacks import split_for_qt

class TextCorpus(RawCorpus):
    NAME = 'text'
    DESCRIPTION = 'generic newline-separated text corpus'

    def __init__(self, chunk_lines=0, *args, **kwargs):
        super(TextCorpus, self).__init__(*args, **kwargs)
        self.chunk_lines = int(chunk_lines)  # Why do I need this?!

    @contextmanager
    def instream(self, input_file):
        def __instream():
            with super(TextCorpus, self).instream(input_file) as inf:
                lines = []
                for l in inf:
                    line = l.rstrip('\n')
                    if len(line) > 0:
                        lines.append(line)
                        # self.logger.info('lines: {}, chunk_lines: {}, {}, {}, {}'.format(
                        #     len(lines), self.chunk_lines, type(len(lines)),
                        #     type(self.chunk_lines), len(lines) == self.chunk_lines))
                        if len(lines) == self.chunk_lines:
                            for chunk in split_for_qt(u'\n'.join(lines)):
                                yield chunk
                            lines = []
                    elif lines:
                        for chunk in split_for_qt(u'\n'.join(lines)):
                            yield chunk
                        lines = []
                else:
                    if lines:
                        for chunk in split_for_qt(u'\n'.join(lines)):
                            yield chunk
        yield __instream()
