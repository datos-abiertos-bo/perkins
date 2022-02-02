import random

import numpy as np
import pandas as pd


def build_query(
    connection,
    from_tables,
    select_columns,
    where_conditions=[],
    order_by=[]
):
    application_context = connection['application_context']
    model_id = connection['model_id']

    return {
      "version": "1.0.0",
      "queries": [{
        "Query": {
          "Commands": [{
            "SemanticQueryDataShapeCommand": {
              "Query": {
                "Version": 2,
                "From": from_tables,
                "Select": select_columns,
                "Where": where_conditions,
                "OrderBy": order_by
              },
              "Binding": {
                "Primary": {
                  "Groupings": [{
                    "Projections": [*range(len(select_columns))]
                  }]
                },
                "DataReduction": {
                  "DataVolume": 6,
                  "Primary": {
                    "BinnedLineSample": {},
                  }
                },
                "Version": 1
              }
            }
          }]
        },
        "CacheKey": "test_query: {}".format(random.random()),
        "QueryId": "",
        "ApplicationContext": application_context
      }],
      "cancelQueries": [],
      "modelId": model_id
    }


def build_fields(table, column, type='Column', op=None):
    name = "{}.{}".format(table['Entity'], column)
    if op is not None:
        name = '{}({})'.format(op, name)

    return {
      type: {
        "Expression": {
          "SourceRef": {
            "Source": table['Name']
          }
        },
        "Property": column
      },
      "Name": name
    }


def build_where(table, column, value, kind=2, type='Column', condition='Comparison'):
    column = {
        type: {
            'Expression': {
                'SourceRef': {'Source': table['Name']}
            },
            'Property': column
        }
    }
    value = {'Literal': {'Value': value}}

    if condition == 'Comparison':
        condition = {
            'Comparison': {
                'ComparisonKind': kind,
                'Left': column,
                'Right': value
            }
        }

    elif condition == 'In':
        condition = {
            'In': {
                'Expressions': [column],
                'Values': [[value]]
            }
        }

    else:
        raise(Exception('Not supported condition: {}'.format(condition)))

    return {'Condition': condition}


def inflate_data(data, columns):
    data_store = data['results'][0]['result']['data']['dsr']['DS'][0]['PH'][0]['DM0']
    inflated_data = [data_store[0]['C']]

    for data_element in data_store[1:]:
        arr = np.full(len(columns), '', dtype=object)
        mask = np.full(len(columns), False)

        if 'R' in data_element.keys():
            mask = np.array([
                bool(data_element['R'] & (1<<n)) for n in range(len(columns))
            ])

        if 'Ø' in data_element.keys():
            negative_mask = ~np.array([
                bool(data_element['Ø'] & (1<<n)) for n in range(len(columns))
            ])
            arr[negative_mask] = '--'

            mask = ~mask & negative_mask
            mask = ~mask

        arr[~mask] = data_element['C']

        inflated_data.append(arr)

    inflated_data = pd.DataFrame(inflated_data, columns=columns)

    return inflated_data
