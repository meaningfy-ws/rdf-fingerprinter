# file:     df_diff_stats
# created:  11/10/16
# author:   Eugeniu Costetchi
"""
this module generated descriptive statistics derived from the following spo query

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
from df_desc_stats import df_prop_stats
from pylatex import NoEscape, Section, Subsection

from fingerprint.df_tex_utils import transform_into_tabularx


def df_to_set_of_tuples(df, structural_columns=["stype", "p", "ootype"]):
    """
    :param df: the fingerprint dataframe
    :param structural_columns: in case it is a fingerprint with counts then this is an option
            to remove the count column, or select any combination of columns
    :return: set of tuples
    """
    return set([tuple(line) for line in df[structural_columns].values.tolist()])


def df_diff(alpha, beta, structural_columns=["stype", "p", "ootype"]):
    """
    provides the set difference between two data frames
    :param structural_columns:
    :param alpha: first dataframe
    :param beta: second dataframe
    :return: (a^b, a - b, b - a)
    """
    a = df_to_set_of_tuples(alpha, structural_columns)
    b = df_to_set_of_tuples(beta, structural_columns)
    return a.intersection(b), a.difference(b), b.difference(a)


def diff_to_latex_section(tex_doc, alpha, alpha_description, beta, beta_description, ):
    """
    :param tex_doc: the pylatex document
    :param alpha: the first fingerprint
    :param alpha_description: the first fingerprint description
    :param beta: the second fingerprint
    :param beta_description: the second fingerprint description
    :return: returns a section of latex document with deltas
    """

    alpha = df_prop_stats(alpha)
    beta = df_prop_stats(beta)
    cmn_s, adb_s, bda_s = df_diff(alpha, beta, structural_columns=['stype', 'p', 'ootype'])

    cols = ["Subject", "Predicate", "Object"] # list of columns for recreating dataframes from list of tuples
    cmn_df = pd.DataFrame(list(cmn_s), columns=cols, )
    cmn_df.sort_values(by=cols, inplace=True)

    adb_df = pd.DataFrame(list(adb_s), columns=cols, )
    adb_df.sort_values(by=cols, inplace=True)

    bda_df = pd.DataFrame(list(bda_s), columns=cols, )
    bda_df.sort_values(by=cols, inplace=True)

    ref_alpha = alpha_description["title"]
    ref_beta = beta_description["title"]

    section_title = 'Difference between ' + ref_alpha + ' and ' + ref_beta

    # if isLandscape:
    #     tex_doc = tex_doc.create(LandscapeEnvironment())
    #     with tex_doc.create(LandscapeEnvironment()):
    with tex_doc.create(Section(section_title)):
        # tex_doc.append(alpha_description)
        # tex_doc.append(beta_description)
        with tex_doc.create(Subsection("Common parts")) as subsec:
            subsec.append("The table below represents the elements common to both datasets.")

            # tex_doc.append(NoEscape(cmn_df.to_latex(longtable=True, index=False, na_rep="*")))
            tex_doc.append(NoEscape(transform_into_tabularx(
                    cmn_df.to_latex(longtable=True, index=False, float_format="%.2f", na_rep="*",
                                        column_format="llX"))))



        with tex_doc.create(Subsection("Unique to " + ref_alpha)) as subsec:
            subsec.append(
                "The table below represents the elements present in " + ref_alpha + " but missing in " + ref_beta + ".")
            # tex_doc.append(NoEscape(adb_df.to_latex(longtable=True, index=False, na_rep="*")))
            tex_doc.append(NoEscape(transform_into_tabularx(
                    adb_df.to_latex(longtable=True, index=False, float_format="%.2f", na_rep="*",
                                        column_format="llX"))))

        with tex_doc.create(Subsection("Unique to " + ref_beta)) as subsec:
            subsec.append(
                "The table below represents the elements present in " + ref_beta + " but missing in " + ref_alpha + ".")
            # tex_doc.append(NoEscape(bda_df.to_latex(longtable=True, index=False, na_rep="*")))
            tex_doc.append(NoEscape(transform_into_tabularx(
                    bda_df.to_latex(longtable=True, index=False, float_format="%.2f", na_rep="*",
                                        column_format="llX"))))



if __name__ == "__main__":
    pass
