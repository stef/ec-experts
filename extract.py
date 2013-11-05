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

from lxml.etree import parse, tostring
from collections import OrderedDict
import json, csv, sys, cStringIO, codecs, datetime

ns={'t': 'http://ec.europa.eu/transparency/regexpert/'}
def extract_text_field(root):
    path='.//text()'
    return unws(' '.join(root.xpath(path, namespaces=ns)))

def extract_list(root):
    path='.//text()'
    return [unws(x) for x in root.xpath(path, namespaces=ns)
            if unws(x)]

def extract_date(root):
    day=root.xpath('t:day/text()', namespaces=ns)
    month=root.xpath('t:month/text()', namespaces=ns)
    year=root.xpath('t:year/text()', namespaces=ns)
    return datetime.date(int(year[0]), int(month[0]), int(day[0]))

def extract_authorities(root):
    path='./t:public_authority/t:name/text()'
    return [unws(x) for x in root.xpath(path, namespaces=ns)
            if unws(x)]

def extract_more_info(root):
    path='./*'
    infos=[]
    for infoelem in root.xpath(path, namespaces=ns):
        info=OrderedDict([('type',stripns(infoelem.tag))])
        for elem in infoelem.xpath(path, namespaces=ns):
            name=stripns(elem.tag)
            res=extract_info(elem)
            if res!=None:
                info.update(res)
        if len(info):
            infos.append(info)
    if len(infos):
        return infos

def extract_info(root):
    path='./*'
    fields=OrderedDict([('info', extract_text_field),
                        ('link', extract_text_field),
                        ('documents', extract_doc),
                        ])
    info=OrderedDict()
    for tag in root.xpath(path, namespaces=ns):
        name=stripns(tag.tag)
        res=fields.get(name, debug)(tag)
        if res!=None:
            info[name]=res
    if len(info):
        return info

def extract_doc(root):
    fields=OrderedDict([('size', extract_text_field),
                        ('type', extract_text_field),
                        ('title', extract_text_field),
                        ('link', extract_text_field),
                        ])
    docs=[]
    for docelem in root.xpath('./t:document', namespaces=ns):
        doc=OrderedDict()
        for tag in docelem.xpath('./*'):
            name=stripns(tag.tag)
            res=fields.get(name, debug)(tag)
            if res!=None:
                doc[name]=res
        if len(doc):
            docs.append(doc)
    if len(docs):
        return docs

def extract_sub_group(root):
    fields=OrderedDict([('duration', extract_text_field),
                        ('name', extract_text_field),
                        ('members', extract_member_type),
                        ])
    subgroups=[]
    for sgelem in root.xpath('./t:sub_group', namespaces=ns):
        sg=OrderedDict()
        for tag in sgelem.xpath('./*'):
            name=stripns(tag.tag)
            res=fields.get(name, debug)(tag)
            if res!=None:
                sg[name]=res
        if len(sg):
            subgroups.append(sg)
    if len(subgroups):
        return subgroups

def extract_member_type(root):
    fields=OrderedDict([('name', extract_text_field),
                        ('member', extract_member),
                        ])
    members_types=[]
    for docelem in root.xpath('./t:member_type', namespaces=ns):
        member_type=OrderedDict()
        for tag in docelem.xpath('./*'):
            name=stripns(tag.tag)
            res=fields.get(name, debug)(tag)
            if res!=None:
                if name=='member':
                    try:
                        member_type['members'].append(res)
                    except KeyError:
                        member_type['members']=[res]
                else:
                    member_type[name]=res
        if len(member_type):
            members_types.append(member_type)
    if len(members_types):
        return members_types

def extract_member(root):
    fields=OrderedDict([('name', extract_text_field),
                        ('type', extract_text_field),
                        ('status', extract_text_field),
                        ('country', extract_text_field),
                        ('prof_title', extract_text_field),
                        ('nationality', extract_text_field),
                        ('gender', extract_text_field),
                        ('prof_profiles', extract_list),
                        ('interests_represented', extract_list),
                        ('areas_countries_represented', extract_list),
                        ('categories', extract_list),
                        ('representatives', extract_reps),
                        ('public_authorities', extract_authorities),
                        ])
    member=OrderedDict()
    for tag in root.xpath('./*'):
        name=stripns(tag.tag)
        res=fields.get(name, debug)(tag)
        if res!=None:
            member[name]=res
    if len(member):
        return member

def extract_reps(root):
    fields=OrderedDict([('name', extract_text_field),
                        ('nationality', extract_text_field),
                        ('gender', extract_text_field),
                        ])
    reps=[]
    for repelem in root.xpath('./t:representative',namespaces=ns):
        rep=OrderedDict()
        for tag in repelem.xpath('./*'):
            name=stripns(tag.tag)
            res=fields.get(name, debug)(tag)
            if res!=None:
                rep[name]=res
        if len(rep):
            reps.append(rep)
    if len(reps):
        return reps

def extract_groups(root):
    types=root.xpath('./t:member_types', namespaces=ns)
    if len(types)!=1:
        raise ValueError
    res=extract_member_type(types[0])
    if res!=None and len(res)>0:
        return res

def debug(root):
    print 'debug\n', tostring(root)

def unws(txt):
    return u' '.join(txt.split())

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
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

def stripns(attr):
   ns = ["{http://ec.europa.eu/transparency/regexpert/}",
         "{http://www.w3.org/2001/XMLSchema-instance}",
         "{http://ec.europa.eu/transparency/regexpert/view/transparency/RegExp_v1.xsd}"]
   for n in ns:
       if attr.startswith(n):
           return attr[len(n):]
   return attr

def dateJSONhandler(obj):
    if hasattr(obj, 'isoformat'):
        return unicode(obj.isoformat())
    elif type(obj)==ObjectId:
        return unicode(obj)
    else:
        raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj))

def parse_group(root):
    fields=OrderedDict([('id', extract_text_field),
                        ('name', extract_text_field),
                        ('abbreviation', extract_text_field),
                        ('active_since', extract_date),
                        ('status', extract_text_field),
                        ('lead_dg', extract_text_field),
                        ('last_updated', extract_date),
                        ('scope', extract_text_field),
                        ('mission', extract_text_field),
                        ('types', extract_list),
                        ('policy_areas', extract_list),
                        ('associated_dgs', extract_list),
                        ('tasks', extract_list),
                        ('additional_information', extract_more_info),
                        ('sub_groups', extract_sub_group),
                        ('group_members', extract_groups),
                        ])
    group=OrderedDict()
    for tag in root.xpath('./*',
                      namespaces=ns):
        name=stripns(tag.tag)
        res=fields.get(name, debug)(tag)
        if res!=None:
            group[name]=res
    return group

def extract(fname):
    with open(fname, 'r') as fd:
        root=parse(fd)
    return [parse_group(group)
            for group
            in root.xpath('//t:groups/*',
                          namespaces=ns)]

if __name__ == "__main__":
    res=extract(sys.argv[1])
    #writer = UnicodeWriter(sys.stdout)
    #writer.writerow([str(x) if not isinstance(x,unicode) else x for x in group.values()])
    print json.dumps(res, indent=1, default=dateJSONhandler, ensure_ascii=False).encode('utf8')
