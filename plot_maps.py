import re

import matplotlib.pyplot as plt
import networkx as nx
from pyvis.network import Network


def plot_edges(edges, descs, fname=None, show=False):
    names = {}
    for loc, desc in descs.items():
        m = re.search(r'== (.*?) ==', desc)
        names[loc] = m.group(1) if m else str(loc)

    plt.figure(figsize=(8, 6))

    G = nx.DiGraph()

    for loc in edges:
        G.add_node(loc, label=names.get(loc, str(loc)))

    for src, targets in edges.items():
        for dst, action in targets:
            if src != dst:
                G.add_edge(src, dst, label=action)

    pos = nx.spring_layout(G, seed=42, iterations=500, k=1.5)

    node_colors = [G.nodes[n]['color'] for n in G.nodes]

    nx.draw(
        G,
        pos,
        node_size=400,
        node_color=node_colors,
        edge_color='gray',
        arrows=True,
        with_labels=False,
    )

    node_labels = {n: names.get(n, str(n)) for n in G.nodes}
    nx.draw_networkx_labels(G, pos, node_labels, font_size=8)

    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=7)

    plt.title('Location Graph')
    plt.axis('off')
    plt.tight_layout()

    if show:
        plt.show()

    if fname:
        plt.savefig(fname, dpi=300)


def node_style_from_name(name: str):

    if 'Dark' in name:
        return {
            'color': '#04387b',
            'group': 'dark_passage',
        }
    elif 'Moss cavern' in name:
        return {
            'color': '#116622',
            'group': 'dark_passage',
        }
    elif 'Tropical' in name:
        return {
            'color': '#11bb22',
            'group': 'vault',
        }
    elif 'Beach' in name:
        return {
            'color': '#ffd700',
            'group': 'vault',
        }
    elif 'Vault' in name:
        return {
            'color': '#800080',
            'group': 'vault',
        }
    elif 'Twisty' in name:
        return {
            'color': '#e74c3c',
            'group': 'twisty',
        }
    elif 'Ruins' in name:
        return {
            'color': '#FF8C00',
            'group': 'ruins',
        }
    else:
        return {
            'color': '#3498db',
            'group': 'normal',
        }


def plot_edges_interactive(edges, descs, fname='graph.html'):

    names = {}
    for loc, desc in descs.items():
        m = re.search(r'== (.*?) ==', desc)
        names[loc] = m.group(1) if m else str(loc)

    G = nx.DiGraph()

    for loc in edges:
        name = names.get(loc, str(loc))
        style = node_style_from_name(name)
        G.add_node(
            loc,
            label=name,
            color=style['color'],
            title=f"<b>Location:</b> {loc}<br><pre>{descs.get(loc, '')}</pre>",
        )

    for src, targets in edges.items():
        for dst, action in targets:
            if src != dst:
                G.add_edge(
                    src,
                    dst,
                    label=action,
                    title=action,
                )

    net = Network(
        height='1400px',
        width='100%',
        directed=True,
        bgcolor='#ffffff',
        font_color='black',
    )

    net.from_nx(G)

    net.set_options(
        '''
    {
      "physics": {
        "enabled": true,
        "solver": "forceAtlas2Based",
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 120,
          "springConstant": 0.08
        },
        "stabilization": {
          "iterations": 200
        }
      },
      "edges": {
        "arrows": {
          "to": { "enabled": true }
        },
        "font": { "size": 10 }
      },
      "nodes": {
        "shape": "dot",
        "size": 16,
        "font": { "size": 12 }
      }
    }
    '''
    )

    net.write_html(fname)
    print(f'Saved graph to {fname}')
