import datetime
import unittest


class MyTestCase(unittest.TestCase):
    def test_timetable_addition(self):
        timetable = Timetable()
        start_time = datetime.datetime.now()
        new_item = TimeTableItem(start_time,start_time, "Test")

        timetable.add_item(new_item)

        print(timetable.daytables_by_date)
        self.assertEqual(timetable.daytables_by_date[start_time.date()][0], new_item)

    def test_timetable_ordered_addition(self):
        timetable = Timetable()
        start_time_1 = datetime.datetime.now().replace(hour=10)
        new_item_1 = TimeTableItem(start_time_1, start_time_1, "Test")

        start_time_2 = datetime.datetime.now().replace(hour=5)
        new_item_2 = TimeTableItem(start_time_2, start_time_1, "Test")

        timetable.add_item(new_item_1)
        timetable.add_item(new_item_2)

        print(timetable.daytables_by_date)
        self.assertEqual(timetable.daytables_by_date[start_time_1.date()][0], new_item_2)


if __name__ == '__main__':
    unittest.main()
