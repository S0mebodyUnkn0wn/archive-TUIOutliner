import curses
import datetime
import calendar
from dataclasses import dataclass

from .configs import session_config


@dataclass
class Event:
    text: str
    date: datetime.date
    place: str = None
    time: datetime.time = None

    @property
    def icon(self):
        return session_config.Icons.generic_event_icon

    @property
    def time_str(self):
        if self.time is not None:
            return '{:%H:%M} '.format(self.time)
        else:
            return ""

    def __str__(self):
        return self.text


class EventCalendar:
    event_dict: dict

    def __init__(self, event_dict=None):
        super().__init__()
        if event_dict is None:
            self.event_dict = {}
        else:
            self.event_dict = event_dict

    def add_item(self, new_event: Event):
        if new_event.date in self.event_dict.keys():
            event_list: list[Event] = self.event_dict[new_event.date]
            if new_event.time is None:
                for i in range(len(event_list)):
                    if event_list[i].time is not None or event_list[i].text > new_event.text:
                        event_list.insert(i, new_event)
                        break
                else:
                    event_list.append(new_event)
            else:
                for i in range(len(event_list)):
                    if event_list[i].time is not None and event_list[i].time > new_event.time:
                        event_list.insert(i, new_event)
                        break
                else:
                    event_list.append(new_event)
        else:
            self.event_dict[new_event.date] = [new_event]

    def remove_item(self, date: datetime.date, i: int):
        if date in self.event_dict.keys():
            event_list: list[Event] = self.event_dict[date]
            if 0 < i <= len(event_list):
                event_list.pop(i - 1)

    def set_events(self, new_calendar: dict):
        self.event_dict = new_calendar


if __name__ == '__main__':
    cal = EventCalendar()

'''
class Month:

    year: NotImplemented
    days: tuple
    length: int
    index: int

    @property
    def name(self):
        match self.index:
            case 0:
                return "January"
            case 1:
                return "Febuary"
            case 2:
                return "March"
            case 3:
                return "April"
            case 4:
                return "May"
            case 5:
                return "June"
            case 6:
                return "July"
            case 7:
                return "August"
            case 8:
                return "September"
            case 9:
                return "October"
            case 10:
                return "November"
            case 11:
                return "December"
    

    def day(self, date: int):
        return self.days[date-1]


    def __init__(self, month_in_a_year: int):
        self.index=month_in_a_year-1
        datetime.date.

class Day:

    month: Month
    events: NotImplemented
    date: int
    index: int

    @property
    def name(self):
        match self.index % 7:
            case 0:
                return "Monday"
            case 1:
                return "Tuesday"
            case 2:
                return "Wednesday"
            case 3:
                return "Thursday"
            case 4:
                return "Friday"
            case 5:
                return "Saturday"
            case 6:
                return "Sunday"
'''
