# file:     triple_profiler
# created:  05/10/16
# author:   Eugeniu Costetchi

from __future__ import division

import os

from pylatex import Document, Package, Command
from pylatex.utils import NoEscape

from fingerprint.df_desc_stats import df_stats_to_latex, confidence_category
from fingerprint.df_diff_stats import diff_to_latex_section
from fingerprint.df_io import read_prefixes, read_fp_spo_count, replace_ns, compile_tex_file_multipass, read_config

import json

# import click

configuration_dict = {
    "author": "Generated with RDF Fingerprinter (by Eugeniu Costetchi)",
    "title-stats": "Data-set Fingerprint Report - Application Profile and descriptive statistics",
    "title-diff": "Data-set Fingerprint Diff Report - Application Profile Diffs and descriptive statistics",
    # "type": "difference between two dataset fingerprints",
    "ns_file": "resources/prefix.csv",
    "alpha": {"title": "EuroVoc 4.4",
              "filename": "resources/fingerprint.rq_eurovoc44.log",
              "desc": "EuroVoc 4.4 was released a long time ago using EuroVoc Ontology."},
    "beta": {"title": "EuroVoc 4.5(bc)",
             "filename": "resources/fingerprint.rq_EV45OLD.log",
             "desc": "EuroVoc 4.5 backward compatible (bc) was released in July 2016 with "
                     "SKOS-AP-EU and then converted to fit also the old profile of EuroVoc Ontology."},
}


# @click.group()
# def cli():
#     pass

def generate_stats_csv(output, alpha_filename, config=configuration_dict):
    ns = read_prefixes(config["ns_file"])
    fp_sp = read_fp_spo_count(alpha_filename)
    fp_sp = replace_ns(fp_sp, ns)
    fp_sp.to_csv(output)


# @cli.command("stats")
# @click.argument('filename', type=click.Path(exists=False))
# @click.argument('cfile', type=click.Path(exists=True))
def generate_stats_document(config_fn):
    """
    Generates the PDF report using parameters from from config_fn JSON file
    :param config_fn: a file containing the script configuration parameters
    :return: None
    """
    config = read_config(config_fn)

    doc = Document(documentclass=Command(command="documentclass", arguments=["article"],
                                         options=["10pt", "a4paper", "titlepage", "final"]))

    doc.packages.append(Package('longtable'))
    doc.packages.append(Package('booktabs'))
    doc.packages.append(Package('float'))
    doc.packages.append(Package('ltablex'))
    doc.packages.append(Package('geometry', options=["left=2.00cm", "right=2.00cm", "top=2.00cm", "bottom=2.00cm"]))

    doc.preamble.append(NoEscape("\\author{" + config["author"] + "}"))
    doc.preamble.append(NoEscape("\\title{" + config["title"] + "}"))
    doc.append(Command(command="maketitle"))
    doc.append(Command(command="tableofcontents"))
    doc.append(Command(command="newpage"))
    # header end

    ns = read_prefixes(config["ns_file"])
    fp_sp = read_fp_spo_count(config["alpha"]["file"]["path"])
    fp_sp = replace_ns(fp_sp, ns)

    df_stats_to_latex(doc, fp_sp, config["alpha"])

    doc.generate_tex(filepath=config["output"])
    compile_tex_file_multipass(config["output"])


# @cli.command("diff")
# @click.argument('filename', type=click.Path(exists=False))
# @click.argument('cfile', type=click.Path(exists=True))
def generate_diff_document(output_fn, alpha_filename, alpha_description, beta_filename, beta_description,
                           config=configuration_dict):
    """
    :param beta_description:
    :param beta_filename:
    :param alpha_description:
    :param alpha_filename:
    :param config:
    :param output_fn: filename for the tex document
    :return: None
    """
    config['alpha'] = {}
    config['alpha']['title'] = os.path.basename(alpha_filename) + ' dataset'
    config['alpha']['filename'] = alpha_filename
    config['alpha']['desc'] = alpha_description

    config['beta'] = {}
    config['beta']['title'] = os.path.basename(beta_filename) + ' dataset'
    config['beta']['filename'] = beta_filename
    config['beta']['desc'] = beta_description

    doc = Document(documentclass=Command(command="documentclass", arguments=["article"],
                                         options=["10pt", "a4paper", "titlepage", "final"]))
    doc.packages.append(Package('longtable'))
    doc.packages.append(Package('booktabs'))
    doc.packages.append(Package('float'))
    doc.packages.append(Package('ltablex'))
    doc.packages.append(Package('geometry', options=["left=2.00cm", "right=2.00cm", "top=2.00cm", "bottom=2.00cm"]))
    doc.preamble.append(NoEscape("\\author{" + config["author"] + "}"))
    doc.preamble.append(NoEscape("\\title{" + config["title-diff"] + "}"))
    doc.append(Command(command="maketitle"))
    doc.append(Command(command="tableofcontents"))

    doc.append(Command(command="newpage"))
    # headder end

    ns = read_prefixes(config["ns_file"])
    alpha_spo = read_fp_spo_count(config["alpha"]["filename"])
    alpha_spo = replace_ns(alpha_spo, ns)

    beta_spo = read_fp_spo_count(config["beta"]["filename"])
    beta_spo = replace_ns(beta_spo, ns)

    diff_to_latex_section(doc, alpha_spo, config["alpha"], beta_spo, config["beta"])
    df_stats_to_latex(doc, alpha_spo, config["alpha"])
    df_stats_to_latex(doc, beta_spo, config["beta"])

    doc.generate_tex(filepath=output_fn)
    compile_tex_file_multipass(output_fn)


if __name__ == "__main__":
    # generate_diff_document("temp/diff_report", )
    # generate_stats_document(output_fn='temp/stats',  alpha_filename='resources/fingerprint.rq_eurovoc44.log',
    #                         alpha_description="Some dataset")

    # generate_diff_document(output_fn='temp/stats',  alpha_filename='resources/fingerprint.rq_eurovoc44.log',
    #                         alpha_description="Some dataset", beta_filename='resources/fingerprint.rq_EV45OLD.log',
    #                        beta_description="Some other dataset")
    # generate_stats('temp/stats.csv',  'resources/fingerprint.rq_eurovoc44.log')

    pass
    # generate_stats_document('./resources/config_37cd5ef2-2a98-4974-87ab-92823d5c33ed.json')
    # cli()
