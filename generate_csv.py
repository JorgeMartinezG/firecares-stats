import json
import os
import pandas as pd
import requests

from glob import glob

from urllib.parse import urlencode


def create_fd_groups(api_key):
    groups = 'https://firecares.freshdesk.com/api/v2/groups'
    response_groups = requests.get(groups, auth=(api_key, 'X')).json()
    fd_groups = {x['id']: x['name'] for x in response_groups}

    return fd_groups


def include_stats_fields(ticket):
    for key, value in ticket['stats'].items():
        ticket[key] = value

    return ticket


def save_response(response, page_no, folder_name='jsons'):
    # Create folder if does not exist.
    if not os.path.isdir(folder_name):
        os.makedirs(folder_name)

    # Save results into file.
    with open(os.path.join(folder_name, '{0}.json'.format(page_no)), 'w') as f:
        json.dump(response, f, indent=4)


def get_firecares_response(page_number, query_string, api_key):
    endpoint = 'https://firecares.freshdesk.com/api/v2/tickets?'
    query_string['page'] = page_number

    # Perform request to given url.
    response = requests.get(url=endpoint + urlencode(query_string),
                            auth=(api_key, 'X')).json()

    # Including stats into one higher level in json tree.
    response = [include_stats_fields(ticket) for ticket in response]

    # Save response into json file.
    #save_response(response.json(), page_number)
    return response


def Main():
    # Define parameters.
    number_pages = range(1, 13)
    api_key = 'CHANGEME'
    # Query string.
    query_string =dict(updated_since='2017-01-01T00:00:00Z',
                       order_by='created_at',
                       order_type='desc',
                       per_page='100',
                       include='stats'
    )
    # Firecares url
    fd_groups = create_fd_groups(api_key)
    # Create all queries
    responses = [get_firecares_response(page, query_string, api_key)
                 for page in number_pages]
    # Remove empty lists.
    responses = [r for r in responses if len(r) != 0]

    # Make a single list.
    responses = [r for sublist in responses for r in sublist]
    df = pd.DataFrame(responses)
    statuses = {
        2: 'open',
        3: 'pending',
        4: 'resolved',
        5: 'closed'
    }
    # Lambda functions.
    df['status_name'] = df['status'].apply(lambda x: statuses[x])
    df['assigned_group'] = df['group_id'].apply(lambda x: fd_groups.get(x,
                                                          'Unassigned'))

    cols = ["id", "subject", "status_name", "assigned_group", "created_at", "updated_at",
            "first_responded_at", "closed_at", "resolved_at"]
    terse_df = df[cols]
    terse_df.to_csv('tickets.csv')


if __name__ == '__main__':
	Main()