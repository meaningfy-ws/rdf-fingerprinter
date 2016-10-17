# file:     triple_profiler
# created:  05/10/16
# author:   Eugeniu Costetchi

from __future__ import division
from pylatex import Section, Subsection, Document, Package, Command
from pylatex.utils import NoEscape

from df_desc_stats import df_stats_to_latex, df_class_stats_to_latex
from df_diff_stats import diff_to_latex_section
from df_io import read_prefixes, read_fp_spo_count, replace_ns, compile_tex_file_multipass


configuration_dict = {
    "author": "Eugeniu Costetchi",
    "title": "EuroVoc Fingerprint Report - From Old to New and Back",
    "type": "difference between two dataset fingerprints",
    "ns_file": "resources/prefix.csv",
    "alpha": {"title": "EuroVoc 4.4",
              "filename": "resources/fingerprint.rq_eurovoc44.log",
              "desc": "EuroVoc 4.4 was released a long time ago using EuroVoc Ontology."},
    "beta": {"title": "EuroVoc 4.5(bc)",
             "filename": "resources/fingerprint.rq_EV45OLD.log",
             "desc": "EuroVoc 4.5 backward compatible (bc) was released in July 2016 with "
                     "SKOS-AP-EU and then converted to fit also the old profile of EuroVoc Ontology."},
}


def generate_stats_document(filename, config=configuration_dict):
    """
    :param filename: filename for the tex document
    :param config:
    :return: None
    """
    geometry_options = {
        "head": "40pt",
        "margin": "0.5in",
        "bottom": "0.6in",
        "includeheadfoot": True
    }
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
    fp_sp = read_fp_spo_count(config["alpha"]["filename"])
    fp_sp = replace_ns(fp_sp, ns)

    # df_stats_to_latex(doc, fp_sp, config["alpha"])
    df_stats_to_latex(doc, fp_sp, config["alpha"])

    doc.generate_tex(filepath=filename)
    compile_tex_file_multipass(filename)


def generate_diff_document(filename, config=configuration_dict):
    """
    :param filename: filename for the tex document
    :param config:
    :return: None
    """
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
    alpha_spo = read_fp_spo_count(config["alpha"]["filename"])
    alpha_spo = replace_ns(alpha_spo, ns)

    beta_spo = read_fp_spo_count(config["beta"]["filename"])
    beta_spo = replace_ns(beta_spo, ns)

    diff_to_latex_section(doc, alpha_spo, config["alpha"], beta_spo, config["beta"])
    df_stats_to_latex(doc, alpha_spo, config["alpha"])
    df_stats_to_latex(doc, beta_spo, config["beta"])

    doc.generate_tex(filepath=filename)
    compile_tex_file_multipass(filename)

if __name__ == "__main__":
    generate_diff_document("temp/diff_report", configuration_dict)