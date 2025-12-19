import re

import matplotlib.pyplot as plt
import networkx as nx


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

    nx.draw(
        G,
        pos,
        node_size=400,
        node_color='lightblue',
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
