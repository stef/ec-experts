#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    This file is part of composite data analysis tools (cdat)

#    composite data analysis tools (cdat) is free software: you can
#    redistribute it and/or modify it under the terms of the GNU
#    Affero General Public License as published by the Free Software
#    Foundation, either version 3 of the License, or (at your option)
#    any later version.

#    composite data analysis tools (cdat) is distributed in the hope
#    that it will be useful, but WITHOUT ANY WARRANTY; without even
#    the implied warranty of MERCHANTABILITY or FITNESS FOR A
#    PARTICULAR PURPOSE.  See the GNU Affero General Public License
#    for more details.

#    You should have received a copy of the GNU Affero General Public
#    License along with composite data analysis tools (cdat) If not,
#    see <http://www.gnu.org/licenses/>.

# (C) 2011 by Stefan Marsiske, <stefan.marsiske@gmail.com>

import sys
import pprint

def unws(txt):
    return u' '.join(txt.split())

def dump_schema(items, skip=[], title=None, format="text"):
    """
    Dump schema: takes a list of data structures and computes a
    probabalistic schema out of the samples, it prints out the result
    to the output.
    @param count is optional and in case your items list is some kind of cursor that has no __len__
    @param skip is an optional list of keys to skip on the top structure
    @param title is the name for the data structure to be displayed
    @param format <text|full-html|html> - html is default - full html adds a js/css header and a legend
    """
    ax={}
    count=0
    for item in items:
        ax=scan(dict([(k,v) for k,v in item.items() if k not in skip]),ax)
        count+=1
    #pprint.pprint(ax)
    #if title:
    #    ax['name']=title
    if format=='text':
        print_schema(ax,0,count)
        return
    elif format=='full-html':
        print '%s<div class="schema">%s</div>%s' % (_html_header(),
                                                    '\n'.join([str(x) for x in html_schema(ax,0,count)]),
                                                    _html_footer())
    else:
        print '<div class="schema">%s</div>' % '\n'.join([str(x) for x in html_schema(ax,0,count)])

def scan(d, node):
    """ helper for dump_schema"""
    if not 'types' in node:
        node['types']={}
    if hasattr(d, 'keys'):
        for k, v in d.items():
            if not 'items' in node:
                node['items']={}
            if not k in node['items']:
                node['items'][k]={'name':k}
            node['items'][k]=scan(v,node['items'][k])
    elif isinstance(d,str):
        d=d.decode('utf8')
    elif hasattr(d, '__iter__'):
        if not 'elems' in node:
            node['elems']={}
        for v in d:
            stype=str(type(v))
            node['elems'][stype]=scan(v,node['elems'].get(stype,{}))
    if isinstance(d, unicode):
        d=unws(d) or None
    mtype=str(type(d))
    tmp=node['types'].get(mtype,{'count': 0, 'example': None})
    tmp['count']+=1
    if d and not tmp['example'] and not isinstance(d,dict):
        tmp['example']=d
    node['types'][mtype]=tmp
    return node

def merge_dict_lists(node):
    # ultra ugly. see test code in arch
    if ('elems' in node and
        'items' in node and
        'items' in node['elems'].values()[0] and
        sorted(node['items'].keys())==sorted(node['elems'].values()[0]['items'].keys())):

        node['types']["<type 'list'>"]['count']+=node['types']["<type 'dict'>"]['count']
        node['elems']["<type 'dict'>"]['types']["<type 'dict'>"]['count']+=node['types']["<type 'dict'>"]['count']
        del node['types']["<type 'dict'>"]

        for k,v in node['items'].items():
            if not k in node['elems'].values()[0]['items']:
                node['elems'].values()[0]['items'][k]=v
                continue
            for tk, tv in v['types'].items():
                if tk in node['elems'].values()[0]['items'][k]['types']:
                    node['elems'].values()[0]['items'][k]['types'][tk]['count']+=tv['count']
                else:
                    node['elems'].values()[0]['items'][k]['types'][tk]=tv
        del node['items']
    return node

def print_schema(node,indent,parent):
    """ helper for dump_schema"""
    merge_dict_lists(node)
    for k,v in sorted(node['types'].items(),key=lambda x: x[1]['count'],reverse=True):
        print "{0:>3}".format((v['count']*100)/parent), '  '*indent, node.get('name',''), k,
        if k=="<type 'list'>":
            print ''
            for x in node['elems'].values():
                print_schema(x,indent+1,v['count'])
        elif k=="<type 'dict'>":
            print ''
            for x in node['items'].values():
                print_schema(x,indent+1,v['count'])
        elif k=="<type 'unicode'>":
             print v['example'].encode('utf8')
        else:
             print v['example']

