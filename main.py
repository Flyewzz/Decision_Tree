import mysql.connector


class Tree:
    def __init__(self, _settings, result_column):
        self.connect = mysql.connector.connect(user=settings['user'], password=settings['password'],
                                               host=settings['host'], database=settings['database'])
        self.settings = _settings
        self.db = self.connect.cursor()
        self.result_column = result_column
        self.result_values = set()
        self.db.execute("SELECT DISTINCT %s FROM %s " % (result_column, _settings['table']))
        [self.result_values.add(row[0]) for row in self.db]
        self.db.execute("SELECT COUNT(*)/(SELECT COUNT(*) FROM %s) FROM Tennis"
                        " GROUP BY %s" % (_settings['table'], result_column))
        self.globEntropy = Tree.entropy(float(row[0]) for row in self.db)
        self.db.execute("SELECT COUNT(*) FROM %s" % self.settings['table'])
        self.count_of_rows = 0
        for row in self.db:
            self.count_of_rows = row[0]

    def get_glob_entropy(self):
        return self.globEntropy

    # def gain(self, SpA):
    #     return self.globEntropy - sum(map(lambda prob: prob * Tree.entropy(prob), SpA))

    @staticmethod
    def entropy(probabilities):
        from math import log2
        result = 0
        for probability in probabilities:
            result -= probability * log2(probability)
        return result

    def calculate_gains(self):
        columns = set()
        self.db.execute("SHOW COLUMNS FROM %s" % self.settings['table'])
        [columns.add(row[0]) for row in self.db]
        columns.remove('Day')
        columns.remove(self.result_column)
        gains = dict()
        for column in columns:
            self.db.execute("SELECT DISTINCT %s  FROM %s" % (column, self.settings['table']))
            print('Column %s:' % column)
            gain = self.globEntropy
            values = set()
            [values.add(row[0]) for row in self.db]
            print('Values: ', ' '.join(values))
            print('|Attribute|Result|')
            for value in values:
                print('Value %s' % value, ':')
                current_table = "SELECT COUNT(*) FROM %s WHERE %s = '%s'" \
                                % (self.settings['table'], column, value)
                self.db.execute(current_table)
                value_part = 0
                for row in self.db:
                    value_part = row[0] / self.count_of_rows
                probabilities = list()
                for result_value in self.result_values:
                    self.db.execute("SELECT COUNT(*)/(%s) FROM %s WHERE %s = '%s' AND %s = '%s' GROUP BY %s"
                                    % (current_table, self.settings['table'], column, value,
                                       self.result_column, result_value, self.result_column))
                    for row in self.db:
                        print(result_value, ':', row[0])
                        probabilities.append(float(row[0]))
                gain -= value_part * Tree.entropy(probabilities)

            gains[column] = gain
        for key in gains:
            print(key, ' --- ', gains[key])

        def get_max(dictionary):
            mx = max(dictionary.values())
            for index in dictionary.keys():
                if dictionary[index] == mx:
                    break
            return index
        print('Root is', get_max(gains))

    def clear(self):
        self.db.close()


settings = {
    'user': 'root',
    'password': '123',
    'host': 'localhost',
    'database': 'Tennis',
    'table': 'Tennis',
}
tree = Tree(settings, 'Decision')
print(tree.get_glob_entropy())
tree.calculate_gains()
tree.clear()

