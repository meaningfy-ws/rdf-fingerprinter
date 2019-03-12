# file:     df_stats
# created:  11/10/16
# author:   Eugeniu Costetchi
# TODO: work towards refactoring of this file
"""
    this module generates descriptive statistics based on the spo query below
    data fingerprint work columns are:
        "stype",
        "p",
        "ootype",
        "propType",
        "scnt",
        "ocnt",
        "cnt",
        "min_sp",
        "max_sp",
        "avg_sp"

    select distinct ?stype ?p ?ootype ?propType (count(distinct ?s) as ?scnt) (count(distinct ?o) as ?ocnt)
    (count(*) as ?cnt) (min(?sp_star) as ?min_sp) (max(?sp_star) as ?max_sp) (avg(?sp_star) as ?avg_sp)
    where
    {

      ?s ?p ?o .
      ?s a ?stype .
      optional {
        ?o a ?otype .
      }
      {
        select distinct ?s ?p (count(*)as ?sp_star)
                  {
                    ?s ?p [].
                  } group by ?s ?p
      }
      bind( if(?p=rdf:type, ?stype, if(bound(?otype),?otype, datatype(?o) )) as ?ootype )
      bind( if(?p=rdf:type,"object", if(bound(?otype),"object","data")) as ?propType)
    }
    group by ?stype ?p ?ootype ?propType
    order by ?stype ?p ?ootype ?propType

"""

import pandas as pd
from deprecated import deprecated
from pylatex import NoEscape, Section, Subsection, Subsubsection

from fingerprint.df_tex_utils import transform_into_tabularx


def df_class_stats(df):
    """
    basic class statistics
    :param df:
    :return:
    """
    df = df[df['p'] == 'rdf:type'][['stype', 'scnt']].sort_values(by='scnt', ascending=False)
    total_scnt = df['scnt'].sum()
    df['rel_stype_scnt'] = df['scnt'] / total_scnt * 100
    return df


def df_class_stats_to_latex(tex_doc, df, description):
    """
    append class stats to tex document
    depends on df_class_stats
    :param df:
    :param tex_doc:
    :param description:
    :return:
    """
    df = df_class_stats(df)
    df.rename(columns={'stype': 'Class', 'scnt': 'Unique instances', 'rel_stype_scnt': '% unique instance sum'},
              inplace=True)
    # the story of class stats
    with tex_doc.create(Subsection("Class instantiation overview for " + description['title'])):
        tex_doc.append('The table below describes how are classes instantiated. Please note that the instance counts'
                       'are different from total number of unique instances in the data-set. When an individual'
                       'instantiates multiple classes, then it is counted once for each class it instantiates. The relative'
                       'number of instances is scaled to the total number of unique instances per class.')
        tex_doc.append(NoEscape(df.to_latex(longtable=True, index=False, float_format=lambda x: "%.2f" % x)))


confidence = {"certain": 93, "likely": 86, "possible": 47, "unlikely": 12, "rare": 5, "very rare": -1}


def confidence_category(r, conf=confidence):
    """
    :param r: target relative number , expected between 0 and 100
    :param confidence: category definitions
    :return: the category given a target number
    """
    confidence_inv = {v: k for k, v in confidence.items()}
    return confidence_inv[max([x for x in confidence_inv.keys() if r >= x])]


