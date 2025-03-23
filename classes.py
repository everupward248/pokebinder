class Binder:
    def __init__(self, sheets, rows, columns):

        self.sheets = sheets
        self.rows = rows
        self.columns = columns
        self.pages = sheets * 2
        self.slots = self.pages * self.rows * self.columns