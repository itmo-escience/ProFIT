import graphviz as gv
import os

class Renderer():

    def __init__(self):
        self.GV = None

    def update(self, TM, G):
        T, nodes, edges = TM.T, G.nodes, G.edges
        G = gv.Digraph(strict=False, format='png')
        G.attr(rankdir='TB')
        G.attr('edge', fontname='Sans Not-Rotated 14')
        G.attr('node', shape='box', style='filled', fontname='Sans Not-Rotated 14')
        
        # 1. Node color and shape
        F = {a: nodes[a][0] for a in nodes} # Activities absolute frequencies
        case_cnt = sum([v[0] for v in T['start'].values()])
        x_max, x_min = max(F.values()), min(F.values())
        for a in nodes:
            color = int((x_max - F[a]) / (x_max - x_min + 1e-6) * 100.)
            fill, font = "#ffffff", 'black'
            if colored:
                for interval in color_map:
                    if color in interval:
                        fill = color_map[interval]
                        break
            else: fill = 'gray' + str(color)
            if color < 50:
                font = 'white'
            if type(a) == tuple:
                node_label = a[0]
                for i in range(1,len(a)):
                    node_label += '\n' + a[i]
                node_label += '\n(' + str(nodes[a][0]) + ')'
                G.node(str(a), label=node_label, fillcolor=fill, fontcolor=font, shape='octagon')
            else:
                node_label = a + ' (' + str(F[a]) + ')'
                G.node(a, label=node_label, fillcolor=fill, fontcolor=font)
        G.node("start", shape="circle", label=str(case_cnt), \
                fillcolor="#95d600" if colored else "#ffffff", margin='0.05')
        G.node("end", shape="doublecircle", label='', \
                fillcolor="#ea4126" if colored else "#ffffff")
        
        # 2. Edge thickness and style
        values = [edges[e][0] for e in edges]
        if values: t_min, t_max = min(values), max(values)
        for e in edges:
            if edges[e] == (0,0):
                G.edge(str(e[0]), str(e[1]), style='dotted')
                continue
            if (e[0] == 'start') | (e[1] == 'end'):
                G.edge(str(e[0]), str(e[1]), label=str(edges[e][0]), style='dashed')
            else:
                y = 1.0 + (5.0 - 1.0) * (edges[e][0] - t_min) / (t_max - t_min + 1e-6)
                G.edge(str(e[0]), str(e[1]), label=str(edges[e][0]), penwidth=str(y))
        
        self.GV = G

    def save(self, save_path): 
        gv_format_save = input("Save in GV format? (y/n): ").lower() == 'y'
        save_name = input("Enter file name: ")
        self.GV.render(save_path + save_name, view=False)
        if not gv_format_save:
            os.remove(save_path + save_name)