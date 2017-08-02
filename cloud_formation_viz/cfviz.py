#!/usr/bin/env python

import datetime
import json
import sys
from numbers import Number


def main():
    if sys.argv[1:2] != []:
        with open(sys.argv[1]) as f:
            template = json.load(f)
    else:
        template = json.load(sys.stdin)

    graph, edges = extract_graph(template.get('Description', ''),
                                 template['Resources'])
    graph['edges'].extend(edges)
    handle_terminals(template, graph, 'Parameters', 'source')
    handle_terminals(template, graph, 'Outputs', 'sink')
    graph['subgraphs'].append(handle_psuedo_params(graph['edges']))

    render(graph)


def handle_terminals(template, graph, name, rank):
    if name in template:
        (subgraph, edges) = extract_graph(name, template[name])
        subgraph['rank'] = rank
        subgraph['style'] = 'filled,rounded'
        graph['subgraphs'].append(subgraph)
        graph['edges'].extend(edges)


def handle_psuedo_params(edges):
    graph = {
        'name': 'Psuedo Parameters',
        'nodes': [],
        'edges': [],
        'subgraphs': [],
    }
    graph['shape'] = 'ellipse'
    params = set()
    for e in edges:
        if e['from'].startswith('AWS::'):
            params.add(e['from'])
    graph['nodes'].extend({'name': n} for n in params)
    return graph


def extract_graph(name, elem):
    graph = {'name': name, 'nodes': [], 'edges': [], 'subgraphs': []}
    edges = []
    for item, details in elem.items():
        graph['nodes'].append({'name': item})
        edges.extend(find_refs(item, details))
    return (graph, edges)


def find_refs(context, elem):
    if isinstance(elem, dict):
        for k, v in elem.items():
            if k == 'Ref':
                assert isinstance(v, str), 'Expected a string: %s' % v
                yield {'from': v, 'to': context}
            elif k == 'Fn::GetAtt':
                assert isinstance(v, list), 'Expected a list: %s' % v
                yield {'from': v[0], 'to': context}
            else:
                yield from find_refs(context, v)
    elif isinstance(elem, list):
        for e in elem:
            yield from find_refs(context, e)
    elif (isinstance(elem, str) or
          isinstance(elem, bool) or
          isinstance(elem, Number) or
          isinstance(elem, datetime.date)):
        pass
    else:
        raise AssertionError('Unexpected type {type_}: {elem}'
                             .format(type_=type(elem), elem=elem))


def render(graph, subgraph=False):
    print('%s "%s" {' % ('subgraph' if subgraph else 'digraph', graph['name']))
    print('labeljust=l;')
    print('node [shape={}];'.format(graph.get('shape', 'box')))
    if 'style' in graph:
        print('node [style="%s"]' % graph['style'])
    if 'rank' in graph:
        print('rank=%s' % graph['rank'])
    for n in graph['nodes']:
        print('"%s"' % n['name'])
    for s in graph['subgraphs']:
        render(s, True)
    for e in graph['edges']:
        print('"%s" -> "%s";' % (e['from'], e['to']))
    print('}')


def debug(*s):
    print(s, file=sys.stderr)
