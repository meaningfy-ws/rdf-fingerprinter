# file:     triple_profiler
# created:  05/10/16
# author:   Eugeniu Costetchi
# TODO: work towards refactoring of this file

from __future__ import division

from pylatex import Document, Package, Command
from pylatex.utils import NoEscape

from fingerprint.document.legacy_latex.df_desc_stats import df_stats_to_latex
from fingerprint.document.legacy_latex.df_diff_stats import diff_to_latex_section
from fingerprint.document.legacy_latex.df_io import read_prefixes, read_fp_spo_count, replace_ns, compile_tex_file_multipass, read_config

import click

class Config(object):
    """util class to pass the arguments from cli group to cli commands"""

    def __init__(self):
        self.verbose = False

# making the decorator that instantiates the config object at the group
# level and passes it as argument to the commands decorated with it
pass_config = click.make_pass_decorator(Config, ensure=True)

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


@click.group()
# @click.option("--verbose", is_flag=True)
# @click.option("--format", default="HTML", help="The output format of the parse results.")
# @click.option("--stanfordHome", help="The path to stanford parser home folder.")
# @pass_config
def cli():
    pass


@cli.command("csv")
@click.argument('config_fn', type=click.Path(exists=True))
# @pass_config
def generate_stats_csv(config_fn):
    """
    Generate the CSV file containing the processed statistics for AP generator
    :param config_fn:
    :return:
    """
    config = read_config(config_fn)
    print("Starting generation of CSV " + config["output"] + ".csv")
    ns = read_prefixes(config["ns_file"])
    fp_sp = read_fp_spo_count(config["alpha"]["file"])
    fp_sp = replace_ns(fp_sp, ns)
    fp_sp.to_csv(config["output"] + ".csv")
    print("Starting generation of " + config["output"])


@cli.command("stats")
@click.argument('config_fn', type=click.Path(exists=True))
# @pass_config
def generate_stats_document(config_fn):
    """
    Generates the PDF report using parameters from from config_fn JSON file
    :param config_fn: a file containing the script configuration parameters
    :return: None
    """
    config = read_config(config_fn)
    print("Starting generation of " + config["output"])

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
    fp_sp = read_fp_spo_count(config["alpha"]["file"])
    fp_sp = replace_ns(fp_sp, ns)

    df_stats_to_latex(doc, fp_sp, config["alpha"])

    doc.generate_tex(filepath=config["output"])
    compile_tex_file_multipass(config["output"])
    print("" + config["output"] + " successfully generated.")


@cli.command("diff")
@click.argument('config_fn', type=click.Path(exists=True))
# @pass_config
def generate_diff_document(config_fn):
    """
    Generates the diff PDF report using parameters from from config_fn JSON file
    :param config_fn: a file containing the script configuration parameters
    :return: None
    """
    config = read_config(config_fn)
    print("Starting generation of " + config["output"])

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
    # headder end

    ns = read_prefixes(config["ns_file"])
    alpha_spo = read_fp_spo_count(config["alpha"]["file"])
    alpha_spo = replace_ns(alpha_spo, ns)

    beta_spo = read_fp_spo_count(config["beta"]["file"])
    beta_spo = replace_ns(beta_spo, ns)

    diff_to_latex_section(doc, alpha_spo, config["alpha"], beta_spo, config["beta"])
    df_stats_to_latex(doc, alpha_spo, config["alpha"])
    df_stats_to_latex(doc, beta_spo, config["beta"])

    doc.generate_tex(filepath=config["output"])
    compile_tex_file_multipass(config["output"])
    print("" + config["output"] + " successfully generated.")

# if __name__ == "__main__":
#     cli()
