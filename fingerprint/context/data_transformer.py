""" 
data_transformer
Created:  11/03/2019
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com

atomic data transformation operations based on configurations

todo: implement, type cast, column rename , sort, column format

"""
from abc import ABC, abstractmethod
import numpy as np


class DataTransformer(ABC):
    def __init__(self, data_frame):
        """
        generic data transformer generator
        """
        self.data_frame = data_frame

    @abstractmethod
    def transform(self):
        """
        transform the data frame and return a data frame
        """
        pass


class ColumnRenamer(DataTransformer):
    def __init__(self, data_frame, name_mapping_dict):
        """
            rename columns of the data_frame as described in  name_mapping_dict
        :param data_frame: the data
        :param name_mapping_dict: contains a dict of the shape
                {"current_column_name 1":"new_column_name 1",
                 "current_column_name 2":"new_column_name 2", ...}
                  dict values must be unique (1-to-1). Labels not contained in a dict will be left as-is.
                  Extra labels listed don’t throw an error.
        """
        super(ColumnRenamer, self).__init__(data_frame)
        self.name_mapping_dict = name_mapping_dict

    def transform(self):
        return self.data_frame.rename(index=str, columns=self.name_mapping_dict)


class StringStripper(DataTransformer):
    def __init__(self, data_frame, target_columns):
        """
            trims the values from the target columns removing extra blank spaces
        :param data_frame: the data
        :param target_columns: the columns that will be subject to change
        """
        super(StringStripper, self).__init__(data_frame)
        self.target_columns = target_columns

    def transform(self):
        # get all the string columns
        obj_columns = self.data_frame.select_dtypes([np.object]).columns  # [1:]
        # limit to columns indicated in the self.target_columns
        if self.target_columns:
            obj_columns = [column for column in obj_columns if column in self.target_columns]
        self.data_frame[obj_columns] = self.data_frame[obj_columns].apply(lambda x: x.str.strip())
        return self.data_frame


class StringReplacer(DataTransformer):
    def __init__(self, data_frame, target_columns, value_mapping_dict):
        """
            replaces the string values from the target columns with new values as described in the value_mapping_dict
        :param data_frame: the data
        :param target_columns:  the columns that will be subject to change
        :param value_mapping_dict: the mapping rules as a dictionary of the following structure
                {"current value 1":"current value 1",
                 "current value 2":"current value 2", ...}
        """
        super(StringReplacer, self).__init__(data_frame)
        self.target_columns = target_columns
        self.value_mapping_dict = value_mapping_dict

    def transform(self):
        # get all the string columns
        obj_columns = self.data_frame.select_dtypes([np.object]).columns  # [1:]
        # columns = self.target_columns if self.target_columns else self.data_frame.columns
        # limit to columns indicated in the self.target_columns
        if self.target_columns:
            obj_columns = [column for column in obj_columns if column in self.target_columns]
        # create a nested dictionary that pandas replace understand
        # For a DataFrame nested dictionaries, e.g., {'a': {'b': np.nan}},
        # are read as follows: look in column ‘a’ for the value ‘b’ and
        # replace it with NaN. The value parameter should be None
        # to use a nested dict in this way.
        nested_dict = {column: self.value_mapping_dict for column in obj_columns}
        self.data_frame[obj_columns] = self.data_frame[obj_columns].replace(to_replace=nested_dict, value=None)
        return self.data_frame


class NamespaceReducer(DataTransformer):
    def __init__(self, data_frame, target_columns, namespace_mapping_dict):
        """

        :param data_frame:
        :param target_columns:
        :param namespace_mapping_dict:
        """
        super(StringReplacer, self).__init__(data_frame)
        self.target_columns = target_columns
        self.namespace_mapping_dict = namespace_mapping_dict

    def transform(self):
        # todo: continue here
        pass


class TypeCaster(DataTransformer):
    def __init__(self, data_frame, column_type_dict):
        super(TypeCaster, self).__init__(data_frame)
        self.column_type_dict = column_type_dict

    def transform(self):
        # todo, implement
        pass


class ColumnFormatter(DataTransformer):
    def __init__(self, data_frame, column_format_dict):
        super(ColumnFormatter, self).__init__(data_frame)
        self.column_format_dict = column_format_dict

    def transform(self):
        # todo, implement
        pass
