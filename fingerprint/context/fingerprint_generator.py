""" 
fingerprint_generator
Created:  19/03/2019
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com


    This module generates descriptive statistics based on the spo query below.
    The assumption is that the SPARQL query is executed at an endpoint and the
    result is available as an CSV file.

    The aim is to populate build a context object that can further be used to
    populate a document template.

    The work columns are:
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

    SPARQL query:
    ---
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
    ---

"""

# todo: write the fingerprint data context generaor
from fingerprint.context.context_generator import DataContextGenerator
from fingerprint.context.iri_utils import NamespaceReducer
import pandas as pd
from deprecated import deprecated


class ApplicationProfileContextGenerator(DataContextGenerator):
    def __init__(self, alpha, beta=None, namespace_mapping_dict={}):
        """
            Fingerprinter data context is:
                - dataset stats for alpha and beta
                - dataset application profiles for alpha and beta
                - difference between alpha and beta application profiles

        :param alpha: - the alpha tabular
        :param beta: - the beta tabular
        :param gamma: - the gamma tabular
        :param namespace_mapping_dict - the namespace mapping dict
        """
        # self.configuration = configuration
        self.alpha = alpha
        self.beta = beta
        self.namespace_mapping_dict = namespace_mapping_dict

    def generate(self):
        self.reduce_namespaces()
        result = {"alpha": {}, "beta": {}}

        # column mapping from technical to publishable
        class_statistics_columns = {'stype': 'Class', 'scnt': 'Unique instances',
                                    'rel_stype_scnt': '% unique instance sum'}

        # alpha: generate the class statistics and rename the columns

        alpha_class_statistics = df_class_stats(self.alpha)
        alpha_class_statistics.rename(
            columns=class_statistics_columns,
            inplace=True)
        result["alpha"]["class_statistics"] = alpha_class_statistics

        # beta: generate the class statistics and rename the columns
        if self.beta is not None:
            beta_class_statistics = df_class_stats(self.beta)
            beta_class_statistics.rename(
                columns=class_statistics_columns,
                inplace=True)
            result["beta"]["class_statistics"] = beta_class_statistics

        # alpha: AP

        # alpha: per class profile
        alpha_per_class_profile = df_prop_stats(self.alpha)
        custom_type_cast(alpha_per_class_profile)

        # alpha: per class property usage statistics
        alpha_property_usages = property_usage_stats(alpha_per_class_profile)
        result["alpha"]["property_usages"] = alpha_property_usages

        # alpha: per class application profile
        alpha_application_profiles = spo_to_profiles(alpha_per_class_profile)
        result["alpha"]["application_profiles"] = alpha_application_profiles

        # beta: AP
        if self.beta is not None:
            # alpha: per class profile
            beta_per_class_profile = df_prop_stats(self.alpha)
            custom_type_cast(beta_per_class_profile)

            # beta: per class property usage statistics
            beta_property_usages = property_usage_stats(beta_per_class_profile)
            result["beta"]["property_usages"] = beta_property_usages

            # beta: per class application profile
            beta_application_profiles = spo_to_profiles(beta_per_class_profile)
            result["beta"]["application_profiles"] = beta_application_profiles

        # todo: implement the diff statistics into the data context

        return result

    def reduce_namespaces(self):
        """
            reduce namespaces to prefixes in alpha and beta data-sets
        :return:
        """
        self.alpha = NamespaceReducer(data_frame=self.alpha,
                                      namespace_mapping_dict=self.namespace_mapping_dict).transform()
        if self.beta is not None:
            self.beta = NamespaceReducer(data_frame=self.beta,
                                         namespace_mapping_dict=self.namespace_mapping_dict).transform()

    def generate_dataset_diff(self):
        """
            if beta is available, generate the diff between the application profiles
        :return:
        """
        pass


class LexicalisationProfileContextGenerator(DataContextGenerator):
    """
                - link-set stats for gamma
                - link-set stats in relation to alpha and beta
                - lexicalisation stats for alpha
                - lexicalisation stats for beta
                - link-set lexicalisation stats in relation to alpha and beta
        #todo: implement
    """


@deprecated
def df_class_stats(df):
    """
    # todo refactor
    basic class statistics
    :param df:
    :return:
    """
    df = df[df['p'] == 'rdf:type'][['stype', 'scnt']].sort_values(by='scnt', ascending=False)
    total_scnt = df['scnt'].sum()
    df['rel_stype_scnt'] = df['scnt'] / total_scnt * 100
    return df


confidence = {"certain": 93, "likely": 86, "possible": 47, "unlikely": 12, "rare": 5, "very rare": -1}

# silence the warnings about chained assignments
pd.options.mode.chained_assignment = None  # default='warn'

@deprecated
def confidence_category(r, conf=confidence):
    """
    :param r: target relative number , expected between 0 and 100
    :param confidence: category definitions
    :return: the category given a target number
    """
    confidence_inv = {v: k for k, v in confidence.items()}
    return confidence_inv[max([x for x in confidence_inv.keys() if r >= x])]


@deprecated
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
                g = group[0:1].copy()
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
        # if not group.index.is_unique:
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


@deprecated
def custom_type_cast(group):
    group['cnt'] = group['cnt'].astype(int)
    group['scnt'] = group['scnt'].astype(int)
    group['min_sp'] = group['min_sp'].astype(int)
    group['max_sp'] = group['max_sp'].astype(int)
    group['avg_sp'] = group['avg_sp'].astype(int)
    group['scnt/type-scnt'] = group['scnt/type-scnt'].astype(int)
    group['cnt/type-cnt'] = group['cnt/type-cnt'].astype(int)


@deprecated
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


@deprecated
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
