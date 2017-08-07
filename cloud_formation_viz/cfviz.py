import datetime
import io
import sys
from numbers import Number

import click

from cloud_formation_viz import cf_template


def format_node_name(item):
    return item.replace('.', '_')


def format_node_label(item, details):
    try:
        ingress = details['Properties']['SecurityGroupIngress']
        ports = ', '.join([str(x['FromPort']) for x in ingress])
        return '\\nports: '.join((item, ports))
    except KeyError:
        return item


VALID_TYPES = [
    str,
    bool,
    Number,
    datetime.date,
]


def find_refs(context, elem):
    if isinstance(elem, dict):
        for k, v in elem.items():
            if k == 'Ref':
                assert isinstance(v, str), 'Expected a string: %s' % v
                yield {'from': format_node_name(v), 'to': context}
            elif k == 'Fn::GetAtt':
                assert isinstance(v, list), 'Expected a list: %s' % v
                yield {'from': format_node_name(v[0]), 'to': context}
            else:
                yield from find_refs(context, v)
    elif isinstance(elem, list):
        for e in elem:
            yield from find_refs(context, e)
    else:
        is_valid_type = any(isinstance(elem, cls) for cls in VALID_TYPES)
        assert is_valid_type, ('Unexpected type {type_}: {elem}'
                               .format(type_=type(elem), elem=elem))


def extract_graph(elem,
                  excl=(),
                  excl_pseudo_params=False,
                  excl_second_level=False,
                  **kwargs):
    nodes = []
    edges = []
    for item, details in elem.items():
        name = format_node_name(item)
        label = format_node_label(item, details)
        nodes.append({'name': name, 'label': label})
        edges.extend(find_refs(name, details))

    if excl:
        edges = filter(lambda e: e['from'] not in excl and e['to'] not in excl,
                       edges)
    if excl_pseudo_params:
        edges = filter(lambda e: not e['from'].startswith('AWS::'), edges)

    if excl_second_level:
        keys = elem.keys()
        edges = filter(lambda e: e['from'] in keys, edges)

    graph = {
        'nodes': nodes,
        'edges': list(edges),
        'subgraphs': [],
    }
    graph.update(kwargs)
    return graph


def handle_terminals(template, graph, name, rank):
    if name in template:
        subgraph = extract_graph(template[name],
                                 name=name,
                                 rank=rank,
                                 style='filled,rounded')
        graph['subgraphs'].append(subgraph)
        graph['edges'].extend(subgraph['edges'])


def handle_psuedo_params(edges):
    nodes = set(
        {'name': e['form']}
        for e in edges if e['from'].startswith('AWS::')
    )
    return {
        'name': 'Psuedo Parameters',
        'shape': 'ellipse',
        'nodes': nodes,
        'edges': [],
        'subgraphs': [],
    }


def render(graph, subgraph=False):
    print('%s "%s" {' % ('subgraph' if subgraph else 'digraph', graph['name']))
    print('labeljust=l;')
    print('node [shape={}];'.format(graph.get('shape', 'box')))
    if 'style' in graph:
        print('node [style="%s"]' % graph['style'])
    if 'rank' in graph:
        print('rank=%s' % graph['rank'])
    for n in graph['nodes']:
        print('{} [label = "{}"]'.format(n['name'], n['label']))
    for s in graph['subgraphs']:
        render(s, True)
    for e in graph['edges']:
        print('%s -> %s;' % (e['from'], e['to']))
    print('}')


def viz(template,
        print_parameters,
        print_outputs,
        print_pseudo_params,
        print_second_level_resources):
    if not print_parameters:
        excl = template.get('Parameters', {}).keys()
    else:
        excl = ()

    graph = extract_graph(template['Resources'],
                          excl=excl,
                          excl_pseudo_params=not print_pseudo_params,
                          excl_second_level=not print_second_level_resources,
                          name=template.get('Description', ''))

    if print_parameters:
        handle_terminals(template, graph, 'Parameters', 'source')

    if print_outputs:
        handle_terminals(template, graph, 'Outputs', 'sink')

    if print_pseudo_params:
        graph['subgraphs'].append(handle_psuedo_params(graph['edges']))

    render(graph)


@click.command()
@click.argument('path', required=False)
@click.option('--print-parameters', is_flag=True)
@click.option('--print-outputs', is_flag=True)
@click.option('--print-pseudo-params', is_flag=True)
@click.option('--print-second-level-resources', is_flag=True)
def cli(path, **kwargs):
    if path:
        with open(path) as f:
            template = cf_template.load(f)
    else:
        template = cf_template.load(io.StringIO(sys.stdin.read()))
    viz(template, **kwargs)
