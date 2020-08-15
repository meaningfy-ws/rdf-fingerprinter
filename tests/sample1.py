import pathlib
import pandas as pd

import jinja2

from fingerprint.document.legacy_latex.df_desc_stats import df_prop_stats, custom_type_cast, df_class_stats
from fingerprint.document.legacy_latex.df_io import read_prefixes, read_fp_spo_count, replace_ns


def spo_to_profiles(alpha_spo):
    result = []
    for name, group in alpha_spo.groupby('stype'):
        # select only a few columns
        group = group.sort_values(['scnt/type-scnt', 'card', 'p'], ascending=False)
        group = group[['p', 'card', 'propType', 'ootype', "conf"]]
        # rename column names
        group.rename(columns={'stype': 'Class',
                              'scnt': 'Norm usg/a',  # absolute normalised usage
                              'cnt': 'Usage/a',  # absolute usage
                              'p': 'Property',
                              'min_sp': 'Min',
                              'max_sp': 'Max',
                              'avg_sp': 'Avg',
                              'ootype': 'Range',
                              'propType': 'Type',
                              'card': 'Cardinality',
                              "scnt/type-scnt": 'Norm usg/r',  # relative normalised usage
                              "cnt/type-cnt": 'Usage/r',  # relative usage
                              "conf": 'Confidence',
                              },
                     inplace=True)
        result.append((name, group))
    return result


def property_usage_stats(ppdf):
    result = []
    for name, group in ppdf.groupby('stype'):
        group = group[
            ['p', 'scnt', 'cnt', 'min_sp', 'max_sp', 'avg_sp', "scnt/type-scnt", "cnt/type-cnt", ]].sort_values(
            ['scnt', 'cnt', 'p'], ascending=False)
        # rename column names
        group.rename(columns={'stype': 'Class',
                              'scnt': 'Norm usg/a',  # absolute normalised usage
                              'cnt': 'Usage/a',  # absolute usage
                              'p': 'Property',
                              'min_sp': 'Min',
                              'max_sp': 'Max',
                              'avg_sp': 'Avg',
                              "scnt/type-scnt": 'Norm usg/r',  # relative normalised usage
                              "cnt/type-cnt": 'Usage/r',  # relative usage
                              },
                     inplace=True)
        result.append((name, group))
    return result


template_folder = pathlib.Path(__file__).parents[1] / "resources" / "templates" / "pubap" / "fragments"
resources_folder = pathlib.Path(__file__).parents[1] / "resources"
output_file = template_folder.parent / "index.html"

TEMPLATE_FILE = "doc.html"

templateLoader = jinja2.FileSystemLoader(searchpath=str(template_folder))
templateEnv = jinja2.Environment(loader=templateLoader)

TEMPLATE_FILE = "main.html"
template = templateEnv.get_template(TEMPLATE_FILE)

df = pd.DataFrame(data={'col1': [1, 2], 'col2': [3, 4]})
sample_description = {
    "title": "EuroVoc Fingerprint Report - From Old to New and Back",
    "type": "difference between two dataset fingerprints",
    "author": "Eugeniu Costetchi",
    "ns_file": str(resources_folder / "prefix.csv"),
    "output": str(output_file),
    "alpha": {
        "file": str(resources_folder / "samples" / "fingerprint.rq_eurovoc44.log.csv"),
        "title": "EuroVoc 4.4",
        "desc": "EuroVoc 4.4 was released a long time ago using EuroVoc Ontology."
    },
    "beta": {
        "file": str(resources_folder / "fingerprint.rq_EV45OLD.log.csv"),
        "title": "EuroVoc 4.5(bc)",
        "desc": "EuroVoc 4.5 backward compatible (bc) was released in July 2016 with SKOS-AP-EU and then converted to fit also the old profile of EuroVoc Ontology."
    }
}

# initital phase
config = sample_description
print("Starting generation of CSV " + config["output"] + ".csv")

ns = read_prefixes(config["ns_file"])
alpha_spo = read_fp_spo_count(config["alpha"]["file"])
alpha_spo = replace_ns(alpha_spo, ns)

# class stats data
df_class_stats = df_class_stats(alpha_spo)
df_class_stats.rename(columns={'stype': 'Class', 'scnt': 'Unique instances', 'rel_stype_scnt': '% unique instance sum'},
                      inplace=True)

#  application profile data
per_class_profile = df_prop_stats(alpha_spo)
custom_type_cast(per_class_profile)
application_profiles = spo_to_profiles(per_class_profile)

# appending: property usage statistics
property_usage = property_usage_stats(per_class_profile)

# outputText = template.render(general=sample_description, class_overview=df)
template.stream(general=sample_description,
                class_overview=df_class_stats,
                application_profiles=application_profiles,
                property_usage=property_usage).dump(
    config["output"])
