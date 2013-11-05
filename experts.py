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
debug = False

# loads deduped mappings
def load_mappings(fname):
    mappings={}
    with open(fname,'r') as fd:
        mapping={}
        for i, line in enumerate(fd.readlines()):
            if line.strip().startswith('[x]'):
                # canonical names
                if not mapping == {}:
                    print >>sys.stderr, "mapping not empty", i
                    raise ValueError
                mapping['name']=line.strip()[4:].decode('utf8')
                continue
            if line.strip().startswith('[>]'):
                # aliases
                if not 'name' in mapping:
                    print >>sys.stderr, "no name in mapping", i
                    raise ValueError
                if not 'aliases' in mapping:
                    mapping['aliases'] = []
                mapping['aliases'].append(line.strip()[4:].decode('utf8'))
                continue
            if len(line.strip())>0:
                # parser errors
                print >>sys.stderr, "no leading token", i
                raise ValueError
            if mapping == {}:
                # ignore consecutive empty lines
                continue
            if not len(mapping.get('aliases',[])):
                print >>sys.stderr, "no alias yet", i
                raise ValueError
            for alias in mapping['aliases']:
                mappings[alias]=mapping['name']
            mapping={}
        for alias in mapping.get('aliases',[]):
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
        self.writer.writerow([(row.get(x,'') or '').encode("utf-8") for x in self.fieldnames])
        #self.writer.writerow([(row.get(x,'') or '') for x in self.fieldnames])
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
                    tmp=member.copy()
                    tmp.update({u'group': grp['name'],
                                u'dg': grp['lead_dg'],
                                u'id': grp['id'],
                                u'active_since': grp['active_since'],
                                u'group_type': grptype['name']})
                    if maps:
                        if debug: print >>sys.stderr, repr(tmp['name'])
                        if debug: print >>sys.stderr, repr(maps.get(tmp['name']))
                        tmp['name']=maps.get(tmp['name'],tmp['name']).strip()
                        if debug: print >>sys.stderr, repr(tmp['name'])
                        if debug: print >>sys.stderr, 'asdf'
                    yield tmp
                elif 'name' in member:
                    for rep in member.get('representatives',[]):
                        tmp=rep.copy()
                        tmp.update({u'group': grp['name'],
                                    u'dg': grp['lead_dg'],
                                    u'id': grp['id'],
                                    u'active_since': grp['active_since'],
                                    u'group_type': grptype['name'],
                                    u'org_name': member['name'],
                                    u'org_type': member['type'],
                                    })
                        if maps:
                            if debug: print >>sys.stderr, repr(tmp['org_name'])
                            if debug: print >>sys.stderr, repr(maps.get(tmp['org_name']))
                            tmp['org_name']=maps.get(tmp['org_name'],tmp['org_name']).strip()
                            tmp['name']=maps.get(tmp['name'],tmp['name']).strip()
                            if debug: print >>sys.stderr, repr(tmp['org_name'])
                            if debug: print >>sys.stderr, 'asdf'
                        yield tmp
                    if not member.get('representatives'):
                        tmp={u'group': grp['name'],
                             u'dg': grp['lead_dg'],
                             u'id': grp['id'],
                             u'active_since': grp['active_since'],
                             u'group_type': grptype['name'],
                             u'noreps': 'yes',
                             }
                        if 'name' in member:
                            if maps:
                                if debug: print >>sys.stderr, repr(member['name'])
                                if debug: print >>sys.stderr, repr(maps.get(member['name']))
                                tmp['org_name'] = maps.get(member['name'],member['name']).strip()
                                if debug: print >>sys.stderr, repr(tmp['org_name'])
                                if debug: print >>sys.stderr, 'asdf'
                            else:
                                tmp['org_name'] = member['name'].strip()
                        if 'type' in member:
                             tmp['org_type']= member['type']
                        yield tmp
        for subgrp in grp.get('sub_groups',[]):
            for org in subgrp.get('members',[]):
                if 'gender' in org:
                    tmp=org.copy()
                    tmp.update({u'group': grp['name'],
                                u'dg': grp['lead_dg'],
                                u'id': grp['id'],
                                u'active_since': grp['active_since'],
                                u'sub_group': subgrp['name']})
                    if maps:
                        if debug: print >>sys.stderr, repr(tmp['name'])
                        if debug: print >>sys.stderr, repr(maps.get(tmp['name']))
                        tmp['name']=maps.get(tmp['name'],tmp['name']).strip()
                        if debug: print >>sys.stderr, repr(tmp['name'])
                        if debug: print >>sys.stderr, 'asdf'
                    yield tmp
                for member in org.get('members',[]):
                    for rep in member.get('representatives',[]):
                        tmp=rep.copy()
                        tmp.update({u'group': grp['name'],
                                    u'dg': grp['lead_dg'],
                                    u'id': grp['id'],
                                    u'active_since': grp['active_since'],
                                    u'group_type': org['name'],
                                    u'sub_group': subgrp['name'],
                                    u'org_name': member['name'],
                                    u'org_type': member['type'],
                                    })
                        if maps:
                            if debug: print >>sys.stderr, repr(tmp['org_name'])
                            if debug: print >>sys.stderr, repr(maps.get(tmp['org_name']))
                            tmp['org_name']=maps.get(tmp['org_name'],tmp['org_name']).strip()
                            tmp['name']=maps.get(tmp['name'],tmp['name']).strip()
                            if debug: print >>sys.stderr, repr(tmp['org_name'])
                            if debug: print >>sys.stderr, 'asdf'
                        yield tmp
                    if not member.get('representatives'):
                        tmp={u'group': grp['name'],
                             u'dg': grp['lead_dg'],
                             u'id': grp['id'],
                             u'active_since': grp['active_since'],
                             u'group_type': org['name'],
                             u'sub_group': subgrp['name'],
                             u'noreps': 'yes',
                             }
                        if 'name' in member:
                            if maps:
                                if debug: print >>sys.stderr, repr(member['name'])
                                if debug: print >>sys.stderr, repr(maps.get(member['name']))
                                tmp[u'org_name'] = maps.get(member['name'],member['name']).strip()
                                if debug: print >>sys.stderr, repr(tmp['org_name'])
                                if debug: print >>sys.stderr, 'asdf'
                            else:
                                tmp[u'org_name'] = member['name'].strip()
                        if 'type' in member:
                             tmp[u'org_type']= member['type']
                        yield tmp

