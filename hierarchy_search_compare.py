# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 13:56:25 2022

Program to test the performance difference of package_show and package_search
with an explicit field list to return in the search results.

@author: Keith.Tucker
"""
import getpass
import logging
import os
import sys
import timeit
from collections import OrderedDict

import ckanapi

def encapsulate(func, *args, **kwargs):
    def encapsulated():
        return func(*args, **kwargs)
    return encapsulated

def get_relationships_from_api(connection,
                               package_id,
                               relationship_type,
                               hierarchy=None,
                               i=1):
    relationships = []

    if hierarchy is None:
        hierarchy = list()

    try:
        relationships = connection.call_action(action='package_relationships_list',
                                              data_dict = {'id': package_id, 'rel': relationship_type})

    except ckanapi.errors.NotFound:
        logging.info('No %s relationships found for %s',
            relationship_type,
            package_id
        )
        return hierarchy

    if relationship_type == 'parent_of':
        hierarchy += [
            {'name': c['object'], 'parent': c['subject'], 'level': i}
            for c in relationships
        ]
        i += 1

        for child in relationships:
            get_relationships_from_api(
                connection,
                child['object'],
                relationship_type,
                hierarchy,
                i
            )
        return hierarchy

    else:
        return get_relationships_from_api(
            connection,
            relationships[0]['object'],
            relationship_type,
            relationships
        )

def remove_private_relationships_show(connection, relationships, hierarchy=False):

    for relationship in relationships:
        if hierarchy is False:
            package_id = relationship.get('id')

            try:
                connection.call_action(action='package_show', data_dict={'id': package_id})
            except ckanapi.errors.NotAuthorized:
                relationships.remove(relationship)
        else:
            relationship_object = relationship.get('object')
            relationship_subject = relationship.get('subject')

            try:
                connection.call_action(action='package_show', data_dict={'id': relationship_object})
                connection.call_action(action='package_show', data_dict={'id': relationship_subject})
            except ckanapi.errors.NotAuthorized:
                relationships.remove(relationship)

    return relationships

def get_hierarchy_show(connection, data_dict):
    package_id = data_dict.get('id')

    top_level_parent = get_relationships_from_api(
        connection,
        package_id,
        'child_of'
    )

    top_level_parent = remove_private_relationships_show(connection, top_level_parent, True)

    if isinstance(top_level_parent, list):
        if not top_level_parent or top_level_parent[0].get('object') is None:
            top_level_parent_id = connection.call_action(action='package_show', data_dict= {'id': package_id}).get('name')
        else:
            top_level_parent_id = top_level_parent[0].get('object')

        hierarchy = [
            {'name': top_level_parent_id, 'parent': None, 'level': 0}
        ] + get_relationships_from_api(
            connection,
            top_level_parent_id,
            'parent_of'
        )
        
        lowest_level = max([level['level'] for level in hierarchy])
        nested_hierarchy = {}

        for i in range(lowest_level, -1, -1):
            tmp_nested_hierarchy = {}

            current_level = [
                relationship for relationship in hierarchy
                if relationship['level'] == i
            ]

            for relationship in current_level:
                cur_pkg = {}

                try:
                    cur_pkg = connection.call_action(action='package_show', data_dict={'id': relationship['name']})
                except ckanapi.NotFound:
                    logging.debug('Unable to retrieve package for name: {}'
                              .format(relationship['name']))

                if cur_pkg.get('type') != 'dataset':
                    continue

                updated_hierarchy = OrderedDict({
                    relationship['name']: OrderedDict([
                        ('title', cur_pkg.get('title')),
                        ('level', relationship['level']),
                        ('parent', relationship['parent']),
                        ('children', nested_hierarchy.get(
                            relationship['name']
                        ))
                    ])
                })

                if relationship['parent'] in tmp_nested_hierarchy:
                    tmp_nested_hierarchy[relationship['parent']].update(
                        updated_hierarchy)
                elif i > 0:
                    tmp_nested_hierarchy[relationship['parent']] = \
                        updated_hierarchy
                else:
                    tmp_nested_hierarchy = updated_hierarchy

            nested_hierarchy = tmp_nested_hierarchy

        return nested_hierarchy

def remove_private_relationships_search(connection, relationships, hierarchy=False):

    for relationship in relationships:
        if hierarchy is False:
            package_id = relationship.get('id')

            try:
                connection.call_action(action='package_search', data_dict={'q':'name:' + package_id, 'fl': 'id,name'})
            except ckanapi.errors.NotAuthorized:
                relationships.remove(relationship)
        else:
            relationship_object = relationship.get('object')
            relationship_subject = relationship.get('subject')

            try:
                connection.call_action(action='package_search', data_dict={'q':'name:' + relationship_object, 'fl':'id,name'})
                connection.call_action(action='package_search', data_dict={'q':'name:' + relationship_subject, 'fl': 'id,name'})
            except ckanapi.errors.NotAuthorized:
                relationships.remove(relationship)

    return relationships

def get_hierarchy_search(connection, data_dict):
    package_id = data_dict.get('id')

    top_level_parent = get_relationships_from_api(
        connection,
        package_id,
        'child_of'
    )

    top_level_parent = remove_private_relationships_search(connection, top_level_parent, True)

    if isinstance(top_level_parent, list):
        if not top_level_parent or top_level_parent[0].get('object') is None:
            top_level_parent_id = connection.call_action(action='package_search', data_dict= {'q':'name:' + package_id, 'fl':'id,name'}).get('name')
        else:
            top_level_parent_id = top_level_parent[0].get('object')

        hierarchy = [
            {'name': top_level_parent_id, 'parent': None, 'level': 0}
        ] + get_relationships_from_api(
            connection,
            top_level_parent_id,
            'parent_of'
        )
        
        lowest_level = max([level['level'] for level in hierarchy])
        nested_hierarchy = {}

        for i in range(lowest_level, -1, -1):
            tmp_nested_hierarchy = {}

            current_level = [
                relationship for relationship in hierarchy
                if relationship['level'] == i
            ]

            for relationship in current_level:
                cur_pkg = {}

                try:
                    cur_pkg = connection.call_action(action='package_search', data_dict={'q':'name:' + relationship['name'], 'fl': 'id, name'})
                except ckanapi.NotFound:
                    logging.debug('Unable to retrieve package for name: {}'
                              .format(relationship['name']))

                if cur_pkg.get('type') != 'dataset':
                    continue

                updated_hierarchy = OrderedDict({
                    relationship['name']: OrderedDict([
                        ('title', cur_pkg.get('title')),
                        ('level', relationship['level']),
                        ('parent', relationship['parent']),
                        ('children', nested_hierarchy.get(
                            relationship['name']
                        ))
                    ])
                })

                if relationship['parent'] in tmp_nested_hierarchy:
                    tmp_nested_hierarchy[relationship['parent']].update(
                        updated_hierarchy)
                elif i > 0:
                    tmp_nested_hierarchy[relationship['parent']] = \
                        updated_hierarchy
                else:
                    tmp_nested_hierarchy = updated_hierarchy

            nested_hierarchy = tmp_nested_hierarchy

        return nested_hierarchy

if __name__ == '__main__':

    url = os.getenv('ED_CKAN_URL', None)
    api_key = os.getenv('ED_CKAN_KEY', None)
    iterations = 1

    errors = []

    if not url:
        url = raw_input('Enter CKAN URL:')
    if not api_key:
        api_key = getpass.getpass('Enter CKAN API key:')

    remote = ckanapi.RemoteCKAN(url, api_key)
    
    id = ''
    if len(sys.argv) > 1:
        id = sys.argv[1]
    else:
        id = raw_input('Enter dataset identifier:')

    using_show = encapsulate(get_hierarchy_show, remote, data_dict={'id':id})
    using_show_timing = timeit.timeit(stmt=using_show, number=iterations)
    
    using_search = encapsulate(get_hierarchy_search, remote, data_dict={'id':id})
    using_search_timing = timeit.timeit(stmt=using_search, number=iterations)
    
    print('Time using show: {} seconds'.format(using_show_timing))
    print('Time using search: {} seconds'.format(using_search_timing))

