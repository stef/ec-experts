#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    This program is free software: you can redistribute it and/or modify it
#    under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public
#    License along with this program. If not, see
#    <http://www.gnu.org/licenses/>.

# (C) 2013 by Stefan Marsiske, <s@ctrlc.hu>

import json, sys, csv, codecs, cStringIO

# loads deduped mappings
def load_mappings(fname):
    mappings={}
    with open(fname,'r') as fd:
        mapping={}
        for i, line in enumerate(fd.readlines()):
            if line.strip().startswith('[x]'):
                # canonical names
                if not mapping == {}:
                    print "mapping not empty", i
                    raise ValueError
                mapping['name']=line.strip()[4:].decode('utf8')
                continue
            if line.strip().startswith('[>]'):
                # aliases
                if not 'name' in mapping:
                    print "no name in mapping", i
                    raise ValueError
                if not 'aliases' in mapping:
                    mapping['aliases'] = []
                mapping['aliases'].append(line.strip()[4:].decode('utf8'))
                continue
            if len(line.strip())>0:
                # parser errors
                print "no leading token", i
                raise ValueError
            if mapping == {}:
                # ignore consecutive empty lines
                continue
            if not len(mapping.get('aliases',[])):
                print "no alias yet", i
                raise ValueError
            for alias in mapping['aliases']:
                mappings[alias]=mapping['name']
            mapping={}
    return mappings

class UnicodeDictWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, fieldnames, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.fieldnames = fieldnames
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writeheader(self):
        self.writer.writerow(self.fieldnames)

    def writerow(self, row):
        self.writer.writerow([row.get(x,'').encode("utf-8") for x in self.fieldnames])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

def transform(fname, maps=None):
    with open(fname, 'r') as fd:
        groups=json.load(fd)
    for grp in groups:
        for grptype in grp.get('group_members',[]):
            for member in grptype.get('members',[]):
                if 'gender' in member:
                    tmp=rep.copy()
                    tmp.update({u'group': grp['name'],
                         u'dg': grp['lead_dg'],
                         u'active_since': grp['active_since'],
                         u'group_type': grptype['name']})
                    if maps: tmp['name']=maps.get(tmp['name'],tmp['name'])
                    yield tmp
                if 'name' in member:
                    for rep in member.get('representatives',[]):
                        tmp=rep.copy()
                        tmp.update({u'group': grp['name'],
                             u'dg': grp['lead_dg'],
                             u'active_since': grp['active_since'],
                             u'group_type': grptype['name'],
                             u'org_name': member['name'],
                             u'org_type': member['type'],
                             })
                        if maps: tmp['org_name']=maps.get(tmp['org_name'],tmp['org_name'])
                        yield tmp
        for subgrp in grp.get('sub_groups',[]):
            for org in subgrp.get('members',[]):
                if 'gender' in org:
                    tmp=rep.copy()
                    tmp.update({u'group': org['name'],
                         u'dg': grp['lead_dg'],
                         u'active_since': grp['active_since'],
                         u'sub_group': subgrp['name']})
                    if maps: tmp['name']=maps.get(tmp['name'],tmp['name'])
                    yield tmp
                for member in org.get('members',[]):
                    for rep in member.get('representatives',[]):
                        tmp=rep.copy()
                        tmp.update({u'group': grp['name'],
                             u'dg': grp['lead_dg'],
                             u'active_since': grp['active_since'],
                             u'group_type': org['name'],
                             u'sub_group': subgrp['name'],
                             u'org_name': member['name'],
                             u'org_type': member['type'],
                             })
                        if maps: tmp['org_name']=maps.get(tmp['org_name'],tmp['org_name'])
                        yield tmp

if __name__ == "__main__":
    #print json.dumps(transform(sys.argv[1])).encode('utf8')
    emaps=None
    if len(sys.argv)>2:
        emaps=load_mappings(sys.argv[2])
    # TODO urls to linkedin http://linkedin.com/in/firstlastname
    # google is better: "https://encrypted.google.com/search?q=%s+european+commission+expert" % name
    fields=[ u'dg', u'org_name', u'status', u'interests_represented', u'sub_group', u'group', u'name', u'gender', u'prof_title', u'org_type', u'prof_profiles', u'nationality', u'group_type', u'active_since']
    w = UnicodeDictWriter(sys.stdout, fields)
    w.writeheader()
    keys=set([])
    for entity in transform(sys.argv[1], emaps):
        #keys.update(entity.keys())
        if 'prof_profiles' in entity:
            entity['prof_profiles']=json.dumps(entity['prof_profiles'])
        if 'interests_represented' in entity:
            entity['interests_represented']=json.dumps(entity['interests_represented'])
        w.writerow(entity)
    #print keys