def load_cols(master, dedups):
    mappings = {}
    with open(master,'r') as master:
        fields=master.readline().strip().split(',')
        reader = csv.DictReader(master, fields)
        for row in reader:
            if not row['org_name']: continue
            row['org_name']=row['org_name'].decode('utf8')
            # COPA-COGECA (Comité des Organisations Professionnelles Agricoles - Confédération Générale de la Coopération Agricole)
            #print >>sys.stderr, row['org_name'].encode('utf8')
            #print >>sys.stderr, repr(dedups.get(row['org_name']))
            #print >>sys.stderr, 'asdf'
            row['org_name'] = (dedups.get(row['org_name']) or row['org_name']).strip()
            if not row['org_name'] in mappings:
                mappings[row['org_name']]={'u':False}

            for var in ['Wrong label?', 'org_type_[alter-eu]', 'alter-eu_reason',
                        'interest_represented_[alter-eu]', 'Notes', 'group_type_[alter-eu]']:
                if len(row.get(var, '').strip()):
                    if var in mappings[row['org_name']] and mappings[row['org_name']][var].strip() != row[var].strip().decode('utf8'):
                        print >>sys.stderr, "conflicting data for", var, repr(row['org_name']), '\n\t', repr(row[var]), '\n\t', repr(mappings[row['org_name']][var])
                    else:
                        mappings[row['org_name']][var] = row[var].decode('utf8')
    return mappings

if __name__ == "__main__":
    #print json.dumps(transform(sys.argv[1])).encode('utf8')
    emaps=None
    master=None
    if len(sys.argv)>3:
        emaps=load_mappings(sys.argv[-1])
        if debug:
            import pprint
            pprint.pprint(emaps, stream=sys.stderr)
        master=load_cols(sys.argv[-2], emaps)
    # TODO urls to linkedin http://linkedin.com/in/firstlastname
    # google is better: "https://encrypted.google.com/search?q=%s+european+commission+expert" % name
    if sys.argv[1]=='-d':
        fields=sys.stdin.readline().strip().split(',')
        w = csv.DictWriter(sys.stdout, fields)
        w.writeheader()
        reader = csv.DictReader(sys.stdin, fields)
        for row in reader:
            row['org_name']=emaps.get(row['org_name'],row['org_name'])
            alias=emaps.get(row['name'])
            #row['name']=alias.encode('utf8') if alias else row['name']
            row['name']=alias if alias else row['name']
            w.writerow(row)
    else:
        fields=['dg', 'org_name', 'status', 'interests_represented',
                'sub_group', 'group', 'name', 'gender', 'prof_title',
                'org_type', 'prof_profiles', 'nationality', 'group_type',
                'active_since','Wrong label?', 'org_type_[alter-eu]',
                'alter-eu_reason', 'interest_represented_[alter-eu]', 'Notes',
                'group_type_[alter-eu]', '_id']
        w = UnicodeDictWriter(sys.stdout, fields)
        #w = csv.DictWriter(sys.stdout, fields)
        w.writeheader()
        for i, entity in enumerate(transform(sys.argv[1], emaps)):
            if entity.get('org_name'):
                if entity.get('org_name') in master:
                    master[entity['org_name']]['u']=True
                    entity.update(master[entity['org_name']])
                #else:
                #    print >>sys.stderr, 'no merge for', entity['org_name'].encode('utf8')
            if 'prof_profiles' in entity:
                entity['prof_profiles']=json.dumps(entity['prof_profiles'])
            if 'interests_represented' in entity:
                entity['interests_represented']=json.dumps(entity['interests_represented'])
            entity['_id']=str(i)
            try:
                w.writerow(entity)
            except:
                print >>sys.stderr, repr(entity)
                raise
        #for k,v in master.items():
        #    if v['u'] or len(v)==1: continue
        #    print >>sys.stderr, 'unmerged', k.encode('utf8')
        #    #print >>sys.stderr, v