def df_prop_stats(df, conf=confidence):
    """
     for each group of ['stype','p'] aim at reducing duplicates to one record bu following method.
     If the 'propType' is 'data' then sum the 'scnt', 'ocnt', 'cnt' and average the 'min_sp',
     'max_sp' and 'avg_sp'.  If the 'propType' is 'object' then expect the numbers to be exactly the
     same on every row and then just copy the values of the first row.

     :param df: the original dataframe
     :returns  a richer dataframe containing two more columns with relative values. the additional columns are
     ['scnt/type-scnt',cnt/type-cnt]
    """

    df_reduced = pd.DataFrame(columns=df.columns)

    # reducing the groups to single row groups
    # iterate over the groups of ['stype', 'p']
    for name, group in df.groupby(['stype', 'p']):
        if len(group) > 1:
            if len(group[group['propType'] == 'data']['propType']) > 0:
                # process data rows
                aggregated = {'stype': name[0], 'p': name[1], 'propType': 'data', }
                aggregated['scnt'] = [group['scnt'].sum()]
                aggregated['ocnt'] = [group['ocnt'].sum()]
                aggregated['cnt'] = [group['cnt'].sum()]
                aggregated['min_sp'] = [group['min_sp'].min()]
                aggregated['max_sp'] = [group['max_sp'].max()]
                aggregated['avg_sp'] = [group['avg_sp'].mean()]
                aggregated['ootype'] = ", ".join(group['ootype'].astype(str))
                df_reduced = df_reduced.append(pd.DataFrame(aggregated, columns=df.columns))
            elif len(group[group['propType'] == 'object']['propType']) > 0:
                # process object rows
                g = group[0:1]
                g['ootype'].iloc[0] = ", ".join(group['ootype'])
                df_reduced = df_reduced.append(g)
            else:
                # serios offense this palce should never be reached
                raise Exception("Is the query distinguishing more then two types of properties?")
        else:
            # simple group of single row
            df_reduced = df_reduced.append(group)

    # Next step
    df_stats = None

    # confidence_inv = {v: k for k, v in confidence.iteritems()}

    # calculating the averages and relatives per class for each property
    # iterate over the groups of ['stype']
    for name, group in df_reduced.groupby(['stype']):
        if not group.index.is_unique:
            group.reset_index(inplace=True)
        type_scnt = group[group['p'] == 'rdf:type']['scnt'].iloc[0]
        type_cnt = group[group['p'] == 'rdf:type']['cnt'].iloc[0]
        group["scnt/type-scnt"] = group['scnt'] / type_scnt * 100
        group["cnt/type-cnt"] = group['cnt'] / max(group['cnt']) * 100
        group['min_ap'] = group[group['scnt/type-scnt'] > conf['likely']]['min_sp'].astype(int).astype(str)
        group['min_ap'].fillna(0, inplace=True)
        group['max_ap'] = group[(group['scnt/type-scnt'] > conf['likely']) & (group['max_sp'] == 1)][
            'max_sp'].astype(int).astype(str)
        group['max_ap'].fillna("*", inplace=True)

        group["card"] = group['min_ap'].astype(str) + " .. " + group['max_ap']
        group["conf"] = group['scnt/type-scnt'].apply(confidence_category, confidence)
        if df_stats is None:
            df_stats = pd.DataFrame(columns=group.columns)
        df_stats = df_stats.append(group)
    return df_stats


def custom_type_cast(group):
    group['cnt'] = group['cnt'].astype(int)
    group['scnt'] = group['scnt'].astype(int)
    group['min_sp'] = group['min_sp'].astype(int)
    group['max_sp'] = group['max_sp'].astype(int)
    group['avg_sp'] = group['avg_sp'].astype(int)
    group['scnt/type-scnt'] = group['scnt/type-scnt'].astype(int)
    group['cnt/type-cnt'] = group['cnt/type-cnt'].astype(int)


