from django.db import connection
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = "Compute and load collocation data into the database"

    def handle(self, *args, **options):
        self.stdout.write("Correcting collation")
        cursor = connection.cursor()
        cursor.execute('SHOW TABLES')
        results=[]
        for row in cursor.fetchall(): results.append(row)
        for row in results: cursor.execute('ALTER TABLE %s CONVERT TO CHARACTER SET utf8 COLLATE     utf8_general_cs;' % (row[0]))
