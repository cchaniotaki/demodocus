import networkx as nx
import matplotlib.pyplot as plt

# Load GML
graph = nx.read_gml("/Users/christinechaniotaki/Documents/Krawler-study/state-of-the-art-tools/demodocus/output/without-proxy/chrome/analyzed_full_graph.gml")

# Draw Graph
nx.draw(graph, with_labels=True, node_color="skyblue", font_weight="bold")
plt.show()