def df_prop_stats_to_latex(tex_doc, df, description):
    ppdf = df_prop_stats(df)
    custom_type_cast(ppdf)
    with tex_doc.create(Subsection("Property usage statistics for " + description['title'])):
        #  TODO: insert table descriptions
        tex_doc.append("This section provides descriptive statistical indicators for each class."
                       "The tables below contain the following columns: property name, absolute "
                       "normalised usage (Norm usg/a), absolute actual usage(Usage/a), normalised "
                       "minimum (Min), normalised maximum (Max), normalised average (Avg), "
                       "relative normalised usage (Norm usg/r), relative actual usage (Usage/r)."
                       "\n\n"
                       "The normalization mentioned above refers to counting out of all class"
                       "individuals how many are actually using the property at least once while"
                       "the actual property usage refers to counting all occurrences for a given class."
                       "The rdf:type property plays a special role because it indicates the number"
                       "of unique class instances and in case of multiple class instantiation the number "
                       "is scaled by the  number of distinct parent classes. "
                       "\n\n"
                       "The relative actual usage (Usage/r) is calculated with respect to a sibling property "
                       "that maximally occurs in all class instances. Therefore there is no standard property"
                       "to be chosen as reference like in the case of rdf:type but it varies from case to case.")
        for name, group in ppdf.groupby('stype'):
            with tex_doc.create(Subsubsection("Propoerty statistics for " + name + " class")):
                # select only a few columns
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
                tex_doc.append(NoEscape(group.to_latex(longtable=True, index=False, float_format=lambda x: "%.2f" % x)))


def df_ap_guess_to_latex(tex_doc, df, description):
    """
    cl, prop, propType, otype, min, max, confidence

    confidence table: certain, highly probable, likely, possible, unlikely, very rare

    cardinality: [0..max(avg)] = conf < highly probable
                 [1..max(avg)] = conf > certain

    out of AP (blacklist) * props that are < possible

    tries to guess the ap ued in the data

    :param df:
    :return:
    """
    ppdf = df_prop_stats(df)
    custom_type_cast(ppdf)
    with tex_doc.create(Subsection("Application profile reconstruction for " + description['title'])):
        # TODO: insert description of tables
        tex_doc.append("This section attempts at reconstructing the profiled shapes for each class. "
                       "The profile is deduced based on descriptive statistics presented elsewhere. "
                       "The tables below contain the following columns: Property name, Cardinality, "
                       "Property Type, Property Range and Confidence. \n\n Confidence is a categorial value "
                       "derived from the property usage relative to the total number of unique individuals "
                       "instantiating this class.Property range is a list of distinct encountered object "
                       "types. In case of higher number of object type the list is non-exhaustive. "
                       "Cardinality of the property is expressed in terms of minimum and maximum occurrences "
                       "of the property. The minimum value varies from zero (0) meaning that the property is "
                       "optional to one (1) meaning that the property is mandatory while the maximum value varies"
                       "from one (1) meaning that the property is sufficient to star (*) meaning that the "
                       "property is maximally unbound. Finally the type indicates whether the property range"
                       "is whether a data type or an individual URI.")
        for name, group in ppdf.groupby('stype'):
            with tex_doc.create(Subsubsection("Estimated Application Profile for " + name + " class")):
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
                tex_doc.append(NoEscape(transform_into_tabularx(
                    group.to_latex(longtable=True, index=False, float_format=lambda x: "%.2f" % x, na_rep="*",
                                   column_format="lllXr"))))


@deprecated
def generate_missing_ns(df, structural_columns=['stype', 'p', 'ootype']):
    """
    given a dataframe detect unique namespaces
    :param df:
    :return:
    """
    unique_uris = set()
    for col in structural_columns:
        unique_uris = unique_uris.union(set(df[col]))
    print(unique_uris)


def df_stats_to_latex(tex_doc, df, description):
    """
    :param tex_doc: the pylatex document
    :param df: the fingerprint data frame
    """
    # total_triples, class_stats, prop_stats = df_stats_calculation(df)
    # pprint(prop_stats)
    with tex_doc.create(Section("What do data say about " + description['title'])):
        # TODO: add acknowledgements and footnote that this is automatically generated with this software
        # adding instantiation description
        df_class_stats_to_latex(tex_doc, df, description)
        df_ap_guess_to_latex(tex_doc, df, description)
        df_prop_stats_to_latex(tex_doc, df, description)


if __name__ == "__main__":
    pass
