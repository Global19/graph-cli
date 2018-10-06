#!/usr/bin/python3

from sys import stdin
import numpy as np
import pickle

# disables screen requirement for plotting
# must be called before importing matplotlib.pyplot
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import pandas as pd
import numpy as np

graph_global_fns = ['update_globals', 'dump', 'remove_global_flags']

class Graph:
    # static variables
    xlabel = None
    xscale = None
    xrange = None
    ylabel = None
    yscale = None
    yrange = None
    title = None
    figsize = None
    fontsize = None
    xtick_fontsize = None
    ytick_fontsize = None
    xlabel_fontsize = None
    ylabel_fontsize = None
    def __init__(self):
        self.xcol = None
        self.ycol = None
        self.legend = None
        self.color = None
        self.style = None
        self.marker = None
        self.linewidth = None
        self.markersize = None
        self.output = None
        self.time_format = None
        self.resample = None
        self.sort = None
    def __str__(self):
        return str(self.__data__())
    def __repr__(self):
        return self.__str__()
    def __data__(self):
        data = {'globals': {}, 'attributes': {}}
        for attr in [y for y in dir(Graph)
                if not (y.startswith('__') and y.endswith('__'))]:
            if attr in graph_global_fns: continue
            data['globals'][attr] = getattr(Graph, attr)
        for attr in [y for y in dir(self)
                if not (y.startswith('__') and y.endswith('__'))]:
            if attr in graph_global_fns: continue
            if attr in data['globals']: continue
            data['attributes'][attr] = getattr(self, attr)
        data['attributes']['xcol'] = str(data['attributes']['xcol']).split('\n')[-1]
        data['attributes']['ycol'] = str(data['attributes']['ycol']).split('\n')[-1]
        return data
    @staticmethod
    def update_globals(args):
        # first load previous pickled globals
        # loop through all attributes that don't start and end with '__'
        for attr in [y for y in dir(Graph)
                if not (y.startswith('__') and y.endswith('__'))]:
            if attr in graph_global_fns: continue
            if attr not in dir(args): continue
            val = getattr(args, attr)
            cur = getattr(Graph, attr)
            # if the attribute has already been set and index 1
            # (flag for user-set) is False, then update
            if cur is None:
                setattr(Graph, attr, val)
            if type(cur) is tuple and not cur[1]:
                setattr(Graph, attr, val)
            if type(cur) is tuple and cur[1] and type(val) is tuple and val[1]:
                setattr(Graph, attr, val)
    @staticmethod
    def dump(graphs):
        return (graphs, graphs[0].__data__()['globals'])
    @staticmethod
    def remove_global_flags():
        for attr in [y for y in dir(Graph)
                if not (y.startswith('__') and y.endswith('__'))]:
            if attr in graph_global_fns: continue
            val = getattr(Graph, attr)
            if type(val) is tuple:
                setattr(Graph, attr, val[0])

def get_graph_def(xcol, ycol, legend, color, style, marker, linewidth,
        markersize, output, time_format, resample, sort):
    # get dict of args (must match Graph attribute names)
    try:
        # automatically convert to datetime
        if time_format is not None:
            xcol = pd.to_datetime(xcol, format=time_format)
        elif xcol.dtype == np.dtype('O'):
            xcol = pd.to_datetime(xcol)
    except: pass
    if sort:
        df = pd.DataFrame({xcol.name: xcol, ycol.name: ycol})
        df.sort_values(xcol.name, inplace=True)
        xcol, ycol = df[xcol.name], df[ycol.name]
    kvs = locals()
    g = Graph()
    for attr, val in kvs.items():
        setattr(g, attr, val)
    return g

def get_graph_defs(args):
    graphs, globals = read_chain(args)
    class AttrDict(dict):
        def __init__(self, *args, **kwargs):
            super(AttrDict, self).__init__(*args, **kwargs)
            self.__dict__ = self
    Graph.update_globals(AttrDict(globals))

    # zip together options.specific_attrs with default values
    # and generate graphs definitions
    for g in zip(args.xcol, args.ycol, args.legend, args.color, args.style,
            args.marker, args.linewidth, args.markersize, args.output,
            args.time_format, args.resample, args.sort):
        graphs += [get_graph_def(*g)]

    return graphs

def read_chain(args):
    chain = ([], {})
    # read stdin for chained data and unpickle into chain array
    # check if stdin is not a terminal
    if not stdin.isatty() and args.file != '-':
        chain = pickle.loads(stdin.buffer.read())

    # check our data is what we expect it to be
    # TODO: error handling
    assert(type(chain) is tuple)
    assert(len(chain) == 2)
    assert(type(chain[0]) is list)
    assert(type(chain[1]) is dict)
    for link in chain[0]:
        assert(type(link) is Graph)

    return chain

def create_graph(graphs):
    # make Graph.global = (val, flag) just val
    Graph.remove_global_flags()

    # create figure
    fig, ax = plt.subplots(figsize=(Graph.figsize))
    matplotlib.rcParams.update({'font.size': Graph.fontsize})

    # iterate over graphs array
    for graph in graphs:
        ax.plot(graph.xcol, graph.ycol, label=graph.legend,
            marker=graph.marker, color=graph.color, linestyle=graph.style,
            linewidth=graph.linewidth, markersize=graph.markersize)
        if graph.output:
            apply_globals(ax)
            plt.savefig(graph.output)

def apply_globals(ax):
    plt.xlabel(Graph.xlabel, fontsize=Graph.xlabel_fontsize)
    plt.ylabel(Graph.ylabel, fontsize=Graph.ylabel_fontsize)
    plt.title(Graph.title)
    plt.setp(ax.get_xticklabels(), fontsize=Graph.xtick_fontsize)
    plt.setp(ax.get_yticklabels(), fontsize=Graph.ytick_fontsize)

    if Graph.xscale is not None:
        plt.xticks(np.arange(round(ax.get_xlim()[0] / Graph.xscale) *
            Graph.xscale, ax.get_xlim()[1], Graph.xscale))
    if Graph.yscale is not None:
        plt.yticks(np.arange(round(ax.get_ylim()[0] / Graph.yscale) *
            Graph.yscale, ax.get_ylim()[1], Graph.yscale))
    if Graph.xrange is not None:
        plt.xlim(*Graph.xrange)
    if Graph.yrange is not None:
        plt.ylim(*Graph.yrange)

    # TODO: make these configurable
    plt.grid(True, alpha=0.5, linestyle='-.')
    plt.legend()