schematpl="<dl style='background-color: #{3:02x}{3:02x}{3:02x};'><dt>{1} <span class='p'>({0}%)</span></dt><dd> <div class='{4}'>{2}</div></dd></dl>"
def html_schema(node,indent,parent):
    """ helper for dump_schema"""
    merge_dict_lists(node)
    res=[]
    for k,v in sorted(node['types'].items(),key=lambda x: x[1]['count'],reverse=True):
        if k=="<type 'list'>":
            data="<ul>{0}</ul>".format(''.join(["<li>{0}</li>".format(y) for x in node['elems'].values() for y in html_schema(x,indent+1,v['count'])]))
            clss='contents'
        elif k=="<type 'dict'>":
            data="<ul>{0}</ul>".format(''.join(["<li>{0}</li>".format(y) for x in node['items'].values() for y in html_schema(x,indent+1,v['count'])]))
            clss='contents'
        elif k=="<type 'unicode'>":
            data="Example: {0}".format(v['example'].encode('utf8'))
            clss='example'
        elif k=="<type 'str'>":
            data="Example: {0}".format(v['example'])
            clss='example'
        else:
            data="Example: {0}".format(v['example'])
            clss= 'example'
        res.append(schematpl.format(int(float(v['count'])/parent*100 if k!="<type 'list'>" else v['count']),
                                    node.get('name','&lt;listitem&gt;'),
                                    data,
                                    256-int(64*(1 if v['count']>=parent else float(v['count'])/parent)),
                                    clss,
                                    ))
    return res

def _html_header():
    """ helper for html_schema"""
    return """
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
    <head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8" />
    <style>
    dt { display: inline; cursor: pointer; color: #288; }
    dd { display: inline; margin-left: 0;}
    dl { margin-top: .4em; }
    ul { list-style: none; }
    .contents, .example { margin-left: 2em; background-color: white}
    .type { font-style: italic }
    .p { font-size: .8em }
    .schema-legend { font-size: .8em; font-style: italic; }
    </style>
    <script type="text/javascript" src="http://code.jquery.com/jquery-1.6.2.js"> </script>
    <script type="text/javascript">
    $(document).ready(function() {
       $('div.contents').hide();
       $('.schema > dl > dd > div.contents').show();
       $('dt').click(function() {
         $(this).parent().find('div.contents:first').toggle();
       });
    });
    </script>
    </head>
    <body>
    <div class="schema-legend">Click on the names to fold/expand levels. Percentages show probability of this field appearing under it's parent. In case of lists, percentage also shows average length of list.</div>
    """

def _html_footer():
    """ helper for html_schema"""
    return """
    </body>
    </html>
    """

def stripns(attr):
   ns = ["{http://ec.europa.eu/transparency/regexpert/}",
         "{http://www.w3.org/2001/XMLSchema-instance}",
         "{http://ec.europa.eu/transparency/regexpert/view/transparency/RegExp_v1.xsd}"]
   for n in ns:
       if attr.startswith(n):
           return attr[len(n):]
   return attr

def _xml2obj(elem,c=False):
    res={}
    if elem.text:
        #if c: print "text", stripns(elem.tag)
        res[stripns(elem.tag)]=unws(elem.text)
    if len(elem.attrib)>0:
        if stripns(elem.tag) in [stripns(x) for x in elem.attrib]:
            print >>sys.stderr, "attribute clashes with element", stripns(elem.tag), "suppressed attribute value", elem.attrib[stripns(elem.tag)]
        #if c: print "attr", stripns(elem.tag)
        res.update({stripns(attr): elem.attrib[attr] for attr in elem.attrib})
    kids=elem.xpath('./*')
    if len(kids)>0:
        if len(set((stripns(kid.tag) for kid in kids)))==len(kids):
            #if c: print "dict", stripns(elem.tag)
            res[stripns(elem.tag)]={stripns(kid.tag): _xml2obj(kid)[stripns(kid.tag)] for kid in kids if _xml2obj(kid, c=True)}
        else:
            #if c: print "list", stripns(elem.tag)
            res[stripns(elem.tag)]=[_xml2obj(kid) for kid in kids if _xml2obj(kid)]
    #if c: pprint.pprint(res), stripns(elem.tag)
    return res

def xml2obj(root):
    for elem in root.xpath('//t:groups/t:group',
                           namespaces={'t': 'http://ec.europa.eu/transparency/regexpert/'}):
        yield _xml2obj(elem)

def test_dump(fname, html_only=False):
    from lxml.etree import parse
    root=None
    with open(fname, 'r') as fd:
        root=parse(fd)
    elements=xml2obj(root)
    if html_only:
        dump_schema(elements,title='expertregister',format='full-html')
    else:
        dump_schema(elements,title='expertregister', format='text')

if __name__ == "__main__":
    test_dump(sys.argv[1], html_only=True)
    #test_dump(sys.argv[1], html_only=False)
