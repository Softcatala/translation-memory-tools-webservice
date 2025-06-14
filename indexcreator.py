# -*- encoding: utf-8 -*-
#
# Copyright (c) 2013 Jordi Mas i Hernandez <jmas@softcatala.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import os
import ijson
from whoosh.analysis import StandardAnalyzer
from whoosh.fields import BOOLEAN, TEXT, Schema, STORED, ID
from whoosh.index import create_in
from whoosh.filedb.filestore import RamStorage
from cleanupfilter import CleanUpFilter


class IndexCreator(object):
    def __init__(self, json_file):
        self.dir_name = "indexdir"
        self.writer = None
        self.words = 0
        self.projects = 0
        self.sentences_indexed = 0
        self.sentences = 0
        self.json_file = json_file
        self.project_ids = set()
        self.words_count = 0

    def get_projects_count(self):
        return len(self.project_ids)

    def get_words_count(self):
        return self.words_count

    def process_entries(self):
        with open(self.json_file) as json_fh:
            objects = ijson.items(json_fh, "item")
            for o in objects:
                self.write_entry(
                    o["s"], o["t"], o["c"], o["x"], o["pi"], o["pn"], o["sc"]
                )
                self.sentences += 1

        self.save_index()

    def write_entry(
        self, source, target, comment, context, project_id, project_name, softcatala
    ):
        self.writer.add_document(
            source=source,
            target=target,
            comment=comment,
            context=context,
            project_id=project_id,
            project=project_name,
            softcatala=softcatala,
        )
        if project_id not in self.project_ids:
            self.project_ids.add(project_id)

        string_words = target.split(" ")
        self.words_count += len(string_words)
        self.sentences_indexed += 1

    def save_index(self):
        self.writer.commit()

    def create(self, in_memory=False):
        analyzer = StandardAnalyzer(minsize=1, stoplist=None) | CleanUpFilter()
        schema = Schema(
            source=TEXT(stored=True, analyzer=analyzer),
            target=TEXT(stored=True, analyzer=analyzer),
            comment=STORED,
            context=STORED,
            softcatala=BOOLEAN,
            project_id=ID(stored=True),
            project=STORED,
        )

        if in_memory:
            st = RamStorage()
            ix = st.create_index(schema)
        else:
            if not os.path.exists(self.dir_name):
                os.mkdir(self.dir_name)

            ix = create_in(self.dir_name, schema)

        self.writer = ix.writer()
        return ix
