# (c) Copyright 2014-2016 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import logging

from pprint import pformat

from cliff.lister import Lister
from cliff.show import ShowOne

from freezerclient import exceptions
from freezerclient.utils import prepare_search


logging = logging.getLogger(__name__)


class BackupShow(ShowOne):
    """Show the metadata of a single backup"""
    def get_parser(self, prog_name):
        parser = super(BackupShow, self).get_parser(prog_name)
        parser.add_argument(dest='backup_uuid',
                            help='UUID of the backup')
        return parser

    def take_action(self, parsed_args):
        # due to the fact that a backup_id is composed of several strings
        # some of them may include a slash "/" so it will never find the
        # correct backup, so the workaround for this version is to use the
        # backup_uuid as a filter for the search. this won't work when the
        # user wants to delete a backup, but that functionality is yet to be
        # provided by the api.
        search = {"match": [{"backup_uuid": parsed_args.backup_uuid}, ], }
        backup = self.app.client.backups.list(search=search)

        if not backup:
            raise exceptions.ApiClientException('Backup not found')

        backup = backup[0]

        column = (
            'Backup ID',
            'Backup UUID',
            'Metadata'
        )
        data = (
            backup.get('backup_id'),
            backup.get('backup_uuid'),
            pformat(backup.get('backup_metadata'))
        )
        return column, data


class BackupList(Lister):
    """List all backups for your user"""
    def get_parser(self, prog_name):
        parser = super(BackupList, self).get_parser(prog_name)

        parser.add_argument(
            '--limit',
            dest='limit',
            default=100,
            help='Specify a limit for search query',
        )

        parser.add_argument(
            '--offset',
            dest='offset',
            default=0,
            help='',
        )

        parser.add_argument(
            '--search',
            dest='search',
            default='',
            help='Define a filter for the query',
        )
        return parser

    def take_action(self, parsed_args):
        search = prepare_search(parsed_args.search)

        backups = self.app.client.backups.list(limit=parsed_args.limit,
                                               offset=parsed_args.offset,
                                               search=search)
        return (('Backup UUID', 'Hostname', 'Path', 'Created at', 'Level'),
                ((b.get('backup_uuid'),
                  b.get('backup_metadata', {}).get('hostname'),
                  b.get('backup_metadata', {}).get('path_to_backup'),
                  datetime.datetime.fromtimestamp(
                      int(b.get('backup_metadata', {}).get('time_stamp'))),
                  b.get('backup_metadata', {}).get('curr_backup_level')
                  ) for b in backups))
