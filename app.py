################################################################################
#                             Titanic - Dashboard                              #
# ---------------------------------------------------------------------------- #
# Author:  Dario Radecic                                                       #
# Version: 1.0                                                                 #
################################################################################

################################################################################
#                                  > IMPORTS                                   #
################################################################################
import math
import numpy as np
import pandas as pd

from bokeh.embed import components
from bokeh.layouts import column, gridplot, layout, row
from bokeh.models import ColumnDataSource, HoverTool, PrintfTickFormatter
from bokeh.plotting import figure
from bokeh.transform import factor_cmap

from flask import Flask, render_template, request

df = pd.read_csv('../data/titanic.csv')
df['Title'] = df['Name'].apply(lambda x: x.split(',')[1].strip().split(' ')[0])

################################################################################
#                             - END OF IMPORTS -                               #
################################################################################


################################################################################
#                               > CONSTANT VALUES                              #
################################################################################
palette = ['#ba32a0', '#f85479', '#f8c260', '#00c2ba']

chart_font = 'Helvetica'
chart_title_font_size = '16pt'
chart_title_alignment = 'center'
axis_label_size = '14pt'
axis_ticks_size = '12pt'
default_padding = 30
chart_inner_left_padding = 0.015
chart_font_style_title = 'bold italic'

################################################################################
#                          - END OF CONSTANT VALUES -                          #
################################################################################


################################################################################
#                             > HELPER FUNCTIONS                               #
################################################################################
def palette_generator(length, palette):
    int_div = length // len(palette)
    remainder = length % len(palette)
    return (palette * int_div) + palette[:remainder]


def plot_styler(p):
    p.title.text_font_size = chart_title_font_size
    p.title.text_font  = chart_font
    p.title.align = chart_title_alignment
    p.title.text_font_style = chart_font_style_title
    p.y_range.start = 0
    p.x_range.range_padding = chart_inner_left_padding
    p.xaxis.axis_label_text_font = chart_font
    p.xaxis.major_label_text_font = chart_font
    p.xaxis.axis_label_standoff = default_padding
    p.xaxis.axis_label_text_font_size = axis_label_size
    p.xaxis.major_label_text_font_size = axis_ticks_size
    p.yaxis.axis_label_text_font = chart_font
    p.yaxis.major_label_text_font = chart_font
    p.yaxis.axis_label_text_font_size = axis_label_size
    p.yaxis.major_label_text_font_size = axis_ticks_size
    p.yaxis.axis_label_standoff = default_padding
    p.toolbar.logo = None
    p.toolbar_location = None


def redraw(p_class):
    survived_chart = survived_bar_chart(df, p_class)
    title_chart = class_titles_bar_chart(df, p_class)
    hist_age = age_hist(df, p_class)
    return (
        survived_chart,
        title_chart,
        hist_age
    )

################################################################################
#                          - END OF HELPER FUNCTIONS -                         #
################################################################################


################################################################################
#                               > MAIN ROUTE                                   #
################################################################################
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def chart():
    selected_class = request.form.get('dropdown-select')

    if selected_class == 0 or selected_class == None:
        survived_chart, title_chart, hist_age = redraw(1)
    else:
        survived_chart, title_chart, hist_age = redraw(selected_class)

    script_survived_chart, div_survived_chart = components(survived_chart)
    script_title_chart, div_title_chart = components(title_chart)
    script_hist_age, div_hist_age = components(hist_age)

    return render_template(
        'index.html',
        div_survived_chart=div_survived_chart,
        script_survived_chart=script_survived_chart,
        div_title_chart=div_title_chart,
        script_title_chart=script_title_chart,
        div_hist_age=div_hist_age,
        script_hist_age=script_hist_age,
        selected_class=selected_class
    )

################################################################################
#                            - END OF MAIN ROUTE -                             #
################################################################################


################################################################################
#                        > CHART GENERATION FUNCTIONS                          #
################################################################################

def survived_bar_chart(dataset, pass_class, cpalette=palette[1:3]):
    surv_data = dataset[dataset['Pclass'] == int(pass_class)]
    surv_possibilities = list(surv_data['Survived'].value_counts().index)
    surv_values = list(surv_data['Survived'].value_counts().values)
    surv_possibilities_text = ['Did not Survive', 'Survived']
        
    source = ColumnDataSource(data={
        'possibilities': surv_possibilities,
        'possibilities_txt': surv_possibilities_text,
        'values': surv_values
    })

    hover_tool = HoverTool(
        tooltips=[('Survived?', '@possibilities_txt'), ('Count', '@values')]
    )
    
    p = figure(tools=[hover_tool], plot_height=400, title='Did/Did not Survive for Current Class')
    p.vbar(x='possibilities', top='values', source=source, width=0.9,
           fill_color=factor_cmap('possibilities_txt', palette=palette_generator(len(source.data['possibilities_txt']), cpalette), factors=source.data['possibilities_txt']))
    
    plot_styler(p)
    p.xaxis.ticker = source.data['possibilities']
    p.xaxis.major_label_overrides = { 0: 'Did not Survive', 1: 'Survived' }
    p.sizing_mode = 'scale_width'
    
    return p


def class_titles_bar_chart(dataset, pass_class, cpalette=palette):
    ttl_data = dataset[dataset['Pclass'] == int(pass_class)]
    title_possibilities = list(ttl_data['Title'].value_counts().index)
    title_values = list(ttl_data['Title'].value_counts().values)
    int_possibilities = np.arange(len(title_possibilities))
    
    source = ColumnDataSource(data={
        'titles': title_possibilities,
        'titles_int': int_possibilities,
        'values': title_values
    })

    hover_tool = HoverTool(
        tooltips=[('Title', '@titles'), ('Count', '@values')]
    )
    
    chart_labels = {}
    for val1, val2 in zip(source.data['titles_int'], source.data['titles']):
        chart_labels.update({ int(val1): str(val2) })
        
    p = figure(tools=[hover_tool], plot_height=300, title='Titles for Current Class')
    p.vbar(x='titles_int', top='values', source=source, width=0.9,
           fill_color=factor_cmap('titles', palette=palette_generator(len(source.data['titles']), cpalette), factors=source.data['titles']))
    
    plot_styler(p)
    p.xaxis.ticker = source.data['titles_int']
    p.xaxis.major_label_overrides = chart_labels
    p.xaxis.major_label_orientation = math.pi / 4
    p.sizing_mode = 'scale_width'
    
    return p


def age_hist(dataset, pass_class, color=palette[1]):
    hist, edges = np.histogram(dataset[dataset['Pclass'] == int(pass_class)]['Age'].fillna(df['Age'].mean()), bins=25)
    
    source = ColumnDataSource({
        'hist': hist,
        'edges_left': edges[:-1],
        'edges_right': edges[1:]
    })

    hover_tool = HoverTool(
        tooltips=[('From', '@edges_left'), ('Thru', '@edges_right'), ('Count', '@hist')], 
        mode='vline'
    )
    
    p = figure(plot_height=400, title='Age Histogram', tools=[hover_tool])
    p.quad(top='hist', bottom=0, left='edges_left', right='edges_right', source=source,
            fill_color=color, line_color='black')

    plot_styler(p)
    p.sizing_mode = 'scale_width'

    return p

################################################################################
#                    - END OF CHART GENERATION FUNCTIONS -                     #
################################################################################



if __name__ == '__main__':
    app.run(debug=True)